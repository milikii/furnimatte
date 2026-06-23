【锚点】你在 /home/projects/furnimatte 工作。`项目架构.md` §2.5、§4、规范第 7 节是契约。动手前读：`项目架构.md` §2.5、§4；`T08_image_view.md`（ImageView 已提供 view_to_image）。前置 T08。本任务 **T09 框选器**。

【范围 + 文件白名单】仅建 `furniture_cutout/box_selector.py`。不改其它文件。

【任务】实现 `furniture_cutout/box_selector.py`：
1. `from PySide6.QtCore import Qt, QPoint, Signal, QObject`；`from PySide6.QtGui import QMouseEvent, QPainter, QColor, QPen`。
2. `from furniture_cutout.image_view import ImageView`
3. `class BoxSelector(QObject)`：安装在左侧 ImageView 上的事件过滤器。
   - `box_drawn = Signal(int, int, int, int)` — 原图坐标 (x, y, w, h)。
   - `__init__(self, view: ImageView)`：`self._view=view`；`view.installEventFilter(self)`；`self._start=QPoint()`；`self._end=QPoint()`；`self._active=False`；`self._has_box=False`。
   - `eventFilter(self, obj, event)`：
     - 鼠标左键按下 → `_active=True`；`_start=_end=view.view_to_image(event.position().toPoint())`（**原图坐标**）。
     - 鼠标移动且 _active → `_end=view.view_to_image(...)`；`view.update()`（触发重画框，需 view 支持；可在 view paintEvent 后画——简化：BoxSelector 维护框，view 用 `update()`，框绘制通过给 view 加 `extra_paint` 回调或子类化。**简化方案**：让 BoxSelector 在 eventFilter 里直接 `view.update()`，并在 view 暴露 `set_overlay_rect`/绘制；若 view 无此能力，则 BoxSelector 通过 QPainter 在 view 上绘制需在 paintEvent 内——因此**改为**：T09 同时给 ImageView 增加 `overlay_rect` 属性与 paintEvent 末尾绘制半透明矩形。**但这会改 image_view.py（越界）**。→ 采纳：BoxSelector 不改 view 文件；改为 BoxSelector 子类化 ImageView → 但本任务白名单只有 box_selector.py。→ **最终方案**：BoxSelector 用 `view.paintEvent` 替换/monkey-patch 不优雅。改为：**BoxSelector 自己持有一个 overlay，view 的 paintEvent 通过查询一个全局/attached 属性绘制**——又越界。
   - **解决方案（采纳，不改 view）**：BoxSelector 监听 view 的 paint 不可行。因此 BoxSelector 在鼠标抬起时才 `box_drawn`，**实时拖动期间的半透明矩形**通过 `QRubberBand`（PySide6.QtWidgets.QRubberBand）实现——这是 Qt 标准做法，在 view 上显示选择框，不侵入 view paintEvent。用 QRubberBand(view)，setGeometry 到视图坐标（event.position().toPoint()），抬起时 hide。
   - 实现：
     - 按下：`self._rubber=QRubberBand(QRubberBand.Rectangle, view)`；`self._start_view=event.position().toPoint()`；`self._rubber.setGeometry(QRect(start,start))`；`self._rubber.show()`；`_start_img=view.view_to_image(start)`。
     - 移动：`self._rubber.setGeometry(QRect(start_view, event.position().toPoint()).normalized())`。
     - 抬起：`_end_img=view.view_to_image(event.position().toPoint())`；`self._rubber.hide()`；算 `x=min,y=min,w=abs,h=abs`（原图坐标）；`box_drawn.emit(x,y,w,h)`；`_has_box=True`。
   - `clear(self)`：`_has_box=False`；若 rubber 存在 hide。
   - `has_box` property。
4. 小框保护（<50px）**不在本类判定**，由 main_window 收到 box_drawn 后判断并弹消息框。

【决策规则】
- 坐标一律用 `view.view_to_image()` 转原图坐标后 emit，保证缩放/拖动后准确（§4）。
- 用 QRubberBand 显示选择框，不修改 image_view.py。
- 框坐标 emit (x,y,w,h) 原图整数坐标。
- 不 `git commit`。

【完成门槛——逐条亲自跑】
- `python -c "from furniture_cutout import box_selector as b; print('BoxSelector' in dir(b))"` 成功
- `python -c "from furniture_cutout.box_selector import BoxSelector; print(all(hasattr(BoxSelector,s) for s in ['box_drawn','clear','has_box','eventFilter']))"` 输出 True
- `ruff check furniture_cutout/box_selector.py` 退出 0
- grep 自检：`grep -nE "type: ignore|except\s*:\s*pass" furniture_cutout/box_selector.py` 为空
- grep 自检：`grep -n "view_to_image" furniture_cutout/box_selector.py` 存在（坐标换算）
- grep 自检：`grep -n "QRubberBand" furniture_cutout/box_selector.py` 存在
- `git status`：仅 `furniture_cutout/box_selector.py`

【铁律】不得改 image_view.py。需要改白名单外文件则停下报告。禁止 `git commit`。

【报告格式】文件改了什么 + 每条门槛实际结果。
