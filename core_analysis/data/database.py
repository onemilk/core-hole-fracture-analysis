"""ProjectManager — SQLite database creation, connection, migration."""

import sqlite3
import os


class ProjectManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._persistent_conn: sqlite3.Connection | None = None

    def initialize(self):
        """Create tables if they don't exist. Idempotent."""
        conn = self.get_connection()
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

            CREATE TABLE IF NOT EXISTS grain_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER REFERENCES images(id),
                session_id INTEGER REFERENCES analysis_sessions(id),
                region_index INTEGER,
                area_mm2 REAL,
                equivalent_d_mm REAL,
                perimeter_mm REAL,
                feret_long_mm REAL,
                feret_short_mm REAL,
                circularity REAL,
                size_category TEXT,
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

    def get_connection(self) -> sqlite3.Connection:
        """Return a connection. For :memory: databases, reuse a persistent
        connection so that schema and data survive across calls."""
        if self.db_path == ":memory:":
            if self._persistent_conn is None:
                self._persistent_conn = sqlite3.connect(":memory:")
                self._persistent_conn.row_factory = sqlite3.Row
                self._persistent_conn.execute("PRAGMA foreign_keys = ON")
            return self._persistent_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def close(self):
        """Close the persistent connection if one was opened (e.g. :memory:)."""
        if self._persistent_conn is not None:
            self._persistent_conn.close()
            self._persistent_conn = None
