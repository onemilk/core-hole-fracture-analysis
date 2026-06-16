"""岩心孔洞裂缝分析教学系统 — 入口"""

import sys
import os
from PySide6.QtWidgets import QApplication
from core_analysis.ui.main_window import MainWindow


def _get_db_path():
    """Return absolute db path. Works for both python and PyInstaller exe."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller exe — db next to exe
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as python script — db in project root
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "core_analysis.db")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("岩心孔洞裂缝分析教学系统")
    db_path = _get_db_path()
    window = MainWindow(db_path)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
