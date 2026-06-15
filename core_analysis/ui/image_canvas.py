"""ImageCanvas — QGraphicsView-based canvas with 3-layer rendering."""

import cv2
import numpy as np
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QBrush
from PySide6.QtCore import Qt, QRectF, Signal, QPointF
from core_analysis.data.models import MaskRegion


class Layer:
    IMAGE = 0
    OVERLAY = 1
    ANNOTATION = 2


class ImageCanvas(QGraphicsView):
    region_selected = Signal(int)
    color_sampled = Signal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        self._image_item = QGraphicsPixmapItem()
        self._image_item.setZValue(Layer.IMAGE)
        self._scene.addItem(self._image_item)

        self._overlay_item = QGraphicsPixmapItem()
        self._overlay_item.setZValue(Layer.OVERLAY)
        self._overlay_item.setOpacity(0.5)
        self._scene.addItem(self._overlay_item)

        self._annotation_item = QGraphicsPixmapItem()
        self._annotation_item.setZValue(Layer.ANNOTATION)
        self._scene.addItem(self._annotation_item)

        self._image_bgr = None
        self._regions = []
        self._overlay_visible = True
        self._annotation_visible = True

    def load_image(self, filepath: str):
        bgr = cv2.imread(filepath)
        if bgr is None:
            raise FileNotFoundError(f"Cannot load image: {filepath}")
        self._image_bgr = bgr
        self._refresh_image_layer()
        self._overlay_item.setPixmap(QPixmap())
        self._annotation_item.setPixmap(QPixmap())
        self._regions = []
        self._fit_to_window()

    def load_image_from_array(self, bgr: np.ndarray):
        self._image_bgr = bgr.copy()
        self._refresh_image_layer()
        self._fit_to_window()

    def _refresh_image_layer(self):
        if self._image_bgr is None:
            return
        rgb = cv2.cvtColor(self._image_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, w * ch, QImage.Format_RGB888)
        self._image_item.setPixmap(QPixmap.fromImage(qimg))
        self._scene.setSceneRect(QRectF(0, 0, w, h))

    def _fit_to_window(self):
        if self._image_bgr is not None:
            self.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)

    def set_regions(self, regions: list):
        self._regions = regions
        self._refresh_overlay()

    def _refresh_overlay(self):
        if self._image_bgr is None or not self._overlay_visible:
            self._overlay_item.setPixmap(QPixmap())
            return
        h, w = self._image_bgr.shape[:2]
        overlay = np.zeros((h, w, 4), dtype=np.uint8)
        for i, region in enumerate(self._regions):
            pts = np.array(region.contour, dtype=np.int32)
            if pts.ndim == 2 and pts.shape[0] >= 3:
                cv2.drawContours(overlay, [pts], -1, (255, 60, 60, 180), -1)
                cv2.drawContours(overlay, [pts], -1, (255, 0, 0, 255), 1)
        qimg = QImage(overlay.data, w, h, w * 4, QImage.Format_RGBA8888)
        self._overlay_item.setPixmap(QPixmap.fromImage(qimg))

    def toggle_overlay(self, visible: bool):
        self._overlay_visible = visible
        self._refresh_overlay()

    def toggle_annotation(self, visible: bool):
        self._annotation_visible = visible

    def zoom_in(self):
        self.scale(1.25, 1.25)

    def zoom_out(self):
        self.scale(0.8, 0.8)

    def zoom_fit(self):
        self._fit_to_window()

    def zoom_100(self):
        self.resetTransform()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            for i, region in enumerate(self._regions):
                pts = np.array(region.contour, dtype=np.int32)
                if pts.ndim == 2 and pts.shape[0] >= 3:
                    if cv2.pointPolygonTest(pts, (pos.x(), pos.y()), False) >= 0:
                        self.region_selected.emit(i)
                        break
            if self._image_bgr is not None:
                px, py = int(pos.x()), int(pos.y())
                h, w = self._image_bgr.shape[:2]
                if 0 <= px < w and 0 <= py < h:
                    self.color_sampled.emit(self._image_bgr[py, px])
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    @property
    def regions(self) -> list:
        return self._regions

    @property
    def image_bgr(self):
        return self._image_bgr

    @property
    def image_size(self) -> tuple:
        if self._image_bgr is None:
            return (0, 0)
        return self._image_bgr.shape[:2]
