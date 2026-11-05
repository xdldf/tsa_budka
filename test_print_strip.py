"""Local rendering checks only; these tests never submit a print job."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

from print_strip import ROOT, single_cut_job


class StripTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.photos = []
        for index, color in enumerate(((255, 0, 0), (0, 255, 0), (0, 0, 255))):
            path = self.folder / f"photo-{index}.png"
            Image.new("RGB", (800, 1200), color).save(path)
            self.photos.append(str(path))
        # Catch accidental print submission even if preview mode regresses.
        bin_dir = self.folder / "bin"
        bin_dir.mkdir()
        fake_lp = bin_dir / "lp"
        fake_lp.write_text('#!/bin/sh\ntouch "$PRINT_SENTINEL"\nexit 99\n')
        fake_lp.chmod(0o755)
        self.env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}",
                        PRINT_SENTINEL=str(self.folder / "PRINT_WAS_SENT"))

    def invoke(self, photos):
        return subprocess.run(
            [sys.executable, str(ROOT / "print_strip.py"), *photos,
             "--preview-only", "--output-dir", str(self.folder / "results")],
            env=self.env, capture_output=True, text=True,
        )

    def test_three_photos_render_in_order_with_one_cut_and_no_submission(self):
        result = self.invoke(self.photos)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.folder / "PRINT_WAS_SENT").exists())
        folder, = (self.folder / "results").iterdir()
        with Image.open(folder / "strip.png") as strip:
            self.assertEqual(strip.size, (600, 1200))
            self.assertEqual([strip.getpixel((300, y)) for y in (200, 600, 1000)],
                             [(255, 0, 0), (0, 255, 0), (0, 0, 255)])
        with Image.open(folder / "printer-buffer.png") as preview:
            self.assertEqual(preview.crop((0, 0, 1408, 618)).tobytes(),
                             preview.crop((0, 618, 1408, 1236)).tobytes())
        data = (folder / "print.prn").read_bytes()
        self.assertEqual(data.count(b"020000000000000\r"), 1)
        self.assertNotIn(b"020020000000000\r", data)
        # An already patched file must not silently be accepted as new input.
        with self.assertRaisesRegex(ValueError, "Unexpected cutter"):
            single_cut_job(data)

    def test_bad_photo_never_submits(self):
        broken = self.folder / "broken.jpg"
        broken.write_text("not a photo")
        result = self.invoke([self.photos[0], str(broken), self.photos[2]])
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.folder / "PRINT_WAS_SENT").exists())

    def test_incomplete_printer_data_rejected(self):
        for data in (b"", b"\x1bPIMAGE YPLANE          99999999", b"garbage"):
            with self.subTest(data=data), self.assertRaises(ValueError):
                single_cut_job(data)


if __name__ == "__main__":
    unittest.main()
