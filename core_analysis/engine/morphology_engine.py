"""MorphologyEngine — morphological operations on extracted regions."""

import cv2
import numpy as np
from typing import Optional
from core_analysis.data.models import MaskRegion


class MorphologyEngine:
    @staticmethod
    def _region_to_mask(region: MaskRegion, shape: tuple) -> np.ndarray:
        mask = np.zeros(shape, dtype=np.uint8)
        pts = np.array(region.contour, dtype=np.int32)
        if pts.ndim == 2 and pts.shape[0] >= 3:
            cv2.drawContours(mask, [pts], -1, 255, -1)
        return mask

    @staticmethod
    def _mask_to_region(mask: np.ndarray, offset_x: int = 0,
                        offset_y: int = 0) -> Optional[MaskRegion]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        cnt = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(cnt)
        if area < 1:
            return None
        M = cv2.moments(cnt)
        cx = M["m10"] / M["m00"] if M["m00"] != 0 else 0.0
        cy = M["m01"] / M["m00"] if M["m00"] != 0 else 0.0
        x, y, w, h = cv2.boundingRect(cnt)
        return MaskRegion(
            contour=cnt.squeeze(1).tolist() if len(cnt.shape) == 3 else [],
            area_px=area,
            centroid=(cx + offset_x, cy + offset_y),
            bbox=(x + offset_x, y + offset_y, w, h)
        )

    @staticmethod
    def dilate_region(region: MaskRegion, kernel_size: int = 3,
                      iterations: int = 1) -> Optional[MaskRegion]:
        bx, by, bw, bh = region.bbox
        pad = kernel_size * iterations + 5
        shape = (bh + pad * 2, bw + pad * 2)
        mask = MorphologyEngine._region_to_mask(region, shape)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        dilated = cv2.dilate(mask, kernel, iterations=iterations)
        return MorphologyEngine._mask_to_region(dilated, bx - pad, by - pad)

    @staticmethod
    def erode_region(region: MaskRegion, kernel_size: int = 3,
                     iterations: int = 1) -> Optional[MaskRegion]:
        bx, by, bw, bh = region.bbox
        pad = kernel_size * iterations + 5
        shape = (bh + pad * 2, bw + pad * 2)
        mask = MorphologyEngine._region_to_mask(region, shape)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        eroded = cv2.erode(mask, kernel, iterations=iterations)
        return MorphologyEngine._mask_to_region(eroded, bx - pad, by - pad)

    @staticmethod
    def denoise_by_area(regions: list, min_area_px: float = 10,
                        max_area_px: float = float('inf')) -> list:
        return [r for r in regions if min_area_px <= r.area_px <= max_area_px]

    @staticmethod
    def fill_holes(region: MaskRegion, max_hole_size: float = 500) -> Optional[MaskRegion]:
        bx, by, bw, bh = region.bbox
        pad = 20
        shape = (bh + pad * 2, bw + pad * 2)
        mask = MorphologyEngine._region_to_mask(region, shape)
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        if hierarchy is None:
            return region
        for i, (cnt, h) in enumerate(zip(contours, hierarchy[0])):
            if h[3] != -1 and cv2.contourArea(cnt) <= max_hole_size:
                cv2.drawContours(mask, [cnt], -1, 255, -1)
        result = MorphologyEngine._mask_to_region(mask, bx - pad, by - pad)
        return result if result is not None else region
