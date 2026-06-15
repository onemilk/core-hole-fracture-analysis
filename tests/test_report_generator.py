"""Tests for ReportGenerator"""
from core_analysis.engine.report_generator import ReportGenerator


class TestReportGenerator:
    def test_generate_hole_report(self):
        summary = {
            "total_count": 3, "total_area_mm2": 45.0, "avg_area_mm2": 15.0,
            "porosity_percent": 8.2, "avg_equivalent_d_mm": 3.6,
            "max_equivalent_d_mm": 12.3, "min_equivalent_d_mm": 0.8,
            "size_distribution": {"大洞": 1, "中洞": 1, "小洞": 1, "针孔/溶孔": 0},
            "diameters": [12.3, 5.5, 0.9]
        }
        fill_stats = [
            {"status": "未充填", "count": 1, "area": 18.2, "percent": 40.4},
            {"status": "半充填", "count": 1, "area": 16.8, "percent": 37.3},
            {"status": "全充填", "count": 1, "area": 10.0, "percent": 22.2},
        ]
        effect = {"valid": 1, "semi_valid": 1, "invalid": 1}
        info = {"image_id": "J12-3-1560", "well": "J12-3", "depth": "1560.0",
                "layer": "沙河街组", "lithology": "灰岩", "scale": "0.05",
                "date": "2026-06-16", "analyst": "测试"}

        html = ReportGenerator.generate_hole_report(summary, fill_stats, effect, info)
        assert "<!DOCTYPE html>" in html
        assert "J12-3" in html
        assert "孔洞总数" in html

    def test_generate_fracture_report(self):
        summary = {
            "total_count": 3, "total_area_mm2": 32.6, "porosity_percent": 5.5,
            "total_length_mm": 156.3, "surface_density": 0.26,
            "linear_density": 1.6, "avg_spacing_mm": 13.4
        }
        fractures = [
            {"length_mm": 28.5, "width_mm": 0.45, "area_mm2": 12.8,
             "fracture_type": "构造缝", "fill_status": "张开缝(未充填)", "effectiveness": "有效"},
        ]
        type_stats = [{"type": "构造缝", "count": 2, "total_length": 68.5}]
        info = {"image_id": "J12-3-1560", "well": "J12-3", "depth": "1560.0",
                "layer": "沙河街组", "lithology": "灰岩", "scale": "0.05",
                "date": "2026-06-16", "analyst": "测试"}

        html = ReportGenerator.generate_fracture_report(summary, fractures, type_stats, info)
        assert "<!DOCTYPE html>" in html
        assert "J12-3" in html
        assert "裂缝总条数" in html
