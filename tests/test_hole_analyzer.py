"""Tests for HoleAnalyzer"""
import numpy as np
import cv2
from core_analysis.engine.hole_analyzer import HoleAnalyzer
from core_analysis.data.models import MaskRegion


def _make_regions():
    """Create two simulated hole regions (circular masks)."""
    mask1 = np.zeros((100, 100), dtype=np.uint8)
    cv2.circle(mask1, (30, 30), 20, 255, -1)
    cnt1, _ = cv2.findContours(mask1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    r1 = MaskRegion(
        contour=cnt1[0].squeeze(1).tolist(),
        area_px=cv2.contourArea(cnt1[0]),
        centroid=(30, 30),
        bbox=(10, 10, 40, 40)
    )
    mask2 = np.zeros((100, 100), dtype=np.uint8)
    cv2.circle(mask2, (70, 70), 10, 255, -1)
    cnt2, _ = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    r2 = MaskRegion(
        contour=cnt2[0].squeeze(1).tolist(),
        area_px=cv2.contourArea(cnt2[0]),
        centroid=(70, 70),
        bbox=(60, 60, 20, 20)
    )
    return [r1, r2]


class TestHoleAnalyzer:
    def test_analyze_regions(self):
        regions = _make_regions()
        scale = 0.05
        image_area_px = 10000
        results, summary = HoleAnalyzer.analyze(regions, scale, image_area_px)
        assert len(results) == 2
        for r in results:
            assert r.area_mm2 > 0
            assert r.equivalent_d_mm > 0
            assert r.size_category in ("大洞", "中洞", "小洞", "针孔/溶孔")
        assert summary["total_count"] == 2
        assert summary["total_area_mm2"] > 0
        assert 0 < summary["porosity_percent"] < 100

    def test_size_classification(self):
        regions = _make_regions()
        scale = 1.0
        image_area_px = 10000
        _, summary = HoleAnalyzer.analyze(regions, scale, image_area_px)
        assert "size_distribution" in summary

    def test_empty_regions(self):
        results, summary = HoleAnalyzer.analyze([], 0.05, 10000)
        assert results == []
        assert summary["total_count"] == 0
        assert summary["porosity_percent"] == 0.0
