"""Canvas manager - handles dual-canvas synchronization"""

from typing import Optional, Dict, Any
from PyQt6.QtGui import QColor

from .canvas import DrawingCanvas


class CanvasManager:
    """Manages main canvas and overlay canvas synchronization

    This class eliminates the need for scattered dual-canvas update logic
    by providing a single place to update both canvases.
    """

    def __init__(self, main_canvas: DrawingCanvas):
        """Initialize canvas manager

        Args:
            main_canvas: The main drawing canvas
        """
        self.main_canvas = main_canvas
        self.overlay_canvas: Optional[DrawingCanvas] = None

    def set_overlay_canvas(self, canvas: Optional[DrawingCanvas]):
        """Set overlay canvas

        Args:
            canvas: Overlay canvas instance (or None to clear)
        """
        self.overlay_canvas = canvas

        # Sync user_colors and user_alphas to overlay
        if canvas and self.main_canvas:
            canvas.user_colors = self.main_canvas.user_colors.copy()
            canvas.user_alphas = self.main_canvas.user_alphas.copy()

    def get_canvases(self) -> list[DrawingCanvas]:
        """Get list of active canvases

        Returns:
            List of canvases (main + overlay if exists)
        """
        canvases = [self.main_canvas]
        if self.overlay_canvas:
            canvases.append(self.overlay_canvas)
        return canvases

    # === Participant Management ===

    def add_participant(self, user_id: str, color: QColor, alpha: float = 1.0):
        """Add participant to all canvases

        Args:
            user_id: User ID
            color: User color
            alpha: User alpha (0.0 - 1.0)
        """
        for canvas in self.get_canvases():
            canvas.user_colors[user_id] = color
            canvas.user_alphas[user_id] = alpha

    def remove_participant(self, user_id: str):
        """Remove participant from all canvases

        Args:
            user_id: User ID
        """
        for canvas in self.get_canvases():
            if user_id in canvas.user_colors:
                del canvas.user_colors[user_id]
            if user_id in canvas.user_alphas:
                del canvas.user_alphas[user_id]

    def update_participant_color(self, user_id: str, color: QColor):
        """Update participant color in all canvases

        Args:
            user_id: User ID
            color: New color
        """
        for canvas in self.get_canvases():
            canvas.user_colors[user_id] = color

    def update_participant_alpha(self, user_id: str, alpha: float):
        """Update participant alpha in all canvases

        Args:
            user_id: User ID
            alpha: New alpha (0.0 - 1.0)
        """
        for canvas in self.get_canvases():
            canvas.user_alphas[user_id] = max(0.0, min(1.0, alpha))

    # === Drawing Events ===

    def handle_drawing_start(self, line_id: str, user_id: str, message: Dict[str, Any]):
        """Handle drawing start on all canvases

        Args:
            line_id: Line ID
            user_id: User ID
            message: Drawing start message
        """
        for canvas in self.get_canvases():
            canvas.handle_drawing_start(line_id, user_id, message)

    def handle_drawing_update(self, line_id: str, user_id: str, message: Dict[str, Any]):
        """Handle drawing update on all canvases

        Args:
            line_id: Line ID
            user_id: User ID
            message: Drawing update message
        """
        for canvas in self.get_canvases():
            canvas.handle_drawing_update(line_id, user_id, message)

    def handle_drawing_end(self, line_id: str, user_id: str):
        """Handle drawing end on all canvases

        Args:
            line_id: Line ID
            user_id: User ID
        """
        for canvas in self.get_canvases():
            canvas.handle_drawing_end(line_id, user_id)

    # === Canvas Operations ===

    def clear_all_drawings(self):
        """Clear all drawings on overlay canvas only"""
        if self.overlay_canvas:
            self.overlay_canvas.clear_all_drawings()

    def set_user_id(self, user_id: str):
        """Set user ID on all canvases

        Args:
            user_id: User ID
        """
        for canvas in self.get_canvases():
            canvas.set_user_id(user_id)
