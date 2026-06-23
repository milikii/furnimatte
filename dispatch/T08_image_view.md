【锚点】你在 /home/projects/furnimatte 工作。`项目架构.md` §2.4、§4 是契约。动手前读：`项目架构.md` §2.4、§4 坐标系。前置 T03（image_processing.qimage_from_pil/checkerboard 已存在）。本任务 **T08 图像视图**。

【范围 + 文件白名单】仅建 `furniture_cutout/image_view.py`。不改其它文件。

【任务】实现 `furniture_cutout/image_view.py`：
1. `from PySide6.QtWidgets import QWidget`；`from PySide6.QtGui import QPainter, QImage, QPaintEvent, QWheelEvent, QMouseEvent, QColor`；`from PySide6.QtCore import Qt, QPoint`。
2. `from furniture_cutout import image_processing as ip`
3. `class ImageView(QWidget)`：
   - `__init__(self, parent=None)`：建 `self._image=None`（QImage 原图，原图尺寸）、`self._bg_image=None`（背景 QImage，棋盘/白/黑，视图尺寸）、`self._scale=1.0`、`self._offset=QPoint(0,0)`、`self._bg_mode="checker"`、`self._dragging=False`、`self._drag_start=QPoint()`、`self._image_size=(0,0)`（原图 w,h）。
   - `set_original(self, pil_img)`：存原图 QImage（ip.qimage_from_pil），记录原图尺寸，`update()`。
   - `set_result(self, rgba_pil)`：存结果 QImage，`update()`。（左侧不用，右侧用）
   - `set_background(self, mode)`：mode ∈ {"checker","white","black"}；`self._bg_mode=mode`；`update()`。
   - `paintEvent`：先画背景（棋盘用 ip.checkerboard，白/黑用纯色），再按 `_scale`+`_offset` 画 image。
   - `wheelEvent`：缩放（以鼠标位置为中心），`_scale` 限制 [0.1, 8.0]，`update()`。
   - `mousePressEvent`/`mouseMoveEvent`/`mouseReleaseEvent`：中键或左键（左键拖动留作 box，这里用中键拖动画布；左键拖动**不**在此处理，留给 BoxSelector，但若该 view 未装 BoxSelector，左键也可拖动——实现时左键拖动画布，BoxSelector 装在左 view 时由 BoxSelector 处理，详见 T09；本类提供 `_pan_with_left` 开关，默认 True）。简化：**统一用中键拖动画布**，左键留给 BoxSelector。`_offset` 更新。
   - `view_to_image(self, pos: QPoint) -> QPoint`：把视图坐标转原图坐标：`(pos - self._offset) / self._scale`。这是 §4 关键换算，**必须准确**，缩放/平移后仍成立。
   - `resizeEvent`：背景需随尺寸重建，`update()`。

【决策规则】
- 视图坐标→原图坐标换算必须严格 `(view - offset)/scale`，不得近似。
- 不要在本类实现框选逻辑（T09 做）。
- 背景三模式：checker/white/black。
- 不 `git commit`。

【完成门槛——逐条亲自跑】
- `python -c "from furniture_cutout import image_view as v; print('ImageView' in dir(v))"` 成功
- `python -c "from furniture_cutout.image_view import ImageView; iv=ImageView(); print(all(hasattr(iv,m) for m in ['set_original','set_result','set_background','view_to_image']))"` 输出 True（构造 QWidget 无 QApplication 可能警告，但不崩；若崩则用 `from PySide6.QtWidgets import QApplication; import sys; app=QApplication.instance() or QApplication(sys.argv)` 包裹再测）
- `ruff check furniture_cutout/image_view.py` 退出 0
- grep 自检：`grep -nE "type: ignore|except\s*:\s*pass" furniture_cutout/image_view.py` 为空
- grep 自检：`grep -n "view_to_image" furniture_cutout/image_view.py` 存在且实现含 `self._scale` 与 `self._offset`
- `git status`：仅 `furniture_cutout/image_view.py`

【铁律】需要改白名单外文件则停下报告。禁止 `git commit`。

【报告格式】文件改了什么 + 每条门槛实际结果。
