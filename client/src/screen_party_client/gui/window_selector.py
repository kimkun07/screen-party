"""Window selection dialog for share mode"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from ..utils.window_manager import WindowInfo, WindowManager


class WindowSelectorDialog(QDialog):
    """Window selection dialog"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.window_manager: Optional[WindowManager] = None
        self.windows: list[WindowInfo] = []
        self.selected_handle: Optional[int] = None

        # Try to create window manager (will fail on non-Windows)
        try:
            self.window_manager = WindowManager()
        except (NotImplementedError, ImportError) as e:
            # Show error and close dialog
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(
                self,
                "Platform Not Supported",
                f"Share mode is only supported on Windows.\n\nError: {str(e)}",
            )
            self.selected_handle = None
            return

        self.init_ui()
        self.refresh_window_list()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Select Window to Share")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout()

        # Title
        title = QLabel("Select Window to Share")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search windows...")
        self.search_input.textChanged.connect(self.filter_windows)
        layout.addWidget(self.search_input)

        # Window list
        self.window_list = QListWidget()
        self.window_list.itemDoubleClicked.connect(self.on_window_double_clicked)
        self.window_list.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.window_list)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_window_list)
        button_layout.addWidget(self.refresh_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.select_button = QPushButton("Select")
        self.select_button.setEnabled(False)
        self.select_button.clicked.connect(self.on_select_clicked)
        button_layout.addWidget(self.select_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def refresh_window_list(self):
        """Refresh window list"""
        if not self.window_manager:
            return

        self.window_list.clear()
        self.windows = self.window_manager.get_window_list()

        if not self.windows:
            # Show message if no windows found
            item = QListWidgetItem()
            item.setText("No windows found. Please open an application first.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make it non-selectable
            self.window_list.addItem(item)
            return

        for window in self.windows:
            item = QListWidgetItem()
            # Format: "Title\n(process.exe)"
            item.setText(f"{window.title}\n({window.process_name})")
            item.setData(Qt.ItemDataRole.UserRole, window.handle)
            self.window_list.addItem(item)

    def filter_windows(self, text: str):
        """Filter windows based on search text"""
        text = text.lower()
        for i in range(self.window_list.count()):
            item = self.window_list.item(i)
            if item:
                visible = text in item.text().lower()
                item.setHidden(not visible)

    def on_selection_changed(self):
        """Handle selection change"""
        selected_items = self.window_list.selectedItems()
        self.select_button.setEnabled(len(selected_items) > 0)

    def on_window_double_clicked(self, item: QListWidgetItem):
        """Handle double click (select immediately)"""
        handle = item.data(Qt.ItemDataRole.UserRole)
        if handle is not None:
            self.selected_handle = handle
            self.accept()

    def on_select_clicked(self):
        """Handle select button click"""
        selected_items = self.window_list.selectedItems()
        if selected_items:
            handle = selected_items[0].data(Qt.ItemDataRole.UserRole)
            if handle is not None:
                self.selected_handle = handle
                self.accept()

    def get_selected_handle(self) -> Optional[int]:
        """Get selected window handle"""
        return self.selected_handle
