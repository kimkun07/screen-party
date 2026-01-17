"""Transparent overlay window for drawing"""

from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QIcon

from ..drawing.canvas import DrawingCanvas


class OverlayWindow(QWidget):
    """Transparent overlay window for drawing"""

    # Signals
    drawing_mode_changed = pyqtSignal(bool)

    def __init__(
        self,
        user_id: str,
        pen_color: Optional[QColor] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        self.user_id = user_id
        # Start with drawing disabled (click passthrough)
        self._drawing_enabled = False

        # Resize mode state
        self._resize_mode = False

        if pen_color is None:
            pen_color = QColor(255, 182, 193)  # Default: 파스텔 핑크 (첫 번째 프리셋)

        # QApplication의 아이콘 가져오기 (설정되어 있으면)
        app_icon = QApplication.instance().windowIcon()
        if app_icon and not app_icon.isNull():
            self.setWindowIcon(app_icon)

        self.init_ui(pen_color)

        # Set default geometry (center of screen, 800x600)
        self.setGeometry(100, 100, 800, 600)

    def init_ui(self, pen_color: QColor):
        """Initialize UI"""
        # Window flags for transparent, click-through overlay
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput  # Click passthrough - KEY FEATURE!
        )

        # Transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

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

    def paintEvent(self, event):
        """Paint almost invisible background to receive click events

        CRITICAL: Qt requires non-transparent pixels to receive mouse events.
        Even with WindowTransparentForInput disabled, a completely transparent
        background will not receive clicks. We need alpha > 0 to receive events.

        Using QColor(0, 0, 0, 1) - almost invisible but clickable.
        """
        painter = QPainter(self)

        # CRITICAL: This almost-invisible background enables click events
        # Without this, clicks will pass through even when WindowTransparentForInput is disabled
        # alpha=1: barely visible but clickable
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

        # No need to draw border/handles - Windows will handle it in resize mode

        # Call parent's paintEvent to render DrawingCanvas
        super().paintEvent(event)

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

        # Update window flags (Method 3: Combined Flags)
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

        self.show()
        self.update()

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
                print("[OverlayWindow] ESC pressed - disabling drawing mode")
                self.set_drawing_enabled(False)
            event.accept()
        elif event.key() == QtKey.Key.Key_Return or event.key() == QtKey.Key.Key_Enter:
            # Enter key: Disable resize mode
            if self._resize_mode:
                print("[OverlayWindow] Enter pressed - disabling resize mode")
                self.set_resize_mode(False)
            event.accept()
        else:
            super().keyPressEvent(event)

    # ========== Resize Mode Methods ==========

    def is_resize_mode(self) -> bool:
        """Check if resize mode is enabled"""
        return self._resize_mode

    def set_resize_mode(self, enabled: bool):
        """Enable or disable resize mode

        Args:
            enabled: True to enable resize mode, False to disable
        """
        if self._resize_mode == enabled:
            return

        self._resize_mode = enabled

        # Log current geometry when entering resize mode
        import logging
        logger = logging.getLogger(__name__)
        g = self.geometry()
        if enabled:
            logger.info(f"[OverlayWindow] Resize mode ENABLED. Current geometry: pos=({g.x()}, {g.y()}), size={g.width()}x{g.height()}")
        else:
            logger.info(f"[OverlayWindow] Resize mode DISABLED. Final geometry: pos=({g.x()}, {g.y()}), size={g.width()}x{g.height()}")

        # Disable drawing mode when entering resize mode
        if enabled and self._drawing_enabled:
            self.set_drawing_enabled(False)

        # Update window flags and size constraints
        if enabled:
            # Resize mode: Use Windows default window with title bar and resize handles
            # Remove FramelessWindowHint to enable Windows native resize functionality
            self.setWindowFlags(
                Qt.WindowType.Window  # Regular window with title bar and borders
                | Qt.WindowType.WindowStaysOnTopHint
            )
            # Set window title for resize mode
            self.setWindowTitle("그림 영역 크기 조정 (드래그하여 조정)")
            # Set minimum size constraint
            self.setMinimumSize(200, 150)
            # Set window opacity to 30% (transparent enough to see through)
            self.setWindowOpacity(0.3)
        else:
            # Normal mode: Frameless overlay (drawing controlled by user)
            # Remove minimum size constraint
            self.setMinimumSize(0, 0)
            # Restore full opacity
            self.setWindowOpacity(1.0)
            # Set window flags based on drawing state
            if not self._drawing_enabled:
                self.setWindowFlags(
                    Qt.WindowType.FramelessWindowHint
                    | Qt.WindowType.WindowStaysOnTopHint
                    | Qt.WindowType.Tool
                    | Qt.WindowType.WindowTransparentForInput
                )
            else:
                self.setWindowFlags(
                    Qt.WindowType.FramelessWindowHint
                    | Qt.WindowType.WindowStaysOnTopHint
                    | Qt.WindowType.Tool
                )

        self.show()
        self.update()

        # Set focus when enabled
        if enabled:
            self.setFocus()

    # Mouse events are now handled by Windows native resize functionality
    # No need for custom resize logic

    # ========== End Resize Mode Methods ==========

    def closeEvent(self, event):
        """Handle close event"""
        super().closeEvent(event)
