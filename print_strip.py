#!/usr/bin/env python3
"""Build and optionally print one QW410 2x4-inch strip from three photos."""

import argparse
import io
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent
DRIVER = "/usr/lib/cups/driver/gutenprint.5.3"
TWO_CUTS = b"020020000000000\r"
ONE_CUT = b"020000000000000\r"


def make_strip(paths, crop_y):
    strip = Image.new("RGB", (600, 1200))
    for index, path in enumerate(paths):
        with Image.open(path) as source:
            photo = ImageOps.exif_transpose(source).convert("RGB")
            photo = ImageOps.fit(
                photo, (600, 400), Image.Resampling.LANCZOS,
                centering=(0.5, crop_y),
            )
        strip.paste(photo, (0, index * 400))
    return strip


def single_cut_job(data):
    """Patch only the known QW410 layout; reject unexpected driver output.

    The verified driver produces three bottom-up, indexed BMP planes. Their
    first half contains the strip and their second half is blank. Fill both
    halves to cover the region selected by the single-cut command.
    """
    result = bytearray()
    planes = {}
    counts = {}
    offset = 0
    while offset < len(data):
        header = data[offset:offset + 32]
        if len(header) != 32 or header[:2] != b"\x1bP":
            raise ValueError("Invalid or truncated DNP command header")
        size = int(header[24:32].strip() or b"0")
        if size < 0 or offset + 32 + size > len(data):
            raise ValueError("Invalid or truncated DNP command payload")
        command = header[2:24].strip()
        counts[command] = counts.get(command, 0) + 1
        payload = bytearray(data[offset + 32:offset + 32 + size])
        if command == b"CNTRL FULL_CUTTER_SET":
            if payload != TWO_CUTS:
                raise ValueError("Unexpected cutter settings; refusing to print")
            payload[:] = ONE_CUT
        elif command == b"CNTRL QTY" and payload != b"0000001\r":
            raise ValueError("Expected exactly one copy")
        elif command == b"IMAGE MULTICUT" and payload != b"00000047":
            raise ValueError("Expected QW410 4x4 image buffer")
        elif command == b"CNTRL CUTTER":
            raise ValueError("Conflicting cutter command")
        elif command in (b"IMAGE YPLANE", b"IMAGE MPLANE", b"IMAGE CPLANE"):
            if len(payload) < 54 or payload[:2] != b"BM":
                raise ValueError("Invalid BMP plane")
            pixel_offset = struct.unpack_from("<I", payload, 10)[0]
            width, height = struct.unpack_from("<ii", payload, 18)
            bits = struct.unpack_from("<H", payload, 28)[0]
            compression = struct.unpack_from("<I", payload, 30)[0]
            if (width, height, bits, compression) != (1408, 1236, 8, 0):
                raise ValueError("Driver image layout changed; refusing to print")
            half_bytes = 1408 * 618
            if pixel_offset < 54 or pixel_offset + 2 * half_bytes != len(payload):
                raise ValueError("Unexpected BMP pixel boundaries")
            blank = payload[pixel_offset + half_bytes:]
            if any(value != 255 for value in blank):
                raise ValueError("Image was rotated or scaled unexpectedly")
            payload[pixel_offset + half_bytes:] = payload[
                pixel_offset:pixel_offset + half_bytes
            ]
            with Image.open(io.BytesIO(payload)) as plane:
                planes[command] = ImageOps.invert(plane.convert("L"))
        result.extend(header)
        result.extend(payload)
        offset += 32 + size
    required = (
        b"CNTRL FULL_CUTTER_SET", b"CNTRL QTY", b"IMAGE MULTICUT",
        b"IMAGE YPLANE", b"IMAGE MPLANE", b"IMAGE CPLANE", b"CNTRL START",
    )
    if any(counts.get(command) != 1 for command in required):
        raise ValueError("Missing or duplicate required DNP command")
    if command != b"CNTRL START":
        raise ValueError("DNP job must end with START")
    preview = Image.merge("RGB", tuple(
        planes[b"IMAGE " + color + b"PLANE"] for color in (b"C", b"M", b"Y")
    ))
    return bytes(result), preview


def run(command, **kwargs):
    completed = subprocess.run(command, capture_output=True, **kwargs)
    if completed.returncode:
        error = completed.stderr.decode(errors="replace")
        raise RuntimeError(f"{Path(command[0]).name} failed:\n{error[-3000:]}")
    return completed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("photos", nargs=3, type=Path, metavar="PHOTO")
    parser.add_argument("--preview-only", "--dry-run", action="store_true",
                        help="create the preview and printer file without printing")
    parser.add_argument("--printer", default="DP-QW410", help="local QW410 queue name")
    parser.add_argument("--server", default="/run/cups/cups.sock",
                        help="local CUPS server/socket")
    parser.add_argument("--crop-y", type=float, default=0.12,
                        help="vertical crop anchor: 0=top, 0.5=center, 1=bottom (default: 0.12)")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "output" / "strips",
                        help="parent directory for unique output folders")
    args = parser.parse_args()
    if not 0 <= args.crop_y <= 1:
        parser.error("--crop-y must be between 0 and 1")
    for path in args.photos:
        if not path.is_file():
            parser.error(f"photo not found: {path}")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", args.printer):
        parser.error("invalid printer queue name")
    cupsfilter = shutil.which("cupsfilter") or "/usr/sbin/cupsfilter"
    if not Path(DRIVER).is_file() or not Path(cupsfilter).is_file():
        raise RuntimeError("CUPS and the Gutenprint 5.3 QW410 driver are required")
    if not args.preview_only:
        ppd = Path("/etc/cups/ppd") / f"{args.printer}.ppd"
        if not ppd.is_file() or not re.search(
            r'^\*StpDriverName:\s*"dnp-qw410"\s*$', ppd.read_text(), re.MULTILINE
        ):
            raise RuntimeError("Destination is not a verified local Gutenprint QW410 queue")
        run(["lpstat", "-h", args.server, "-p", args.printer])

    args.output_dir.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="strip-", dir=args.output_dir.resolve()))
    strip = make_strip(args.photos, args.crop_y)
    strip.save(folder / "strip.png", dpi=(300, 300))
    canvas = Image.new("RGB", (1200, 1200), "white")
    canvas.paste(strip, (0, 0))
    canvas.save(folder / "driver-input.png", dpi=(300, 300))
    # Regenerate in C locale: the installed PPD had decimal commas.
    env = dict(os.environ, LC_ALL="C", LANG="C")
    clean_ppd = run([DRIVER, "cat", "gutenprint.5.3://dnp-qw410/expert"], env=env)
    ppd_path = folder / "qw410.ppd"
    ppd_path.write_bytes(clean_ppd.stdout)
    rendered = run([
        cupsfilter, "-p", str(ppd_path), "-e", "-m", "printer/foo",
        "-o", "PageSize=w288h288-div2", "-o", "Resolution=300dpi",
        "-o", "orientation-requested=3", "-o", "fit-to-page",
        "-o", "StpiShrinkOutput=Expand", str(folder / "driver-input.png"),
    ], env=env)
    (folder / "render.log").write_bytes(rendered.stderr)
    job, buffer_preview = single_cut_job(rendered.stdout)
    job_path = folder / "print.prn"
    job_path.write_bytes(job)
    buffer_preview.save(folder / "printer-buffer.png")
    print(f"Strip preview: {folder / 'strip.png'}", flush=True)
    print(f"Printer file:  {job_path}", flush=True)
    if args.preview_only:
        print("Preview only: nothing sent to the printer.")
        return
    submitted = run([
        "lp", "-h", args.server, "-d", args.printer, "-n", "1",
        "-t", "Single 2x4 photo strip", "-o", "raw", str(job_path),
    ])
    print(submitted.stdout.decode(errors="replace").strip())
    print("Submitted once. Physical output is not verified; no automatic retries.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
