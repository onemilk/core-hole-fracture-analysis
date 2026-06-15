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
