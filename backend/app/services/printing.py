import asyncio
import shlex
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from app.core.booth_config import PrintConfig


class PrintService:
    async def print_image(self, image: Path) -> None:
        raise NotImplementedError


class LPPrintService(PrintService):
    """Prints a generated image to a CUPS queue (the DNP QW410 photo printer).

    Before submitting, the image is re-rendered to the exact printable area of
    the page (from the high-level [print] config) so the printer gets a raster
    sized precisely for the paper. Depending on `fit`:
      * "fit"  — the ENTIRE image is visible, centered (may leave borders if
                 the image aspect differs from the paper);
      * "fill" — the image fills the whole paper edge-to-edge (overhanging
                 parts are cropped).
    """

    def __init__(self, config: PrintConfig):
        self.config = config

    def _compensate_overscan(self, page: Image.Image) -> Image.Image:
        """Pre-compensate the Gutenprint/DNP borderless overscan.

        The QW410 borderless path enlarges the raster by ~x(1+overscan) and the
        paper shows the center-cropped window, so a few px per edge of the photo
        get lost.  We pre-shrink the photo to 1/(1+overscan) of the page, center
        it, and fill the outer ring with replicated edge pixels (sacrificial
        bleed).  After the driver's enlarge+crop the visible photo is the full
        original at 1:1, edge-to-edge, with no white border.
        """
        overscan = self.config.borderless_overscan
        if overscan < 0:
            # Negative values intentionally add a white safety frame around
            # the photo.  This keeps every pixel inside the printable area
            # when the driver trims an unpredictable borderless edge.
            margin = 1.0 + overscan
            if margin <= 0:
                return page
            content = page.resize((round(page.width * margin), round(page.height * margin)), Image.LANCZOS)
            canvas = Image.new("RGB", page.size, "white")
            canvas.paste(content, ((page.width - content.width) // 2, (page.height - content.height) // 2))
            return canvas
        if overscan == 0:
            return page
        page_w, page_h = page.size
        f = 1.0 + overscan
        cw, ch = round(page_w / f), round(page_h / f)
        if (cw, ch) >= (page_w, page_h):
            return page
        content = page.resize((cw, ch), Image.LANCZOS)
        mx, my = (page_w - cw) // 2, (page_h - ch) // 2
        canvas = Image.new("RGB", (page_w, page_h))

        def band(box: tuple[int, int, int, int], size: tuple[int, int], at: tuple[int, int]) -> None:
            if size[0] > 0 and size[1] > 0:
                canvas.paste(content.crop(box).resize(size, Image.NEAREST), at)

        band((0, 0, 1, ch), (mx, ch), (0, my))                      # left
        band((cw - 1, 0, cw, ch), (page_w - cw - mx, ch), (mx + cw, my))  # right
        band((0, 0, cw, 1), (cw, my), (mx, 0))                     # top
        band((0, ch - 1, cw, ch), (cw, page_h - ch - my), (mx, my + ch))  # bottom
        band((0, 0, 1, 1), (mx, my), (0, 0))                       # corners
        band((cw - 1, 0, cw, 1), (page_w - cw - mx, my), (mx + cw, 0))
        band((0, ch - 1, 1, ch), (mx, page_h - ch - my), (0, my + ch))
        band((cw - 1, ch - 1, cw, ch), (page_w - cw - mx, page_h - ch - my), (mx + cw, my + ch))
        canvas.paste(content, (mx, my))
        return canvas

    def _fit_to_page(self, image: Path) -> Path:
        cfg = self.config
        page_w, page_h, page_dpi = cfg.width_px, cfg.height_px, cfg.dpi

        with Image.open(image) as src:
            src = src.convert("RGB")
            if src.size == (page_w, page_h):
                # Pixel-perfect fast path: the image is already the exact paper
                # raster (1200x1800 at 300 dpi) produced by normalize_to_paper.
                page = src
            else:
                # Fallback: image does not match paper size (e.g. legacy saves,
                # manual tests).  Preserve the configured fit/fill behaviour
                # while still producing a raster exactly page_w x page_h.
                page = Image.new("RGB", (page_w, page_h), "white")

                if cfg.fit == "fill":
                    # Scale to fully cover the page, then center-crop the excess.
                    scale = max(page_w / src.width, page_h / src.height)
                    resized = src.resize(
                        (round(src.width * scale), round(src.height * scale)),
                        Image.LANCZOS,
                    )
                    px = (resized.width - page_w) // 2
                    py = (resized.height - page_h) // 2
                    page.paste(resized.crop((px, py, px + page_w, py + page_h)), (0, 0))
                else:
                    # "fit": scale to fit within the page, preserve aspect, centered.
                    src.thumbnail((page_w, page_h), Image.LANCZOS)
                    if src.width < page_w or src.height < page_h:
                        px = (page_w - src.width) // 2
                        py = (page_h - src.height) // 2
                        page.paste(src, (px, py))
                    else:
                        page = src

        page = self._compensate_overscan(page)
        tmp = Path(tempfile.mkstemp(suffix=".png", prefix="booth_print_")[1])
        page.save(tmp, "PNG", dpi=(page_dpi, page_dpi))
        return tmp

    async def print_image(self, image: Path) -> None:
        cfg = self.config
        if not cfg.enabled:
            return
        if not image.exists():
            raise FileNotFoundError(image)

        with Image.open(image) as source:
            if source.size == (1200, 1200):
                cfg = self.config.model_copy(update={"media": "w288h288", "width_px": 1200, "height_px": 1200, "dpi": 300})
        fitted = LPPrintService(cfg)._fit_to_page(image)

        command = ["lp", "-d", cfg.queue, "-o", f"media={cfg.media}"]

        # The raster produced above is already the EXACT paper size
        # (width_px x height_px pixels at `dpi`), so submit it at natural size:
        # NO `scaling`, NO `fit-to-page`, NO `StpiShrinkOutput` overrides.
        # Any of those makes CUPS/Gutenprint re-render the image onto the PPD
        # page box (on the QW410 the stock PPD uses a 337.92x440.64pt borderless
        # overscan box instead of the real 288x432pt paper) and the driver
        # zooms/crops the photo.  1:1 pixel-to-paper is guaranteed by the PPD
        # geometry fix in scripts/setup-printer.sh, which rewrites
        # PageSize/PageRegion/PaperDimension/ImageableArea of w288h432 to
        # 288x432pt so the CUPS raster is exactly 1200x1800 at 300 dpi.
        for opt in shlex.split(cfg.options):
            command.append("-o")
            command.append(opt)

        command.append(str(fitted))

        def run() -> None:
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=cfg.timeout)
                if result.returncode != 0:
                    raise RuntimeError(f"lp failed ({result.returncode}): {result.stderr.strip() or result.stdout.strip()}")
                print(f"[BOOTH] printed {image.name} via {cfg.queue}", flush=True)
            finally:
                fitted.unlink(missing_ok=True)

        await asyncio.to_thread(run)


class DemoPrintService(PrintService):
    async def print_image(self, image: Path) -> None:
        if not image.exists():
            raise FileNotFoundError(image)


def build_print_service(config: PrintConfig | None = None) -> PrintService:
    from app.core.booth_config import booth_config

    config = config or booth_config.print
    return LPPrintService(config)
