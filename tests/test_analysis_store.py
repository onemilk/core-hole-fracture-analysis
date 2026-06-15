"""Tests for AnalysisStore"""
import json
import pytest
from core_analysis.data.database import ProjectManager
from core_analysis.data.image_repository import ImageRepository
from core_analysis.data.analysis_store import AnalysisStore
from core_analysis.data.models import (
    Category, ImageRecord, HoleResult, FractureResult, AnalysisSession
)


@pytest.fixture
def store(tmp_path):
    db_path = str(tmp_path / "test.db")
    pm = ProjectManager(db_path)
    pm.initialize()
    repo = ImageRepository(pm)
    cat_id = repo.add_category(Category(name="test", type="basin"))
    img_id = repo.add_image(ImageRecord(category_id=cat_id, filename="t.jpg", filepath="/t.jpg"))
    return AnalysisStore(pm), img_id


class TestAnalysisStore:
    def test_create_session(self, store):
        s, img_id = store
        session = AnalysisSession(image_id=img_id, analysis_type="hole",
                                  params_json='{"match":85}')
        session_id = s.create_session(session)
        assert session_id == 1
        loaded = s.get_session(session_id)
        assert loaded.analysis_type == "hole"

    def test_save_hole_results(self, store):
        s, img_id = store
        session = AnalysisSession(image_id=img_id, analysis_type="hole")
        session_id = s.create_session(session)
        results = [
            HoleResult(image_id=img_id, session_id=session_id, region_index=0,
                       area_mm2=10.5, equivalent_d_mm=3.66, fill_status="未充填"),
            HoleResult(image_id=img_id, session_id=session_id, region_index=1,
                       area_mm2=5.0, equivalent_d_mm=2.52, fill_status="半充填"),
        ]
        s.save_hole_results(results)
        loaded = s.get_hole_results(session_id)
        assert len(loaded) == 2
        assert loaded[0].region_index == 0
        assert loaded[0].area_mm2 == 10.5

    def test_save_fracture_results(self, store):
        s, img_id = store
        session = AnalysisSession(image_id=img_id, analysis_type="fracture")
        session_id = s.create_session(session)
        results = [
            FractureResult(image_id=img_id, session_id=session_id, region_index=0,
                           length_mm=28.5, width_mm=0.45, area_mm2=12.8),
        ]
        s.save_fracture_results(results)
        loaded = s.get_fracture_results(session_id)
        assert len(loaded) == 1
        assert loaded[0].length_mm == 28.5

    def test_update_session_report(self, store):
        s, img_id = store
        session = AnalysisSession(image_id=img_id, analysis_type="hole")
        session_id = s.create_session(session)
        s.update_session_report(session_id, "<html>report</html>")
        updated = s.get_session(session_id)
        assert updated.report_html == "<html>report</html>"

    def test_get_sessions_by_image(self, store):
        s, img_id = store
        s.create_session(AnalysisSession(image_id=img_id, analysis_type="hole"))
        s.create_session(AnalysisSession(image_id=img_id, analysis_type="fracture"))
        sessions = s.get_sessions_by_image(img_id)
        assert len(sessions) == 2
