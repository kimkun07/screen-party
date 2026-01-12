"""Transparent overlay window that follows a target window"""

from enum import Enum
from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen

from ..drawing.canvas import DrawingCanvas
from ..utils.window_manager import WindowManager


class ResizeDirection(Enum):
    """Resize direction for overlay window"""
    NONE = 0
    TOP_LEFT = 1
    TOP = 2
    TOP_RIGHT = 3
    RIGHT = 4
    BOTTOM_RIGHT = 5
    BOTTOM = 6
    BOTTOM_LEFT = 7
    LEFT = 8
    MOVE = 9  # Title bar drag (move entire window)


# Resize handle constants
HANDLE_SIZE = 10  # Handle area size (pixels)
HANDLE_COLOR = QColor(0, 120, 215)  # Handle color (blue)
BORDER_COLOR = QColor(0, 120, 215)  # Border color
BORDER_WIDTH = 2  # Border width
MIN_WIDTH = 200  # Minimum window width
MIN_HEIGHT = 150  # Minimum window height


class OverlayWindow(QWidget):
    """Transparent overlay window that follows a target window"""

    # Signals
    target_window_closed = pyqtSignal()
    target_window_minimized = pyqtSignal()
    target_window_restored = pyqtSignal()
    drawing_mode_changed = pyqtSignal(bool)

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
        # Start with drawing disabled (click passthrough)
        self._drawing_enabled = False

        # Resize mode state
        self._resize_mode = False
        self._resize_direction = ResizeDirection.NONE
        self._resize_start_pos = None
        self._resize_start_geometry = None

        if pen_color is None:
            pen_color = QColor(255, 182, 193)  # Default: 파스텔 핑크 (첫 번째 프리셋)

        self.init_ui(pen_color)
        self.setup_sync_timer()

        # Set initial position/size from target window
        self.set_initial_geometry()
        # Start tracking for minimize/close events
        self.sync_with_target()

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

        In resize mode, also draw border and handles.
        """
        painter = QPainter(self)

        # CRITICAL: This almost-invisible background enables click events
        # Without this, clicks will pass through even when WindowTransparentForInput is disabled
        # alpha=1: barely visible but clickable
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

        # Draw border and handles in resize mode
        if self._resize_mode:
            # Draw border
            pen = QPen(BORDER_COLOR, BORDER_WIDTH)
            painter.setPen(pen)
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

            # Draw handles (8 directions)
            painter.setBrush(HANDLE_COLOR)
            painter.setPen(Qt.PenStyle.NoPen)

            w, h = self.width(), self.height()

            # Corner handles
            # Top-left
            painter.drawRect(0, 0, HANDLE_SIZE, HANDLE_SIZE)
            # Top-right
            painter.drawRect(w - HANDLE_SIZE, 0, HANDLE_SIZE, HANDLE_SIZE)
            # Bottom-left
            painter.drawRect(0, h - HANDLE_SIZE, HANDLE_SIZE, HANDLE_SIZE)
            # Bottom-right
            painter.drawRect(w - HANDLE_SIZE, h - HANDLE_SIZE, HANDLE_SIZE, HANDLE_SIZE)

            # Edge handles (centered)
            # Top
            painter.drawRect((w - HANDLE_SIZE) // 2, 0, HANDLE_SIZE, HANDLE_SIZE)
            # Bottom
            painter.drawRect((w - HANDLE_SIZE) // 2, h - HANDLE_SIZE, HANDLE_SIZE, HANDLE_SIZE)
            # Left
            painter.drawRect(0, (h - HANDLE_SIZE) // 2, HANDLE_SIZE, HANDLE_SIZE)
            # Right
            painter.drawRect(w - HANDLE_SIZE, (h - HANDLE_SIZE) // 2, HANDLE_SIZE, HANDLE_SIZE)

        # Call parent's paintEvent to render DrawingCanvas
        super().paintEvent(event)

    def setup_sync_timer(self):
        """Setup timer for syncing with target window"""
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self.sync_with_target)
        self.sync_timer.start(100)  # 100ms interval (10 FPS)

    def set_initial_geometry(self):
        """Set initial position/size from target window"""
        import logging
        logger = logging.getLogger(__name__)

        window_info = self.window_manager.get_window_info(self.target_handle)
        if not window_info:
            logger.error(f"[OverlayWindow] Failed to get window info for handle {self.target_handle}")
            return

        # Set geometry to match target window
        initial_rect = QRect(
            window_info.x, window_info.y, window_info.width, window_info.height
        )
        self.setGeometry(initial_rect)

        logger.info(f"[OverlayWindow] Initial geometry set:")
        logger.info(f"  Position: ({window_info.x}, {window_info.y})")
        logger.info(f"  Size: {window_info.width}x{window_info.height}")
        logger.info(f"  Target handle: {self.target_handle}")

    def sync_with_target(self):
        """Check target window status (minimized/closed only, no position/size sync)"""
        if not self.is_tracking:
            return

        # Check if window still exists
        if not self.window_manager.window_exists(self.target_handle):
            self.target_window_closed.emit()
            self.close()
            return

        # Check if minimized
        is_minimized = self.window_manager.is_window_minimized(
            self.target_handle)

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

        # Update window flags to allow mouse input in resize mode
        if enabled:
            # Resize mode: Remove WindowTransparentForInput (allow mouse input)
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
            )
        else:
            # Normal mode: Add WindowTransparentForInput (click passthrough)
            # unless drawing mode is enabled
            if not self._drawing_enabled:
                self.setWindowFlags(
                    Qt.WindowType.FramelessWindowHint
                    | Qt.WindowType.WindowStaysOnTopHint
                    | Qt.WindowType.Tool
                    | Qt.WindowType.WindowTransparentForInput
                )

        self.show()
        self.update()

        # Set focus to receive mouse events
        if enabled:
            self.setFocus()

    def get_resize_direction(self, pos: QPoint) -> ResizeDirection:
        """Get resize direction from mouse position

        Args:
            pos: Mouse position

        Returns:
            ResizeDirection enum value
        """
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()

        # Define handle regions
        in_left = x < HANDLE_SIZE
        in_right = x > w - HANDLE_SIZE
        in_top = y < HANDLE_SIZE
        in_bottom = y > h - HANDLE_SIZE
        in_title = y < 30 and not (in_left or in_right)  # Title bar area (30px)

        # Check corners first (priority)
        if in_top and in_left:
            return ResizeDirection.TOP_LEFT
        if in_top and in_right:
            return ResizeDirection.TOP_RIGHT
        if in_bottom and in_left:
            return ResizeDirection.BOTTOM_LEFT
        if in_bottom and in_right:
            return ResizeDirection.BOTTOM_RIGHT

        # Check edges
        if in_top:
            return ResizeDirection.TOP
        if in_bottom:
            return ResizeDirection.BOTTOM
        if in_left:
            return ResizeDirection.LEFT
        if in_right:
            return ResizeDirection.RIGHT

        # Title bar (move entire window)
        if in_title:
            return ResizeDirection.MOVE

        return ResizeDirection.NONE

    def get_cursor_for_direction(self, direction: ResizeDirection) -> Qt.CursorShape:
        """Get cursor shape for resize direction

        Args:
            direction: Resize direction

        Returns:
            Qt.CursorShape enum value
        """
        cursor_map = {
            ResizeDirection.TOP_LEFT: Qt.CursorShape.SizeFDiagCursor,
            ResizeDirection.TOP_RIGHT: Qt.CursorShape.SizeBDiagCursor,
            ResizeDirection.BOTTOM_LEFT: Qt.CursorShape.SizeBDiagCursor,
            ResizeDirection.BOTTOM_RIGHT: Qt.CursorShape.SizeFDiagCursor,
            ResizeDirection.TOP: Qt.CursorShape.SizeVerCursor,
            ResizeDirection.BOTTOM: Qt.CursorShape.SizeVerCursor,
            ResizeDirection.LEFT: Qt.CursorShape.SizeHorCursor,
            ResizeDirection.RIGHT: Qt.CursorShape.SizeHorCursor,
            ResizeDirection.MOVE: Qt.CursorShape.SizeAllCursor,
        }
        return cursor_map.get(direction, Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        """Handle mouse press events for resize"""
        if not self._resize_mode:
            super().mousePressEvent(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self._resize_direction = self.get_resize_direction(event.pos())
            if self._resize_direction != ResizeDirection.NONE:
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_geometry = self.geometry()
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events for resize"""
        if not self._resize_mode:
            super().mouseMoveEvent(event)
            return

        # Update cursor based on position
        if self._resize_direction == ResizeDirection.NONE:
            direction = self.get_resize_direction(event.pos())
            self.setCursor(self.get_cursor_for_direction(direction))
            super().mouseMoveEvent(event)
            return

        # Perform resize
        if self._resize_start_pos is None or self._resize_start_geometry is None:
            super().mouseMoveEvent(event)
            return

        delta = event.globalPosition().toPoint() - self._resize_start_pos
        dx, dy = delta.x(), delta.y()

        # Calculate new geometry
        x = self._resize_start_geometry.x()
        y = self._resize_start_geometry.y()
        w = self._resize_start_geometry.width()
        h = self._resize_start_geometry.height()

        direction = self._resize_direction

        if direction == ResizeDirection.TOP_LEFT:
            x += dx
            y += dy
            w -= dx
            h -= dy
        elif direction == ResizeDirection.TOP:
            y += dy
            h -= dy
        elif direction == ResizeDirection.TOP_RIGHT:
            y += dy
            w += dx
            h -= dy
        elif direction == ResizeDirection.RIGHT:
            w += dx
        elif direction == ResizeDirection.BOTTOM_RIGHT:
            w += dx
            h += dy
        elif direction == ResizeDirection.BOTTOM:
            h += dy
        elif direction == ResizeDirection.BOTTOM_LEFT:
            x += dx
            w -= dx
            h += dy
        elif direction == ResizeDirection.LEFT:
            x += dx
            w -= dx
        elif direction == ResizeDirection.MOVE:
            x += dx
            y += dy

        # Apply minimum size constraints
        if w < MIN_WIDTH:
            if direction in [ResizeDirection.LEFT, ResizeDirection.TOP_LEFT, ResizeDirection.BOTTOM_LEFT]:
                x = self._resize_start_geometry.x() + self._resize_start_geometry.width() - MIN_WIDTH
            w = MIN_WIDTH

        if h < MIN_HEIGHT:
            if direction in [ResizeDirection.TOP, ResizeDirection.TOP_LEFT, ResizeDirection.TOP_RIGHT]:
                y = self._resize_start_geometry.y() + self._resize_start_geometry.height() - MIN_HEIGHT
            h = MIN_HEIGHT

        # Update geometry
        self.setGeometry(x, y, w, h)

        # Log geometry change (only on significant changes to reduce spam)
        import logging
        logger = logging.getLogger(__name__)
        if abs(dx) > 5 or abs(dy) > 5:  # Only log if moved/resized more than 5px
            logger.debug(f"[OverlayWindow] Resized: pos=({x}, {y}), size={w}x{h}")

        event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release events for resize"""
        if not self._resize_mode:
            super().mouseReleaseEvent(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            # Log final geometry
            if self._resize_direction != ResizeDirection.NONE:
                import logging
                logger = logging.getLogger(__name__)
                g = self.geometry()
                logger.info(f"[OverlayWindow] Resize completed: pos=({g.x()}, {g.y()}), size={g.width()}x{g.height()}")

            self._resize_direction = ResizeDirection.NONE
            self._resize_start_pos = None
            self._resize_start_geometry = None
            # Update cursor
            direction = self.get_resize_direction(event.pos())
            self.setCursor(self.get_cursor_for_direction(direction))
            event.accept()
            return

        super().mouseReleaseEvent(event)

    # ========== End Resize Mode Methods ==========

    def closeEvent(self, event):
        """Handle close event"""
        self.stop_tracking()
        super().closeEvent(event)
