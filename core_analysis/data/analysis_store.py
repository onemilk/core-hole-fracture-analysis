"""AnalysisStore — CRUD for analysis sessions, hole results, fracture results."""

from typing import Optional
from core_analysis.data.models import HoleResult, FractureResult, AnalysisSession


class AnalysisStore:
    def __init__(self, project_manager):
        self.pm = project_manager

    def create_session(self, session: AnalysisSession) -> int:
        conn = self.pm.get_connection()
        cursor = conn.execute(
            "INSERT INTO analysis_sessions (image_id, analysis_type, params_json) VALUES (?, ?, ?)",
            (session.image_id, session.analysis_type, session.params_json)
        )
        conn.commit()
        sid = cursor.lastrowid
        conn.close()
        return sid

    def get_session(self, session_id: int) -> Optional[AnalysisSession]:
        conn = self.pm.get_connection()
        row = conn.execute(
            "SELECT * FROM analysis_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return AnalysisSession(
            id=row["id"], image_id=row["image_id"],
            analysis_type=row["analysis_type"],
            params_json=row["params_json"] or "",
            report_html=row["report_html"] or "",
            created_at=row["created_at"] or "",
            updated_at=row["updated_at"] or ""
        )

    def get_sessions_by_image(self, image_id: int) -> list:
        conn = self.pm.get_connection()
        rows = conn.execute(
            "SELECT * FROM analysis_sessions WHERE image_id = ? ORDER BY created_at DESC",
            (image_id,)
        ).fetchall()
        conn.close()
        return [AnalysisSession(
            id=r["id"], image_id=r["image_id"], analysis_type=r["analysis_type"],
            params_json=r["params_json"] or "", report_html=r["report_html"] or "",
            created_at=r["created_at"] or "", updated_at=r["updated_at"] or ""
        ) for r in rows]

    def update_session_report(self, session_id: int, report_html: str):
        conn = self.pm.get_connection()
        conn.execute(
            "UPDATE analysis_sessions SET report_html=?, updated_at=datetime('now') WHERE id=?",
            (report_html, session_id)
        )
        conn.commit()
        conn.close()

    def save_hole_results(self, results: list):
        conn = self.pm.get_connection()
        conn.execute("DELETE FROM hole_results WHERE session_id = ?",
                     (results[0].session_id,))
        for r in results:
            conn.execute(
                """INSERT INTO hole_results
                   (image_id, session_id, region_index, area_mm2, equivalent_d_mm,
                    fill_status, fill_material, effectiveness, hole_type,
                    size_category, is_valid, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r.image_id, r.session_id, r.region_index, r.area_mm2,
                 r.equivalent_d_mm, r.fill_status, r.fill_material,
                 r.effectiveness, r.hole_type, r.size_category,
                 int(r.is_valid), r.notes)
            )
        conn.commit()
        conn.close()

    def get_hole_results(self, session_id: int) -> list:
        conn = self.pm.get_connection()
        rows = conn.execute(
            "SELECT * FROM hole_results WHERE session_id = ? ORDER BY region_index",
            (session_id,)
        ).fetchall()
        conn.close()
        return [HoleResult(
            id=r["id"], image_id=r["image_id"], session_id=r["session_id"],
            region_index=r["region_index"], area_mm2=r["area_mm2"],
            equivalent_d_mm=r["equivalent_d_mm"],
            fill_status=r["fill_status"] or "", fill_material=r["fill_material"] or "",
            effectiveness=r["effectiveness"] or "", hole_type=r["hole_type"] or "",
            size_category=r["size_category"] or "", is_valid=bool(r["is_valid"]),
            notes=r["notes"] or "", created_at=r["created_at"] or ""
        ) for r in rows]

    def save_fracture_results(self, results: list):
        conn = self.pm.get_connection()
        conn.execute("DELETE FROM fracture_results WHERE session_id = ?",
                     (results[0].session_id,))
        for r in results:
            conn.execute(
                """INSERT INTO fracture_results
                   (image_id, session_id, region_index, length_mm, width_mm,
                    area_mm2, porosity, fracture_type, fill_status,
                    fill_material, effectiveness, is_valid, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r.image_id, r.session_id, r.region_index, r.length_mm,
                 r.width_mm, r.area_mm2, r.porosity, r.fracture_type,
                 r.fill_status, r.fill_material, r.effectiveness,
                 int(r.is_valid), r.notes)
            )
        conn.commit()
        conn.close()

    def get_fracture_results(self, session_id: int) -> list:
        conn = self.pm.get_connection()
        rows = conn.execute(
            "SELECT * FROM fracture_results WHERE session_id = ? ORDER BY region_index",
            (session_id,)
        ).fetchall()
        conn.close()
        return [FractureResult(
            id=r["id"], image_id=r["image_id"], session_id=r["session_id"],
            region_index=r["region_index"], length_mm=r["length_mm"],
            width_mm=r["width_mm"], area_mm2=r["area_mm2"],
            porosity=r["porosity"],
            fracture_type=r["fracture_type"] or "",
            fill_status=r["fill_status"] or "",
            fill_material=r["fill_material"] or "",
            effectiveness=r["effectiveness"] or "",
            is_valid=bool(r["is_valid"]),
            notes=r["notes"] or "", created_at=r["created_at"] or ""
        ) for r in rows]

    def save_grain_results(self, results: list):
        conn = self.pm.get_connection()
        conn.execute("DELETE FROM grain_results WHERE session_id = ?",
                     (results[0].session_id,))
        for r in results:
            conn.execute(
                """INSERT INTO grain_results
                   (image_id, session_id, region_index, area_mm2, equivalent_d_mm,
                    perimeter_mm, feret_long_mm, feret_short_mm, circularity,
                    size_category, is_valid, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r.image_id, r.session_id, r.region_index, r.area_mm2,
                 r.equivalent_d_mm, r.perimeter_mm, r.feret_long_mm,
                 r.feret_short_mm, r.circularity, r.size_category,
                 int(r.is_valid), r.notes)
            )
        conn.commit()
        conn.close()

    def get_grain_results(self, session_id: int) -> list:
        conn = self.pm.get_connection()
        rows = conn.execute(
            "SELECT * FROM grain_results WHERE session_id = ? ORDER BY region_index",
            (session_id,)
        ).fetchall()
        conn.close()
        from core_analysis.data.models import GrainResult
        return [GrainResult(
            id=r["id"], image_id=r["image_id"], session_id=r["session_id"],
            region_index=r["region_index"], area_mm2=r["area_mm2"],
            equivalent_d_mm=r["equivalent_d_mm"],
            perimeter_mm=r["perimeter_mm"] or 0.0,
            feret_long_mm=r["feret_long_mm"] or 0.0,
            feret_short_mm=r["feret_short_mm"] or 0.0,
            circularity=r["circularity"] or 0.0,
            size_category=r["size_category"] or "",
            is_valid=bool(r["is_valid"]),
            notes=r["notes"] or "", created_at=r["created_at"] or ""
        ) for r in rows]
