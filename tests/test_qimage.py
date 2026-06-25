"""qimage_from_pil must stay pixel-correct after dropping the PNG round-trip."""

from PIL import Image

from furniture_cutout import image_processing as ip


def test_rgba_pixels_preserved(qapp):
    im = Image.new("RGBA", (4, 3), (10, 20, 30, 128))
    im.putpixel((1, 2), (200, 100, 50, 255))

    q = ip.qimage_from_pil(im)

    assert (q.width(), q.height()) == (4, 3)
    assert q.pixelColor(0, 0).getRgb() == (10, 20, 30, 128)
    assert q.pixelColor(1, 2).getRgb() == (200, 100, 50, 255)


def test_rgb_becomes_opaque(qapp):
    im = Image.new("RGB", (2, 2), (7, 8, 9))

    q = ip.qimage_from_pil(im)

    assert (q.width(), q.height()) == (2, 2)
    assert q.pixelColor(0, 0).getRgb() == (7, 8, 9, 255)


def test_qimage_owns_its_memory(qapp):
    """The returned QImage must survive the source PIL/bytes being dropped."""
    q = ip.qimage_from_pil(Image.new("RGBA", (5, 5), (1, 2, 3, 4)))
    # Force some churn; if the QImage still pointed at freed bytes this would
    # read garbage. .copy() in qimage_from_pil guarantees ownership.
    _churn = [bytearray(1024) for _ in range(64)]
    assert q.pixelColor(4, 4).getRgb() == (1, 2, 3, 4)
    del _churn
