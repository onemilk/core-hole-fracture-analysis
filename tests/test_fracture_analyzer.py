"""Tests for FractureAnalyzer"""

import numpy as np
import cv2
from core_analysis.engine.fracture_analyzer import FractureAnalyzer
from core_analysis.data.models import MaskRegion


def _make_line_region():
    """Create a thin rectangular region simulating a fracture."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    cv2.rectangle(mask, (20, 45), (80, 55), 255, -1)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnt = cnts[0]
    return MaskRegion(
        contour=cnt.squeeze(1).tolist(),
        area_px=cv2.contourArea(cnt),
        centroid=(50, 50),
        bbox=(20, 45, 60, 10)
    )


class TestFractureAnalyzer:
    def test_analyze_single_fracture(self):
        region = _make_line_region()
        scale = 0.05
        image_area_px = 10000
        results, summary = FractureAnalyzer.analyze([region], scale, image_area_px, 0.5)
        assert len(results) == 1
        r = results[0]
        assert r.length_mm > 0
        assert r.width_mm > 0
        assert r.area_mm2 > 0
        assert r.porosity < 100

    def test_summary_values(self):
        region = _make_line_region()
        scale = 0.05
        image_area_px = 10000
        _, summary = FractureAnalyzer.analyze([region], scale, image_area_px, 0.5)
        assert summary["total_count"] == 1
        assert summary["total_area_mm2"] > 0
        assert 0 < summary["porosity_percent"] < 100
        assert summary["total_length_mm"] > 0

    def test_empty_regions(self):
        results, summary = FractureAnalyzer.analyze([], 0.05, 10000, 0.5)
        assert results == []
        assert summary["total_count"] == 0
