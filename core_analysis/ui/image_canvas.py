"""ImageCanvas — QGraphicsView-based canvas with 3-layer rendering."""

import cv2
import numpy as np
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtGui import QPixmap, QImage, QPainter, QTransform
from PySide6.QtCore import Qt, QRectF, Signal, QPointF
from core_analysis.data.models import MaskRegion
from core_analysis.engine.morphology_engine import MorphologyEngine


class Layer:
    IMAGE = 0
    OVERLAY = 1
    ANNOTATION = 2


class ImageCanvas(QGraphicsView):
    region_selected = Signal(int)
    color_sampled = Signal(np.ndarray)
    point_sampled = Signal(int, int)  # x, y

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
        self._image_item.setTransformationMode(Qt.SmoothTransformation)
        self._scene.addItem(self._image_item)

        self._overlay_item = QGraphicsPixmapItem()
        self._overlay_item.setZValue(Layer.OVERLAY)
        self._overlay_item.setOpacity(0.5)
        self._overlay_item.setTransformationMode(Qt.SmoothTransformation)
        self._scene.addItem(self._overlay_item)

        self._annotation_item = QGraphicsPixmapItem()
        self._annotation_item.setZValue(Layer.ANNOTATION)
        self._scene.addItem(self._annotation_item)

        # State
        self._image_bgr = None
        self._regions = []
        self._overlay_visible = True
        self._annotation_visible = True
        self._rotation_angle = 0.0
        self._analysis_mask = None
        self._roi_rect_start = None
        self._selected_regions = set()
        self._drawing_mode = None  # 'erase', 'add', or None
        self._brush_mask = None
        self._brush_radius = 15

    # ── Image Loading ──

    def load_image(self, filepath: str):
        with open(filepath, 'rb') as f:
            data = np.frombuffer(f.read(), dtype=np.uint8)
        bgr = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if bgr is None:
            raise FileNotFoundError(f"Cannot load image: {filepath}")
        self._image_bgr = bgr
        self._rotation_angle = 0.0
        self._refresh_image_layer()
        self._overlay_item.setPixmap(QPixmap())
        self._annotation_item.setPixmap(QPixmap())
        self._annotation_item.setVisible(False)
        self._regions = []
        self._fit_to_window()

    def load_image_from_array(self, bgr: np.ndarray):
        self._image_bgr = bgr.copy()
        self._rotation_angle = 0.0
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

    # ── Rotation (Qt native transform, no pixel modification) ──

    def rotate_view(self, delta_degrees: float):
        """Rotate view by delta, applied to scene items. No pixel changes."""
        self._rotation_angle = (self._rotation_angle + delta_degrees) % 360
        center = self._scene.sceneRect().center()
        t = QTransform()
        t.translate(center.x(), center.y())
        t.rotate(self._rotation_angle)
        t.translate(-center.x(), -center.y())
        self._image_item.setTransform(t)
        self._overlay_item.setTransform(t)
        self._annotation_item.setTransform(t)

    def reset_rotation(self):
        self._rotation_angle = 0.0
        self._image_item.setTransform(QTransform())
        self._overlay_item.setTransform(QTransform())
        self._annotation_item.setTransform(QTransform())

    # ── Overlay ──

    def set_regions(self, regions: list):
        self._regions = regions
        # Keep selections valid — remove stale indices
        max_idx = len(regions) - 1
        self._selected_regions = {i for i in self._selected_regions if i <= max_idx}
        self._refresh_overlay()

    def toggle_region_selection(self, idx: int):
        if idx in self._selected_regions:
            self._selected_regions.discard(idx)
        else:
            self._selected_regions.add(idx)
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
                if i in self._selected_regions:
                    cv2.drawContours(overlay, [pts], -1, (0, 100, 255, 180), -1)
                    cv2.drawContours(overlay, [pts], -1, (0, 120, 255, 255), 2)
                else:
                    cv2.drawContours(overlay, [pts], -1, (255, 60, 60, 180), -1)
                    cv2.drawContours(overlay, [pts], -1, (255, 0, 0, 255), 1)
        qimg = QImage(overlay.data, w, h, w * 4, QImage.Format_RGBA8888)
        self._overlay_item.setPixmap(QPixmap.fromImage(qimg))

    def toggle_overlay(self, visible: bool):
        self._overlay_visible = visible
        self._refresh_overlay()

    def toggle_annotation(self, visible: bool):
        self._annotation_visible = visible

    def set_drawing_mode(self, mode: str):
        """Set brush mode: 'erase', 'add', or None to disable."""
        self._drawing_mode = mode
        if mode:
            self._brush_mask = np.zeros(self._image_bgr.shape[:2], dtype=np.uint8) if self._image_bgr is not None else None
            self.setCursor(Qt.CrossCursor)
        else:
            self._brush_mask = None
            self.setCursor(Qt.ArrowCursor)

    def _draw_sample_marker(self, px, py):
        """Draw a bright green crosshair at the sampled point."""
        if self._image_bgr is None:
            return
        h, w = self._image_bgr.shape[:2]
        marker = np.zeros((h, w, 4), dtype=np.uint8)
        r = 10
        cv2.line(marker, (px - r, py), (px + r, py), (0, 255, 0, 255), 2)
        cv2.line(marker, (px, py - r), (px, py + r), (0, 255, 0, 255), 2)
        cv2.circle(marker, (px, py), r, (0, 255, 0, 255), 1)
        qimg = QImage(marker.data, w, h, w * 4, QImage.Format_RGBA8888)
        self._annotation_item.setPixmap(QPixmap.fromImage(qimg))
        self._annotation_item.setVisible(True)

    # ── Zoom ──

    def zoom_in(self):
        self.scale(1.25, 1.25)

    def zoom_out(self):
        self.scale(0.8, 0.8)

    def zoom_fit(self):
        self._fit_to_window()

    def zoom_100(self):
        self.resetTransform()

    # ── Mouse Events ──

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._drawing_mode and self._image_bgr is not None:
            self._draw_brush_at(self.mapToScene(event.pos()))
            self._is_drawing = True
            event.accept()
            return
        if event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            clicked_region = False
            for i, region in enumerate(self._regions):
                pts = np.array(region.contour, dtype=np.int32)
                if pts.ndim == 2 and pts.shape[0] >= 3:
                    if cv2.pointPolygonTest(pts, (pos.x(), pos.y()), False) >= 0:
                        self.region_selected.emit(i)
                        clicked_region = True
                        break
            if not clicked_region and self._image_bgr is not None:
                px, py = int(pos.x()), int(pos.y())
                h, w = self._image_bgr.shape[:2]
                if 0 <= px < w and 0 <= py < h:
                    self.color_sampled.emit(self._image_bgr[py, px])
                    self.point_sampled.emit(px, py)
                    self._draw_sample_marker(px, py)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drawing_mode and getattr(self, '_is_drawing', False):
            self._draw_brush_at(self.mapToScene(event.pos()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if getattr(self, '_is_drawing', False):
            self._is_drawing = False
            self._apply_brush()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _draw_brush_at(self, pos):
        if self._brush_mask is None: return
        px, py = int(pos.x()), int(pos.y())
        r = self._brush_radius
        val = 0 if self._drawing_mode == 'erase' else 255
        cv2.circle(self._brush_mask, (px, py), r, val, -1)
        # Show brush preview on annotation layer
        self._refresh_brush_preview()

    def _refresh_brush_preview(self):
        if self._brush_mask is None or self._image_bgr is None: return
        h, w = self._image_bgr.shape[:2]
        preview = np.zeros((h, w, 4), dtype=np.uint8)
        mask_bin = (self._brush_mask > 0).astype(np.uint8)
        preview[mask_bin > 0] = (0, 255, 0, 100) if self._drawing_mode == 'add' else (255, 0, 0, 100)
        qimg = QImage(preview.data, w, h, w * 4, QImage.Format_RGBA8888)
        self._annotation_item.setPixmap(QPixmap.fromImage(qimg))
        self._annotation_item.setVisible(True)

    def _apply_brush(self):
        """Merge brush strokes into existing regions."""
        if self._brush_mask is None or self._image_bgr is None: return
        h, w = self._image_bgr.shape[:2]
        # Build mask from existing regions
        existing = np.zeros((h, w), dtype=np.uint8)
        for region in self._regions:
            pts = np.array(region.contour, dtype=np.int32)
            if pts.ndim == 2 and pts.shape[0] >= 3:
                cv2.drawContours(existing, [pts], -1, 255, -1)
        # Apply brush
        if self._drawing_mode == 'erase':
            existing[self._brush_mask > 0] = 0  # remove
        else:
            existing[self._brush_mask > 0] = 255  # add
        # Extract new regions
        contours, _ = cv2.findContours(existing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        new_regions = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 5: continue
            M = cv2.moments(cnt)
            cx = M["m10"] / M["m00"] if M["m00"] != 0 else 0.0
            cy = M["m01"] / M["m00"] if M["m00"] != 0 else 0.0
            x, y, bw, bh = cv2.boundingRect(cnt)
            from core_analysis.data.models import MaskRegion
            new_regions.append(MaskRegion(
                contour=cnt.squeeze(1).tolist() if len(cnt.shape) == 3 else [],
                area_px=area, centroid=(cx, cy), bbox=(x, y, bw, bh)))
        self.set_regions(new_regions)
        self._brush_mask = np.zeros((h, w), dtype=np.uint8)
        self._annotation_item.setVisible(False)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            delta = 2 if event.angleDelta().y() > 0 else -2
            self.rotate_view(delta)
            event.accept()
            return
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    # ── Properties ──

    def set_roi_rect(self, x1, y1, x2, y2):
        """Set a rectangular analysis mask. Only pixels inside are analyzed."""
        if self._image_bgr is None: return
        h, w = self._image_bgr.shape[:2]
        if x1 > x2: x1, x2 = x2, x1
        if y1 > y2: y1, y2 = y2, y1
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        self._analysis_mask = np.zeros((h, w), dtype=np.uint8)
        self._analysis_mask[y1:y2, x1:x2] = 255
        self._show_roi_overlay()

    def clear_roi(self):
        """Remove analysis mask."""
        self._analysis_mask = None
        self._show_roi_overlay()

    def _show_roi_overlay(self):
        """Draw ROI boundary on annotation layer."""
        if self._image_bgr is None: return
        h, w = self._image_bgr.shape[:2]
        overlay = np.zeros((h, w, 4), dtype=np.uint8)
        if self._analysis_mask is not None:
            contours, _ = cv2.findContours(self._analysis_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(overlay, contours, -1, (0, 255, 0, 255), 2)
        qimg = QImage(overlay.data, w, h, w * 4, QImage.Format_RGBA8888)
        self._annotation_item.setPixmap(QPixmap.fromImage(qimg))
        self._annotation_item.setVisible(True)

    @property
    def analysis_mask(self):
        return self._analysis_mask

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
