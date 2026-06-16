"""岩心孔洞裂缝分析教学系统 — 入口"""

import sys
import os
from PySide6.QtWidgets import QApplication
from core_analysis.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("岩心孔洞裂缝分析教学系统")
    # Use fixed path relative to this file, not CWD
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core_analysis.db")
    window = MainWindow(db_path)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
