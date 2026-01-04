"""Floating Action Button (FAB) menu for overlay controls"""

from typing import Optional

from PyQt6.QtWidgets import QWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QMouseEvent


class FloatingActionMenu(QWidget):
    """Floating action button menu (draggable)"""

    # Signals
    exit_clicked = pyqtSignal()  # Share mode exit requested
    clear_clicked = pyqtSignal()  # Clear drawings requested

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.is_expanded = False
        self.drag_position: Optional[QPoint] = None

        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        # Independent window (NOT child of overlay)
        # This allows it to receive mouse input while overlay is click-through
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        # Semi-transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(
            """
            QWidget {
                background-color: rgba(50, 50, 50, 200);
                border-radius: 25px;
            }
            QPushButton {
                background-color: rgba(100, 100, 100, 200);
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(150, 150, 150, 200);
            }
            QPushButton:pressed {
                background-color: rgba(80, 80, 80, 200);
            }
        """
        )

        # Layout
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)

        # Exit button (hidden initially)
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.exit_clicked.emit)
        self.exit_button.hide()
        self.layout.addWidget(self.exit_button)

        # Clear button (hidden initially)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_clicked.emit)
        self.clear_button.hide()
        self.layout.addWidget(self.clear_button)

        # Toggle button (always visible)
        self.toggle_button = QPushButton("●")
        self.toggle_button.setFixedSize(40, 40)
        self.toggle_button.clicked.connect(self.toggle_menu)
        self.layout.addWidget(self.toggle_button)

        self.setLayout(self.layout)

        # Set initial size
        self.adjustSize()

    def toggle_menu(self):
        """Toggle between collapsed and expanded state"""
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            self.exit_button.show()
            self.clear_button.show()
        else:
            self.exit_button.hide()
            self.clear_button.hide()

        self.adjustSize()

    def mousePressEvent(self, event: QMouseEvent):
        """Start dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Only start drag if not clicking on a button
            widget = self.childAt(event.pos())
            if widget is None or widget == self:
                self.drag_position = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )
                event.accept()
            else:
                super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle dragging"""
        if (
            event.buttons() == Qt.MouseButton.LeftButton
            and self.drag_position is not None
        ):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """End dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
