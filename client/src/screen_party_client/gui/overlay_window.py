"""Transparent overlay window that follows a target window"""

from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QRect, pyqtSignal
from PyQt6.QtGui import QColor

from ..drawing.canvas import DrawingCanvas
from ..utils.window_manager import WindowManager, WindowInfo


class OverlayWindow(QWidget):
    """Transparent overlay window that follows a target window"""

    # Signals
    target_window_closed = pyqtSignal()  # Emitted when target window is closed
    target_window_minimized = pyqtSignal()  # Emitted when target window is minimized
    target_window_restored = pyqtSignal()  # Emitted when target window is restored
    geometry_changed = pyqtSignal(QRect)  # Emitted when overlay geometry changes
    drawing_mode_changed = pyqtSignal(bool)  # Emitted when drawing mode changes (True=enabled, False=disabled)

    def __init__(
        self,
        target_handle: int,
        user_id: str,
        pen_color: Optional[QColor] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        self.target_handle = target_handle
        self.user_id = user_id
        self.window_manager = WindowManager()
        self.is_tracking = True
        self._was_minimized = False
        self._drawing_enabled = False  # Start with drawing disabled (click passthrough)

        if pen_color is None:
            pen_color = QColor(255, 0, 0)  # Default: red

        self.init_ui(pen_color)
        self.setup_sync_timer()

        # Initial sync
        self.sync_with_target()

    def init_ui(self, pen_color: QColor):
        """Initialize UI"""
        # Window flags for transparent, click-through overlay
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint  # No borders
            | Qt.WindowType.WindowStaysOnTopHint  # Always on top
            | Qt.WindowType.Tool  # Don't show in taskbar
            | Qt.WindowType.WindowTransparentForInput  # Click passthrough - KEY FEATURE!
        )

        # Transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        # Enable focus to receive keyboard events (ESC key)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Drawing canvas (reuse existing implementation)
        self.drawing_canvas = DrawingCanvas(
            parent=self,
            user_id=self.user_id,
            pen_color=pen_color,
            pen_width=3,
        )
        layout.addWidget(self.drawing_canvas)

        self.setLayout(layout)

    def setup_sync_timer(self):
        """Setup timer for syncing with target window"""
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self.sync_with_target)
        self.sync_timer.start(100)  # 100ms interval (10 FPS)

    def sync_with_target(self):
        """Sync overlay position/size with target window"""
        if not self.is_tracking:
            return

        # Check if window still exists
        if not self.window_manager.window_exists(self.target_handle):
            self.target_window_closed.emit()
            self.close()
            return

        # Check if minimized
        is_minimized = self.window_manager.is_window_minimized(self.target_handle)

        if is_minimized:
            if self.isVisible():
                self.hide()
                self._was_minimized = True
                self.target_window_minimized.emit()
            return
        else:
            if self._was_minimized and not self.isVisible():
                self.show()
                self._was_minimized = False
                self.target_window_restored.emit()

        # Get current window info
        window_info = self.window_manager.get_window_info(self.target_handle)
        if not window_info:
            return

        # Update geometry if changed
        new_rect = QRect(
            window_info.x, window_info.y, window_info.width, window_info.height
        )
        if self.geometry() != new_rect:
            self.setGeometry(new_rect)
            self.geometry_changed.emit(new_rect)

    def stop_tracking(self):
        """Stop tracking target window"""
        self.is_tracking = False
        self.sync_timer.stop()

    def resume_tracking(self):
        """Resume tracking target window"""
        self.is_tracking = True
        self.sync_timer.start(100)

    def get_canvas(self) -> DrawingCanvas:
        """Get the drawing canvas"""
        return self.drawing_canvas

    def is_drawing_enabled(self) -> bool:
        """Check if drawing mode is enabled"""
        return self._drawing_enabled

    def set_drawing_enabled(self, enabled: bool):
        """Enable or disable drawing mode

        Args:
            enabled: True to enable drawing (disable click passthrough),
                    False to disable drawing (enable click passthrough)
        """
        if self._drawing_enabled == enabled:
            return

        self._drawing_enabled = enabled

        # Store current geometry
        current_geometry = self.geometry()

        # Update window flags
        if enabled:
            # Drawing enabled: Remove WindowTransparentForInput (allow mouse input)
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
                # No WindowTransparentForInput - mouse input allowed!
            )
        else:
            # Drawing disabled: Add WindowTransparentForInput (click passthrough)
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
                | Qt.WindowType.WindowTransparentForInput  # Click passthrough
            )

        # CRITICAL: Must hide and show to apply flag changes
        self.setGeometry(current_geometry)  # Restore geometry
        self.show()

        # Set focus when drawing is enabled (to receive keyboard events)
        if enabled:
            self.setFocus()

        # Emit signal
        self.drawing_mode_changed.emit(enabled)

    def keyPressEvent(self, event):
        """Handle key press events"""
        from PyQt6.QtCore import Qt as QtKey

        if event.key() == QtKey.Key.Key_Escape:
            # ESC key: Disable drawing mode
            if self._drawing_enabled:
                self.set_drawing_enabled(False)
            event.accept()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """Handle close event"""
        self.stop_tracking()
        super().closeEvent(event)
