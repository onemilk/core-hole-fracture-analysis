"""ImageLibraryWidget — QDockWidget with category tree and thumbnail grid."""

import os
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem,
    QLineEdit, QPushButton, QFileDialog, QMenu, QInputDialog, QMessageBox,
    QLabel
)
from PySide6.QtGui import QIcon, QPixmap, QAction, QImage
from PySide6.QtCore import Qt, Signal
import cv2
from core_analysis.data.models import Category, ImageRecord


class ImageLibraryWidget(QDockWidget):
    image_selected = Signal(int)
    image_imported = Signal(int)
    category_added = Signal(int)

    def __init__(self, image_repository, parent=None):
        super().__init__("图像库", parent)
        self._repo = image_repository
        self._setup_ui()
        self.refresh_tree()

    def _setup_ui(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        search_row = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 搜索...")
        self._search_input.returnPressed.connect(self._on_search)
        search_row.addWidget(self._search_input)
        import_btn = QPushButton("+导入")
        import_btn.clicked.connect(self._on_import)
        search_row.addWidget(import_btn)
        layout.addLayout(search_row)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        self._tree.itemClicked.connect(self._on_tree_item_clicked)
        layout.addWidget(self._tree)

        self._thumb_list = QListWidget()
        self._thumb_list.setViewMode(QListWidget.IconMode)
        self._thumb_list.setIconSize(self._thumb_list.iconSize().scaled(120, 120, Qt.KeepAspectRatio))
        self._thumb_list.setResizeMode(QListWidget.Adjust)
        self._thumb_list.itemDoubleClicked.connect(self._on_thumb_double_clicked)
        layout.addWidget(self._thumb_list)

        self.setWidget(widget)

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
            if os.path.exists(img.filepath):
                bgr = cv2.imread(img.filepath)
                if bgr is not None:
                    h, w = bgr.shape[:2]
                    scale = min(120 / w, 120 / h)
                    thumb = cv2.resize(bgr, (int(w * scale), int(h * scale)))
                    rgb = cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)
                    h2, w2, ch = rgb.shape
                    qimg = QImage(rgb.data, w2, h2, w2 * ch, QImage.Format_RGB888)
                    item.setIcon(QIcon(QPixmap.fromImage(qimg)))
            self._thumb_list.addItem(item)

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
        cats = self._repo.get_category_tree()
        cat_name, ok = QInputDialog.getItem(
            self, "选择分类", "将图像导入到:", [c.name for c in cats], 0, False)
        if not ok or not cats:
            return
        cat = next((c for c in cats if c.name == cat_name), cats[0])
        for f in files:
            img = ImageRecord(category_id=cat.id, filename=os.path.basename(f), filepath=f)
            img_id = self._repo.add_image(img)
            self.image_imported.emit(img_id)
        self.refresh_tree()

    def _on_tree_item_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if data is None: return
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
        add_cat = QAction("添加分类", self)
        add_cat.triggered.connect(self._on_add_category)
        menu.addAction(add_cat)
        if item:
            del_action = QAction("删除", self)
            del_action.triggered.connect(lambda: self._on_delete_item(item))
            menu.addAction(del_action)
        menu.exec_(self._tree.viewport().mapToGlobal(pos))

    def _on_add_category(self):
        name, ok = QInputDialog.getText(self, "添加分类", "分类名称:")
        if ok and name:
            type_name, ok2 = QInputDialog.getItem(self, "分类类型", "类型:",
                ["basin", "block", "structure", "well"], 0, False)
            if ok2:
                cat = Category(name=name, type=type_name)
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
        if data is None: return
        dtype, obj_id = data
        reply = QMessageBox.question(self, "确认删除", f"确定删除此项?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes and dtype == "image":
            self._repo.delete_image(obj_id)
            self.refresh_tree()
