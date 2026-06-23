"""
设置模块：Settings dataclass、读写 config.json、设置对话框。
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

CONFIG_PATH = "config.json"


class SettingsError(Exception):
    """设置操作失败。"""
    pass


@dataclass
class Settings:
    model_id: str = "ZhengPeng7/BiRefNet_HR-matting"
    model_cache_dir: str = ""
    box_pad_ratio: float = 0.05
    cpu_threads: int = 0  # 0 = auto（运行期由 engine 算 max(1,cpu-2)）
    output_dir: str = ""
    save_alpha: bool = False
    auto_cutout_on_open: bool = False
    hf_mirror: bool = True


def load() -> Settings:
    """从 config.json 读配置，缺失字段用默认补。文件不存在或损坏则返回默认 Settings。"""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, PermissionError):
        return Settings()

    # 字段映射，处理 cpu_threads 的 "auto" 字符串
    kwargs = {}
    for field_name in (
        "model_id",
        "model_cache_dir",
        "box_pad_ratio",
        "cpu_threads",
        "output_dir",
        "save_alpha",
        "auto_cutout_on_open",
        "hf_mirror",
    ):
        if field_name not in data:
            continue
        val = data[field_name]
        if field_name == "cpu_threads":
            if isinstance(val, str) and val.strip().lower() == "auto":
                kwargs["cpu_threads"] = 0
            else:
                try:
                    kwargs["cpu_threads"] = int(val)
                except (ValueError, TypeError):
                    kwargs["cpu_threads"] = 0
        elif field_name == "box_pad_ratio":
            kwargs["box_pad_ratio"] = float(val)
        elif field_name in ("save_alpha", "auto_cutout_on_open", "hf_mirror"):
            kwargs[field_name] = bool(val)
        elif field_name in ("model_cache_dir", "output_dir"):
            kwargs[field_name] = str(val)
        else:
            kwargs[field_name] = val

    return Settings(**kwargs)


def save(settings: Settings) -> None:
    """写 config.json。失败抛 SettingsError。"""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(asdict(settings), f, indent=2, ensure_ascii=False)
    except (OSError, PermissionError) as e:
        raise SettingsError(f"保存设置失败：{e}") from e


def resolve_cpu_threads(s: Settings) -> int:
    """返回实际 CPU 线程数。0=auto → max(1, cpu_count-2)。"""
    if s.cpu_threads and s.cpu_threads > 0:
        return s.cpu_threads
    return max(1, (os.cpu_count() or 6) - 2)


class SettingsDialog(QDialog):
    """设置对话框。"""

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self._settings = settings
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # 模型缓存目录
        self._cache_dir_edit = QLineEdit(self._settings.model_cache_dir)
        browse_cache_btn = QPushButton("浏览…")
        browse_cache_btn.clicked.connect(self._browse_cache_dir)
        cache_layout = QHBoxLayout()
        cache_layout.addWidget(self._cache_dir_edit)
        cache_layout.addWidget(browse_cache_btn)
        form.addRow("模型缓存目录", cache_layout)

        # 框选扩展比例
        self._pad_spin = QDoubleSpinBox()
        self._pad_spin.setRange(0.00, 0.15)
        self._pad_spin.setSingleStep(0.01)
        self._pad_spin.setDecimals(2)
        self._pad_spin.setValue(self._settings.box_pad_ratio)
        form.addRow("框选扩展比例", self._pad_spin)

        # CPU 线程数
        self._threads_spin = QSpinBox()
        self._threads_spin.setRange(0, 32)
        self._threads_spin.setSpecialValueText("自动")
        self._threads_spin.setValue(self._settings.cpu_threads)
        form.addRow("CPU 线程数", self._threads_spin)

        # 默认输出目录
        self._out_dir_edit = QLineEdit(self._settings.output_dir)
        browse_out_btn = QPushButton("浏览…")
        browse_out_btn.clicked.connect(self._browse_out_dir)
        out_layout = QHBoxLayout()
        out_layout.addWidget(self._out_dir_edit)
        out_layout.addWidget(browse_out_btn)
        form.addRow("默认输出目录", out_layout)

        # 同时保存 Alpha
        self._save_alpha_cb = QCheckBox("同时保存 Alpha 蒙版")
        self._save_alpha_cb.setChecked(self._settings.save_alpha)
        form.addRow(self._save_alpha_cb)

        # 打开后自动抠图
        self._auto_cutout_cb = QCheckBox("打开图片后自动开始抠图")
        self._auto_cutout_cb.setChecked(self._settings.auto_cutout_on_open)
        form.addRow(self._auto_cutout_cb)

        layout.addLayout(form)

        # 按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _browse_cache_dir(self):
        """选择模型缓存目录。"""
        path = QFileDialog.getExistingDirectory(self, "选择模型缓存目录")
        if path:
            self._cache_dir_edit.setText(path)

    def _browse_out_dir(self):
        """选择默认输出目录。"""
        path = QFileDialog.getExistingDirectory(self, "选择默认输出目录")
        if path:
            self._out_dir_edit.setText(path)

    def get_settings(self) -> Settings:
        """从表单收集设置。"""
        s = Settings(
            model_id=self._settings.model_id,
            model_cache_dir=self._cache_dir_edit.text().strip(),
            box_pad_ratio=self._pad_spin.value(),
            cpu_threads=self._threads_spin.value(),
            output_dir=self._out_dir_edit.text().strip(),
            save_alpha=self._save_alpha_cb.isChecked(),
            auto_cutout_on_open=self._auto_cutout_cb.isChecked(),
            hf_mirror=self._settings.hf_mirror,
        )
        return s

    def accept(self):
        """接受时保存设置。"""
        s = self.get_settings()
        save(s)
        self._settings = s
        super().accept()
