"""KnowledgeDialog — searchable sedimentary knowledge base browser."""

import json
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QTextBrowser, QSplitter
)
from PySide6.QtCore import Qt


class KnowledgeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("沉积知识库")
        self.resize(800, 500)
        self._data = {}
        self._load_data()
        self._setup_ui()

    def _load_data(self):
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "sedimentary_knowledge.json"
        )
        with open(json_path, 'r', encoding='utf-8') as f:
            self._data = json.load(f)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索知识库...")
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        splitter = QSplitter(Qt.Horizontal)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.itemClicked.connect(self._on_item_clicked)
        splitter.addWidget(self._tree)

        self._detail = QTextBrowser()
        self._detail.setOpenExternalLinks(False)
        self._detail.anchorClicked.connect(self._on_link_clicked)
        splitter.addWidget(self._detail)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        self._populate_tree()

    def _populate_tree(self, filter_text: str = ""):
        self._tree.clear()
        categories = self._data.get("categories", {})
        for cat_name, entries in categories.items():
            cat_item = QTreeWidgetItem([cat_name])
            cat_item.setData(0, Qt.UserRole, ("category", cat_name))
            has_visible_children = False
            for entry_name, entry_data in entries.items():
                match_in_name = filter_text.lower() in entry_name.lower() if filter_text else True
                match_in_def = filter_text.lower() in entry_data.get("definition", "").lower() if filter_text else True
                if not filter_text or match_in_name or match_in_def:
                    item = QTreeWidgetItem([entry_name])
                    item.setData(0, Qt.UserRole, ("entry", cat_name, entry_name))
                    cat_item.addChild(item)
                    has_visible_children = True
            if has_visible_children or not filter_text:
                self._tree.addTopLevelItem(cat_item)
        self._tree.expandAll()

    def _on_item_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if data is None: return
        if data[0] == "entry":
            self._show_entry(data[1], data[2])

    def _show_entry(self, category: str, entry_name: str):
        entries = self._data.get("categories", {}).get(category, {})
        entry = entries.get(entry_name, {})
        definition = entry.get("definition", "")
        related = entry.get("related", [])

        html = f"<h3>{entry_name}</h3><p style='line-height:1.8;'>{definition}</p>"
        if related:
            html += "<hr><b>相关条目:</b><ul>"
            for r in related:
                html += f'<li><a href="#{r}">{r}</a></li>'
            html += "</ul>"
        self._detail.setHtml(html)

    def _on_link_clicked(self, url):
        target = url.toString().lstrip("#")
        self._search.setText("")
        self._populate_tree()
        for i in range(self._tree.topLevelItemCount()):
            cat_item = self._tree.topLevelItem(i)
            for j in range(cat_item.childCount()):
                child = cat_item.child(j)
                data = child.data(0, Qt.UserRole)
                if data and data[0] == "entry" and data[2] == target:
                    cat_item.setExpanded(True)
                    self._tree.setCurrentItem(child)
                    self._show_entry(data[1], data[2])
                    return

    def _on_search(self, text: str):
        self._populate_tree(text)
        self._tree.expandAll()
