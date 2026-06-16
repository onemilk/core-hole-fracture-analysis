"""Tests for image rotation and flip operations."""
import numpy as np
import cv2
from core_analysis.engine.image_processor import ImageProcessor


def _make_test_image(w=120, h=80):
    img = np.ones((h, w, 3), dtype=np.uint8) * 200
    cv2.rectangle(img, (40, 30), (80, 50), (50, 50, 50), -1)
    return img


class TestRotation:
    def test_rotate_90(self):
        img = _make_test_image()
        result = ImageProcessor.rotate(img, 90)
        assert result.shape[0] == img.shape[1]
        assert result.shape[1] == img.shape[0]

    def test_rotate_180_shape_unchanged(self):
        img = _make_test_image()
        result = ImageProcessor.rotate(img, 180)
        assert result.shape == img.shape

    def test_rotate_45(self):
        img = _make_test_image()
        result = ImageProcessor.rotate(img, 45)
        assert result.shape[0] >= img.shape[0]

    def test_flip_horizontal(self):
        img = _make_test_image()
        result = ImageProcessor.flip_horizontal(img)
        assert result.shape == img.shape
        assert result[0, 0, 0] == img[0, -1, 0]

    def test_flip_vertical(self):
        img = _make_test_image()
        result = ImageProcessor.flip_vertical(img)
        assert result.shape == img.shape
        assert result[-1, 0, 0] == img[0, 0, 0]

    def test_detect_orientation_returns_angle(self):
        img = np.ones((100, 200, 3), dtype=np.uint8) * 200
        cv2.line(img, (40, 50), (160, 50), (30, 30, 30), 3)
        angle = ImageProcessor.detect_orientation(img)
        assert abs(abs(angle) - 0) < 10 or abs(abs(angle) - 180) < 10

    def test_auto_rotate(self):
        img = np.ones((200, 200, 3), dtype=np.uint8) * 200
        cv2.line(img, (50, 50), (150, 150), (30, 30, 30), 3)
        result = ImageProcessor.auto_rotate(img)
        assert result.shape == img.shape
        assert result.dtype == np.uint8


class TestRegionRotation:
    def test_rotate_region_stays_valid(self):
        """Region rotated 90 should still produce a valid MaskRegion."""
        import cv2
        from core_analysis.data.models import MaskRegion
        from core_analysis.engine.morphology_engine import MorphologyEngine

        mask = np.zeros((100, 100), dtype=np.uint8)
        cv2.rectangle(mask, (20, 45), (80, 55), 255, -1)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        region = MaskRegion(
            contour=cnts[0].squeeze(1).tolist(),
            area_px=cv2.contourArea(cnts[0]),
            centroid=(50, 50),
            bbox=(20, 45, 60, 10)
        )
        result = MorphologyEngine.rotate_region(region, 90, (100, 100))
        assert result is not None
        assert result.area_px > 0
