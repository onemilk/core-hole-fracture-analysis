"""End-to-end smoke test — validates the full pipeline without Qt."""

import pytest
import numpy as np
import cv2
from core_analysis.data.database import ProjectManager
from core_analysis.data.image_repository import ImageRepository
from core_analysis.data.analysis_store import AnalysisStore
from core_analysis.data.models import (
    Category, ImageRecord, HoleResult, FractureResult, AnalysisSession
)
from core_analysis.engine.image_processor import ImageProcessor
from core_analysis.engine.region_extractor import RegionExtractor
from core_analysis.engine.morphology_engine import MorphologyEngine
from core_analysis.engine.hole_analyzer import HoleAnalyzer
from core_analysis.engine.fracture_analyzer import FractureAnalyzer
from core_analysis.engine.report_generator import ReportGenerator


class TestFullPipeline:
    def test_hole_analysis_pipeline(self, tmp_path):
        # 1. Create a synthetic rock core image with holes
        img = np.ones((200, 300, 3), dtype=np.uint8) * 200
        cv2.circle(img, (60, 100), 25, (30, 30, 30), -1)
        cv2.circle(img, (150, 80), 18, (40, 40, 40), -1)
        cv2.circle(img, (220, 150), 30, (35, 35, 35), -1)
        img_path = str(tmp_path / "core.jpg")
        cv2.imwrite(img_path, img)

        # 2. Database setup
        db_path = str(tmp_path / "test.db")
        pm = ProjectManager(db_path)
        pm.initialize()
        repo = ImageRepository(pm)
        store = AnalysisStore(pm)

        cat_id = repo.add_category(Category(name="test", type="basin"))
        img_id = repo.add_image(ImageRecord(
            category_id=cat_id, filename="core.jpg", filepath=img_path,
            scale_value=0.05, lithology="灰岩"
        ))

        # 3. Extract regions
        loaded = cv2.imread(img_path)
        preprocessed = ImageProcessor.auto_levels(loaded)
        sample_color = preprocessed[100, 60]  # inside first hole
        regions = RegionExtractor.extract_by_color_sample(
            preprocessed, sample_color, match_tolerance=40)

        # 4. Morphology
        regions = MorphologyEngine.denoise_by_area(regions, min_area_px=20)
        assert len(regions) >= 3, f"Expected >=3 regions, got {len(regions)}"

        # 5. Hole analysis
        h, w = preprocessed.shape[:2]
        results, summary = HoleAnalyzer.analyze(regions, 0.05, h * w)
        assert summary["total_count"] >= 3
        assert summary["porosity_percent"] > 0

        # 6. Generate report
        fill_stats = [
            {"status": "未充填", "count": summary["total_count"],
             "area": summary["total_area_mm2"], "percent": 100.0}
        ]
        effect = {"valid": summary["total_count"], "semi_valid": 0, "invalid": 0}
        info = {"image_id": "test", "well": "test", "depth": "100",
                "layer": "test", "lithology": "灰岩", "scale": "0.05",
                "date": "2026-06-16", "analyst": "test"}
        html = ReportGenerator.generate_hole_report(summary, fill_stats, effect, info)
        assert "孔洞总数" in html or "total_count" in html.lower()

        # 7. Report has charts (base64 images)
        assert "base64" in html or "<img" in html
