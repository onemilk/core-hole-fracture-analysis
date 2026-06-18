"""ToolPanel — Left tool bar + right parameter panel for hole/fracture analysis."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSlider, QComboBox, QCheckBox, QSpinBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal


class ToolPanel(QWidget):
    tool_changed = Signal(str)
    auto_extract_requested = Signal()
    match_tolerance_changed = Signal(int)
    continuous_mode_changed = Signal(bool)
    denoise_threshold_changed = Signal(int)
    morphology_requested = Signal(str)
    fill_status_changed = Signal(str)
    fill_material_changed = Signal(str)
    effectiveness_changed = Signal(str)
    model_changed = Signal(str)  # "classic" | "unet"
    roi_select_requested = Signal()
    roi_clear_requested = Signal()
    brush_confirm_requested = Signal()
    save_params_requested = Signal()
    view_report_requested = Signal()

    TOOLS = [
        ("pan", "\U0001f590", "漫游"), ("select", "⬚", "选择"), ("multi_select", "▣", "多选"),
        ("segment", "\U0001f3af", "区域分割"), ("eraser_minus", "\U0001f9f9", "橡皮擦-"),
        ("eraser_plus", "\U0001f9f9+", "橡皮擦+"), ("dilate_local", "⭢", "局部膨胀"),
        ("erode_local", "⭠", "局部腐蚀"), ("brush", "✏️", "画笔"),
        ("rect", "▭", "矩形"), ("ellipse", "○", "椭圆"), ("text", "T", "文字"),
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

        # Left Tool Bar
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

        # Right Parameter Panel
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
        self._match_slider.valueChanged.connect(lambda v: self._match_label.setText(str(v)))
        auto_layout.addWidget(self._match_label)
        self._continuous_cb = QCheckBox("连续区域")
        self._continuous_cb.toggled.connect(self.continuous_mode_changed.emit)
        auto_layout.addWidget(self._continuous_cb)
        self._model_combo = QComboBox()
        self._model_combo.addItems(["经典颜色分割", "U-Net 深度学习"])
        self._model_combo.currentIndexChanged.connect(
            lambda i: self.model_changed.emit("unet" if i == 1 else "classic"))
        auto_layout.addWidget(QLabel("分割模型"))
        auto_layout.addWidget(self._model_combo)
        extract_btn = QPushButton("一键提取")
        extract_btn.clicked.connect(self.auto_extract_requested.emit)
        auto_layout.addWidget(extract_btn)
        roi_btn = QPushButton("📐 框定分析区域")
        roi_btn.clicked.connect(self.roi_select_requested.emit)
        auto_layout.addWidget(roi_btn)
        clear_roi_btn = QPushButton("清除区域")
        clear_roi_btn.clicked.connect(self.roi_clear_requested.emit)
        auto_layout.addWidget(clear_roi_btn)
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
        for name, op in [("膨胀", "dilate"), ("腐蚀", "erode"), ("填充", "fill")]:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, o=op: self.morphology_requested.emit(o))
            morph_row.addWidget(btn)
        edit_layout.addRow(morph_row)
        confirm_btn = QPushButton("✅ 确认涂改")
        confirm_btn.clicked.connect(self.brush_confirm_requested.emit)
        edit_layout.addRow(confirm_btn)
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

        save_btn = QPushButton("✅ 修改保存")
        save_btn.clicked.connect(self.save_params_requested.emit)
        right_panel.addWidget(save_btn)
        report_btn = QPushButton("📊 查看报告")
        report_btn.clicked.connect(self.view_report_requested.emit)
        right_panel.addWidget(report_btn)
        right_panel.addStretch()
        main_layout.addLayout(right_panel)

    def match_tolerance(self) -> int: return self._match_slider.value()
    def is_continuous_mode(self) -> bool: return self._continuous_cb.isChecked()
    def denoise_threshold(self) -> int: return self._denoise_spin.value()
    def current_fill_status(self) -> str: return self._fill_status_combo.currentText()
    def current_fill_material(self) -> str: return self._fill_material_combo.currentText()
    def current_effectiveness(self) -> str: return self._effectiveness_combo.currentText()
