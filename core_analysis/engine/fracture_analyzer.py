"""FractureAnalyzer — quantitative fracture analysis from extracted regions."""

import cv2
import numpy as np
import math
from core_analysis.data.models import MaskRegion, FractureResult


class FractureAnalyzer:
    @staticmethod
    def analyze(regions: list, scale_mm_per_px: float,
                image_area_px: float, core_length_m: float) -> tuple:
        """Analyze fracture regions. Returns (list of FractureResult, summary_dict).
        Uses skeletonization (Zhang-Suen thinning) for length.
        Width = Area / Length."""
        results = []
        total_area_mm2 = 0.0
        total_length_mm = 0.0

        for i, region in enumerate(regions):
            bx, by, bw, bh = region.bbox
            pad = 10
            mask = np.zeros((bh + pad * 2, bw + pad * 2), dtype=np.uint8)
            pts = np.array(region.contour, dtype=np.int32)
            if pts.ndim == 2 and pts.shape[0] >= 3:
                pts_shifted = pts - [bx - pad, by - pad]
                cv2.drawContours(mask, [pts_shifted], -1, 255, -1)

            skeleton = cv2.ximgproc.thinning(mask, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
            length_px = np.count_nonzero(skeleton)
            area_px = region.area_px

            length_mm = length_px * scale_mm_per_px
            area_mm2 = area_px * (scale_mm_per_px ** 2)
            width_mm = area_mm2 / length_mm if length_mm > 0 else 0.0
            porosity = (area_mm2 / (image_area_px * scale_mm_per_px ** 2)) * 100 \
                       if image_area_px > 0 else 0.0

            result = FractureResult(
                region_index=i,
                length_mm=round(length_mm, 4),
                width_mm=round(width_mm, 4),
                area_mm2=round(area_mm2, 4),
                porosity=round(porosity, 4)
            )
            results.append(result)
            total_area_mm2 += area_mm2
            total_length_mm += length_mm

        n = len(results)
        total_porosity = (total_area_mm2 / (image_area_px * scale_mm_per_px ** 2) * 100) \
                         if image_area_px > 0 else 0.0
        image_area_m2 = image_area_px * (scale_mm_per_px ** 2) / 1_000_000
        surface_density = (total_length_mm / 1000) / image_area_m2 if image_area_m2 > 0 else 0.0
        linear_density = n / core_length_m if core_length_m > 0 else 0.0
        avg_spacing = (core_length_m * 1000 - total_length_mm) / n if n > 1 else 0.0

        summary = {
            "total_count": n,
            "total_area_mm2": round(total_area_mm2, 4),
            "porosity_percent": round(total_porosity, 2),
            "total_length_mm": round(total_length_mm, 4),
            "surface_density": round(surface_density, 4),
            "linear_density": round(linear_density, 4),
            "avg_spacing_mm": round(avg_spacing, 4),
        }
        return results, summary
