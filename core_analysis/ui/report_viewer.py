"""ReportViewer — HTML report display with export capability."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser,
    QPushButton, QFileDialog
)
from PySide6.QtPrintSupport import QPrinter


class ReportViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._report_html = ""

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        export_html_btn = QPushButton("导出 HTML")
        export_html_btn.clicked.connect(self._export_html)
        export_pdf_btn = QPushButton("导出 PDF")
        export_pdf_btn.clicked.connect(self._export_pdf)
        close_btn = QPushButton("关闭")
        toolbar.addWidget(export_html_btn)
        toolbar.addWidget(export_pdf_btn)
        toolbar.addStretch()
        toolbar.addWidget(close_btn)
        layout.addLayout(toolbar)

        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        layout.addWidget(self._browser)

        close_btn.clicked.connect(self.hide)

    def show_report(self, html: str):
        self._report_html = html
        self._browser.setHtml(html)
        self.show()

    def _export_html(self):
        if not self._report_html: return
        path, _ = QFileDialog.getSaveFileName(self, "导出 HTML 报告", "report.html",
                                              "HTML files (*.html);;All files (*)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self._report_html)

    def _export_pdf(self):
        if not self._report_html: return
        path, _ = QFileDialog.getSaveFileName(self, "导出 PDF 报告", "report.pdf",
                                              "PDF files (*.pdf);;All files (*)")
        if path:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            self._browser.print_(printer)
