"""BiRefNet engine smoke test (skipped without FURNIMATTE_MODEL=1)."""

import numpy as np
import pytest
from PIL import Image


@pytest.mark.model
def test_engine_basic_inference():
    """Load model, infer on synthetic image, verify output shape and range."""
    from furniture_cutout.birefnet_engine import BiRefNetEngine  # noqa: PLC0415

    eng = BiRefNetEngine(num_threads=2)
    eng.load()
    assert eng.is_loaded

    # Small synthetic image (model will resize internally)
    im = Image.new("RGB", (512, 384), color=(128, 128, 128))
    # Draw a white rectangle
    for x in range(100, 300):
        for y in range(50, 200):
            im.putpixel((x, y), (255, 255, 255))

    alpha = eng.infer(im)
    assert isinstance(alpha, np.ndarray)
    assert alpha.shape == (384, 512), f"Expected (384,512) got {alpha.shape}"
    assert alpha.dtype == np.float32
    assert alpha.min() >= 0.0 and alpha.max() <= 1.0
    # Should not be uniform (there IS content)
    assert alpha.std() > 0.01, "Alpha too uniform, inference probably failed"

    # Second call should reuse loaded model
    alpha2 = eng.infer(im)
    assert alpha2.shape == (384, 512)
