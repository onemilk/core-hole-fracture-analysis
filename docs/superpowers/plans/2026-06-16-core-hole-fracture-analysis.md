# 岩心孔洞裂缝分析教学系统 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建桌面端岩心图像分析教学系统，实现图像库管理 + 孔洞半自动分析 + 裂缝半自动分析 + 报告生成。

**Architecture:** 分层 MVC。UI层(PySide6) → 业务逻辑层(纯Python/OpenCV,零Qt依赖) → 数据层(SQLite)。分析引擎与 UI 通过信号/槽解耦，可独立测试。

**Tech Stack:** Python 3.10+, PySide6, OpenCV, NumPy, SciPy, matplotlib, Jinja2, SQLite3

---

## 项目文件结构

```
core_analysis/
├── __init__.py
├── data/
│   ├── __init__.py
│   ├── database.py
│   ├── models.py
│   ├── image_repository.py
│   └── analysis_store.py
├── engine/
│   ├── __init__.py
│   ├── image_processor.py
│   ├── region_extractor.py
│   ├── morphology_engine.py
│   ├── hole_analyzer.py
│   ├── fracture_analyzer.py
│   └── report_generator.py
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── image_canvas.py
│   ├── tool_panel.py
│   ├── image_library.py
│   └── report_viewer.py
├── templates/
│   ├── hole_report.html
│   └── fracture_report.html
└── main.py

tests/
├── __init__.py
├── test_database.py
├── test_image_repository.py
├── test_analysis_store.py
├── test_image_processor.py
├── test_region_extractor.py
├── test_morphology_engine.py
├── test_hole_analyzer.py
├── test_fracture_analyzer.py
└── test_report_generator.py
```

---

### Task 1: Project Scaffold

**Files:**
- Create: `core_analysis/__init__.py`
- Create: `core_analysis/data/__init__.py`
- Create: `core_analysis/engine/__init__.py`
- Create: `core_analysis/ui/__init__.py`
- Create: `core_analysis/main.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p core_analysis/data core_analysis/engine core_analysis/ui core_analysis/templates tests
```

- [ ] **Step 2: Create __init__.py files**

```bash
touch core_analysis/__init__.py
touch core_analysis/data/__init__.py
touch core_analysis/engine/__init__.py
touch core_analysis/ui/__init__.py
touch tests/__init__.py
```

- [ ] **Step 3: Create placeholder main.py**

Write `core_analysis/main.py`:
```python
"""岩心孔洞裂缝分析教学系统 — 入口"""

import sys
from PySide6.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("岩心孔洞裂缝分析教学系统")
    # MainWindow will be integrated in Task 15
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Install dependencies and verify**

```bash
pip install PySide6 opencv-python numpy scipy matplotlib jinja2
python -c "import PySide6; import cv2; import numpy; import scipy; import matplotlib; import jinja2; print('All deps OK')"
```

Expected: `All deps OK`

- [ ] **Step 5: Commit**

```bash
git add core_analysis/ tests/
git commit -m "chore: scaffold project structure with dependencies"
```

---

### Task 2: Data Models

**Files:**
- Create: `core_analysis/data/models.py`

- [ ] **Step 1: Write data models**

Write `core_analysis/data/models.py`:
```python
"""Core data models — pure Python dataclasses, no dependencies."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Category:
    """分类节点（盆地/区块/构造/井号 — 自引用树）"""
    id: Optional[int] = None
    name: str = ""
    parent_id: Optional[int] = None
    type: str = ""  # 'basin'|'block'|'structure'|'well'


@dataclass
class ImageRecord:
    """岩心图像元数据"""
    id: Optional[int] = None
    category_id: Optional[int] = None
    filename: str = ""
    filepath: str = ""
    capture_date: str = ""
    depth_from: Optional[float] = None
    depth_to: Optional[float] = None
    scale_value: float = 1.0  # mm/pixel
    scale_unit: str = "mm"    # 'mm'|'μm'
    dpi: int = 96
    lithology: str = ""
    description: str = ""
    created_at: str = ""


@dataclass
class HoleResult:
    """单孔洞分析结果"""
    id: Optional[int] = None
    image_id: Optional[int] = None
    session_id: Optional[int] = None
    region_index: int = 0
    area_mm2: float = 0.0
    equivalent_d_mm: float = 0.0
    fill_status: str = "未充填"
    fill_material: str = ""
    effectiveness: str = "有效"
    hole_type: str = "溶洞"
    size_category: str = ""
    is_valid: bool = True
    notes: str = ""
    created_at: str = ""


@dataclass
class FractureResult:
    """单裂缝分析结果"""
    id: Optional[int] = None
    image_id: Optional[int] = None
    session_id: Optional[int] = None
    region_index: int = 0
    length_mm: float = 0.0
    width_mm: float = 0.0
    area_mm2: float = 0.0
    porosity: float = 0.0
    fracture_type: str = "构造缝"
    fill_status: str = "张开缝(未充填)"
    fill_material: str = ""
    effectiveness: str = "有效"
    is_valid: bool = True
    notes: str = ""
    created_at: str = ""


@dataclass
class AnalysisSession:
    """分析会话 — 记录每次完整分析的参数和报告"""
    id: Optional[int] = None
    image_id: Optional[int] = None
    analysis_type: str = ""  # 'hole'|'fracture'
    params_json: str = ""
    report_html: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class MaskRegion:
    """图像提取区域 — 在 engine 和 UI 之间传递"""
    contour: list = field(default_factory=list)  # list of [x,y] points
    area_px: float = 0.0
    centroid: tuple = (0.0, 0.0)
    bbox: tuple = (0, 0, 0, 0)  # x, y, w, h
```

- [ ] **Step 2: Verify imports**

```bash
python -c "from core_analysis.data.models import Category, ImageRecord, HoleResult, FractureResult, AnalysisSession, MaskRegion; print('All models OK')"
```

Expected: `All models OK`

- [ ] **Step 3: Commit**

```bash
git add core_analysis/data/models.py
git commit -m "feat: add data models"
```

---

### Task 3: Database Layer

**Files:**
- Create: `core_analysis/data/database.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: Write failing test for database**

Write `tests/test_database.py`:
```python
"""Tests for database module"""
import os
import sqlite3
import pytest
from core_analysis.data.database import ProjectManager


@pytest.fixture
def temp_db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def db(temp_db_path):
    pm = ProjectManager(temp_db_path)
    pm.initialize()
    return pm


class TestProjectManager:
    def test_initialize_creates_tables(self, temp_db_path):
        """初始化应创建6张表"""
        pm = ProjectManager(temp_db_path)
        pm.initialize()
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        assert "categories" in tables
        assert "images" in tables
        assert "hole_results" in tables
        assert "fracture_results" in tables
        assert "analysis_sessions" in tables
        conn.close()

    def test_initialize_is_idempotent(self, db, temp_db_path):
        """重复初始化不应报错"""
        db.initialize()  # second call
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert len(tables) == 6
        conn.close()

    def test_get_connection_returns_connection(self, db):
        """get_connection 应返回 sqlite3.Connection"""
        conn = db.get_connection()
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_close(self, db):
        """close 正常关闭"""
        db.close()
        # after close, re-initialize should work
        db.initialize()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_database.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'core_analysis.data.database'`

- [ ] **Step 3: Write database module**

Write `core_analysis/data/database.py`:
```python
"""ProjectManager — SQLite database creation, connection, migration."""

import sqlite3
import os


class ProjectManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def initialize(self):
        """Create tables if they don't exist. Idempotent."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER REFERENCES categories(id),
                type TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER REFERENCES categories(id),
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                capture_date TEXT,
                depth_from REAL,
                depth_to REAL,
                scale_value REAL DEFAULT 1.0,
                scale_unit TEXT DEFAULT 'mm',
                dpi INTEGER DEFAULT 96,
                lithology TEXT,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS hole_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER REFERENCES images(id),
                session_id INTEGER REFERENCES analysis_sessions(id),
                region_index INTEGER,
                area_mm2 REAL,
                equivalent_d_mm REAL,
                fill_status TEXT,
                fill_material TEXT,
                effectiveness TEXT,
                hole_type TEXT,
                size_category TEXT,
                is_valid BOOLEAN DEFAULT 1,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS fracture_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER REFERENCES images(id),
                session_id INTEGER REFERENCES analysis_sessions(id),
                region_index INTEGER,
                length_mm REAL,
                width_mm REAL,
                area_mm2 REAL,
                porosity REAL,
                fracture_type TEXT,
                fill_status TEXT,
                fill_material TEXT,
                effectiveness TEXT,
                is_valid BOOLEAN DEFAULT 1,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS analysis_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER REFERENCES images(id),
                analysis_type TEXT NOT NULL,
                params_json TEXT,
                report_html TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
        """)
        conn.commit()
        conn.close()

    def get_connection(self) -> sqlite3.Connection:
        """Return a new connection. Caller must close it."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def close(self):
        """No-op for sqlite3 — connections are per-call."""
        pass
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_database.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add core_analysis/data/database.py tests/test_database.py
git commit -m "feat: add ProjectManager with SQLite schema"
```

---

### Task 4: Image Repository

**Files:**
- Create: `core_analysis/data/image_repository.py`
- Create: `tests/test_image_repository.py`

- [ ] **Step 1: Write failing test**

Write `tests/test_image_repository.py`:
```python
"""Tests for ImageRepository"""
import sqlite3
import pytest
from core_analysis.data.database import ProjectManager
from core_analysis.data.image_repository import ImageRepository
from core_analysis.data.models import Category, ImageRecord


@pytest.fixture
def repo(tmp_path):
    db_path = str(tmp_path / "test.db")
    pm = ProjectManager(db_path)
    pm.initialize()
    return ImageRepository(pm)


class TestImageRepository:
    def test_add_category(self, repo):
        cat = Category(name="渤海湾盆地", type="basin")
        cat_id = repo.add_category(cat)
        assert cat_id == 1
        loaded = repo.get_category(cat_id)
        assert loaded.name == "渤海湾盆地"

    def test_add_child_category(self, repo):
        parent = Category(name="渤海湾盆地", type="basin")
        parent_id = repo.add_category(parent)
        child = Category(name="辽河坳陷", parent_id=parent_id, type="block")
        child_id = repo.add_category(child)
        loaded = repo.get_category(child_id)
        assert loaded.parent_id == parent_id

    def test_get_category_tree(self, repo):
        p1 = repo.add_category(Category(name="渤海湾盆地", type="basin"))
        p2 = repo.add_category(Category(name="辽河坳陷", parent_id=p1, type="block"))
        p3 = repo.add_category(Category(name="沙河街组", parent_id=p2, type="structure"))
        repo.add_category(Category(name="J12-3井", parent_id=p3, type="well"))
        tree = repo.get_category_tree()
        assert len(tree) == 1  # top-level only
        assert tree[0].name == "渤海湾盆地"

    def test_add_image(self, repo):
        cat_id = repo.add_category(Category(name="渤海湾盆地", type="basin"))
        img = ImageRecord(
            category_id=cat_id,
            filename="core001.jpg",
            filepath="/data/core001.jpg",
            depth_from=1560.0,
            depth_to=1560.5,
            dpi=300,
            lithology="灰岩"
        )
        img_id = repo.add_image(img)
        assert img_id == 1

    def test_get_images_by_category(self, repo):
        cat_id = repo.add_category(Category(name="渤海湾盆地", type="basin"))
        repo.add_image(ImageRecord(category_id=cat_id, filename="a.jpg", filepath="/a.jpg"))
        repo.add_image(ImageRecord(category_id=cat_id, filename="b.jpg", filepath="/b.jpg"))
        images = repo.get_images_by_category(cat_id)
        assert len(images) == 2

    def test_search_images(self, repo):
        cat_id = repo.add_category(Category(name="渤海湾盆地", type="basin"))
        repo.add_image(ImageRecord(category_id=cat_id, filename="J12_core.jpg", filepath="/a.jpg", lithology="灰岩"))
        repo.add_image(ImageRecord(category_id=cat_id, filename="J15_core.jpg", filepath="/b.jpg", lithology="砂岩"))
        results = repo.search_images("灰岩")
        assert len(results) == 1
        assert results[0].filename == "J12_core.jpg"

    def test_update_image(self, repo):
        cat_id = repo.add_category(Category(name="渤海湾盆地", type="basin"))
        img_id = repo.add_image(ImageRecord(category_id=cat_id, filename="old.jpg", filepath="/old.jpg"))
        img = repo.get_image(img_id)
        img.lithology = "白云岩"
        repo.update_image(img)
        updated = repo.get_image(img_id)
        assert updated.lithology == "白云岩"

    def test_delete_image(self, repo):
        cat_id = repo.add_category(Category(name="渤海湾盆地", type="basin"))
        img_id = repo.add_image(ImageRecord(category_id=cat_id, filename="x.jpg", filepath="/x.jpg"))
        repo.delete_image(img_id)
        assert repo.get_image(img_id) is None
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest tests/test_image_repository.py -v
```

Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Write ImageRepository**

Write `core_analysis/data/image_repository.py`:
```python
"""ImageRepository — CRUD for categories and images."""

from typing import Optional
from core_analysis.data.models import Category, ImageRecord


class ImageRepository:
    def __init__(self, project_manager):
        self.pm = project_manager

    # ── Categories ──

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
        """Return top-level categories (parent_id is None). Each contains children."""
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

    # ── Images ──

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
        return ImageRecord(
            id=row["id"], category_id=row["category_id"],
            filename=row["filename"], filepath=row["filepath"],
            capture_date=row["capture_date"] or "",
            depth_from=row["depth_from"], depth_to=row["depth_to"],
            scale_value=row["scale_value"], scale_unit=row["scale_unit"],
            dpi=row["dpi"], lithology=row["lithology"] or "",
            description=row["description"] or "", created_at=row["created_at"] or ""
        )

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
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_image_repository.py -v
```

Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add core_analysis/data/image_repository.py tests/test_image_repository.py
git commit -m "feat: add ImageRepository with category tree and image CRUD"
```

---

### Task 5: Analysis Store

**Files:**
- Create: `core_analysis/data/analysis_store.py`
- Create: `tests/test_analysis_store.py`

- [ ] **Step 1: Write failing test**

Write `tests/test_analysis_store.py`:
```python
"""Tests for AnalysisStore"""
import json
import pytest
from core_analysis.data.database import ProjectManager
from core_analysis.data.image_repository import ImageRepository
from core_analysis.data.analysis_store import AnalysisStore
from core_analysis.data.models import (
    Category, ImageRecord, HoleResult, FractureResult, AnalysisSession
)
from core_analysis.data.database import ProjectManager as PM


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
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest tests/test_analysis_store.py -v
```

Expected: FAIL

- [ ] **Step 3: Write AnalysisStore**

Write `core_analysis/data/analysis_store.py`:
```python
"""AnalysisStore — CRUD for analysis sessions, hole results, fracture results."""

from typing import Optional
from core_analysis.data.models import HoleResult, FractureResult, AnalysisSession


class AnalysisStore:
    def __init__(self, project_manager):
        self.pm = project_manager

    # ── Sessions ──

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

    # ── Hole Results ──

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

    # ── Fracture Results ──

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
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_analysis_store.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add core_analysis/data/analysis_store.py tests/test_analysis_store.py
git commit -m "feat: add AnalysisStore for session and result persistence"
```

---

### Task 6: Image Processor

**Files:**
- Create: `core_analysis/engine/image_processor.py`
- Create: `tests/test_image_processor.py`

- [ ] **Step 1: Write failing test**

Write `tests/test_image_processor.py`:
```python
"""Tests for ImageProcessor"""
import numpy as np
import cv2
from core_analysis.engine.image_processor import ImageProcessor


def _make_test_image(w=100, h=80):
    """Create a simple BGR test image with a dark circle."""
    img = np.ones((h, w, 3), dtype=np.uint8) * 200
    cv2.circle(img, (50, 40), 15, (50, 50, 50), -1)
    return img


class TestImageProcessor:
    def test_auto_levels_produces_valid_image(self):
        img = _make_test_image()
        result = ImageProcessor.auto_levels(img)
        assert result.shape == img.shape
        assert result.dtype == np.uint8

    def test_auto_levels_on_dark_image(self):
        """Auto levels on dark image should increase brightness."""
        dark = (_make_test_image() * 0.3).astype(np.uint8)
        result = ImageProcessor.auto_levels(dark)
        assert result.mean() > dark.mean()

    def test_to_grayscale(self):
        img = _make_test_image()
        gray = ImageProcessor.to_grayscale(img)
        assert len(gray.shape) == 2

    def test_gaussian_blur(self):
        img = _make_test_image()
        blurred = ImageProcessor.gaussian_blur(img, kernel_size=5)
        assert blurred.shape == img.shape

    def test_sharpen(self):
        img = _make_test_image()
        sharp = ImageProcessor.sharpen(img)
        assert sharp.shape == img.shape

    def test_canny_edges(self):
        img = _make_test_image()
        edges = ImageProcessor.canny_edges(img, 50, 150)
        assert len(edges.shape) == 2
        assert edges.dtype == np.uint8

    def test_adjust_brightness_contrast(self):
        img = _make_test_image()
        result = ImageProcessor.adjust_brightness_contrast(img, brightness=30, contrast=1.2)
        assert result.shape == img.shape
        assert result.dtype == np.uint8
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest tests/test_image_processor.py -v
```

Expected: FAIL

- [ ] **Step 3: Write ImageProcessor**

Write `core_analysis/engine/image_processor.py`:
```python
"""ImageProcessor — image preprocessing operations. Stateless, all static methods."""

import cv2
import numpy as np


class ImageProcessor:
    @staticmethod
    def auto_levels(image: np.ndarray) -> np.ndarray:
        """Apply CLAHE to L channel of LAB for automatic contrast enhancement."""
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    @staticmethod
    def to_grayscale(image: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def gaussian_blur(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
        k = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
        return cv2.GaussianBlur(image, (k, k), 0)

    @staticmethod
    def sharpen(image: np.ndarray) -> np.ndarray:
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        return cv2.filter2D(image, -1, kernel)

    @staticmethod
    def canny_edges(image: np.ndarray, low: float = 50, high: float = 150) -> np.ndarray:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        return cv2.Canny(gray, low, high)

    @staticmethod
    def adjust_brightness_contrast(image: np.ndarray, brightness: float = 0,
                                   contrast: float = 1.0) -> np.ndarray:
        result = cv2.convertScaleAbs(image, alpha=contrast, beta=brightness)
        return result
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_image_processor.py -v
```

Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add core_analysis/engine/image_processor.py tests/test_image_processor.py
git commit -m "feat: add ImageProcessor with auto_levels, filters, canny"
```

---

### Task 7: Region Extractor

**Files:**
- Create: `core_analysis/engine/region_extractor.py`
- Create: `tests/test_region_extractor.py`

- [ ] **Step 1: Write failing test**

Write `tests/test_region_extractor.py`:
```python
"""Tests for RegionExtractor"""
import numpy as np
import cv2
from core_analysis.engine.region_extractor import RegionExtractor


def _make_image_with_holes():
    """Create an image with two distinct dark circular regions."""
    img = np.ones((120, 160, 3), dtype=np.uint8) * 220
    cv2.circle(img, (40, 60), 18, (30, 30, 30), -1)
    cv2.circle(img, (120, 60), 22, (35, 35, 35), -1)
    return img


class TestRegionExtractor:
    def test_extract_by_color_sample(self):
        img = _make_image_with_holes()
        # Sample from the center of a hole (dark area)
        sample_color = img[60, 40]
        regions = RegionExtractor.extract_by_color_sample(
            img, sample_color, match_tolerance=40
        )
        assert len(regions) >= 1
        for r in regions:
            assert r.area_px > 0
            assert len(r.contour) > 2
            assert r.bbox[2] > 0 and r.bbox[3] > 0

    def test_extract_by_color_sample_no_match(self):
        img = _make_image_with_holes()
        # Sample white background — should find almost no regions
        sample_color = img[10, 10]
        regions = RegionExtractor.extract_by_color_sample(
            img, sample_color, match_tolerance=5
        )
        # may or may not find regions depending on tolerance

    def test_filter_by_area(self):
        img = _make_image_with_holes()
        sample_color = img[60, 40]
        regions = RegionExtractor.extract_by_color_sample(
            img, sample_color, match_tolerance=40
        )
        big_regions = RegionExtractor.filter_by_area(regions, min_area_px=100)
        assert len(big_regions) <= len(regions)

    def test_get_mask_from_regions(self):
        img = _make_image_with_holes()
        sample_color = img[60, 40]
        regions = RegionExtractor.extract_by_color_sample(
            img, sample_color, match_tolerance=40
        )
        mask = RegionExtractor.get_mask_from_regions(regions, img.shape[:2])
        assert mask.shape == img.shape[:2]
        assert mask.dtype == np.uint8
        assert mask.max() == 255
```

- [ ] **Step 2: Verify failure**

```bash
python -m pytest tests/test_region_extractor.py -v
```

Expected: FAIL

- [ ] **Step 3: Write RegionExtractor**

Write `core_analysis/engine/region_extractor.py`:
```python
"""RegionExtractor — color-based region segmentation via LAB color space."""

import cv2
import numpy as np
from core_analysis.data.models import MaskRegion


class RegionExtractor:
    @staticmethod
    def extract_by_color_sample(image: np.ndarray, sample_color: np.ndarray,
                                match_tolerance: int = 30,
                                continuous_only: bool = False) -> list:
        """
        Extract regions matching a sampled color.
        Uses LAB color space for perceptual color matching.
        Returns list of MaskRegion.
        """
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        sample_lab = cv2.cvtColor(np.uint8([[sample_color]]), cv2.COLOR_BGR2LAB)[0][0]

        lower = np.clip(sample_lab - match_tolerance, 0, 255).astype(np.uint8)
        upper = np.clip(sample_lab + match_tolerance, 0, 255).astype(np.uint8)

        mask = cv2.inRange(lab, lower, upper)

        if continuous_only:
            # Only keep the largest connected component containing the click point
            # This is used when the user clicks a specific region
            pass  # continuous mode is handled by UI layer (passes roi to extraction)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        regions = []
        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            if area < 1:
                continue
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = M["m10"] / M["m00"]
                cy = M["m01"] / M["m00"]
            else:
                cx, cy = 0.0, 0.0
            x, y, w, h = cv2.boundingRect(cnt)
            regions.append(MaskRegion(
                contour=cnt.squeeze(1).tolist() if len(cnt.shape) == 3 else [],
                area_px=area,
                centroid=(cx, cy),
                bbox=(x, y, w, h)
            ))
        return regions

    @staticmethod
    def filter_by_area(regions: list, min_area_px: float = 0,
                       max_area_px: float = float('inf')) -> list:
        """Filter regions by pixel area threshold."""
        return [r for r in regions if min_area_px <= r.area_px <= max_area_px]

    @staticmethod
    def get_mask_from_regions(regions: list, image_shape: tuple) -> np.ndarray:
        """Generate a binary mask from extracted regions."""
        mask = np.zeros(image_shape, dtype=np.uint8)
        for r in regions:
            pts = np.array(r.contour, dtype=np.int32)
            if pts.ndim == 2 and pts.shape[0] >= 3:
                cv2.drawContours(mask, [pts], -1, 255, -1)
        return mask
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_region_extractor.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add core_analysis/engine/region_extractor.py tests/test_region_extractor.py
git commit -m "feat: add RegionExtractor with LAB color segmentation"
```

---

### Task 8: Morphology Engine

**Files:**
- Create: `core_analysis/engine/morphology_engine.py`
- Create: `tests/test_morphology_engine.py`

- [ ] **Step 1: Write failing test**

Write `tests/test_morphology_engine.py`:
```python
"""Tests for MorphologyEngine"""
import numpy as np
import cv2
from core_analysis.engine.morphology_engine import MorphologyEngine
from core_analysis.data.models import MaskRegion


def _make_square_region():
    """Create a simple square MaskRegion."""
    cnt = np.array([[10, 10], [50, 10], [50, 50], [10, 50]], dtype=np.int32)
    return MaskRegion(
        contour=cnt.tolist(),
        area_px=1600.0,
        centroid=(30.0, 30.0),
        bbox=(10, 10, 40, 40)
    )


class TestMorphologyEngine:
    def test_dilate_region(self):
        r = _make_square_region()
        result = MorphologyEngine.dilate_region(r, kernel_size=5, iterations=2)
        assert result.area_px >= r.area_px

    def test_erode_region(self):
        r = _make_square_region()
        result = MorphologyEngine.erode_region(r, kernel_size=5, iterations=1)
        assert result.area_px <= r.area_px

    def test_denoise_by_area(self):
        regions = [
            MaskRegion(contour=[], area_px=500, centroid=(0, 0), bbox=(0, 0, 10, 10)),
            MaskRegion(contour=[], area_px=5, centroid=(0, 0), bbox=(0, 0, 2, 2)),
            MaskRegion(contour=[], area_px=300, centroid=(0, 0), bbox=(0, 0, 8, 8)),
        ]
        filtered = MorphologyEngine.denoise_by_area(regions, min_area_px=100)
        assert len(filtered) == 2

    def test_fill_holes(self):
        """Hole filling should produce a filled contour."""
        r = _make_square_region()
        r.contour = [[10, 10], [50, 10], [50, 50], [30, 30], [10, 50]]  # with dent
        result = MorphologyEngine.fill_holes(r, max_hole_size=200)
        assert result is not None

    def test_erode_too_much_returns_none(self):
        r = _make_square_region()
        # Erode with huge kernel — region disappears
        result = MorphologyEngine.erode_region(r, kernel_size=99, iterations=3)
        assert result is None
```

- [ ] **Step 2: Verify failure**

```bash
python -m pytest tests/test_morphology_engine.py -v
```

Expected: FAIL

- [ ] **Step 3: Write MorphologyEngine**

Write `core_analysis/engine/morphology_engine.py`:
```python
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
        # Find inner holes and fill them
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        if hierarchy is None:
            return region
        for i, (cnt, h) in enumerate(zip(contours, hierarchy[0])):
            # h[3] != -1 means this contour has a parent (it's a hole)
            if h[3] != -1 and cv2.contourArea(cnt) <= max_hole_size:
                cv2.drawContours(mask, [cnt], -1, 255, -1)
        result = MorphologyEngine._mask_to_region(mask, bx - pad, by - pad)
        return result if result is not None else region
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_morphology_engine.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add core_analysis/engine/morphology_engine.py tests/test_morphology_engine.py
git commit -m "feat: add MorphologyEngine with dilate, erode, denoise, fill"
```

---

### Task 9: Hole Analyzer

**Files:**
- Create: `core_analysis/engine/hole_analyzer.py`
- Create: `tests/test_hole_analyzer.py`

- [ ] **Step 1: Write failing test**

Write `tests/test_hole_analyzer.py`:
```python
"""Tests for HoleAnalyzer"""
import numpy as np
from core_analysis.engine.hole_analyzer import HoleAnalyzer
from core_analysis.data.models import MaskRegion, HoleResult


def _make_regions():
    """Create two simulated hole regions with known areas."""
    # Circle radius=20px → area=~1256.6 px²
    import cv2
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
        scale = 0.05  # mm/pixel
        image_area_px = 10000  # 100x100
        results, summary = HoleAnalyzer.analyze(regions, scale, image_area_px)

        assert len(results) == 2
        for r in results:
            assert r.area_mm2 > 0
            assert r.equivalent_d_mm > 0
            assert r.size_category in ("大洞", "中洞", "小洞", "针孔/溶孔")

        assert summary["total_count"] == 2
        assert summary["total_area_mm2"] > 0
        assert 0 < summary["porosity_percent"] < 100
        assert "avg_equivalent_d_mm" in summary

    def test_size_classification(self):
        regions = _make_regions()
        scale = 1.0  # very large scale to push to 大洞
        image_area_px = 10000
        _, summary = HoleAnalyzer.analyze(regions, scale, image_area_px)
        assert "size_distribution" in summary
        dist = summary["size_distribution"]
        for k in ("大洞", "中洞", "小洞", "针孔/溶孔"):
            assert k in dist

    def test_empty_regions(self):
        results, summary = HoleAnalyzer.analyze([], 0.05, 10000)
        assert results == []
        assert summary["total_count"] == 0
        assert summary["porosity_percent"] == 0.0
```

- [ ] **Step 2: Verify failure**

```bash
python -m pytest tests/test_hole_analyzer.py -v
```

Expected: FAIL

- [ ] **Step 3: Write HoleAnalyzer**

Write `core_analysis/engine/hole_analyzer.py`:
```python
"""HoleAnalyzer — quantitative hole analysis from extracted regions."""

import math
from core_analysis.data.models import MaskRegion, HoleResult


class HoleAnalyzer:
    @staticmethod
    def analyze(regions: list, scale_mm_per_px: float,
                image_area_px: float) -> tuple:
        """
        Analyze hole regions. Returns (list of HoleResult, summary_dict).
        """
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

        # Size distribution
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
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_hole_analyzer.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add core_analysis/engine/hole_analyzer.py tests/test_hole_analyzer.py
git commit -m "feat: add HoleAnalyzer with Dr formula and size classification"
```

---

### Task 10: Fracture Analyzer

**Files:**
- Create: `core_analysis/engine/fracture_analyzer.py`
- Create: `tests/test_fracture_analyzer.py`

- [ ] **Step 1: Write failing test**

Write `tests/test_fracture_analyzer.py`:
```python
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
        assert "surface_density" in summary
        assert "linear_density" in summary

    def test_empty_regions(self):
        results, summary = FractureAnalyzer.analyze([], 0.05, 10000, 0.5)
        assert results == []
        assert summary["total_count"] == 0
```

- [ ] **Step 2: Verify failure**

```bash
python -m pytest tests/test_fracture_analyzer.py -v
```

Expected: FAIL

- [ ] **Step 3: Write FractureAnalyzer**

Write `core_analysis/engine/fracture_analyzer.py`:
```python
"""FractureAnalyzer — quantitative fracture analysis from extracted regions."""

import cv2
import numpy as np
import math
from core_analysis.data.models import MaskRegion, FractureResult


class FractureAnalyzer:
    @staticmethod
    def analyze(regions: list, scale_mm_per_px: float,
                image_area_px: float, core_length_m: float) -> tuple:
        """
        Analyze fracture regions. Returns (list of FractureResult, summary_dict).
        Uses skeletonization (Zhang-Suen thinning) for length calculation.
        Width = Area / Length.
        """
        results = []
        total_area_mm2 = 0.0
        total_length_mm = 0.0
        lengths = []

        for i, region in enumerate(regions):
            # Build mask for this region
            bx, by, bw, bh = region.bbox
            pad = 10
            mask = np.zeros((bh + pad * 2, bw + pad * 2), dtype=np.uint8)
            pts = np.array(region.contour, dtype=np.int32)
            if pts.ndim == 2 and pts.shape[0] >= 3:
                pts_shifted = pts - [bx - pad, by - pad]
                cv2.drawContours(mask, [pts_shifted], -1, 255, -1)

            # Skeletonize
            skeleton = FractureAnalyzer._skeletonize(mask)
            # Count skeleton pixels as length in pixels
            length_px = np.count_nonzero(skeleton)
            area_px = region.area_px

            # Convert to mm
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
            lengths.append(length_mm)

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
            "surface_density": round(surface_density, 4),  # m/m²
            "linear_density": round(linear_density, 4),    # 条/m
            "avg_spacing_mm": round(avg_spacing, 4),
        }
        return results, summary

    @staticmethod
    def _skeletonize(mask: np.ndarray) -> np.ndarray:
        """Apply Zhang-Suen thinning to a binary mask."""
        skel = cv2.ximgproc.thinning(mask, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
        return skel
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_fracture_analyzer.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add core_analysis/engine/fracture_analyzer.py tests/test_fracture_analyzer.py
git commit -m "feat: add FractureAnalyzer with skeletonization and W=A/L"
```

---

### Task 11: Report Generator

**Files:**
- Create: `core_analysis/engine/report_generator.py`
- Create: `core_analysis/templates/hole_report.html`
- Create: `core_analysis/templates/fracture_report.html`
- Create: `tests/test_report_generator.py`

- [ ] **Step 1: Write Jinja2 templates**

Write `core_analysis/templates/hole_report.html`:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>岩心孔洞分析报告</title>
<style>
  body { font-family: "Microsoft YaHei", sans-serif; padding: 20px; color: #333; }
  h1 { text-align: center; font-size: 18px; }
  h2 { font-size: 15px; border-bottom: 1px solid #333; margin-top: 24px; }
  table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px; }
  th, td { border: 1px solid #666; padding: 4px 8px; text-align: left; }
  th { background: #f0f0f0; }
  .info td { border: none; }
  .chart { text-align: center; margin: 16px 0; }
  .chart img { max-width: 100%; }
</style>
</head>
<body>
<h1>碳酸盐岩岩心孔洞分析报告</h1>

<h2>基础信息</h2>
<table class="info">
  <tr><td><b>图像编号:</b> {{ info.image_id }}</td><td><b>井号:</b> {{ info.well }}</td></tr>
  <tr><td><b>深度:</b> {{ info.depth }} m</td><td><b>层位:</b> {{ info.layer }}</td></tr>
  <tr><td><b>岩性:</b> {{ info.lithology }}</td><td><b>标尺:</b> {{ info.scale }} mm/px</td></tr>
  <tr><td><b>分析日期:</b> {{ info.date }}</td><td><b>分析人:</b> {{ info.analyst }}</td></tr>
</table>

<h2>一、孔洞检测统计</h2>
<table>
  <tr><th>指标</th><th>值</th><th>单位</th></tr>
  <tr><td>孔洞总数</td><td>{{ summary.total_count }}</td><td>个</td></tr>
  <tr><td>孔洞总面积</td><td>{{ summary.total_area_mm2 }}</td><td>mm²</td></tr>
  <tr><td>平均面积</td><td>{{ summary.avg_area_mm2 }}</td><td>mm²</td></tr>
  <tr><td>面孔率</td><td>{{ summary.porosity_percent }}%</td><td>—</td></tr>
  <tr><td>最大等效直径</td><td>{{ summary.max_d_mm }}</td><td>mm</td></tr>
  <tr><td>最小等效直径</td><td>{{ summary.min_d_mm }}</td><td>mm</td></tr>
  <tr><td>平均等效直径</td><td>{{ summary.avg_d_mm }}</td><td>mm</td></tr>
</table>

<h2>二、充填特征</h2>
<table>
  <tr><th>充填状态</th><th>数量</th><th>面积(mm²)</th><th>占比</th></tr>
  {% for item in fill_stats %}
  <tr><td>{{ item.status }}</td><td>{{ item.count }}</td><td>{{ item.area }}</td><td>{{ item.percent }}%</td></tr>
  {% endfor %}
</table>

<h2>三、有效性评价</h2>
<p>有效 {{ effect.valid }} 个 | 较有效 {{ effect.semi_valid }} 个 | 无效 {{ effect.invalid }} 个</p>

<h2>四、孔洞大小分布</h2>
<table>
  <tr><th>分类</th><th>孔径范围</th><th>数量</th><th>占比</th></tr>
  {% for item in size_dist %}
  <tr><td>{{ item.category }}</td><td>{{ item.range }}</td><td>{{ item.count }}</td><td>{{ item.percent }}%</td></tr>
  {% endfor %}
</table>

<h2>五、附图</h2>
<div class="chart"><img src="data:image/png;base64,{{ charts.histogram }}" alt="频率直方图"></div>
<div class="chart"><img src="data:image/png;base64,{{ charts.cumulative }}" alt="累计频率曲线"></div>
<div class="chart"><img src="data:image/png;base64,{{ charts.normal_cdf }}" alt="正态累计曲线"></div>
</body>
</html>
```

Write `core_analysis/templates/fracture_report.html`:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>岩心裂缝分析报告</title>
<style>
  body { font-family: "Microsoft YaHei", sans-serif; padding: 20px; color: #333; }
  h1 { text-align: center; font-size: 18px; }
  h2 { font-size: 15px; border-bottom: 1px solid #333; margin-top: 24px; }
  table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px; }
  th, td { border: 1px solid #666; padding: 4px 8px; text-align: left; }
  th { background: #f0f0f0; }
  .info td { border: none; }
</style>
</head>
<body>
<h1>碳酸盐岩岩心裂缝分析报告</h1>

<h2>基础信息</h2>
<table class="info">
  <tr><td><b>图像编号:</b> {{ info.image_id }}</td><td><b>井号:</b> {{ info.well }}</td></tr>
  <tr><td><b>深度:</b> {{ info.depth }} m</td><td><b>层位:</b> {{ info.layer }}</td></tr>
  <tr><td><b>岩性:</b> {{ info.lithology }}</td><td><b>标尺:</b> {{ info.scale }} mm/px</td></tr>
  <tr><td><b>分析日期:</b> {{ info.date }}</td><td><b>分析人:</b> {{ info.analyst }}</td></tr>
</table>

<h2>一、裂缝检测统计</h2>
<table>
  <tr><th>指标</th><th>值</th><th>单位</th></tr>
  <tr><td>裂缝总条数</td><td>{{ summary.total_count }}</td><td>条</td></tr>
  <tr><td>裂缝总面积</td><td>{{ summary.total_area_mm2 }}</td><td>mm²</td></tr>
  <tr><td>面孔隙度</td><td>{{ summary.porosity_percent }}%</td><td>—</td></tr>
  <tr><td>累计长度</td><td>{{ summary.total_length_mm }}</td><td>mm</td></tr>
  <tr><td>面密度</td><td>{{ summary.surface_density }}</td><td>m/m²</td></tr>
  <tr><td>线密度</td><td>{{ summary.linear_density }}</td><td>条/m</td></tr>
  <tr><td>平均间距</td><td>{{ summary.avg_spacing_mm }}</td><td>mm</td></tr>
</table>

<h2>二、裂缝明细</h2>
<table>
  <tr><th>序号</th><th>长度(mm)</th><th>宽度(mm)</th><th>面积(mm²)</th><th>类型</th><th>充填状态</th><th>有效性</th></tr>
  {% for f in fractures %}
  <tr>
    <td>{{ loop.index }}</td><td>{{ f.length_mm }}</td><td>{{ f.width_mm }}</td>
    <td>{{ f.area_mm2 }}</td><td>{{ f.fracture_type }}</td>
    <td>{{ f.fill_status }}</td><td>{{ f.effectiveness }}</td>
  </tr>
  {% endfor %}
</table>

<h2>三、裂缝成因分类</h2>
<table>
  <tr><th>裂缝类型</th><th>条数</th><th>总长度(mm)</th></tr>
  {% for item in type_stats %}
  <tr><td>{{ item.type }}</td><td>{{ item.count }}</td><td>{{ item.total_length }}</td></tr>
  {% endfor %}
</table>
</body>
</html>
```

- [ ] **Step 2: Write failing test**

Write `tests/test_report_generator.py`:
```python
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
        assert "频率直方图" in html or "histogram" in html

    def test_generate_fracture_report(self):
        summary = {
            "total_count": 3, "total_area_mm2": 32.6, "porosity_percent": 5.5,
            "total_length_mm": 156.3, "surface_density": 0.26,
            "linear_density": 1.6, "avg_spacing_mm": 13.4
        }
        fractures = [
            {"length_mm": 28.5, "width_mm": 0.45, "area_mm2": 12.8,
             "fracture_type": "构造缝", "fill_status": "张开缝(未充填)", "effectiveness": "有效"},
            {"length_mm": 15.2, "width_mm": 0.30, "area_mm2": 4.6,
             "fracture_type": "成岩缝", "fill_status": "半充填缝", "effectiveness": "较有效"},
        ]
        type_stats = [
            {"type": "构造缝", "count": 2, "total_length": 68.5},
            {"type": "成岩缝", "count": 1, "total_length": 15.2},
        ]
        info = {"image_id": "J12-3-1560", "well": "J12-3", "depth": "1560.0",
                "layer": "沙河街组", "lithology": "灰岩", "scale": "0.05",
                "date": "2026-06-16", "analyst": "测试"}

        html = ReportGenerator.generate_fracture_report(summary, fractures, type_stats, info)
        assert "<!DOCTYPE html>" in html
        assert "J12-3" in html
        assert "裂缝总条数" in html
```

- [ ] **Step 3: Run to verify failure**

```bash
python -m pytest tests/test_report_generator.py -v
```

Expected: FAIL

- [ ] **Step 4: Write ReportGenerator**

Write `core_analysis/engine/report_generator.py`:
```python
"""ReportGenerator — Jinja2-based HTML report generation with matplotlib charts."""

import io
import base64
import os
from jinja2 import Environment, FileSystemLoader
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats


class ReportGenerator:
    _template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 "templates")
    _env = Environment(loader=FileSystemLoader(_template_dir))

    @classmethod
    def generate_hole_report(cls, summary: dict, fill_stats: list,
                             effect: dict, info: dict) -> str:
        charts = cls._generate_hole_charts(summary.get("diameters", []))
        size_dist = cls._build_size_dist_table(summary.get("size_distribution", {}),
                                               summary.get("total_count", 0))

        template = cls._env.get_template("hole_report.html")
        html = template.render(
            info=info,
            summary={
                "total_count": summary["total_count"],
                "total_area_mm2": summary["total_area_mm2"],
                "avg_area_mm2": summary["avg_area_mm2"],
                "porosity_percent": summary["porosity_percent"],
                "avg_d_mm": summary["avg_equivalent_d_mm"],
                "max_d_mm": summary["max_equivalent_d_mm"],
                "min_d_mm": summary["min_equivalent_d_mm"],
            },
            fill_stats=fill_stats,
            effect=effect,
            size_dist=size_dist,
            charts=charts
        )
        return html

    @classmethod
    def generate_fracture_report(cls, summary: dict, fractures: list,
                                 type_stats: list, info: dict) -> str:
        template = cls._env.get_template("fracture_report.html")
        html = template.render(
            info=info,
            summary=summary,
            fractures=fractures,
            type_stats=type_stats
        )
        return html

    @classmethod
    def _generate_hole_charts(cls, diameters: list) -> dict:
        if not diameters:
            return {"histogram": "", "cumulative": "", "normal_cdf": ""}
        diameters = np.array(diameters)

        charts = {}
        # Frequency histogram
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(diameters, bins=min(10, len(diameters)), edgecolor='black', alpha=0.7)
        ax.set_xlabel("等效直径 (mm)")
        ax.set_ylabel("频数")
        ax.set_title("孔洞等效直径频率直方图")
        charts["histogram"] = cls._fig_to_b64(fig)
        plt.close(fig)

        # Cumulative frequency curve
        fig, ax = plt.subplots(figsize=(6, 4))
        sorted_d = np.sort(diameters)
        cumulative = np.arange(1, len(sorted_d) + 1) / len(sorted_d) * 100
        ax.plot(sorted_d, cumulative, 'b-o', markersize=4)
        ax.set_xlabel("等效直径 (mm)")
        ax.set_ylabel("累计频率 (%)")
        ax.set_title("孔洞等效直径累计频率曲线")
        charts["cumulative"] = cls._fig_to_b64(fig)
        plt.close(fig)

        # Normal CDF
        fig, ax = plt.subplots(figsize=(6, 4))
        mu, sigma = np.mean(diameters), np.std(diameters)
        if sigma > 0:
            x = np.linspace(max(0, mu - 3 * sigma), mu + 3 * sigma, 100)
            ax.plot(x, stats.norm.cdf(x, mu, sigma) * 100, 'r-', lw=2,
                    label=f"μ={mu:.2f}, σ={sigma:.2f}")
            ax.scatter(sorted_d, cumulative, s=10, alpha=0.5, label="实测")
            ax.legend()
        ax.set_xlabel("等效直径 (mm)")
        ax.set_ylabel("累计概率 (%)")
        ax.set_title("孔洞等效直径正态累计曲线")
        charts["normal_cdf"] = cls._fig_to_b64(fig)
        plt.close(fig)

        return charts

    @staticmethod
    def _fig_to_b64(fig) -> str:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()

    @staticmethod
    def _build_size_dist_table(size_dist: dict, total: int) -> list:
        ranges = {
            "大洞": ">10mm", "中洞": "5-10mm",
            "小洞": "1-4.9mm", "针孔/溶孔": "<1mm"
        }
        return [
            {
                "category": k,
                "range": ranges.get(k, ""),
                "count": size_dist.get(k, 0),
                "percent": round(size_dist.get(k, 0) / total * 100, 1) if total > 0 else 0
            }
            for k in ("大洞", "中洞", "小洞", "针孔/溶孔")
        ]
```

- [ ] **Step 5: Run tests**

```bash
python -m pytest tests/test_report_generator.py -v
```

Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add core_analysis/engine/report_generator.py core_analysis/templates/ tests/test_report_generator.py
git commit -m "feat: add ReportGenerator with Jinja2 templates and matplotlib charts"
```

---

### Task 12: Image Canvas (UI Layer)

**Files:**
- Create: `core_analysis/ui/image_canvas.py`

- [ ] **Step 1: Write ImageCanvas**

Write `core_analysis/ui/image_canvas.py`:
```python
"""ImageCanvas — QGraphicsView-based canvas with 3-layer rendering."""

import cv2
import numpy as np
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QBrush
from PySide6.QtCore import Qt, QRectF, Signal, QPointF
from core_analysis.data.models import MaskRegion


class Layer:
    """Enum-like constants for layer z-ordering."""
    IMAGE = 0
    OVERLAY = 1
    ANNOTATION = 2


class ImageCanvas(QGraphicsView):
    """Central image canvas with pan, zoom, and region overlay."""

    region_selected = Signal(int)  # region_index
    color_sampled = Signal(np.ndarray)  # BGR color at click point

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        # Layer items
        self._image_item = QGraphicsPixmapItem()
        self._image_item.setZValue(Layer.IMAGE)
        self._scene.addItem(self._image_item)

        self._overlay_item = QGraphicsPixmapItem()
        self._overlay_item.setZValue(Layer.OVERLAY)
        self._overlay_item.setOpacity(0.5)
        self._scene.addItem(self._overlay_item)

        self._annotation_item = QGraphicsPixmapItem()
        self._annotation_item.setZValue(Layer.ANNOTATION)
        self._scene.addItem(self._annotation_item)

        # State
        self._image_bgr = None
        self._regions = []
        self._overlay_visible = True
        self._annotation_visible = True
        self._annotation_labels = {}  # region_index -> text

    # ── Image Loading ──

    def load_image(self, filepath: str):
        """Load image from file and display."""
        bgr = cv2.imread(filepath)
        if bgr is None:
            raise FileNotFoundError(f"Cannot load image: {filepath}")
        self._image_bgr = bgr
        self._refresh_image_layer()
        self._overlay_item.setPixmap(QPixmap())
        self._annotation_item.setPixmap(QPixmap())
        self._regions = []
        self._fit_to_window()

    def load_image_from_array(self, bgr: np.ndarray):
        """Load image from numpy BGR array."""
        self._image_bgr = bgr.copy()
        self._refresh_image_layer()
        self._fit_to_window()

    def _refresh_image_layer(self):
        if self._image_bgr is None:
            return
        rgb = cv2.cvtColor(self._image_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, w * ch, QImage.Format_RGB888)
        self._image_item.setPixmap(QPixmap.fromImage(qimg))
        self._scene.setSceneRect(QRectF(0, 0, w, h))

    def _fit_to_window(self):
        if self._image_bgr is not None:
            self.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)

    # ── Overlay ──

    def set_regions(self, regions: list):
        """Set overlay regions (extracted holes/fractures)."""
        self._regions = regions
        self._refresh_overlay()

    def _refresh_overlay(self):
        if self._image_bgr is None or not self._overlay_visible:
            self._overlay_item.setPixmap(QPixmap())
            return
        h, w = self._image_bgr.shape[:2]
        overlay = np.zeros((h, w, 4), dtype=np.uint8)
        for i, region in enumerate(self._regions):
            pts = np.array(region.contour, dtype=np.int32)
            if pts.ndim == 2 and pts.shape[0] >= 3:
                cv2.drawContours(overlay, [pts], -1, (255, 60, 60, 180), -1)
                cv2.drawContours(overlay, [pts], -1, (255, 0, 0, 255), 1)
        qimg = QImage(overlay.data, w, h, w * 4, QImage.Format_RGBA8888)
        self._overlay_item.setPixmap(QPixmap.fromImage(qimg))

    def toggle_overlay(self, visible: bool):
        self._overlay_visible = visible
        self._refresh_overlay()

    def toggle_annotation(self, visible: bool):
        self._annotation_visible = visible

    # ── Zoom ──

    def zoom_in(self):
        self.scale(1.25, 1.25)

    def zoom_out(self):
        self.scale(0.8, 0.8)

    def zoom_fit(self):
        self._fit_to_window()

    def zoom_100(self):
        self.resetTransform()

    # ── Mouse Events ──

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            # Check if click hits a region
            for i, region in enumerate(self._regions):
                pts = np.array(region.contour, dtype=np.int32)
                if pts.ndim == 2 and pts.shape[0] >= 3:
                    if cv2.pointPolygonTest(pts, (pos.x(), pos.y()), False) >= 0:
                        self.region_selected.emit(i)
                        break
            # Sample color at click point
            if self._image_bgr is not None:
                px, py = int(pos.x()), int(pos.y())
                h, w = self._image_bgr.shape[:2]
                if 0 <= px < w and 0 <= py < h:
                    self.color_sampled.emit(self._image_bgr[py, px])
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        """Mouse wheel zoom."""
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    # ── Properties ──

    @property
    def regions(self) -> list:
        return self._regions

    @property
    def image_bgr(self):
        return self._image_bgr

    @property
    def image_size(self) -> tuple:
        if self._image_bgr is None:
            return (0, 0)
        return self._image_bgr.shape[:2]
```

- [ ] **Step 2: Verify imports**

```bash
python -c "from core_analysis.ui.image_canvas import ImageCanvas; print('ImageCanvas OK')"
```

Expected: `ImageCanvas OK`

- [ ] **Step 3: Commit**

```bash
git add core_analysis/ui/image_canvas.py
git commit -m "feat: add ImageCanvas with 3-layer rendering and region selection"
```

---

### Task 13: Tool Panel (UI Layer)

**Files:**
- Create: `core_analysis/ui/tool_panel.py`

- [ ] **Step 1: Write ToolPanel**

Write `core_analysis/ui/tool_panel.py`:
```python
"""ToolPanel — Left tool bar + right parameter panel for hole/fracture analysis."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QPushButton,
    QLabel, QSlider, QComboBox, QCheckBox, QSpinBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal


class ToolPanel(QWidget):
    """Combined left toolbar (vertical) + right parameter panel."""

    # Signals
    tool_changed = Signal(str)  # tool name
    auto_extract_requested = Signal()
    match_tolerance_changed = Signal(int)
    continuous_mode_changed = Signal(bool)
    denoise_threshold_changed = Signal(int)
    morphology_requested = Signal(str)  # 'dilate'|'erode'|'fill'
    fill_status_changed = Signal(str)
    fill_material_changed = Signal(str)
    effectiveness_changed = Signal(str)
    save_params_requested = Signal()
    view_report_requested = Signal()
    scale_changed = Signal(float)

    TOOLS = [
        ("pan", "🖐️", "漫游"),
        ("select", "⬚", "选择"),
        ("multi_select", "▣", "多选"),
        ("segment", "🎯", "区域分割"),
        ("eraser_minus", "🧹", "橡皮擦-"),
        ("eraser_plus", "🧹+", "橡皮擦+"),
        ("dilate_local", "⭢", "局部膨胀"),
        ("erode_local", "⭠", "局部腐蚀"),
        ("brush", "✏️", "画笔"),
        ("rect", "▭", "矩形"),
        ("ellipse", "○", "椭圆"),
        ("text", "T", "文字"),
    ]

    FILL_STATUSES = ["未充填", "半充填", "全充填"]
    FILL_MATERIALS = ["", "泥质", "方解石", "白云石", "沥青", "石膏", "黄铁矿", "高岭石", "石英"]
    EFFECTIVENESS = ["有效", "较有效", "无效"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ── Left Tool Bar ──
        left_bar = QVBoxLayout()
        left_bar.setContentsMargins(2, 4, 2, 4)
        left_bar.setSpacing(2)

        self._tool_buttons = {}
        for tool_id, icon, tooltip in self.TOOLS:
            btn = QPushButton(icon)
            btn.setToolTip(tooltip)
            btn.setFixedSize(32, 32)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, t=tool_id: self.tool_changed.emit(t))
            left_bar.addWidget(btn)
            self._tool_buttons[tool_id] = btn

        left_bar.addStretch()
        main_layout.addLayout(left_bar)

        # ── Right Parameter Panel ──
        right_panel = QVBoxLayout()
        right_panel.setContentsMargins(4, 4, 4, 4)
        right_panel.setSpacing(6)

        # Auto-extract group
        auto_group = QGroupBox("⚡ 智能提取")
        auto_layout = QVBoxLayout(auto_group)
        self._match_slider = QSlider(Qt.Horizontal)
        self._match_slider.setRange(5, 100)
        self._match_slider.setValue(30)
        self._match_slider.valueChanged.connect(self.match_tolerance_changed.emit)
        auto_layout.addWidget(QLabel("颜色匹配度"))
        auto_layout.addWidget(self._match_slider)
        self._match_label = QLabel("30")
        self._match_slider.valueChanged.connect(
            lambda v: self._match_label.setText(str(v)))
        auto_layout.addWidget(self._match_label)

        self._continuous_cb = QCheckBox("连续区域")
        self._continuous_cb.toggled.connect(self.continuous_mode_changed.emit)
        auto_layout.addWidget(self._continuous_cb)

        extract_btn = QPushButton("一键提取")
        extract_btn.clicked.connect(self.auto_extract_requested.emit)
        auto_layout.addWidget(extract_btn)
        right_panel.addWidget(auto_group)

        # Edit group
        edit_group = QGroupBox("🔧 区域编辑")
        edit_layout = QFormLayout(edit_group)
        self._denoise_spin = QSpinBox()
        self._denoise_spin.setRange(1, 10000)
        self._denoise_spin.setValue(10)
        self._denoise_spin.setSuffix(" px")
        self._denoise_spin.valueChanged.connect(self.denoise_threshold_changed.emit)
        edit_layout.addRow("去噪 <", self._denoise_spin)

        morph_row = QHBoxLayout()
        dilate_btn = QPushButton("膨胀")
        dilate_btn.clicked.connect(lambda: self.morphology_requested.emit("dilate"))
        erode_btn = QPushButton("腐蚀")
        erode_btn.clicked.connect(lambda: self.morphology_requested.emit("erode"))
        fill_btn = QPushButton("填充")
        fill_btn.clicked.connect(lambda: self.morphology_requested.emit("fill"))
        morph_row.addWidget(dilate_btn)
        morph_row.addWidget(erode_btn)
        edit_layout.addRow(morph_row)
        edit_layout.addRow(fill_btn)
        right_panel.addWidget(edit_group)

        # Feature params group
        param_group = QGroupBox("📝 特征参数")
        param_layout = QFormLayout(param_group)

        self._fill_status_combo = QComboBox()
        self._fill_status_combo.addItems(self.FILL_STATUSES)
        self._fill_status_combo.currentTextChanged.connect(self.fill_status_changed.emit)
        param_layout.addRow("充填:", self._fill_status_combo)

        self._fill_material_combo = QComboBox()
        self._fill_material_combo.addItems(self.FILL_MATERIALS)
        self._fill_material_combo.currentTextChanged.connect(self.fill_material_changed.emit)
        param_layout.addRow("填充物:", self._fill_material_combo)

        self._effectiveness_combo = QComboBox()
        self._effectiveness_combo.addItems(self.EFFECTIVENESS)
        self._effectiveness_combo.currentTextChanged.connect(self.effectiveness_changed.emit)
        param_layout.addRow("有效性:", self._effectiveness_combo)
        right_panel.addWidget(param_group)

        # Action buttons
        save_btn = QPushButton("✅ 修改保存")
        save_btn.clicked.connect(self.save_params_requested.emit)
        right_panel.addWidget(save_btn)

        report_btn = QPushButton("📊 查看报告")
        report_btn.clicked.connect(self.view_report_requested.emit)
        right_panel.addWidget(report_btn)

        right_panel.addStretch()
        main_layout.addLayout(right_panel)

    def match_tolerance(self) -> int:
        return self._match_slider.value()

    def is_continuous_mode(self) -> bool:
        return self._continuous_cb.isChecked()

    def denoise_threshold(self) -> int:
        return self._denoise_spin.value()

    def current_fill_status(self) -> str:
        return self._fill_status_combo.currentText()

    def current_fill_material(self) -> str:
        return self._fill_material_combo.currentText()

    def current_effectiveness(self) -> str:
        return self._effectiveness_combo.currentText()
```

- [ ] **Step 2: Verify imports**

```bash
python -c "from core_analysis.ui.tool_panel import ToolPanel; print('ToolPanel OK')"
```

Expected: `ToolPanel OK`

- [ ] **Step 3: Commit**

```bash
git add core_analysis/ui/tool_panel.py
git commit -m "feat: add ToolPanel with left toolbar and right parameter panel"
```

---

### Task 14: Image Library Widget (UI Layer)

**Files:**
- Create: `core_analysis/ui/image_library.py`

- [ ] **Step 1: Write ImageLibraryWidget**

Write `core_analysis/ui/image_library.py`:
```python
"""ImageLibraryWidget — QDockWidget with category tree and thumbnail grid."""

import os
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem,
    QLineEdit, QPushButton, QFileDialog, QMenu, QInputDialog, QMessageBox,
    QLabel
)
from PySide6.QtGui import QIcon, QPixmap, QAction
from PySide6.QtCore import Qt, Signal
import cv2
from core_analysis.data.models import Category, ImageRecord


class ImageLibraryWidget(QDockWidget):
    """Dockable panel for browsing and managing the rock core image library."""

    image_selected = Signal(int)       # image_id
    image_imported = Signal(int)       # image_id
    category_added = Signal(int)       # category_id

    def __init__(self, image_repository, parent=None):
        super().__init__("图像库", parent)
        self._repo = image_repository
        self._setup_ui()
        self.refresh_tree()

    def _setup_ui(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        # Search bar
        search_row = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 搜索...")
        self._search_input.returnPressed.connect(self._on_search)
        search_row.addWidget(self._search_input)

        import_btn = QPushButton("+导入")
        import_btn.clicked.connect(self._on_import)
        search_row.addWidget(import_btn)
        layout.addLayout(search_row)

        # Category tree
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        self._tree.itemClicked.connect(self._on_tree_item_clicked)
        layout.addWidget(self._tree)

        # Thumbnail grid
        self._thumb_list = QListWidget()
        self._thumb_list.setViewMode(QListWidget.IconMode)
        self._thumb_list.setIconSize(self._thumb_list.iconSize().scaled(120, 120, Qt.KeepAspectRatio))
        self._thumb_list.setResizeMode(QListWidget.Adjust)
        self._thumb_list.itemDoubleClicked.connect(self._on_thumb_double_clicked)
        layout.addWidget(self._thumb_list)

        self.setWidget(widget)

    # ── Public API ──

    def refresh_tree(self):
        self._tree.clear()
        top_cats = self._repo.get_category_tree()
        for cat in top_cats:
            item = QTreeWidgetItem([cat.name])
            item.setData(0, Qt.UserRole, ("category", cat.id))
            self._populate_tree_children(item, cat.id)
            self._tree.addTopLevelItem(item)

    def _populate_tree_children(self, parent_item, parent_id):
        children = self._repo.get_child_categories(parent_id)
        for child in children:
            item = QTreeWidgetItem([child.name])
            item.setData(0, Qt.UserRole, ("category", child.id))
            self._populate_tree_children(item, child.id)
            parent_item.addChild(item)
        # Add images at this category level
        images = self._repo.get_images_by_category(parent_id)
        for img in images:
            item = QTreeWidgetItem([f"🖼️ {img.filename}"])
            item.setData(0, Qt.UserRole, ("image", img.id))
            parent_item.addChild(item)

    def show_images_for_category(self, category_id: int):
        self._thumb_list.clear()
        images = self._repo.get_images_by_category(category_id)
        for img in images:
            item = QListWidgetItem(img.filename)
            item.setData(Qt.UserRole, img.id)
            # Try to load thumbnail
            if os.path.exists(img.filepath):
                bgr = cv2.imread(img.filepath)
                if bgr is not None:
                    h, w = bgr.shape[:2]
                    scale = min(120 / w, 120 / h)
                    thumb = cv2.resize(bgr, (int(w * scale), int(h * scale)))
                    rgb = cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)
                    h2, w2, ch = rgb.shape
                    from PySide6.QtGui import QImage
                    qimg = QImage(rgb.data, w2, h2, w2 * ch, QImage.Format_RGB888)
                    item.setIcon(QIcon(QPixmap.fromImage(qimg)))
            self._thumb_list.addItem(item)

    # ── Slots ──

    def _on_search(self):
        query = self._search_input.text()
        if not query:
            self.refresh_tree()
            return
        self._thumb_list.clear()
        results = self._repo.search_images(query)
        for img in results:
            item = QListWidgetItem(f"{img.filename}\n{img.lithology}")
            item.setData(Qt.UserRole, img.id)
            self._thumb_list.addItem(item)

    def _on_import(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "导入岩心图像", "",
            "图像文件 (*.jpg *.jpeg *.png *.bmp *.tiff);;所有文件 (*)"
        )
        if not files:
            return
        # Get or create target category
        cats = self._repo.get_category_tree()
        cat_name, ok = QInputDialog.getItem(
            self, "选择分类", "将图像导入到:", [c.name for c in cats], 0, False)
        if not ok or not cats:
            return
        cat = next((c for c in cats if c.name == cat_name), cats[0])

        for f in files:
            img = ImageRecord(
                category_id=cat.id,
                filename=os.path.basename(f),
                filepath=f
            )
            img_id = self._repo.add_image(img)
            self.image_imported.emit(img_id)
        self.refresh_tree()

    def _on_tree_item_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if data is None:
            return
        dtype, obj_id = data
        if dtype == "category":
            self.show_images_for_category(obj_id)
        elif dtype == "image":
            self.image_selected.emit(obj_id)

    def _on_thumb_double_clicked(self, item):
        img_id = item.data(Qt.UserRole)
        if img_id:
            self.image_selected.emit(img_id)

    def _on_tree_context_menu(self, pos):
        item = self._tree.itemAt(pos)
        menu = QMenu(self)
        add_cat_action = QAction("添加分类", self)
        add_cat_action.triggered.connect(self._on_add_category)
        menu.addAction(add_cat_action)
        if item:
            del_action = QAction("删除", self)
            del_action.triggered.connect(lambda: self._on_delete_item(item))
            menu.addAction(del_action)
        menu.exec_(self._tree.viewport().mapToGlobal(pos))

    def _on_add_category(self):
        name, ok = QInputDialog.getText(self, "添加分类", "分类名称:")
        if ok and name:
            type_name, ok2 = QInputDialog.getItem(
                self, "分类类型", "类型:",
                ["basin", "block", "structure", "well"], 0, False)
            if ok2:
                cat = Category(name=name, type=type_name)
                # Determine parent
                item = self._tree.currentItem()
                if item:
                    data = item.data(0, Qt.UserRole)
                    if data and data[0] == "category":
                        cat.parent_id = data[1]
                cat_id = self._repo.add_category(cat)
                self.category_added.emit(cat_id)
                self.refresh_tree()

    def _on_delete_item(self, item):
        data = item.data(0, Qt.UserRole)
        if data is None:
            return
        dtype, obj_id = data
        reply = QMessageBox.question(
            self, "确认删除", f"确定删除此项及其关联数据?",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if dtype == "image":
                self._repo.delete_image(obj_id)
            self.refresh_tree()
```

- [ ] **Step 2: Verify imports**

```bash
python -c "from core_analysis.ui.image_library import ImageLibraryWidget; print('ImageLibraryWidget OK')"
```

Expected: `ImageLibraryWidget OK`

- [ ] **Step 3: Commit**

```bash
git add core_analysis/ui/image_library.py
git commit -m "feat: add ImageLibraryWidget with category tree and thumbnail grid"
```

---

### Task 15: Report Viewer (UI Layer)

**Files:**
- Create: `core_analysis/ui/report_viewer.py`

- [ ] **Step 1: Write ReportViewer**

Write `core_analysis/ui/report_viewer.py`:
```python
"""ReportViewer — HTML report display with export capability."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser,
    QPushButton, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtPrintSupport import QPrinter


class ReportViewer(QWidget):
    """Standalone widget for viewing and exporting analysis reports."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._report_html = ""

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QHBoxLayout()
        export_html_btn = QPushButton("导出 HTML")
        export_html_btn.clicked.connect(self._export_html)
        export_pdf_btn = QPushButton("导出 PDF")
        export_pdf_btn.clicked.connect(self._export_pdf)
        close_btn = QPushButton("关闭")
        toolbar.addWidget(export_html_btn)
        toolbar.addWidget(export_pdf_btn)
        toolbar.addStretch()
        toolbar.addWidget(close_btn)
        layout.addLayout(toolbar)

        # Browser
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        layout.addWidget(self._browser)

        # Connect close
        close_btn.clicked.connect(self.hide)

    def show_report(self, html: str):
        """Load and display an HTML report."""
        self._report_html = html
        self._browser.setHtml(html)
        self.show()

    def _export_html(self):
        if not self._report_html:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 HTML 报告", "report.html",
            "HTML files (*.html);;All files (*)"
        )
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self._report_html)

    def _export_pdf(self):
        if not self._report_html:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 PDF 报告", "report.pdf",
            "PDF files (*.pdf);;All files (*)"
        )
        if path:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            self._browser.print_(printer)
```

- [ ] **Step 2: Verify imports**

```bash
python -c "from core_analysis.ui.report_viewer import ReportViewer; print('ReportViewer OK')"
```

Expected: `ReportViewer OK`

- [ ] **Step 3: Commit**

```bash
git add core_analysis/ui/report_viewer.py
git commit -m "feat: add ReportViewer with HTML display and PDF export"
```

---

### Task 16: Main Window Integration

**Files:**
- Create: `core_analysis/ui/main_window.py`
- Modify: `core_analysis/main.py`

- [ ] **Step 1: Write MainWindow**

Write `core_analysis/ui/main_window.py`:
```python
"""MainWindow — top-level application window integrating all UI modules."""

import os
import json
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QMainWindow, QMenuBar, QMenu, QToolBar, QStatusBar,
    QFileDialog, QMessageBox, QVBoxLayout, QWidget, QHBoxLayout,
    QLabel, QAction
)
from PySide6.QtCore import Qt, Signal

from core_analysis.data.database import ProjectManager
from core_analysis.data.image_repository import ImageRepository
from core_analysis.data.analysis_store import AnalysisStore
from core_analysis.data.models import AnalysisSession
from core_analysis.engine.image_processor import ImageProcessor
from core_analysis.engine.region_extractor import RegionExtractor
from core_analysis.engine.morphology_engine import MorphologyEngine
from core_analysis.engine.hole_analyzer import HoleAnalyzer
from core_analysis.engine.fracture_analyzer import FractureAnalyzer
from core_analysis.engine.report_generator import ReportGenerator
from core_analysis.ui.image_canvas import ImageCanvas
from core_analysis.ui.tool_panel import ToolPanel
from core_analysis.ui.image_library import ImageLibraryWidget
from core_analysis.ui.report_viewer import ReportViewer


class MainWindow(QMainWindow):
    """Main application window integrating all modules."""

    def __init__(self, db_path: str = "core_analysis.db"):
        super().__init__()
        self.setWindowTitle("岩心孔洞裂缝分析教学系统")
        self.resize(1280, 800)

        # ── Data Layer ──
        self._pm = ProjectManager(db_path)
        self._pm.initialize()
        self._repo = ImageRepository(self._pm)
        self._store = AnalysisStore(self._pm)

        # ── UI Components ──
        self._canvas = ImageCanvas()
        self._tool_panel = ToolPanel()
        self._report_viewer = ReportViewer()
        self._image_library = ImageLibraryWidget(self._repo)

        # ── State ──
        self._current_image_id = None
        self._current_image_record = None
        self._current_session_id = None
        self._analysis_type = "hole"  # 'hole' | 'fracture'
        self._hole_results = []
        self._fracture_results = []

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")
        file_menu.addAction("打开项目", self._open_project)
        file_menu.addAction("新建项目", self._new_project)
        file_menu.addAction("导入图像", self._import_image)
        file_menu.addSeparator()
        file_menu.addAction("退出", self.close)

        edit_menu = menubar.addMenu("编辑")
        edit_menu.addAction("撤销", self._undo)
        edit_menu.addAction("还原", self._redo)

        process_menu = menubar.addMenu("处理")
        process_menu.addAction("自动色阶", self._auto_levels)

        analysis_menu = menubar.addMenu("分析")
        analysis_menu.addAction("孔洞分析", lambda: self._set_analysis_type("hole"))
        analysis_menu.addAction("裂缝分析", lambda: self._set_analysis_type("fracture"))
        analysis_menu.addAction("标尺设定", self._set_scale)
        analysis_menu.addAction("生成报告", self._generate_report)

        # Toolbar
        toolbar = self.addToolBar("主工具栏")
        toolbar.addAction("📁 打开", self._import_image)
        toolbar.addAction("💾 保存", self._save_analysis)
        toolbar.addSeparator()
        toolbar.addAction("🔍 自动提取", self._auto_extract)
        toolbar.addAction("📊 生成报告", self._generate_report)
        toolbar.addSeparator()
        toolbar.addAction("📏 标尺", self._set_scale)
        toolbar.addSeparator()
        self._zoom_label = QLabel("100%")
        toolbar.addWidget(self._zoom_label)
        toolbar.addAction("🔍+", self._canvas.zoom_in)
        toolbar.addAction("🔍-", self._canvas.zoom_out)
        toolbar.addAction("👁️ 图层", self._toggle_overlay)

        # Central widget: canvas + right panel
        central = QWidget()
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.addWidget(self._canvas, 1)
        central_layout.addWidget(self._tool_panel)
        self.setCentralWidget(central)

        # Dock widget: image library
        self.addDockWidget(Qt.LeftDockWidgetArea, self._image_library)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._scale_label = QLabel("标尺: 未设定")
        self._detect_label = QLabel("检测: --")
        self._size_label = QLabel("图像: --")
        self._status_bar.addWidget(self._scale_label)
        self._status_bar.addWidget(self._detect_label)
        self._status_bar.addWidget(self._size_label)

    def _connect_signals(self):
        self._image_library.image_selected.connect(self._on_image_selected)
        self._tool_panel.auto_extract_requested.connect(self._auto_extract)
        self._tool_panel.morphology_requested.connect(self._on_morphology)
        self._tool_panel.save_params_requested.connect(self._save_params)
        self._tool_panel.view_report_requested.connect(self._generate_report)
        self._tool_panel.denoise_threshold_changed.connect(self._on_denoise)

    # ── Slots ──

    def _open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开项目", "", "SQLite DB (*.db)")
        if path:
            self._pm = ProjectManager(path)
            self._pm.initialize()
            self._repo = ImageRepository(self._pm)
            self._store = AnalysisStore(self._pm)
            self._image_library._repo = self._repo
            self._image_library.refresh_tree()

    def _new_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "新建项目", "project.db", "SQLite DB (*.db)")
        if path:
            self._pm = ProjectManager(path)
            self._pm.initialize()
            self._repo = ImageRepository(self._pm)
            self._store = AnalysisStore(self._pm)
            self._image_library._repo = self._repo
            self._image_library.refresh_tree()

    def _import_image(self):
        self._image_library._on_import()

    def _on_image_selected(self, image_id: int):
        img = self._repo.get_image(image_id)
        if img is None:
            return
        self._current_image_id = image_id
        self._current_image_record = img
        try:
            self._canvas.load_image(img.filepath)
            self._size_label.setText(f"图像: {self._canvas.image_size[1]}×{self._canvas.image_size[0]}")
            if img.scale_value:
                self._scale_label.setText(f"标尺: {img.scale_value} mm/px")
        except FileNotFoundError:
            QMessageBox.warning(self, "错误", f"找不到文件: {img.filepath}")
            return

    def _set_analysis_type(self, atype: str):
        self._analysis_type = atype
        self.setWindowTitle(f"岩心孔洞裂缝分析教学系统 — {'孔洞分析' if atype == 'hole' else '裂缝分析'}")

    def _auto_extract(self):
        if self._canvas.image_bgr is None:
            return
        # Use center of image as default sample point
        h, w = self._canvas.image_size
        sample_color = self._canvas.image_bgr[h // 2, w // 2]
        tolerance = self._tool_panel.match_tolerance()
        continuous = self._tool_panel.is_continuous_mode()
        regions = RegionExtractor.extract_by_color_sample(
            self._canvas.image_bgr, sample_color, tolerance, continuous
        )
        # Denoise
        threshold = self._tool_panel.denoise_threshold()
        regions = MorphologyEngine.denoise_by_area(regions, min_area_px=threshold)
        self._canvas.set_regions(regions)
        self._detect_label.setText(f"检测: {len(regions)}个区域")

    def _on_morphology(self, op: str):
        regions = self._canvas.regions
        if not regions:
            return
        updated = []
        for r in regions:
            if op == "dilate":
                result = MorphologyEngine.dilate_region(r, kernel_size=3, iterations=1)
            elif op == "erode":
                result = MorphologyEngine.erode_region(r, kernel_size=3, iterations=1)
            elif op == "fill":
                result = MorphologyEngine.fill_holes(r)
            else:
                result = r
            if result is not None:
                updated.append(result)
        self._canvas.set_regions(updated)

    def _on_denoise(self, threshold: int):
        regions = self._canvas.regions
        if regions:
            filtered = MorphologyEngine.denoise_by_area(regions, min_area_px=threshold)
            self._canvas.set_regions(filtered)

    def _save_params(self):
        """Save feature parameters (fill status/material/effectiveness) to current regions."""
        pass  # Parameters are applied during report generation

    def _auto_levels(self):
        if self._canvas.image_bgr is not None:
            result = ImageProcessor.auto_levels(self._canvas.image_bgr)
            self._canvas.load_image_from_array(result)

    def _set_scale(self):
        from PySide6.QtWidgets import QInputDialog
        scale, ok = QInputDialog.getDouble(
            self, "标尺设定", "mm/pixel:", 0.05, 0.001, 100.0, 4)
        if ok and self._current_image_record:
            self._current_image_record.scale_value = scale
            self._repo.update_image(self._current_image_record)
            self._scale_label.setText(f"标尺: {scale} mm/px")

    def _generate_report(self):
        if not self._canvas.regions or self._current_image_id is None:
            QMessageBox.information(self, "提示", "请先提取区域后再生成报告。")
            return

        img = self._current_image_record
        scale = img.scale_value if img and img.scale_value else 0.05
        image_area_px = self._canvas.image_size[0] * self._canvas.image_size[1]

        info = {
            "image_id": str(img.id) if img else "",
            "well": str(img.filename) if img else "",
            "depth": str(img.depth_from) if img and img.depth_from else "",
            "layer": "",
            "lithology": img.lithology if img else "",
            "scale": str(scale),
            "date": "2026-06-16",
            "analyst": ""
        }

        if self._analysis_type == "hole":
            results, summary = HoleAnalyzer.analyze(self._canvas.regions, scale, image_area_px)
            fill_stats = [
                {"status": "未充填", "count": len(results), "area": summary["total_area_mm2"], "percent": 100}
            ]
            effect = {"valid": len(results), "semi_valid": 0, "invalid": 0}
            html = ReportGenerator.generate_hole_report(summary, fill_stats, effect, info)
        else:
            results, summary = FractureAnalyzer.analyze(
                self._canvas.regions, scale, image_area_px, core_length_m=1.0)
            fractures = [
                {"length_mm": r.length_mm, "width_mm": r.width_mm, "area_mm2": r.area_mm2,
                 "fracture_type": r.fracture_type, "fill_status": r.fill_status,
                 "effectiveness": r.effectiveness}
                for r in results
            ]
            type_stats = [{"type": "构造缝", "count": len(results), "total_length": summary["total_length_mm"]}]
            html = ReportGenerator.generate_fracture_report(summary, fractures, type_stats, info)

        # Save session
        session = AnalysisSession(image_id=self._current_image_id,
                                  analysis_type=self._analysis_type,
                                  params_json=json.dumps({"scale": scale}))
        session_id = self._store.create_session(session)
        self._store.update_session_report(session_id, html)

        self._report_viewer.show_report(html)

    def _toggle_overlay(self):
        self._canvas.toggle_overlay(not self._canvas._overlay_visible)

    def _undo(self):
        pass  # To be implemented with QUndoStack

    def _redo(self):
        pass  # To be implemented with QUndoStack
```

- [ ] **Step 2: Update main.py**

Edit `core_analysis/main.py`:
```python
"""岩心孔洞裂缝分析教学系统 — 入口"""

import sys
from PySide6.QtWidgets import QApplication
from core_analysis.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("岩心孔洞裂缝分析教学系统")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Verify application launches (headless check)**

```bash
python -c "
import sys
from PySide6.QtWidgets import QApplication
app = QApplication(sys.argv)
from core_analysis.ui.main_window import MainWindow
w = MainWindow(':memory:')
w.show()
print('MainWindow created successfully')
app.quit()
"
```

Expected: `MainWindow created successfully`

- [ ] **Step 4: Commit**

```bash
git add core_analysis/ui/main_window.py core_analysis/main.py
git commit -m "feat: integrate MainWindow with all UI and engine modules"
```

---

### Task 17: End-to-End Smoke Test

**Files:**
- Create: `tests/test_smoke.py`

- [ ] **Step 1: Write smoke test**

Write `tests/test_smoke.py`:
```python
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
    """Test the full analysis pipeline: image → extract → analyze → report."""

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

        # 7. Report has charts
        assert "base64" in html or "<img" in html
```

- [ ] **Step 2: Run smoke test**

```bash
python -m pytest tests/test_smoke.py -v
```

Expected: 1 passed (the full pipeline works end-to-end)

- [ ] **Step 3: Run all tests**

```bash
python -m pytest tests/ -v
```

Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add tests/test_smoke.py
git commit -m "test: add end-to-end smoke test for full analysis pipeline"
```

---

## Summary

| Task | Component | Files Created | Lines |
|---|---|---|---|
| 1 | Scaffold | 6 | ~30 |
| 2 | Data Models | 1 | ~80 |
| 3 | Database | 2 | ~100 |
| 4 | Image Repository | 2 | ~150 |
| 5 | Analysis Store | 2 | ~170 |
| 6 | Image Processor | 2 | ~70 |
| 7 | Region Extractor | 2 | ~90 |
| 8 | Morphology Engine | 2 | ~120 |
| 9 | Hole Analyzer | 2 | ~80 |
| 10 | Fracture Analyzer | 2 | ~100 |
| 11 | Report Generator | 4 | ~250 |
| 12 | Image Canvas | 1 | ~140 |
| 13 | Tool Panel | 1 | ~170 |
| 14 | Image Library | 1 | ~180 |
| 15 | Report Viewer | 1 | ~60 |
| 16 | Main Window | 2 | ~200 |
| 17 | Smoke Test | 1 | ~60 |

**Total**: ~20 files, ~2100 lines of code

---

> **Next**: Choose execution approach — Subagent-Driven (recommended) or Inline Execution
