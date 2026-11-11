from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.core.booth_config import load_booth_config

# Footer graphic composited at the bottom of every photo.
# Rendered full-width as-is so it always spans the whole photo.
FOOTER_GRAPHIC = Path(__file__).resolve().parent.parent / "assets" / "graphics" / "footer.png"


def _parse_aspect(value: str) -> float:
    """Parse 'W:H' (e.g. '2:3') into width/height ratio, defaulting to 2:3."""
    try:
        w, h = value.split(":")
        return float(w) / float(h)
    except (ValueError, AttributeError, ZeroDivisionError):
        return 2.0 / 3.0


def normalize_to_paper(image_path: Path) -> None:
    """Center-crop the image to the configured paper aspect AND resize to the
    exact print pixel size so the on-screen, saved and printed photo are
    pixel-identical (no surprise cropping / zoom at print).

    The image is cropped to ``image.aspect_ratio`` and then resized to
    ``print.width_px × print.height_px`` using LANCZOS.  DPI metadata is
    embedded so CUPS maps pixels 1:1 to paper dots at ``print.dpi``.
    """
    if not image_path.is_file():
        return
    cfg = load_booth_config()
    ratio = _parse_aspect(cfg.image.aspect_ratio)
    target_w, target_h, dpi = cfg.print.width_px, cfg.print.height_px, cfg.print.dpi
    with Image.open(image_path) as im:
        im = im.convert("RGB")
        w, h = im.size
        if w / h - ratio > 1e-3:  # too wide -> crop width
            new_w = round(h * ratio)
            left = (w - new_w) // 2
            im = im.crop((left, 0, left + new_w, h))
        elif ratio - w / h > 1e-3:  # too tall -> crop height
            new_h = round(w / ratio)
            top = (h - new_h) // 2
            im = im.crop((0, top, w, top + new_h))
        # Resize to the exact paper pixel size for 1:1 pixel-to-paper mapping.
        # This guarantees the saved PNG, the on-screen preview and the raster
        # sent to CUPS are the same size – the printer receives 1200×1800 at
        # 300 dpi and prints it at natural size without any zoom/crop.
        if im.size != (target_w, target_h):
            im = im.resize((target_w, target_h), Image.LANCZOS)
        im.save(image_path, "PNG", dpi=(dpi, dpi))


def normalize_to_format(image_path: Path, photo_format: str) -> None:
    """Normalize one generated image for the selected event print format."""
    target = (1200, 1200) if photo_format in {"square", "double_strip"} else (1200, 1800)
    with Image.open(image_path) as source:
        image = source.convert("RGB")
        target_ratio = target[0] / target[1]
        if image.width / image.height > target_ratio:
            width = round(image.height * target_ratio)
            left = (image.width - width) // 2
            image = image.crop((left, 0, left + width, image.height))
        else:
            height = round(image.width / target_ratio)
            top = (image.height - height) // 2
            image = image.crop((0, top, image.width, top + height))
        image.resize(target, Image.LANCZOS).save(image_path, "PNG", dpi=(300, 300))


def compose_double_strip(images: list[Path], output: Path) -> None:
    """Compose six unique square photos as two 2x6 strips on a 4x6 sheet."""
    if len(images) != 6:
        raise ValueError("Double-strip format requires exactly six photos")
    sheet = Image.new("RGB", (1200, 1800), "white")
    for index, path in enumerate(images):
        with Image.open(path) as source:
            cell = source.convert("RGB").resize((600, 600), Image.LANCZOS)
        column, row = divmod(index, 3)
        sheet.paste(cell, (column * 600, row * 600))
    sheet.save(output, "PNG", dpi=(300, 300))


def apply_footer(image_path: Path) -> None:
    """Paste the footer graphic at the bottom of the image, stretched to the
    photo's full width. The image file is modified in place. Runs once on the
    generated result so the on-screen photo, the saved copy and the print all
    share the footer.

    The footer is composited after ``normalize_to_paper`` has already resized
    the photo to the exact print pixel size, so it is rendered at final
    resolution (no double scaling) and the DPI tag is preserved.
    """
    if not image_path.is_file() or not FOOTER_GRAPHIC.is_file():
        return

    cfg = load_booth_config()
    with Image.open(image_path) as base:
        base = base.convert("RGBA")
        page_w, page_h = base.size

        with Image.open(FOOTER_GRAPHIC) as footer:
            footer = footer.convert("RGBA").resize(
                (page_w, round(footer.height * (page_w / footer.width))),
                Image.LANCZOS,
            )

        composite = Image.new("RGBA", (page_w, page_h), (0, 0, 0, 0))
        composite.paste(base, (0, 0))
        composite.alpha_composite(footer, (0, page_h - footer.height))
        composite.convert("RGB").save(image_path, "PNG", dpi=(cfg.print.dpi, cfg.print.dpi))
