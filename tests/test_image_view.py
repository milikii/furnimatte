"""ImageView fit-to-window, coordinate mapping, and re-fit gating."""

from PIL import Image
from PySide6.QtCore import QPoint, QSize
from PySide6.QtGui import QResizeEvent

from furniture_cutout.image_view import ImageView


def _make_view(qapp, w, h):
    view = ImageView()
    view.resize(w, h)
    return view


def test_fit_centers_and_scales_down(qapp):
    """A 1200x400 image in a 600x400 view fits to scale 0.5 and centers vertically."""
    view = _make_view(qapp, 600, 400)
    view.set_result(Image.new("RGBA", (1200, 400), (0, 0, 0, 255)))
    view._apply_fit()

    assert view._scale == 0.5  # min(600/1200, 400/400, 1.0)
    # width fills exactly (1200*0.5=600 -> x offset 0); height 400*0.5=200 -> centered
    assert view._offset == QPoint(0, 100)


def test_fit_never_upscales_small_image(qapp):
    """A 100x100 image stays at 1:1 (no blurry upscale) and is centered."""
    view = _make_view(qapp, 600, 400)
    view.set_result(Image.new("RGBA", (100, 100), (0, 0, 0, 255)))
    view._apply_fit()

    assert view._scale == 1.0
    assert view._offset == QPoint(250, 150)


def test_fit_noop_without_image(qapp):
    """_apply_fit must be a harmless no-op when no image is set."""
    view = _make_view(qapp, 600, 400)
    view._scale = 1.0
    view._apply_fit()  # no image -> iw/ih == 0 guard
    assert view._scale == 1.0  # unchanged, no crash


def test_view_to_image_roundtrip_under_zoom_pan(qapp):
    view = _make_view(qapp, 600, 400)
    view._scale = 0.5
    view._offset = QPoint(10, 20)
    # image point (100, 200) -> view (10 + 50, 20 + 100) = (60, 120)
    assert view.view_to_image(QPoint(60, 120)) == QPoint(100, 200)


def test_resize_refits_until_user_takes_control(qapp):
    view = _make_view(qapp, 600, 400)
    view.set_result(Image.new("RGBA", (1200, 400), (0, 0, 0, 255)))
    view._apply_fit()
    assert view._fit_pending is False

    # A resize while still in auto-fit mode should request another fit.
    view.resizeEvent(QResizeEvent(QSize(800, 600), QSize(600, 400)))
    assert view._fit_pending is True

    # Once the user has zoomed/panned, resizing must NOT clobber their view.
    view._apply_fit()
    view._user_zoomed = True
    view.resizeEvent(QResizeEvent(QSize(900, 700), QSize(800, 600)))
    assert view._fit_pending is False


def test_render_applies_fit_end_to_end(qapp):
    """A real paint pass must run fit + the direct-QImage path without crashing."""
    view = _make_view(qapp, 600, 400)
    view.set_result(Image.new("RGBA", (2400, 1600), (255, 0, 0, 255)))
    assert view._fit_pending is True
    view.grab()  # forces paintEvent
    assert view._fit_pending is False
    assert view._scale == 0.25  # min(600/2400, 400/1600) -> whole 4K-ish image visible

