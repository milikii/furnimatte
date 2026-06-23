"""Tests for box coordinate handling."""

import pytest
from PIL import Image

from furniture_cutout import image_processing as ip


class TestSmallBoxProtection:
    """Small box (<50px) detection is done in main_window, but geometry must be correct."""

    def test_expand_small_box(self):
        """expand_box on a small box should still work geometrically,
        main_window rejects <50 pixels separately."""
        b = ip.expand_box((10, 10, 30, 30), 0.05, (640, 480))
        assert b[2] >= 1  # expanded, still valid
        assert b[0] >= 0 and b[1] >= 0


class TestCoordinateConversion:
    def test_expand_box_zero_padding(self):
        b = ip.expand_box((200, 200, 100, 100), 0, (640, 480))
        assert b == (200, 200, 100, 100)

    def test_expand_box_large_padding(self):
        b = ip.expand_box((200, 200, 100, 100), 0.15, (640, 480))
        # 15% of 100 = 15 per side
        assert b == (185, 185, 130, 130)
