"""MainWindow — top-level application window integrating all UI modules."""

import os, json
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QMainWindow, QMenuBar, QMenu, QToolBar, QStatusBar,
    QFileDialog, QMessageBox, QWidget, QHBoxLayout, QLabel
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

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
from core_analysis.ui.knowledge_dialog import KnowledgeDialog


class MainWindow(QMainWindow):
    def __init__(self, db_path: str = "core_analysis.db"):
        super().__init__()
        self.setWindowTitle("岩心孔洞裂缝分析教学系统")
        self.resize(1280, 800)

        # Data Layer
        self._pm = ProjectManager(db_path)
        self._pm.initialize()
        self._repo = ImageRepository(self._pm)
        self._store = AnalysisStore(self._pm)

        # UI Components
        self._canvas = ImageCanvas()
        self._tool_panel = ToolPanel()
        self._report_viewer = ReportViewer()
        self._image_library = ImageLibraryWidget(self._repo)

        # State
        self._current_image_id = None
        self._current_image_record = None
        self._analysis_type = "hole"

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")
        file_menu.addAction("打开项目", self._open_project)
        file_menu.addAction("新建项目", self._new_project)
        file_menu.addAction("导入图像", self._import_image)
        file_menu.addSeparator()
        file_menu.addAction("退出", self.close)

        process_menu = menubar.addMenu("处理")
        process_menu.addAction("自动色阶", self._auto_levels)

        rotate_menu = process_menu.addMenu("旋转")
        rotate_menu.addAction("↺ 90°左转", lambda: self._canvas.rotate_view(90))
        rotate_menu.addAction("↻ 90°右转", lambda: self._canvas.rotate_view(-90))
        rotate_menu.addAction("180°旋转", lambda: self._canvas.rotate_view(180))
        rotate_menu.addAction("↔ 水平翻转", self._flip_horizontal)
        rotate_menu.addAction("↕ 竖直翻转", self._flip_vertical)
        rotate_menu.addSeparator()
        rotate_menu.addAction("自定义角度...", self._rotate_custom)
        rotate_menu.addAction("重置旋转", self._canvas.reset_rotation)

        analysis_menu = menubar.addMenu("分析")
        analysis_menu.addAction("孔洞分析", lambda: self._set_analysis_type("hole"))
        analysis_menu.addAction("裂缝分析", lambda: self._set_analysis_type("fracture"))
        analysis_menu.addAction("粒度分析", lambda: self._set_analysis_type("grain"))
        analysis_menu.addAction("标尺设定", self._set_scale)
        analysis_menu.addAction("生成报告", self._generate_report)

        help_menu = menubar.addMenu("帮助")
        help_menu.addAction("沉积知识库", self._open_knowledge)

        toolbar = self.addToolBar("主工具栏")
        toolbar.addAction("📁 打开", self._import_image)
        toolbar.addSeparator()
        toolbar.addAction("🔍 自动提取", self._auto_extract)
        toolbar.addAction("📊 生成报告", self._generate_report)
        toolbar.addSeparator()
        toolbar.addAction("📏 标尺", self._set_scale)
        toolbar.addSeparator()
        toolbar.addAction("🔍+", self._canvas.zoom_in)
        toolbar.addAction("🔍-", self._canvas.zoom_out)
        toolbar.addAction("👁️ 图层", self._toggle_overlay)
        toolbar.addSeparator()
        toolbar.addAction("↺ 左转", lambda: self._canvas.rotate_view(90))
        toolbar.addAction("↻ 右转", lambda: self._canvas.rotate_view(-90))
        toolbar.addAction("↔ 翻转", self._flip_horizontal)

        central = QWidget()
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.addWidget(self._canvas, 1)
        central_layout.addWidget(self._tool_panel)
        self.setCentralWidget(central)

        self.addDockWidget(Qt.LeftDockWidgetArea, self._image_library)

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
        if img is None: return
        self._current_image_id = image_id
        self._current_image_record = img
        try:
            self._canvas.load_image(img.filepath)
            self._size_label.setText(f"图像: {self._canvas.image_size[1]}×{self._canvas.image_size[0]}")
            if img.scale_value:
                self._scale_label.setText(f"标尺: {img.scale_value} mm/px")
        except FileNotFoundError:
            QMessageBox.warning(self, "错误", f"找不到文件: {img.filepath}")

    def _set_analysis_type(self, atype: str):
        self._analysis_type = atype
        type_names = {"hole": "孔洞分析", "fracture": "裂缝分析", "grain": "粒度分析"}
        self.setWindowTitle(f"岩心孔洞裂缝分析教学系统 — {type_names.get(atype, '')}")

    def _auto_extract(self):
        if self._canvas.image_bgr is None: return
        h, w = self._canvas.image_size
        sample_color = self._canvas.image_bgr[h // 2, w // 2]
        tolerance = self._tool_panel.match_tolerance()
        regions = RegionExtractor.extract_by_color_sample(
            self._canvas.image_bgr, sample_color, tolerance)
        threshold = self._tool_panel.denoise_threshold()
        regions = MorphologyEngine.denoise_by_area(regions, min_area_px=threshold)
        self._canvas.set_regions(regions)
        self._detect_label.setText(f"检测: {len(regions)}个区域")

    def _on_morphology(self, op: str):
        regions = self._canvas.regions
        if not regions: return
        updated = []
        for r in regions:
            if op == "dilate":
                result = MorphologyEngine.dilate_region(r)
            elif op == "erode":
                result = MorphologyEngine.erode_region(r)
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

    def _auto_levels(self):
        if self._canvas.image_bgr is not None:
            result = ImageProcessor.auto_levels(self._canvas.image_bgr)
            self._canvas.load_image_from_array(result)

    def _set_scale(self):
        from PySide6.QtWidgets import QInputDialog
        scale, ok = QInputDialog.getDouble(self, "标尺设定", "mm/pixel:", 0.05, 0.001, 100.0, 4)
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
            "image_id": str(img.id) if img else "", "well": str(img.filename) if img else "",
            "depth": str(img.depth_from) if img and img.depth_from else "", "layer": "",
            "lithology": img.lithology if img else "", "scale": str(scale),
            "date": "2026-06-16", "analyst": ""
        }
        if self._analysis_type == "hole":
            results, summary = HoleAnalyzer.analyze(self._canvas.regions, scale, image_area_px)
            fill_stats = [{"status": "未充填", "count": len(results), "area": summary["total_area_mm2"], "percent": 100}]
            effect = {"valid": len(results), "semi_valid": 0, "invalid": 0}
            html = ReportGenerator.generate_hole_report(summary, fill_stats, effect, info)
        elif self._analysis_type == "grain":
            from core_analysis.engine.grain_analyzer import GrainAnalyzer
            results, summary = GrainAnalyzer.analyze(self._canvas.regions, scale, image_area_px)
            feret_data = [(r.feret_long_mm, r.feret_short_mm) for r in results]
            summary["feret_data"] = feret_data
            html = ReportGenerator.generate_grain_report(summary, info)
        else:
            results, summary = FractureAnalyzer.analyze(self._canvas.regions, scale, image_area_px, core_length_m=1.0)
            fractures = [{"length_mm": r.length_mm, "width_mm": r.width_mm, "area_mm2": r.area_mm2,
                          "fracture_type": r.fracture_type, "fill_status": r.fill_status, "effectiveness": r.effectiveness} for r in results]
            type_stats = [{"type": "构造缝", "count": len(results), "total_length": summary["total_length_mm"]}]
            html = ReportGenerator.generate_fracture_report(summary, fractures, type_stats, info)
        session = AnalysisSession(image_id=self._current_image_id, analysis_type=self._analysis_type)
        session_id = self._store.create_session(session)
        # Persist individual result records
        for r in results:
            r.image_id = self._current_image_id
            r.session_id = session_id
        if self._analysis_type == "hole":
            self._store.save_hole_results(results)
        elif self._analysis_type == "grain":
            self._store.save_grain_results(results)
        else:
            self._store.save_fracture_results(results)
        self._store.update_session_report(session_id, html)
        self._report_viewer.show_report(html)

    def _flip_horizontal(self):
        if self._canvas.image_bgr is None: return
        flipped = ImageProcessor.flip_horizontal(self._canvas.image_bgr)
        self._canvas.load_image_from_array(flipped)

    def _flip_vertical(self):
        if self._canvas.image_bgr is None: return
        flipped = ImageProcessor.flip_vertical(self._canvas.image_bgr)
        self._canvas.load_image_from_array(flipped)

    def _rotate_custom(self):
        if self._canvas.image_bgr is None: return
        from PySide6.QtWidgets import QInputDialog
        angle, ok = QInputDialog.getDouble(self, "自定义旋转", "角度 (正值=逆时针):",
                                           0, -180, 180, 1)
        if ok:
            self._canvas.rotate_view(angle)

    def _open_knowledge(self):
        dialog = KnowledgeDialog(self)
        dialog.exec()

    def _toggle_overlay(self):
        self._canvas.toggle_overlay(not self._canvas._overlay_visible)
