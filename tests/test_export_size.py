"""Tests for export size and alpha correctness."""

import os
import tempfile

import numpy as np
import pytest
from PIL import Image

from furniture_cutout import exporter


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    # cleanup
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    os.rmdir(d)


class TestExportSize:
    def test_output_size_matches_original(self, temp_dir):
        src = os.path.join(temp_dir, "test.jpg")
        Image.new("RGB", (200, 150)).save(src)
        rgba = Image.new("RGBA", (200, 150))
        out = exporter.save(rgba, src, temp_dir)
        im = Image.open(out)
        assert im.size == (200, 150)
        assert im.mode == "RGBA"

    def test_no_overwrite_source(self, temp_dir):
        """Output must not be the same file as source."""
        src = os.path.join(temp_dir, "test.jpg")
        Image.new("RGB", (100, 100)).save(src)
        rgba = Image.new("RGBA", (100, 100))
        out = exporter.save(rgba, src, temp_dir)
        assert out != src, "output path must differ from source path"

    def test_collision_renaming(self, temp_dir):
        """If output exists, increment suffix."""
        src = os.path.join(temp_dir, "a.jpg")
        Image.new("RGB", (100, 100)).save(src)
        rgba = Image.new("RGBA", (100, 100))
        out1 = exporter.save(rgba, src, temp_dir)
        assert out1.endswith("_cutout.png")
        out2 = exporter.save(rgba, src, temp_dir)
        assert "_cutout_1" in out2
        out3 = exporter.save(rgba, src, temp_dir)
        assert "_cutout_2" in out3

    def test_alpha_channel_present(self, temp_dir):
        src = os.path.join(temp_dir, "a.jpg")
        Image.new("RGB", (50, 50)).save(src)
        rgba = Image.new("RGBA", (50, 50), (255, 0, 0, 128))
        out = exporter.save(rgba, src, temp_dir)
        im = Image.open(out)
        assert im.mode == "RGBA"
        arr = np.array(im)
        assert arr.shape[2] == 4

    def test_straight_alpha_not_premultiplied(self, temp_dir):
        """Semi-transparent pixel keeps original RGB."""
        src = os.path.join(temp_dir, "a.jpg")
        Image.new("RGB", (10, 10)).save(src)
        rgba = Image.new("RGBA", (10, 10), (100, 150, 200, 128))
        out = exporter.save(rgba, src, temp_dir)
        im = Image.open(out)
        arr = np.array(im)
        # RGB should not be premultiplied (should still be ~100,150,200)
        assert abs(int(arr[0, 0, 0]) - 100) <= 2
        assert abs(int(arr[0, 0, 1]) - 150) <= 2
        assert abs(int(arr[0, 0, 2]) - 200) <= 2
        # Alpha preserved
        assert abs(int(arr[0, 0, 3]) - 128) <= 2

    def test_alpha_mask_save(self, temp_dir):
        alpha = np.zeros((50, 50), dtype=np.float32)
        alpha[10:30, 10:30] = 0.8
        src = os.path.join(temp_dir, "a.jpg")
        Image.new("RGB", (50, 50)).save(src)
        out = exporter.save_alpha(alpha, src, temp_dir)
        assert os.path.exists(out)
        im = Image.open(out)
        assert im.mode == "L"
        assert im.size == (50, 50)
