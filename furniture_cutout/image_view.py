"""ImageView widget for left/right image display with zoom, pan, and background."""

from __future__ import annotations

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QImage, QPainter, QWheelEvent, QMouseEvent
from PySide6.QtWidgets import QWidget

from PIL import Image

from furniture_cutout import image_processing as ip


class ImageView(QWidget):
    """A zoomable/pannable image display widget.

    Supports checkerboard/white/black background modes and view→image
    coordinate conversion that stays accurate after zoom and pan.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._image: QImage | None = None          # displayed image (original or result)
        self._scale: float = 1.0                    # current zoom factor
        self._offset: QPoint = QPoint(0, 0)         # pan offset in view pixels
        self._bg_mode: str = "checker"              # "checker" | "white" | "black"
        self._dragging: bool = False
        self._drag_start: QPoint = QPoint(0, 0)
        self._image_size: tuple[int, int] = (0, 0)  # original image (w, h)
        self._bg_image: QImage | None = None        # cached background for current size
        self._overlay_rect = None                    # optional overlay rect (reserved)
        self._fit_pending: bool = False              # re-fit to viewport on next paint
        self._user_zoomed: bool = False              # user took manual zoom/pan control
        self.setMinimumSize(100, 100)
        self.setMouseTracking(False)

    # ---- Public API --------------------------------------------------------

    def set_original(self, pil_img) -> None:
        """Set the original image (left view)."""
        self._image = ip.qimage_from_pil(pil_img)
        self._image_size = (pil_img.width, pil_img.height)
        self._request_fit()
        # Rebuild background for the new image size
        self._rebuild_bg()
        self.update()

    def set_result(self, rgba_pil) -> None:
        """Set the result image (right view, transparent background)."""
        self._image = ip.qimage_from_pil(rgba_pil)
        self._image_size = (rgba_pil.width, rgba_pil.height)
        self._request_fit()
        self._rebuild_bg()
        self.update()

    def set_background(self, mode: str) -> None:
        """Change background display mode.

        Args:
            mode: One of "checker", "white", "black".
        """
        if mode not in ("checker", "white", "black"):
            raise ValueError(f"Unknown background mode: {mode}")
        self._bg_mode = mode
        self._rebuild_bg()
        self.update()

    def clear(self) -> None:
        """Clear the displayed image and reset view state."""
        self._image = None
        self._image_size = (0, 0)
        self._bg_image = None
        self._scale = 1.0
        self._offset = QPoint(0, 0)
        self._fit_pending = False
        self._user_zoomed = False
        self.update()

    def set_overlay_rect(self, rect) -> None:
        """Set an overlay rectangle to draw, or None to clear.

        Currently a no-op placeholder (BoxSelector uses QRubberBand),
        reserved for a future paintEvent-based overlay if needed.
        """
        self._overlay_rect = rect
        self.update()

    def view_to_image(self, pos: QPoint) -> QPoint:
        """Convert viewport coordinates to original image coordinates.

        This is the critical coordinate conversion: must stay accurate
        after zoom and pan. Formula: (view - offset) / scale.
        Returns QPoint in image pixel space.
        """
        x = round((pos.x() - self._offset.x()) / self._scale)
        y = round((pos.y() - self._offset.y()) / self._scale)
        return QPoint(x, y)

    @property
    def image_size(self) -> tuple[int, int]:
        """Original image size (w, h)."""
        return self._image_size

    # ---- Internal helpers --------------------------------------------------

    def _rebuild_bg(self) -> None:
        """Regenerate the background image for the current widget size + mode."""
        w = max(1, self.width())
        h = max(1, self.height())
        if self._bg_mode == "checker":
            self._bg_image = ip.checkerboard(w, h)
        elif self._bg_mode == "white":
            pil = Image.new("RGB", (w, h), (255, 255, 255))
            self._bg_image = ip.qimage_from_pil(pil)
        elif self._bg_mode == "black":
            pil = Image.new("RGB", (w, h), (0, 0, 0))
            self._bg_image = ip.qimage_from_pil(pil)

    def _request_fit(self) -> None:
        """Mark the view to re-fit on the next paint and hand control back to fit."""
        self._fit_pending = True
        self._user_zoomed = False

    def _apply_fit(self) -> None:
        """Center the image in the viewport, scaled down to fit (never upscaled).

        Without this a 4K result would render at 1:1 from the top-left corner,
        so the user would only see a small crop. Fit-to-window shows the whole
        image; manual zoom/pan afterwards disables auto-fit.
        """
        iw, ih = self._image_size
        vw, vh = self.width(), self.height()
        if iw <= 0 or ih <= 0 or vw <= 1 or vh <= 1:
            return  # viewport not laid out yet; retry on the next paint
        scale = min(vw / iw, vh / ih, 1.0)
        self._scale = scale
        self._offset = QPoint(
            round((vw - iw * scale) / 2),
            round((vh - ih * scale) / 2),
        )
        self._fit_pending = False

    # ---- Qt event overrides -----------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw background then image."""
        if self._fit_pending and self._image is not None:
            self._apply_fit()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Background
        if self._bg_image is None or self._bg_image.size() != self.size():
            self._rebuild_bg()
        if self._bg_image is not None:
            painter.drawImage(0, 0, self._bg_image)

        # Image — draw at (offset) scaled by _scale
        if self._image is not None:
            iw, ih = self._image_size
            if iw > 0 and ih > 0:
                ox = self._offset.x()
                oy = self._offset.y()
                painter.save()
                painter.translate(ox, oy)
                painter.scale(self._scale, self._scale)
                painter.drawImage(0, 0, self._image, 0, 0, iw, ih)
                painter.restore()

        painter.end()

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        """Zoom in/out centered on mouse cursor."""
        if self._image is None:
            return

        # Determine zoom direction
        delta = event.angleDelta().y()
        if delta == 0:
            return
        self._user_zoomed = True
        factor = 1.1 if delta > 0 else 1.0 / 1.1

        # Mouse position in viewport
        mouse_pos = event.position().toPoint()

        # Current mouse position in image coordinates
        img_before = self.view_to_image(mouse_pos)

        # Apply zoom
        new_scale = self._scale * factor
        new_scale = max(0.1, min(8.0, new_scale))

        # Adjust offset so image point under cursor stays fixed
        # img_before = (mouse - offset) / scale
        # offset_new = mouse - img_before * new_scale
        ox = round(mouse_pos.x() - img_before.x() * new_scale)
        oy = round(mouse_pos.y() - img_before.y() * new_scale)

        self._scale = new_scale
        self._offset = QPoint(ox, oy)
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Start panning on middle button or left button (left=pan unless BoxSelector is active)."""
        if event.button() == Qt.MiddleButton:
            self._dragging = True
            self._user_zoomed = True
            self._drag_start = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Pan while dragging."""
        if self._dragging:
            pos = event.position().toPoint()
            dx = pos.x() - self._drag_start.x()
            dy = pos.y() - self._drag_start.y()
            self._offset = QPoint(
                self._offset.x() + dx,
                self._offset.y() + dy,
            )
            self._drag_start = pos
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """End panning."""
        if event.button() == Qt.MiddleButton and self._dragging:
            self._dragging = False
            self.setCursor(Qt.ArrowCursor)

    def resizeEvent(self, event) -> None:  # noqa: N802
        """Rebuild background and re-fit the image (unless the user took control)."""
        if self._image is not None and not self._user_zoomed:
            self._fit_pending = True
        self._rebuild_bg()
        self.update()
        super().resizeEvent(event)
