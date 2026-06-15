"""HoleAnalyzer — quantitative hole analysis from extracted regions."""

import math
from core_analysis.data.models import MaskRegion, HoleResult


class HoleAnalyzer:
    @staticmethod
    def analyze(regions: list, scale_mm_per_px: float,
                image_area_px: float) -> tuple:
        """Analyze hole regions. Returns (list of HoleResult, summary_dict)."""
        results = []
        total_area_mm2 = 0.0
        diameters = []

        for i, region in enumerate(regions):
            area_mm2 = region.area_px * (scale_mm_per_px ** 2)
            d = 2.0 * math.sqrt(area_mm2 / math.pi)
            size_cat = HoleAnalyzer._classify_size(d)
            result = HoleResult(
                region_index=i,
                area_mm2=round(area_mm2, 4),
                equivalent_d_mm=round(d, 4),
                size_category=size_cat
            )
            results.append(result)
            total_area_mm2 += area_mm2
            diameters.append(d)

        n = len(results)
        avg_d = round(sum(diameters) / n, 4) if n > 0 else 0.0
        porosity = (total_area_mm2 / (image_area_px * scale_mm_per_px ** 2) * 100) \
                   if image_area_px > 0 else 0.0

        size_dist = {"大洞": 0, "中洞": 0, "小洞": 0, "针孔/溶孔": 0}
        for r in results:
            if r.size_category in size_dist:
                size_dist[r.size_category] += 1

        summary = {
            "total_count": n,
            "total_area_mm2": round(total_area_mm2, 4),
            "avg_area_mm2": round(total_area_mm2 / n, 4) if n > 0 else 0.0,
            "avg_equivalent_d_mm": avg_d,
            "max_equivalent_d_mm": round(max(diameters), 4) if diameters else 0.0,
            "min_equivalent_d_mm": round(min(diameters), 4) if diameters else 0.0,
            "porosity_percent": round(porosity, 2),
            "size_distribution": size_dist,
            "diameters": diameters,
        }
        return results, summary

    @staticmethod
    def _classify_size(diameter_mm: float) -> str:
        if diameter_mm > 10:
            return "大洞"
        elif diameter_mm >= 5:
            return "中洞"
        elif diameter_mm >= 1:
            return "小洞"
        else:
            return "针孔/溶孔"
