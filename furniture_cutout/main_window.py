"""MainWindow: toolbar, status bar, worker integration, drag-drop."""

from __future__ import annotations

import os

from PIL import Image as PILImage
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QStatusBar,
    QToolBar,
    QWidget,
)

from furniture_cutout import exporter, image_processing as ip, logging_config, settings as settings_mod
from furniture_cutout.box_selector import BoxSelector
from furniture_cutout.image_view import ImageView
from furniture_cutout.inference_worker import InferenceWorker
from furniture_cutout.settings import SettingsDialog


class MainWindow(QMainWindow):
    """主窗口：全功能极简家具抠图界面。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("家具自动抠图")
        self.resize(1200, 800)

        # --- State ---
        self.original_rgb: PILImage.Image | None = None
        self.preview: PILImage.Image | None = None
        self.current_alpha = None  # np.ndarray float [0,1]
        self.current_rgba: PILImage.Image | None = None
        self.selected_box: tuple[int, int, int, int] | None = None  # (x,y,w,h)
        self.current_file_path: str | None = None
        self.output_file_path: str | None = None
        self._settings = settings_mod.load()

        # --- UI ---
        self._setup_ui()
        self._setup_toolbar()
        self._setup_status_bar()

        # --- Worker ---
        self._worker = InferenceWorker(self._settings, parent=self)
        self._connect_worker_signals()
        self._model_loaded = False
        self._model_loading = False
        self._busy = False

        # --- Drag-drop ---
        self.setAcceptDrops(True)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)

        self._left_view = ImageView()
        self._right_view = ImageView()

        # Background toggle buttons

        # ... (background buttons attached to right_view via toolbar instead)

        layout.addWidget(self._left_view, 1)
        layout.addWidget(self._right_view, 1)

    def _setup_toolbar(self):
        toolbar = QToolBar("工具栏")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        self._act_open = toolbar.addAction("📂 打开图片")
        self._act_open.triggered.connect(self.open_image)

        toolbar.addSeparator()

        self._act_cutout = toolbar.addAction("✂ 自动抠图")
        self._act_cutout.triggered.connect(self.auto_cutout)
        self._act_cutout.setEnabled(False)

        self._act_box = toolbar.addAction("⬜ 框选重算")
        self._act_box.triggered.connect(self.enter_box_mode)
        self._act_box.setEnabled(False)
        self._act_box.setCheckable(True)

        self._act_cancel_box = toolbar.addAction("⨯ 取消框选")
        self._act_cancel_box.triggered.connect(self.cancel_box)
        self._act_cancel_box.setEnabled(False)

        toolbar.addSeparator()

        self._act_save = toolbar.addAction("💾 保存 PNG")
        self._act_save.triggered.connect(self.save_png)
        self._act_save.setEnabled(False)

        self._act_reset = toolbar.addAction("🔄 重置")
        self._act_reset.triggered.connect(self.reset)

        toolbar.addSeparator()

        # Background buttons
        self._act_bg_checker = toolbar.addAction("棋盘格")
        self._act_bg_checker.triggered.connect(lambda: self._right_view.set_background("checker"))
        self._act_bg_white = toolbar.addAction("白色")
        self._act_bg_white.triggered.connect(lambda: self._right_view.set_background("white"))
        self._act_bg_black = toolbar.addAction("黑色")
        self._act_bg_black.triggered.connect(lambda: self._right_view.set_background("black"))

        toolbar.addSeparator()

        self._act_settings = toolbar.addAction("⚙ 设置")
        self._act_settings.triggered.connect(self.open_settings)

        # Box selector
        self._box_selector = BoxSelector(self._left_view)
        self._box_selector.box_drawn.connect(self._on_box_drawn)

    def _setup_status_bar(self):
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._progress = QProgressBar()
        self._progress.setMaximumWidth(200)
        self._progress.setRange(0, 100)
        self._progress.hide()
        self._status.addPermanentWidget(self._progress)
        self._status_label = self._status.currentMessage()

    # --- Open ---

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "打开图片",
            "",
            "图片文件 (*.jpg *.jpeg *.png *.webp);;所有文件 (*)",
        )
        if not path:
            return
        self._load_image(path)

    def _load_image(self, path: str):
        try:
            rgb, meta = ip.load_image(path)
        except Exception as e:
            QMessageBox.critical(self, "图片读取失败", f"无法读取图片：{path}\n{e}")
            logging_config.log_exception(e)
            return

        self.reset()
        self.original_rgb = rgb
        self.current_file_path = path
        self.preview = ip.make_preview(rgb)
        self._left_view.set_original(self.preview)

        sw, sh = self._left_view.image_size
        self._status.showMessage(f"已打开：{os.path.basename(path)}  ({meta['width']}×{meta['height']})")

        self._act_cutout.setEnabled(True)
        self._act_box.setEnabled(False)
        self._act_save.setEnabled(False)

        if self._settings.auto_cutout_on_open and rgb:
            self.auto_cutout()

    # --- Auto cutout ---

    def auto_cutout(self):
        if self._busy or not self.original_rgb:
            return
        self._set_busy(True)
        self._status.showMessage("正在加载模型…")

        if not self._model_loaded and not self._model_loading:
            self._model_loading = True
            self._worker.request_load()
        self._worker.request_infer_full(self.original_rgb)

    def enter_box_mode(self):
        if self._busy or not self.original_rgb:
            return
        if not self._act_box.isChecked():
            self.cancel_box()
            return
        self._box_selector.set_enabled(True)
        self._act_cancel_box.setEnabled(True)
        self._status.showMessage("请在左侧图片上框选正确的家具")

    def cancel_box(self):
        self._box_selector.set_enabled(False)
        self._box_selector.clear()
        self._act_box.setChecked(False)
        self._act_cancel_box.setEnabled(False)
        self._status.showMessage("已取消框选")

    def _on_box_drawn(self, x, y, w, h):
        self.selected_box = (x, y, w, h)
        # Small box protection
        if w < 50 or h < 50:
            QMessageBox.warning(self, "框选区域太小", "框选区域太小（<50像素），请重新框选家具主体。")
            self.cancel_box()
            return

        if self._busy:
            return
        self._set_busy(True)
        self._act_box.setChecked(False)
        self._status.showMessage("正在对框选区域重算…")

        if not self._model_loaded and not self._model_loading:
            self._model_loading = True
            self._worker.request_load()
        self._worker.request_infer_box(self.original_rgb, (x, y, w, h))

    # --- Save ---

    def save_png(self):
        if self.current_rgba is None or not self.current_file_path:
            QMessageBox.information(self, "提示", "请先完成抠图后再保存。")
            return

        try:
            out_path = exporter.save(
                self.current_rgba,
                self.current_file_path,
                out_dir=self._settings.output_dir or None,
                also_alpha=self._settings.save_alpha,
            )
            self.output_file_path = out_path
            self._status.showMessage(f"已保存：{out_path}")
        except exporter.ExporterError as e:
            QMessageBox.critical(self, "保存失败", str(e))
            logging_config.log_exception(e)

    # --- Reset ---

    def reset(self):
        self.current_alpha = None
        self.current_rgba = None
        self.selected_box = None
        self.output_file_path = None
        self._left_view.clear()
        self._right_view.clear()
        self.cancel_box()
        self._act_cutout.setEnabled(False)
        self._act_box.setEnabled(False)
        self._act_save.setEnabled(False)
        self._progress.hide()
        self._status.showMessage("")

    # --- Settings ---

    def open_settings(self):
        dialog = SettingsDialog(self._settings, self)
        if dialog.exec():
            self._settings = settings_mod.load()
            # Reload settings for worker
            self._worker.settings = self._settings
            if self._model_loaded:
                self._status.showMessage("模型线程数将在下次推理时生效", 3000)

    # --- Worker signals ---

    def _connect_worker_signals(self):
        self._worker.status.connect(self._on_worker_status)
        self._worker.progress.connect(self._on_worker_progress)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.failed.connect(self._on_worker_failed)

    def _on_worker_status(self, msg: str):
        self._status.showMessage(msg)
        if "就绪" in msg:
            self._model_loaded = True
            self._model_loading = False

    def _on_worker_progress(self, msg: str):
        self._status.showMessage(msg)

    def _on_worker_finished(self, result: dict):
        self._set_busy(False)
        self.current_alpha = result.get("alpha")
        self.current_rgba = result.get("rgba")
        elapsed = result.get("elapsed", 0)
        mode = result.get("mode", "full")

        self._right_view.set_result(self.current_rgba)
        self._act_save.setEnabled(True)
        self._act_box.setEnabled(True)
        out_size = self.current_rgba.size if self.current_rgba else (0, 0)
        self._status.showMessage(
            f"{'整图抠图' if mode=='full' else '框选重算'}完成  "
            f"输出 {out_size[0]}×{out_size[1]}  耗时 {elapsed:.1f}s"
        )

    def _on_worker_failed(self, kind: str, message: str, tb: str):
        self._set_busy(False)
        self._model_loading = False
        titles = {
            "model_load": "模型加载失败",
            "download": "模型下载失败",
            "image_read": "图片读取失败",
            "oom": "内存不足",
            "inference": "推理失败",
            "save": "保存失败",
        }
        title = titles.get(kind, "错误")
        if kind == "download":
            QMessageBox.critical(
                self,
                title,
                f"无法下载模型。请检查网络、代理，\n或在设置中开启 HF 镜像、\n或手动选择本地模型目录。\n\n{message}",
            )
        else:
            QMessageBox.critical(self, title, f"{message}\n\n详情见 logs/app.log")
        logging_config.log_exception(Exception(message), context=f"[{kind}]")

    # --- Busy state ---

    def _set_busy(self, busy: bool):
        self._busy = busy
        self._act_cutout.setEnabled(not busy and self.original_rgb is not None)
        self._act_box.setEnabled(not busy and self.original_rgb is not None)
        self._act_save.setEnabled(not busy and self.current_rgba is not None)
        self._act_reset.setEnabled(not busy)
        if busy:
            self._progress.setRange(0, 0)
            self._progress.show()
        else:
            self._progress.setRange(0, 100)
            self._progress.hide()

    # --- Drag-drop ---

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path and path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                self._load_image(path)
                break
