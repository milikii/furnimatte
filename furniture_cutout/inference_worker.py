"""InferenceWorker: QThread background thread for model loading and inference."""

from __future__ import annotations

import time
import traceback

from PySide6.QtCore import QThread, Signal

from furniture_cutout import image_processing as ip
from furniture_cutout.birefnet_engine import BiRefNetEngine, EngineError
from furniture_cutout.settings import Settings, resolve_cpu_threads


class InferenceWorker(QThread):
    """Background worker for BiRefNet model loading and inference.

    Lives in a QThread. Communicates via signals.
    Model is loaded once; inference can be requested multiple times.
    """

    status = Signal(str)
    progress = Signal(str)
    finished = Signal(object)  # dict with keys: rgba, alpha, elapsed, mode
    failed = Signal(str, str, str)  # kind, message, traceback_str

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._engine = None
        self._task = None

    def request_load(self) -> None:
        """Request model load (async)."""
        if self._engine is not None:
            return
        self._task = {"op": "load"}
        if not self.isRunning():
            self.start()

    def request_infer_full(self, rgb_pil) -> None:
        """Request full-image inference."""
        if self.isRunning():
            return
        self._task = {"op": "full", "rgb": rgb_pil}
        self.start()

    def request_infer_box(self, rgb_pil, box: tuple[int, int, int, int]) -> None:
        """Request box-region inference."""
        if self.isRunning():
            return
        self._task = {"op": "box", "rgb": rgb_pil, "box": box}
        self.start()

    def run(self):
        task = self._task
        if task is None:
            return

        op = task.get("op", "")

        try:
            if op == "load":
                self._do_load()
            elif op == "full":
                self._do_infer_full(task["rgb"])
            elif op == "box":
                self._do_infer_box(task["rgb"], task["box"])
        except EngineError as e:
            self.failed.emit(e.kind, e.message, traceback.format_exc())
        except MemoryError:
            self.failed.emit(
                "oom", "内存不足，请尝试较小图片或关闭其他程序。", traceback.format_exc()
            )
        except Exception as e:
            self.failed.emit("inference", f"推理失败：{str(e)}", traceback.format_exc())

    def _do_load(self):
        self.status.emit("正在加载模型…")
        num_threads = resolve_cpu_threads(self.settings)
        cache_dir = self.settings.model_cache_dir or None
        eng = BiRefNetEngine(
            model_id=self.settings.model_id,
            cache_dir=cache_dir,
            num_threads=num_threads,
        )
        eng.load()
        self._engine = eng
        self.status.emit("模型就绪 ✓")

    def _do_infer_full(self, rgb_pil):
        self._ensure_loaded()
        self.status.emit("正在推理（整图）…")
        t0 = time.time()
        alpha = self._engine.infer(rgb_pil)
        rgba = ip.compose_rgba(rgb_pil, alpha)
        elapsed = time.time() - t0
        self.finished.emit(
            {
                "rgba": rgba,
                "alpha": alpha,
                "elapsed": elapsed,
                "mode": "full",
            }
        )

    def _do_infer_box(self, rgb_pil, box):
        self._ensure_loaded()
        status_msg = "正在推理（框选区域）…"
        self.status.emit(status_msg)
        t0 = time.time()

        img_size = (rgb_pil.width, rgb_pil.height)
        pad_ratio = self.settings.box_pad_ratio
        expanded_box = ip.expand_box(box, pad_ratio, img_size)
        x, y, w, h = expanded_box
        if w < 1 or h < 1:
            self.failed.emit("inference", "框选后有效区域太小", "")
            return

        roi_pil = ip.crop_roi(rgb_pil, expanded_box)
        roi_alpha = self._engine.infer(roi_pil)
        full_alpha = ip.map_roi_alpha_to_full(roi_alpha, expanded_box, img_size)
        # Zero out area outside the expanded box (already done by map_roi_alpha_to_full)
        rgba = ip.compose_rgba(rgb_pil, full_alpha)
        elapsed = time.time() - t0
        self.finished.emit(
            {
                "rgba": rgba,
                "alpha": full_alpha,
                "elapsed": elapsed,
                "mode": "box",
            }
        )

    def _ensure_loaded(self):
        """Lazy-load model if not already loaded."""
        if self._engine is not None:
            return
        self.status.emit("正在加载模型…")
        num_threads = resolve_cpu_threads(self.settings)
        cache_dir = self.settings.model_cache_dir or None
        eng = BiRefNetEngine(
            model_id=self.settings.model_id,
            cache_dir=cache_dir,
            num_threads=num_threads,
        )
        eng.load()
        self._engine = eng
        self.status.emit("模型就绪 ✓")
