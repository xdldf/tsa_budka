# QW410 single photo strip

Pass three photos in top-to-bottom order. Each is cropped to fill one third
of a 2 × 4 inch (approximately 5 × 10 cm) strip, without white borders.
The default crop favors faces near the top; use `--crop-y 0.5` for a centered crop.

## Print

```bash
python3 print_strip.py photo1.jpg photo2.jpg photo3.jpg
```

This submits **one job, one copy**, directly to the local `DP-QW410` queue.
It does not retry or change the printer's saved settings.

## Preview without printing

```bash
python3 print_strip.py photo1.jpg photo2.jpg photo3.jpg --preview-only
```

Each run creates a unique folder under `output/strips/` containing:

- `strip.png`: the upright strip preview.
- `print.prn`: the exact data prepared for the printer.
- `printer-buffer.png`: the complete printer buffer, with repeated image regions.
- `driver-input.png`, `qw410.ppd`, `render.log`: rendering inputs and diagnostic information.

The full buffer has duplicate content to populate the region selected by the
single-cut command. That is separate from the number of requested output pieces.

## Requirements and status

Linux, Python 3, Pillow, CUPS (`cupsfilter`, `lp`, `lpstat`), and the Gutenprint
5.3 QW410 driver. These dependencies are present on the machine used to build
this script. Install the Python dependency with `python3 -m pip install -r requirements.txt`
if needed. The printer must already be configured in CUPS.

The script regenerates a PPD with decimal points instead of using the malformed
installed PPD. It renders with Gutenprint, verifies the expected image layout,
fills both image-buffer halves, and changes the cutter payload from
`020020000000000\r` to `020000000000000\r`.

**This single-piece cutter setting is experimental.** On this printer it ejected
one blank strip in the first experiment. A corrected job with the image region
filled was then submitted; the physical photo result has not yet been confirmed.
This script reproduces that corrected job's method. It does not establish support
on other firmware versions or promise reduced ribbon consumption.

Unexpected image dimensions, cutter settings, copy counts, and conflicting commands
stop the script before submission. The printed CUPS job ID means the job was
submitted, not that the physical result has been checked. If submission fails,
check the queue before running again to avoid a duplicate print.
