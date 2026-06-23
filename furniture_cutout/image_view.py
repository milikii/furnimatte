"""ImageView: left/right image display with zoom, pan, and background modes."""

from __future__ import annotations

from PIL import Image as PILImage
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPaintEvent, QPainter, QWheelEvent
from PySide6.QtWidgets import QWidget

from furniture_cutout import image_processing as ip


class ImageView(QWidget):
    """Widget to display an image with zoom/pan support.

    Provides view_to_image() coordinate conversion for box selection.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image: QImage | None = None
        self._result_image: QImage | None = None
        self._scale = 1.0
        self._offset = QPoint(0, 0)
        self._bg_mode = "checker"
        self._image_size = (0, 0)  # original pixels
        self._dragging = False
        self._drag_start = QPoint()
        self._drag_offset_start = QPoint()
        # Overlay rectangle (for box selection preview)
        self._overlay_rect: tuple[int, int, int, int] | None = None
        self.setMinimumSize(200, 200)
        self.setMouseTracking(False)

    def set_original(self, pil_img: PILImage.Image) -> None:
        """Set the original image (left panel)."""
        self._image = ip.qimage_from_pil(pil_img.convert("RGB"))
        self._image_size = (pil_img.width, pil_img.height)
        self._offset = QPoint(0, 0)
        self._fit_to_widget()
        self.update()

    def set_result(self, rgba_pil: PILImage.Image) -> None:
        """Set the result RGBA image (right panel)."""
        self._result_image = ip.qimage_from_pil(rgba_pil)
        self.update()

    def set_background(self, mode: str) -> None:
        """Set background display mode: checker, white, black."""
        self._bg_mode = mode
        self.update()

    def set_overlay_rect(self, rect: tuple[int, int, int, int] | None) -> None:
        """Set an overlay rectangle in view coordinates (x, y, w, h)."""
        self._overlay_rect = rect
        self.update()

    def clear(self) -> None:
        """Clear all images."""
        self._image = None
        self._result_image = None
        self._overlay_rect = None
        self._image_size = (0, 0)
        self._scale = 1.0
        self._offset = QPoint(0, 0)
        self.update()

    def view_to_image(self, view_pos: QPoint) -> QPoint:
        """Convert view coordinates to original image coordinates."""
        img_x = int((view_pos.x() - self._offset.x()) / self._scale)
        img_y = int((view_pos.y() - self._offset.y()) / self._scale)
        return QPoint(max(0, img_x), max(0, img_y))

    def _fit_to_widget(self) -> None:
        """Initial fit: scale image to fit widget."""
        if not self._image or self._image_size == (0, 0):
            return
        w_scale = self.width() / self._image_size[0] if self._image_size[0] > 0 else 1
        h_scale = self.height() / self._image_size[1] if self._image_size[1] > 0 else 1
        self._scale = min(w_scale, h_scale) * 0.9  # leave a small margin
        # Center
        disp_w = self._image_size[0] * self._scale
        disp_h = self._image_size[1] * self._scale
        self._offset = QPoint(
            int((self.width() - disp_w) / 2),
            int((self.height() - disp_h) / 2),
        )

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Background
        self._draw_background(painter)

        # Image
        qimg = self._result_image if self._result_image else self._image
        if qimg:
            scaled = qimg.scaled(
                int(self._image_size[0] * self._scale),
                int(self._image_size[1] * self._scale),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawImage(self._offset, scaled)

        # Overlay rectangle
        if self._overlay_rect:
            x, y, w, h = self._overlay_rect
            painter.setPen(QColor(255, 0, 0, 200))
            painter.setBrush(QColor(255, 0, 0, 30))
            painter.drawRect(x, y, w, h)

    def _draw_background(self, painter: QPainter) -> None:
        if self._bg_mode == "white":
            painter.fillRect(self.rect(), Qt.GlobalColor.white)
        elif self._bg_mode == "black":
            painter.fillRect(self.rect(), Qt.GlobalColor.black)
        else:  # checker
            if self._image:
                checker = ip.checkerboard(self.width(), self.height(), 16)
                painter.drawImage(0, 0, checker)
            else:
                painter.fillRect(self.rect(), Qt.GlobalColor.white)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Zoom in/out around mouse position."""
        if not self._image:
            return
        # Mouse position before zoom
        old_pos = event.position().toPoint()
        old_img = self.view_to_image(old_pos)

        # Zoom factor
        delta = event.angleDelta().y()
        factor = 1.1 if delta > 0 else 1 / 1.1
        new_scale = self._scale * factor
        new_scale = max(0.1, min(8.0, new_scale))
        self._scale = new_scale

        # Adjust offset so mouse position stays on the same image point
        self._offset = QPoint(
            int(old_pos.x() - old_img.x() * self._scale),
            int(old_pos.y() - old_img.y() * self._scale),
        )
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._dragging = True
            self._drag_start = event.position().toPoint()
            self._drag_offset_start = QPoint(self._offset)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging:
            delta = event.position().toPoint() - self._drag_start
            self._offset = self._drag_offset_start + delta
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton and self._dragging:
            self._dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def resizeEvent(self, event) -> None:
        if self._image and self._scale > 0:
            # Keep current zoom, just re-center if needed
            pass
        self.update()

    @property
    def image_size(self) -> tuple[int, int]:
        return self._image_size

    @property
    def current_scale(self) -> float:
        return self._scale

    @property
    def current_offset(self) -> QPoint:
        return self._offset

    @property
    def has_image(self) -> bool:
        return self._image is not None

    def clear_result(self) -> None:
        self._result_image = None
        self.update()
