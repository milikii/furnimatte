"""Tests for image mapping: letterbox, unletterbox, expand_box, map_roi_alpha_to_full."""

import numpy as np
from PIL import Image

from furniture_cutout import image_processing as ip


class TestLetterbox:
    def test_letterbox_keeps_aspect_ratio(self):
        """Letterbox output is square, non-stretched content."""
        im = Image.new("RGB", (640, 480))
        padded, scale, pl, pt = ip.letterbox(im, 1024)
        assert padded.size == (1024, 1024)
        # Valid content area should have same aspect ratio as original
        content_w = 1024 - 2 * pl
        content_h = 1024 - 2 * pt
        assert abs(content_w / content_h - 640 / 480) < 0.05

    def test_letterbox_scale(self):
        """Scale factor is correct."""
        im = Image.new("RGB", (640, 480))
        _, scale, _, _ = ip.letterbox(im, 1024)
        assert abs(scale - 1024 / 640) < 1e-6

    def test_unletterbox_size(self):
        """unletterbox returns original dimensions."""
        mask = np.zeros((1024, 1024), dtype=np.float32)
        result = ip.unletterbox_mask(mask, (480, 640), 1024 / 640, (0, 0))
        assert result.shape == (480, 640)

    def test_letterbox_unletterbox_roundtrip(self):
        """Known mask → letterbox → unletterbox preserves rough shape."""
        im = Image.new("RGB", (300, 200))
        padded, scale, pl, pt = ip.letterbox(im, 512)
        # Create a known mask in the model space
        mask = np.zeros((512, 512), dtype=np.float32)
        center = 256
        mask[center - 50 : center + 50, center - 50 : center + 50] = 1.0
        result = ip.unletterbox_mask(mask, (200, 300), scale, (pl, pt))
        assert result.shape == (200, 300)
        # Center area should have high values
        h, w = result.shape
        center_region = result[h // 2 - 10 : h // 2 + 10, w // 2 - 10 : w // 2 + 10]
        assert center_region.mean() > 0.5


class TestBoxCoordinates:
    def test_expand_box_normal(self):
        b = ip.expand_box((100, 100, 50, 50), 0.1, (640, 480))
        assert b[0] >= 0 and b[1] >= 0
        assert b[0] + b[2] <= 640
        assert b[1] + b[3] <= 480
        # Should be larger than original
        assert b[2] >= 50
        assert b[3] >= 50

    def test_expand_box_clamp(self):
        b = ip.expand_box((600, 400, 50, 50), 0.2, (640, 480))
        assert b[0] + b[2] <= 640
        assert b[1] + b[3] <= 480
        assert b[0] >= 0

    def test_map_roi_alpha_to_full_placement(self):
        roi = np.ones((50, 50), dtype=np.float32)
        full = ip.map_roi_alpha_to_full(roi, (100, 100, 50, 50), (640, 480))
        assert full.shape == (480, 640)
        assert full[100:150, 100:150].mean() == 1.0
        assert full[0, 0] == 0.0
        assert full[0, 99] == 0.0  # outside box on left
        assert full[99, 100] == 0.0  # above box

    def test_crop_roi(self):
        im = Image.new("RGB", (640, 480), color=(255, 0, 0))
        roi = ip.crop_roi(im, (100, 100, 50, 50))
        assert roi.size == (50, 50)
