# -*- coding: utf-8 -*-
# ui.py

import os
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTreeView, QLabel, QFileDialog, QLineEdit,
    QMessageBox, QInputDialog, QFrame, QDialog,
    QDialogButtonBox, QSplitter, QPlainTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QStyle, QTextEdit, QProgressBar, QCheckBox
)
from PyQt6.QtGui import (
    QIcon, QCloseEvent, QStandardItemModel, QStandardItem, 
    QPainter, QColor, QTextFormat, QPaintEvent, QResizeEvent, QMouseEvent, QTextCursor
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QRect, QSize, QPoint, QTimer

class LineNumberArea(QWidget):
    lineClicked = pyqtSignal(int)
    def __init__(self, editor):
        super().__init__(editor)
        self.prompt_editor = editor
        self.start_line_index = 0
    def sizeHint(self): return QSize(self.prompt_editor.lineNumberAreaWidth(), 0)
    def paintEvent(self, a0: QPaintEvent | None):
        if a0: self.prompt_editor.lineNumberAreaPaintEvent(a0)
    def mousePressEvent(self, a0: QMouseEvent | None):
        if a0:
            block = self.prompt_editor.firstVisibleBlock()
            if not block.isValid(): return
            top = self.prompt_editor.blockBoundingGeometry(block).translated(self.prompt_editor.contentOffset()).top()
            bottom = top + self.prompt_editor.blockBoundingRect(block).height()
            while block.isValid():
                if top <= a0.pos().y() <= bottom: self.lineClicked.emit(block.blockNumber()); break
                block = block.next()
                if not block.isValid(): break
                top, bottom = bottom, top + self.prompt_editor.blockBoundingRect(block).height()

class PromptEditor(QPlainTextEdit):
    cursor_line_changed = pyqtSignal(int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.cursorPositionChanged.connect(lambda: self.cursor_line_changed.emit(self.textCursor().blockNumber()))
        self.updateLineNumberAreaWidth(0)
    def lineNumberAreaWidth(self):
        digits = len(str(max(1, self.blockCount())))
        return 25 + self.fontMetrics().horizontalAdvance('9') * digits
    def updateLineNumberAreaWidth(self, _): self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)
    def updateLineNumberArea(self, rect, dy):
        if dy: self.lineNumberArea.scroll(0, dy)
        else: self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        viewport = self.viewport()
        if viewport and rect.contains(viewport.rect()): self.updateLineNumberAreaWidth(0)
    def resizeEvent(self, e: QResizeEvent | None):
        super().resizeEvent(e)
        if e: cr = self.contentsRect(); self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))
    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor("#f8f9fa"))
        block = self.firstVisibleBlock()
        if not block.isValid(): return
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        current_line_number = self.textCursor().blockNumber()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                if blockNumber == self.lineNumberArea.start_line_index:
                    painter.setPen(QColor("#007bff")); painter.drawText(5, int(top), 15, int(self.fontMetrics().height()), Qt.AlignmentFlag.AlignVCenter, "▶")
                font = painter.font(); font.setPixelSize(14)
                if blockNumber == current_line_number: painter.setPen(QColor("#0056b3")); font.setBold(True)
                else: painter.setPen(QColor("#6c757d")); font.setBold(False)
                painter.setFont(font)
                painter.drawText(20, int(top), self.lineNumberArea.width() - 25, int(self.fontMetrics().height()), Qt.AlignmentFlag.AlignRight, number)
            block = block.next(); top = bottom; bottom = top + self.blockBoundingRect(block).height(); blockNumber += 1
    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#e7f3ff"))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor(); selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)
    def set_start_line_indicator(self, index):
        self.lineNumberArea.start_line_index = index; self.lineNumberArea.update()

class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cài đặt")
        self.setMinimumWidth(550)
        layout = QVBoxLayout(self)
        
        hotkey_layout = QHBoxLayout(); hotkey_label = QLabel("Hotkey:")
        self.hotkey_input = QLineEdit(settings.get("hotkey"))
        hotkey_layout.addWidget(hotkey_label); hotkey_layout.addWidget(self.hotkey_input)
        layout.addLayout(hotkey_layout)

        data_path_layout, self.storage_path_input = self._create_path_selector("Thư mục dữ liệu:", settings.get("storage_path", ""))
        layout.addLayout(data_path_layout)
        
        layout.addStretch()

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept); button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_path_selector(self, label_text, current_path):
        layout = QHBoxLayout(); label = QLabel(label_text)
        path_input = QLineEdit(current_path); path_input.setReadOnly(True)
        browse_button = QPushButton("Chọn..."); browse_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        browse_button.clicked.connect(lambda: self.browse_directory(path_input))
        layout.addWidget(label); layout.addWidget(path_input, 1); layout.addWidget(browse_button)
        return layout, path_input

    def browse_directory(self, target_input: QLineEdit):
        current_text = target_input.text()
        directory = QFileDialog.getExistingDirectory(self, "Chọn thư mục", current_text)
        if directory: target_input.setText(directory)
            
    def get_values(self):
        return {
            "hotkey": self.hotkey_input.text().strip().lower(), 
            "storage_path": self.storage_path_input.text().strip()
        }

class DashboardDialog(QDialog):
    def __init__(self, log_file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dashboard Thống Kê")
        self.setMinimumSize(800, 500)
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Bắt đầu", "Kết thúc", "Danh sách", "Đã Paste", "Trạng thái"])
        header = self.table.horizontalHeader()
        if header: header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True); self.table.setSortingEnabled(True)
        self.table.setShowGrid(False)
        v_header = self.table.verticalHeader()
        if v_header: v_header.setVisible(False)
        layout.addWidget(self.table)
        self.load_logs(log_file_path)
    def load_logs(self, log_file_path):
        import json
        if not os.path.exists(log_file_path): return
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f: logs = json.load(f)
            if not isinstance(logs, list): return
            self.table.setRowCount(len(logs))
            for row, log_entry in enumerate(reversed(logs)):
                if not isinstance(log_entry, dict): continue
                self.table.setItem(row, 0, QTableWidgetItem(str(log_entry.get("start_time", ""))))
                self.table.setItem(row, 1, QTableWidgetItem(str(log_entry.get("end_time", ""))))
                self.table.setItem(row, 2, QTableWidgetItem(str(log_entry.get("list_key", ""))))
                self.table.setItem(row, 3, QTableWidgetItem(str(log_entry.get("paste_count", 0))))
                self.table.setItem(row, 4, QTableWidgetItem(str(log_entry.get("status", ""))))
        except Exception as e: print(f"Error loading dashboard logs: {e}")

class MiniController(QFrame):
    stop_signal = pyqtSignal(); pause_resume_signal = pyqtSignal()
    def __init__(self, list_name, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.drag_position = QPoint()
        self.setObjectName("miniControllerFrame")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8); layout.setSpacing(10)
        
        self.info_label = QLabel(f"Đang chạy: <b>{list_name}</b>")
        self.progress_label = QLabel("0/0")
        self.pause_resume_button = QPushButton("Tạm dừng")
        self.stop_button = QPushButton("Dừng")
        
        for btn in [self.pause_resume_button, self.stop_button]: btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pause_resume_button.setCheckable(True)
        self.pause_resume_button.clicked.connect(self.pause_resume_signal.emit)
        self.stop_button.clicked.connect(self.stop_signal.emit)
        
        layout.addWidget(self.info_label); layout.addStretch(); layout.addWidget(self.progress_label)
        layout.addWidget(self.pause_resume_button); layout.addWidget(self.stop_button)
        
        self.setStyleSheet("""
            #miniControllerFrame {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
            QLabel {
                color: #333333;
                background-color: transparent;
            }
            QPushButton {
                background-color: #F0F0F0;
                border: 1px solid #BDBDBD;
                border-radius: 5px;
                padding: 5px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
            QPushButton:checked {
                background-color: #BEE3F8;
                border: 1px solid #90CDF4;
            }
            #stop_button {
                background-color: #FED7D7;
                border: 1px solid #F56565;
            }
            #stop_button:hover {
                 background-color: #FCA5A5;
            }
        """)
        self.stop_button.setObjectName("stop_button")


    def mousePressEvent(self, a0: QMouseEvent | None):
        if a0 and a0.button() == Qt.MouseButton.LeftButton: self.drag_position = a0.globalPosition().toPoint() - self.frameGeometry().topLeft(); a0.accept()
    def mouseMoveEvent(self, a0: QMouseEvent | None):
        if a0 and a0.buttons() == Qt.MouseButton.LeftButton: self.move(a0.globalPosition().toPoint() - self.drag_position); a0.accept()
    def set_paused_state(self, is_paused): self.pause_resume_button.setChecked(is_paused); self.pause_resume_button.setText("Tiếp tục" if is_paused else "Tạm dừng")
    def update_progress(self, current, total): self.progress_label.setText(f"<b>{current}</b>/{total}")

class MainWindow(QMainWindow):
    def __init__(self, core_logic):
        super().__init__()
        self.core = core_logic
        self.mini_controller = None
        self.setWindowTitle(f"Prompt Paster v9.2")
        self.setGeometry(100, 100, 1000, 750)
        
        # Sửa lại vị trí logo
        icon_path = os.path.join("logos", "logo.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Timer for auto-saving prompts
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.setInterval(1500) # 1.5 seconds delay

        self.setup_ui()
        self.connect_signals()
        self._update_ui_state()

    def setup_ui(self):
        central_widget = QWidget(); self.setCentralWidget(central_widget); main_layout = QHBoxLayout(central_widget)
        left_panel = QWidget(); left_panel.setObjectName("leftPanel"); left_layout = QVBoxLayout(left_panel)
        self.tree_view = QTreeView(); self.tree_view.setHeaderHidden(True); self.tree_model = QStandardItemModel(); self.tree_view.setModel(self.tree_model)
        list_mgmt_buttons_layout = QHBoxLayout()
        self.new_folder_button = QPushButton("Thư mục mới"); self.new_list_button = QPushButton("Danh sách mới"); self.delete_item_button = QPushButton("Xóa")
        list_mgmt_buttons_layout.addWidget(self.new_folder_button); list_mgmt_buttons_layout.addWidget(self.new_list_button); list_mgmt_buttons_layout.addWidget(self.delete_item_button)
        
        list_mgmt_label = QLabel("QUẢN LÝ DANH SÁCH"); list_mgmt_label.setObjectName("headerLabel"); list_mgmt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(list_mgmt_label); left_layout.addWidget(self.tree_view); left_layout.addLayout(list_mgmt_buttons_layout)
        
        right_panel = QWidget(); right_layout = QVBoxLayout(right_panel)
        control_frame = QFrame(); control_frame.setObjectName("controlFrame"); control_layout = QVBoxLayout(control_frame)
        top_control_layout = QHBoxLayout()
        
        self.toggle_button = QPushButton("Bắt đầu"); self.toggle_button.setObjectName("startButton"); self.toggle_button.setCheckable(True)
        self.reset_progress_button = QPushButton("Reset"); self.reset_progress_button.setObjectName("resetButton")
        
        top_control_layout.addWidget(self.toggle_button, 2); top_control_layout.addWidget(self.reset_progress_button, 1)
        status_layout = QHBoxLayout()
        self.current_selection_label = QLabel("List: (chưa chọn)")
        self.status_label = QLabel("Trạng thái: 0/0"); self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        status_layout.addWidget(self.current_selection_label); status_layout.addStretch(); status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar(); self.progress_bar.setTextVisible(False); self.progress_bar.setMaximumHeight(6)
        
        control_layout.addLayout(top_control_layout); control_layout.addLayout(status_layout); control_layout.addWidget(self.progress_bar)
        self.prompt_editor = PromptEditor()
        editor_buttons_layout = QHBoxLayout()
        self.save_prompts_button = QPushButton("Lưu thay đổi")
        self.current_line_label = QLabel("Dòng: 1"); self.current_line_label.setObjectName("smallLabel")
        
        editor_buttons_layout.addWidget(self.current_line_label); editor_buttons_layout.addStretch(); editor_buttons_layout.addWidget(self.save_prompts_button)
        footer_frame = QFrame(); footer_layout = QHBoxLayout(footer_frame); footer_layout.setContentsMargins(0,0,0,0)
        self.import_button = QPushButton("Import CSV"); self.export_button = QPushButton("Export CSV"); self.dashboard_button = QPushButton("Dashboard"); self.settings_button = QPushButton("Cài đặt")
        footer_layout.addWidget(self.import_button); footer_layout.addWidget(self.export_button); footer_layout.addStretch(); footer_layout.addWidget(self.dashboard_button); footer_layout.addWidget(self.settings_button)
        right_layout.addWidget(control_frame); right_layout.addWidget(self.prompt_editor, 1); right_layout.addLayout(editor_buttons_layout); right_layout.addWidget(footer_frame)
        splitter = QSplitter(Qt.Orientation.Horizontal); splitter.addWidget(left_panel); splitter.addWidget(right_panel); splitter.setSizes([320, 680]); main_layout.addWidget(splitter)
        for btn in self.findChildren(QPushButton): btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._set_button_icons()
        self.setStyleSheet("""
            QWidget {
                font-size: 14px;
            }
            #leftPanel {
                background-color: #f8f9fa;
                border-right: 1px solid #dee2e6;
            }
            #controlFrame, QFrame {
                border-radius: 5px;
            }
            #controlFrame {
                border: 1px solid #dee2e6;
                background-color: #ffffff;
                padding: 5px;
            }
            QLabel#headerLabel {
                font-weight: bold;
                color: #495057;
                padding: 5px;
                border-bottom: 1px solid #dee2e6;
                background-color: #f1f3f5;
            }
            
            QPushButton {
                padding: 6px 12px;
                border-radius: 5px;
                border: 1px solid #ced4da;
                background-color: #f8f9fa;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #adb5bd;
            }

            QPushButton#startButton {
                font-weight: bold;
                color: white;
                border: none;
                padding: 8px;
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(40, 167, 69, 255), stop:1 rgba(33, 136, 56, 255));
            }
            QPushButton#startButton:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(33, 136, 56, 255), stop:1 rgba(40, 167, 69, 255));
            }
            QPushButton#startButton:checked {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(220, 53, 69, 255), stop:1 rgba(200, 35, 51, 255));
            }
            QPushButton#startButton:checked:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(200, 35, 51, 255), stop:1 rgba(220, 53, 69, 255));
            }

            QPushButton#resetButton {
                font-weight: bold;
                color: #212529;
                border: none;
                padding: 8px;
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 193, 7, 255), stop:1 rgba(224, 168, 0, 255));
            }
            QPushButton#resetButton:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(224, 168, 0, 255), stop:1 rgba(255, 193, 7, 255));
            }
        """)

    def _set_button_icons(self):
        style = self.style()
        if not style: return
        self.new_folder_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)); self.new_list_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        self.delete_item_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)); self.settings_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.dashboard_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)); self.save_prompts_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.reset_progress_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload)); self.import_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowUp))
        self.export_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowDown))

    def connect_signals(self):
        self.new_folder_button.clicked.connect(self.handle_create_folder); self.new_list_button.clicked.connect(self.handle_create_list)
        self.delete_item_button.clicked.connect(self.handle_delete_item)
        self.save_prompts_button.clicked.connect(lambda: self.handle_save_prompts(silent=False))
        self.import_button.clicked.connect(self.handle_import); self.export_button.clicked.connect(self.handle_export)
        self.settings_button.clicked.connect(self.handle_settings); self.dashboard_button.clicked.connect(self.handle_dashboard)
        self.toggle_button.clicked.connect(self.handle_toggle_active); self.reset_progress_button.clicked.connect(self.core.reset_current_list_progress)
        
        selection_model = self.tree_view.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self.handle_tree_selection)
            
        self.prompt_editor.cursor_line_changed.connect(lambda line: self.current_line_label.setText(f"Dòng: {line + 1}"))
        self.prompt_editor.lineNumberArea.lineClicked.connect(self.handle_set_start_index_from_click)
        
        # Auto-save signals
        self.prompt_editor.textChanged.connect(self.auto_save_timer.start)
        self.auto_save_timer.timeout.connect(lambda: self.handle_save_prompts(silent=True))

        self.core.data_changed.connect(self.update_tree_view); self.core.stats_updated.connect(self.update_status_display)
        self.core.show_message.connect(self.show_message_box)
        self.core.show_mini_controller_signal.connect(self.show_mini_controller); self.core.hide_mini_controller_signal.connect(self.hide_mini_controller)
        self.core.update_mini_progress_signal.connect(self.update_mini_controller_progress); self.core.progress_reset.connect(self.on_progress_reset)
        self.core.pause_state_changed.connect(self.handle_pause_state_changed)

    def handle_create_folder(self):
        folder_name, ok = QInputDialog.getText(self, "Tạo Thư mục mới", "Nhập tên thư mục:")
        if ok and folder_name.strip(): self.core.create_new_folder(folder_name.strip())
    
    def handle_create_list(self):
        item_data = self._get_selected_item_data()
        if not item_data: return
        target_folder_path = item_data.get("path") if item_data.get("type") == "folder" else os.path.dirname(item_data.get("path", ""))
        if target_folder_path:
            list_name, ok = QInputDialog.getText(self, "Tạo Danh sách mới", f"Nhập tên danh sách trong '{os.path.basename(target_folder_path)}':")
            if ok and list_name.strip(): self.core.create_new_list(target_folder_path, list_name.strip())

    def handle_delete_item(self):
        item_data = self._get_selected_item_data()
        if not item_data or not item_data.get("path"): return
        item_type = "thư mục" if item_data.get("type") == "folder" else "danh sách"
        item_name = os.path.basename(item_data.get("path", "item"))
        reply = QMessageBox.question(self, "Xác nhận xóa", f"Bạn có chắc muốn xóa {item_type} '{item_name}' không?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes: self.core.delete_item(item_data.get("path"))

    def handle_save_prompts(self, silent=False):
        if not self.core.current_list_name or not self.core.current_folder: return
        prompts = [line.strip() for line in self.prompt_editor.toPlainText().splitlines() if line.strip()]
        key = f"{os.path.basename(self.core.current_folder)}/{self.core.current_list_name}"
        if self.core.save_list_to_file(key, prompts):
            if not silent:
                self.show_message_box("Thành công", f"Đã lưu {len(prompts)} prompt.")
            self.core.update_stats(); self.core.load_all_lists()
        else: 
            if not silent:
                self.show_message_box("Lỗi", "Không thể lưu danh sách.")

    def handle_set_start_index_from_click(self, line_number):
        if not self.core.current_list_name: return
        self.core.set_start_index(line_number); self.core.load_all_lists()

    def handle_import(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file CSV", "", "CSV Files (*.csv)")
        if file_path: self.core.import_from_csv(file_path)

    def handle_export(self):
        if not self.core.current_list_name: return
        file_path, _ = QFileDialog.getSaveFileName(self, "Lưu file CSV", f"{self.core.current_list_name}.csv", "CSV Files (*.csv)")
        if file_path: self.core.export_to_csv(file_path)

    def handle_settings(self):
        current_settings = {
            "hotkey": self.core.hotkey, "storage_path": self.core.storage_path
        }
        dialog = SettingsDialog(current_settings, self)
        if dialog.exec():
            if self.core.update_settings(dialog.get_values()):
                self.show_message_box("Khởi động lại", "Cài đặt đã được lưu. Vui lòng khởi động lại ứng dụng.")
                self.close()

    def handle_dashboard(self): 
        dashboard = DashboardDialog(self.core.log_file, self)
        dashboard.exec()

    def handle_toggle_active(self, checked):
        if checked and (not self.core.current_list_name or not self.core.current_folder):
            self.show_message_box("Chưa chọn danh sách", "Vui lòng chọn danh sách trước khi bắt đầu.")
            self.toggle_button.setChecked(False); return
        self.toggle_button.setText("Dừng" if checked else "Bắt đầu")
        if not self.core.toggle_active_state(checked):
            self.toggle_button.setChecked(False); self.toggle_button.setText("Bắt đầu")

    def handle_tree_selection(self):
        self._update_ui_state()
        item_data = self._get_selected_item_data()
        if not item_data: self._clear_editor(); return
        if item_data.get("type") == "folder": self._handle_folder_selection(item_data)
        elif item_data.get("type") == "list": self._handle_list_selection(item_data)

    def _get_selected_item_data(self):
        indexes = self.tree_view.selectedIndexes()
        if not indexes: return None
        item = self.tree_model.itemFromIndex(indexes[0])
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _clear_editor(self):
        self.prompt_editor.setPlainText("Tạo hoặc chọn một danh sách để xem nội dung."); self.prompt_editor.setReadOnly(True)
        self.core.set_current_list(None, None)
        self.current_selection_label.setText("List: (chưa chọn)")
        self.update_status_display({"total": 0, "pasted": 0, "session_pasted": 0})

    def _handle_folder_selection(self, item_data):
        self.prompt_editor.setPlainText("Chọn một danh sách để xem nội dung."); self.prompt_editor.setReadOnly(True)
        folder_path = item_data.get("path")
        self.core.set_current_list(folder_path, None)
        self.current_selection_label.setText(f"Thư mục: <b>{os.path.basename(folder_path or '')}</b>")
        self.update_status_display({"total": 0, "pasted": 0, "session_pasted": 0})

    def _handle_list_selection(self, item_data):
        self.prompt_editor.setReadOnly(False)
        item_path = item_data.get("path", "")
        folder_path = os.path.dirname(item_path)
        list_name = os.path.splitext(os.path.basename(item_path))[0]
        self.core.set_current_list(folder_path, list_name)
        key = f"{os.path.basename(folder_path)}/{list_name}"
        self.prompt_editor.setPlainText("\n".join(self.core.get_list_content(key)))
        self.current_selection_label.setText(f"Danh sách: <b>{list_name}</b>")
        cursor = self.prompt_editor.textCursor(); cursor.movePosition(QTextCursor.MoveOperation.Start)
        for _ in range(self.core.current_prompt_index):
            if not cursor.movePosition(QTextCursor.MoveOperation.Down): break
        self.prompt_editor.setTextCursor(cursor)
        self.core.update_stats()
        self.prompt_editor.set_start_line_indicator(self.core.current_prompt_index)

    def _update_ui_state(self):
        item_data = self._get_selected_item_data()
        is_folder = bool(item_data and item_data.get("type") == "folder")
        is_list = bool(item_data and item_data.get("type") == "list")
        self.new_list_button.setEnabled(is_folder or is_list)
        self.delete_item_button.setEnabled(is_folder or is_list)
        self.toggle_button.setEnabled(is_list); self.reset_progress_button.setEnabled(is_list)
        self.save_prompts_button.setEnabled(is_list); self.import_button.setEnabled(is_list)
        self.export_button.setEnabled(is_list)

    @pyqtSlot(dict)
    def update_status_display(self, stats):
        total, pasted, session = stats.get('total', 0), stats.get('pasted', 0), stats.get('session_pasted', 0)
        self.status_label.setText(f"Trạng thái: <b>{pasted}/{total}</b> (Phiên: <b>{session}</b>)")
        self.progress_bar.setMaximum(total if total > 0 else 1); self.progress_bar.setValue(pasted)
        self.prompt_editor.set_start_line_indicator(pasted)

    @pyqtSlot()
    def update_tree_view(self):
        root = self.tree_model.invisibleRootItem()
        if not root: return
        
        expanded = set()
        for i in range(root.rowCount()):
            index = self.tree_model.index(i, 0)
            if self.tree_view.isExpanded(index):
                item = self.tree_model.itemFromIndex(index)
                if item:
                    item_data = item.data(Qt.ItemDataRole.UserRole)
                    if isinstance(item_data, dict):
                        path = item_data.get("path")
                        if path:
                            expanded.add(path)

        selected_item_data = self._get_selected_item_data()
        current_path = selected_item_data.get("path") if selected_item_data else None

        self.tree_model.clear()
        
        if not os.path.exists(self.core.storage_path): return
        style = self.style()
        try: folder_names = sorted([n for n in os.listdir(self.core.storage_path) if os.path.isdir(os.path.join(self.core.storage_path, n))])
        except OSError: return
        
        root_item = self.tree_model.invisibleRootItem()
        if not root_item: return

        for folder_name in folder_names:
            folder_path = os.path.join(self.core.storage_path, folder_name)
            folder_item = QStandardItem(folder_name); folder_item.setData({"type": "folder", "path": folder_path}, Qt.ItemDataRole.UserRole)
            if style: folder_item.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
            root_item.appendRow(folder_item)
            try: list_files = sorted([f for f in os.listdir(folder_path) if f.endswith(".json")])
            except OSError: continue
            for list_filename in list_files:
                list_name = os.path.splitext(list_filename)[0]
                key = f"{folder_name}/{list_name}"; state = self.core.get_list_state(key)
                list_item = QStandardItem(f"{list_name} [{state['index']}/{state['total']}]")
                list_item.setData({"type": "list", "path": os.path.join(folder_path, list_filename)}, Qt.ItemDataRole.UserRole)
                if style: list_item.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileIcon))
                folder_item.appendRow(list_item)
        
        for i in range(root_item.rowCount()):
            item = root_item.child(i)
            if item:
                item_data = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(item_data, dict) and item_data.get("path") in expanded: 
                    self.tree_view.expand(self.tree_model.indexFromItem(item))
        
        if current_path: self.select_item_by_path(current_path)

    @pyqtSlot(str, str)
    def show_message_box(self, title, text): QMessageBox.information(self, title, text)
    @pyqtSlot(bool)
    def handle_pause_state_changed(self, is_paused):
        if self.mini_controller: self.mini_controller.set_paused_state(is_paused)
    @pyqtSlot(str)
    def show_mini_controller(self, list_name):
        self.hide(); self.mini_controller = MiniController(list_name)
        self.mini_controller.stop_signal.connect(lambda: self.core.toggle_active_state(False))
        self.mini_controller.pause_resume_signal.connect(self.core.toggle_pause_resume)
        self.mini_controller.set_paused_state(self.core.is_paused)
        screen = QApplication.primaryScreen()
        if screen: self.mini_controller.move(screen.geometry().width() - self.mini_controller.sizeHint().width() - 30, screen.geometry().height() - self.mini_controller.sizeHint().height() - 80)
        self.mini_controller.show()
    @pyqtSlot()
    def hide_mini_controller(self):
        if self.mini_controller: self.mini_controller.close(); self.mini_controller = None
        self.show()
        if self.toggle_button.isChecked(): self.toggle_button.setChecked(False); self.toggle_button.setText("Bắt đầu")
    @pyqtSlot(int, int)
    def update_mini_controller_progress(self, current, total):
        if self.mini_controller: self.mini_controller.update_progress(current, total)
    @pyqtSlot()
    def on_progress_reset(self):
        self.handle_toggle_active(False)
        self.handle_tree_selection()
    def select_item_by_path(self, path_to_select):
        if not path_to_select: return
        root = self.tree_model.invisibleRootItem()
        if not root: return
        for row in range(root.rowCount()):
            folder_item = root.child(row)
            if folder_item:
                folder_data = folder_item.data(Qt.ItemDataRole.UserRole)
                if isinstance(folder_data, dict) and folder_data.get("path") == path_to_select:
                    idx = self.tree_model.indexFromItem(folder_item); self.tree_view.setCurrentIndex(idx); self.tree_view.scrollTo(idx); return
                for sub_row in range(folder_item.rowCount()):
                    list_item = folder_item.child(sub_row)
                    if list_item:
                        list_data = list_item.data(Qt.ItemDataRole.UserRole)
                        if isinstance(list_data, dict) and list_data.get("path") == path_to_select:
                            self.tree_view.expand(self.tree_model.indexFromItem(folder_item))
                            idx = self.tree_model.indexFromItem(list_item); self.tree_view.setCurrentIndex(idx); self.tree_view.scrollTo(idx); return
    def closeEvent(self, a0: QCloseEvent | None):
        try:
            if self.core.is_active: self.core.toggle_active_state(False)
            self.core.save_state(); self.core.stop_hotkey_listener(); self.core._stop_key_listener()
            if self.mini_controller: self.mini_controller.close()
        except Exception as e: print(f"Lỗi khi đóng ứng dụng: {e}")
        finally:
            if a0: a0.accept()
