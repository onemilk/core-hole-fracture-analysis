"""ImageRepository — CRUD for categories and images."""

from typing import Optional
from core_analysis.data.models import Category, ImageRecord


class ImageRepository:
    def __init__(self, project_manager):
        self.pm = project_manager

    def add_category(self, category: Category) -> int:
        conn = self.pm.get_connection()
        cursor = conn.execute(
            "INSERT INTO categories (name, parent_id, type) VALUES (?, ?, ?)",
            (category.name, category.parent_id, category.type)
        )
        conn.commit()
        cat_id = cursor.lastrowid
        conn.close()
        return cat_id

    def get_category(self, category_id: int) -> Optional[Category]:
        conn = self.pm.get_connection()
        row = conn.execute(
            "SELECT id, name, parent_id, type FROM categories WHERE id = ?",
            (category_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return Category(id=row["id"], name=row["name"],
                        parent_id=row["parent_id"], type=row["type"])

    def get_category_tree(self, parent_id: Optional[int] = None) -> list:
        conn = self.pm.get_connection()
        rows = conn.execute(
            "SELECT id, name, parent_id, type FROM categories WHERE parent_id IS ?",
            (parent_id,)
        ).fetchall()
        conn.close()
        return [Category(id=r["id"], name=r["name"],
                         parent_id=r["parent_id"], type=r["type"]) for r in rows]

    def get_child_categories(self, parent_id: int) -> list:
        conn = self.pm.get_connection()
        rows = conn.execute(
            "SELECT id, name, parent_id, type FROM categories WHERE parent_id = ?",
            (parent_id,)
        ).fetchall()
        conn.close()
        return [Category(id=r["id"], name=r["name"],
                         parent_id=r["parent_id"], type=r["type"]) for r in rows]

    def add_image(self, image: ImageRecord) -> int:
        conn = self.pm.get_connection()
        cursor = conn.execute(
            """INSERT INTO images (category_id, filename, filepath, capture_date,
               depth_from, depth_to, scale_value, scale_unit, dpi, lithology, description)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (image.category_id, image.filename, image.filepath, image.capture_date,
             image.depth_from, image.depth_to, image.scale_value, image.scale_unit,
             image.dpi, image.lithology, image.description)
        )
        conn.commit()
        img_id = cursor.lastrowid
        conn.close()
        return img_id

    def get_image(self, image_id: int) -> Optional[ImageRecord]:
        conn = self.pm.get_connection()
        row = conn.execute(
            "SELECT * FROM images WHERE id = ?", (image_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return self._row_to_image(row)

    def get_images_by_category(self, category_id: int) -> list:
        conn = self.pm.get_connection()
        rows = conn.execute(
            "SELECT * FROM images WHERE category_id = ? ORDER BY depth_from",
            (category_id,)
        ).fetchall()
        conn.close()
        return [self._row_to_image(r) for r in rows]

    def search_images(self, query: str) -> list:
        conn = self.pm.get_connection()
        pattern = f"%{query}%"
        rows = conn.execute(
            """SELECT * FROM images WHERE filename LIKE ? OR lithology LIKE ?
               OR description LIKE ?""",
            (pattern, pattern, pattern)
        ).fetchall()
        conn.close()
        return [self._row_to_image(r) for r in rows]

    def update_image(self, image: ImageRecord):
        conn = self.pm.get_connection()
        conn.execute(
            """UPDATE images SET category_id=?, filename=?, filepath=?, capture_date=?,
               depth_from=?, depth_to=?, scale_value=?, scale_unit=?, dpi=?,
               lithology=?, description=? WHERE id=?""",
            (image.category_id, image.filename, image.filepath, image.capture_date,
             image.depth_from, image.depth_to, image.scale_value, image.scale_unit,
             image.dpi, image.lithology, image.description, image.id)
        )
        conn.commit()
        conn.close()

    def delete_image(self, image_id: int):
        conn = self.pm.get_connection()
        conn.execute("DELETE FROM images WHERE id = ?", (image_id,))
        conn.commit()
        conn.close()

    def get_all_images(self) -> list:
        conn = self.pm.get_connection()
        rows = conn.execute("SELECT * FROM images ORDER BY created_at DESC").fetchall()
        conn.close()
        return [self._row_to_image(r) for r in rows]

    def _row_to_image(self, row) -> ImageRecord:
        return ImageRecord(
            id=row["id"], category_id=row["category_id"],
            filename=row["filename"], filepath=row["filepath"],
            capture_date=row["capture_date"] or "",
            depth_from=row["depth_from"], depth_to=row["depth_to"],
            scale_value=row["scale_value"], scale_unit=row["scale_unit"],
            dpi=row["dpi"], lithology=row["lithology"] or "",
            description=row["description"] or "", created_at=row["created_at"] or ""
        )
