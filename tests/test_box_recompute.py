"""Regression: box-recompute must not race model load (the b33a9c5-class bug).

The full-image path was fixed to rely on the worker's internal _ensure_loaded()
instead of firing request_load() first (request_infer_* drops its task when the
thread isRunning()). The box path had the same latent race; these tests pin the
fixed behavior.
"""

from PIL import Image

from furniture_cutout import main_window as mw
from furniture_cutout.main_window import MainWindow


class _RecorderWorker:
    """Stand-in worker that records which request_* methods get called."""

    def __init__(self):
        self.calls = []
        self.settings = None

    def request_load(self):
        self.calls.append("load")

    def request_infer_full(self, rgb):
        self.calls.append("full")

    def request_infer_box(self, rgb, box):
        self.calls.append(("box", box))


def _window_with_image(qapp):
    win = MainWindow()
    win._worker = _RecorderWorker()
    win.original_rgb = Image.new("RGB", (400, 300), (120, 120, 120))
    win._busy = False
    win._model_loaded = False
    return win


def test_box_path_does_not_call_request_load(qapp):
    win = _window_with_image(qapp)

    win._on_box_drawn(10, 10, 100, 100)

    assert "load" not in win._worker.calls
    assert ("box", (10, 10, 100, 100)) in win._worker.calls


def test_small_box_is_rejected_without_dispatch(qapp, monkeypatch):
    # The <50px branch pops a modal warning; stub it so the test stays headless.
    monkeypatch.setattr(mw.QMessageBox, "warning", lambda *a, **k: None)
    win = _window_with_image(qapp)

    win._on_box_drawn(10, 10, 40, 40)  # < 50px -> rejected

    assert win._worker.calls == []
