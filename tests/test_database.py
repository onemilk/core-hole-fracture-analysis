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
        """初始化应创建7张表"""
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
        assert "grain_results" in tables
        assert "analysis_sessions" in tables
        conn.close()

    def test_initialize_is_idempotent(self, db, temp_db_path):
        """重复初始化不应报错"""
        db.initialize()  # second call
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert len(tables) == 7
        conn.close()

    def test_get_connection_returns_connection(self, db):
        """get_connection 应返回 sqlite3.Connection"""
        conn = db.get_connection()
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_close(self, db):
        """close 正常关闭"""
        db.close()
        db.initialize()  # should work after close
