"""岩心孔洞裂缝分析教学系统 — 入口"""

import sys
from PySide6.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("岩心孔洞裂缝分析教学系统")
    # MainWindow will be integrated in Task 15
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
