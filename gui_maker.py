import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, 
                             QVBoxLayout, QWidget, QPushButton, QComboBox, QDialog, 
                             QTextEdit, QDialogButtonBox)
from PyQt5.QtCore import Qt
import window_detector
import json

class JsonViewerDialog(QDialog):
    def __init__(self, content):
        super().__init__()
        self.setWindowTitle("Daas Detector - SKKU CSDF Lab")
        self.setGeometry(100, 100, 1200, 600)

        layout = QVBoxLayout()

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        
        try:
            json_object = json.loads(content)
            formatted_content = json.dumps(json_object, indent=2)
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 원본 문자열 사용
            formatted_content = content

        self.text_edit.setPlainText(formatted_content)
        layout.addWidget(self.text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)

class SettingsViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings Viewer")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        self.service_combo = QComboBox()
        self.service_combo.addItems(["Amazon Workspaces", "Citrix VDI", "Gabia VDI"])
        layout.addWidget(self.service_combo)
        
        self.analyze_button = QPushButton("Analyze")
        layout.addWidget(self.analyze_button)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Type", "File Name", "Path", "Core Artifacts", "Created Date", "Modified Date"])
        layout.addWidget(self.table)
        
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.analyze_button.clicked.connect(self.analyze_service)

    def analyze_service(self):
        selected_service = self.service_combo.currentText()
        print(f"Analyzing {selected_service}")
        
        results = window_detector.main()
        
        self.table.setRowCount(0)
        
        for row, result in enumerate(results):
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(result.get("file_type", "")))
            self.table.setItem(row, 1, QTableWidgetItem(result.get("file_name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(result.get("file_path", "")))
            
            view_button = QPushButton("View")
            view_button.clicked.connect(lambda _, c=result.get("content", ""): self.show_json_viewer(c))
            self.table.setCellWidget(row, 3, view_button)
            
            self.table.setItem(row, 4, QTableWidgetItem(result.get("created_time", "")))
            self.table.setItem(row, 5, QTableWidgetItem(result.get("modified_time", "")))

        self.table.resizeColumnsToContents()

    def show_json_viewer(self, content):
        dialog = JsonViewerDialog(content)
        dialog.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = SettingsViewer()
    viewer.show()
    sys.exit(app.exec_())