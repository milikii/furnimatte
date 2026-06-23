"""BoxSelector: mouse drag rectangle selection on ImageView, emits image-coord box."""

from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, Qt, Signal
from PySide6.QtWidgets import QRubberBand

from furniture_cutout.image_view import ImageView


class BoxSelector(QObject):
    """Event filter on ImageView for drag-select rectangle.

    Emits box_drawn with (x, y, w, h) in original image coordinates.
    Uses QRubberBand for visual overlay (no paintEvent modification needed).
    """

    box_drawn = Signal(int, int, int, int)  # (x, y, w, h) image coords

    def __init__(self, view: ImageView, parent=None):
        super().__init__(parent)
        self._view = view
        self._rubber: QRubberBand | None = None
        self._start_view = QPoint()
        self._start_img = QPoint()
        self._active = False
        self._has_box = False
        self._enabled = False
        view.installEventFilter(self)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable box selection."""
        self._enabled = enabled
        if not enabled:
            self.clear()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def has_box(self) -> bool:
        return self._has_box

    def clear(self) -> None:
        """Clear the selection box."""
        self._has_box = False
        self._active = False
        if self._rubber:
            self._rubber.hide()
        self._view.set_overlay_rect(None)

    def eventFilter(self, obj, event) -> bool:
        if not self._enabled:
            return super().eventFilter(obj, event)

        if event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self._active = True
                self._start_view = event.position().toPoint()
                self._start_img = self._view.view_to_image(self._start_view)
                if not self._rubber:
                    self._rubber = QRubberBand(QRubberBand.Rectangle.Shape.Rectangle, self._view)
                self._rubber.setGeometry(event.position().x(), event.position().y(), 0, 0)
                self._rubber.show()
                return True

        elif event.type() == event.Type.MouseMove:
            if self._active:
                pos = event.position().toPoint()
                x = min(pos.x(), self._start_view.x())
                y = min(pos.y(), self._start_view.y())
                w = abs(pos.x() - self._start_view.x())
                h = abs(pos.y() - self._start_view.y())
                if self._rubber:
                    self._rubber.setGeometry(x, y, w, h)
                return True

        elif event.type() == event.Type.MouseButtonRelease:
            if self._active and event.button() == Qt.MouseButton.LeftButton:
                self._active = False
                end_img = self._view.view_to_image(event.position().toPoint())
                if self._rubber:
                    self._rubber.hide()
                x = min(self._start_img.x(), end_img.x())
                y = min(self._start_img.y(), end_img.y())
                w = abs(end_img.x() - self._start_img.x())
                h = abs(end_img.y() - self._start_img.y())
                if w > 0 and h > 0:
                    self._has_box = True
                    self.box_drawn.emit(x, y, w, h)
                return True

        return super().eventFilter(obj, event)
