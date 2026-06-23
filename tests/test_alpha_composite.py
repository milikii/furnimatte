"""Tests for RGBA composite correctness: straight alpha, transparent region, semi-transparent."""

import numpy as np
import pytest
from PIL import Image

from furniture_cutout import image_processing as ip


class TestAlphaComposite:
    def test_output_rgba_and_same_size(self):
        rgb = Image.new("RGB", (100, 80), color=(255, 0, 0))
        alpha = np.ones((80, 100), dtype=np.float32) * 0.5
        rgba = ip.compose_rgba(rgb, alpha)
        assert rgba.mode == "RGBA"
        assert rgba.size == (100, 80)

    def test_transparent_region_rgb_zeroed(self):
        """Fully transparent pixels have RGB zeroed."""
        rgb = Image.new("RGB", (50, 50), color=(255, 255, 255))
        alpha = np.zeros((50, 50), dtype=np.float32)
        alpha[10:40, 10:40] = 1.0
        rgba = ip.compose_rgba(rgb, alpha)
        arr = np.array(rgba)
        # Transparent corners
        assert arr[0, 0, 3] == 0
        assert arr[0, 0, 0] == 0
        assert arr[0, 0, 1] == 0
        assert arr[0, 0, 2] == 0
        # Opaque center
        assert arr[25, 25, 3] == 255
        assert arr[25, 25, 0] == 255

    def test_semi_transparent_preserves_rgb(self):
        """Semi-transparent pixels keep original RGB (straight alpha)."""
        rgb = Image.new("RGB", (10, 10), color=(100, 150, 200))
        alpha = np.full((10, 10), 0.5, dtype=np.float32)
        rgba = ip.compose_rgba(rgb, alpha)
        arr = np.array(rgba)
        # RGB unchanged
        assert abs(int(arr[0, 0, 0]) - 100) <= 2
        assert abs(int(arr[0, 0, 1]) - 150) <= 2
        assert abs(int(arr[0, 0, 2]) - 200) <= 2
        # Alpha ~128
        assert abs(int(arr[0, 0, 3]) - 128) <= 1

    def test_alpha_not_binarized(self):
        """Alpha values are continuous, not thresholded to 0/255."""
        rgb = Image.new("RGB", (10, 10), color=(255, 255, 255))
        alpha = np.full((10, 10), 0.3, dtype=np.float32)
        rgba = ip.compose_rgba(rgb, alpha)
        arr = np.array(rgba)
        # Should be ~76, not 0 or 255
        assert abs(int(arr[0, 0, 3]) - 76) <= 1

    def test_varying_alpha(self):
        """Different alpha values preserved."""
        rgb = Image.new("RGB", (20, 20), color=(100, 100, 100))
        alpha = np.zeros((20, 20), dtype=np.float32)
        alpha[0:10, 0:10] = 0.0
        alpha[10:20, 10:20] = 1.0
        alpha[5:15, 5:15] = 0.5
        rgba = ip.compose_rgba(rgb, alpha)
        arr = np.array(rgba)
        assert arr[0, 0, 3] == 0  # transparent
        assert arr[15, 15, 3] == 255  # opaque
        assert abs(int(arr[7, 7, 3]) - 128) <= 1  # semi
