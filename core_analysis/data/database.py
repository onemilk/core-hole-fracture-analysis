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
