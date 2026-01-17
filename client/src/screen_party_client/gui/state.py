"""Application state management - single source of truth"""

from typing import Optional, Dict, Callable, List
from dataclasses import dataclass, field
from PyQt6.QtGui import QColor


@dataclass
class AppState:
    """Central application state

    This is the single source of truth for all application state.
    UI components should read from this state and update UI accordingly.
    """
    # Connection state
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    is_connected: bool = False
    server_url: str = ""

    # Overlay state
    is_sharing: bool = False
    overlay_window: Optional[object] = None  # OverlayWindow reference

    # Drawing state
    current_alpha: float = 1.0
    pen_color: QColor = field(default_factory=lambda: QColor(255, 182, 193))

    # Participants (centralized user colors and alphas)
    user_colors: Dict[str, QColor] = field(default_factory=dict)
    user_alphas: Dict[str, float] = field(default_factory=dict)

    # UI state
    current_screen: str = "start"  # "start" or "main"
    status_message: str = ""

    # Resize/drawing mode state
    is_resize_mode: bool = False
    is_drawing_enabled: bool = False

    # Observers (callbacks when state changes)
    _observers: List[Callable[[], None]] = field(default_factory=list, repr=False)

    def add_observer(self, callback: Callable[[], None]):
        """Add a state change observer

        Args:
            callback: Function to call when state changes
        """
        if callback not in self._observers:
            self._observers.append(callback)

    def remove_observer(self, callback: Callable[[], None]):
        """Remove a state change observer

        Args:
            callback: Function to remove
        """
        if callback in self._observers:
            self._observers.remove(callback)

    def notify_observers(self):
        """Notify all observers that state has changed"""
        for observer in self._observers:
            observer()

    # === Participant Management ===

    def add_participant(self, user_id: str, color: QColor, alpha: float = 1.0):
        """Add a participant with color and alpha

        Args:
            user_id: User ID
            color: User color
            alpha: User alpha (0.0 - 1.0)
        """
        self.user_colors[user_id] = color
        self.user_alphas[user_id] = alpha
        self.notify_observers()

    def remove_participant(self, user_id: str):
        """Remove a participant

        Args:
            user_id: User ID to remove
        """
        if user_id in self.user_colors:
            del self.user_colors[user_id]
        if user_id in self.user_alphas:
            del self.user_alphas[user_id]
        self.notify_observers()

    def update_participant_color(self, user_id: str, color: QColor):
        """Update participant color

        Args:
            user_id: User ID
            color: New color
        """
        self.user_colors[user_id] = color
        self.notify_observers()

    def update_participant_alpha(self, user_id: str, alpha: float):
        """Update participant alpha

        Args:
            user_id: User ID
            alpha: New alpha (0.0 - 1.0)
        """
        self.user_alphas[user_id] = max(0.0, min(1.0, alpha))
        self.notify_observers()

    def initialize_participants(self, participants: List[Dict]):
        """Initialize participants from server response

        Args:
            participants: List of participant dicts from server
        """
        for participant in participants:
            user_id = participant.get("user_id")
            color_str = participant.get("color", "#FF0000")
            if user_id:
                color = QColor(color_str)
                self.add_participant(user_id, color, alpha=1.0)

    # === Connection State ===

    def set_connected(self, session_id: str, user_id: str, server_url: str):
        """Set connection state

        Args:
            session_id: Session ID
            user_id: User ID
            server_url: Server URL
        """
        self.session_id = session_id
        self.user_id = user_id
        self.is_connected = True
        self.server_url = server_url
        self.notify_observers()

    def set_disconnected(self):
        """Reset connection state"""
        self.session_id = None
        self.user_id = None
        self.is_connected = False
        self.user_colors.clear()
        self.user_alphas.clear()
        self.notify_observers()

    # === Overlay State ===

    def set_overlay(self, overlay_window: object):
        """Set overlay window

        Args:
            overlay_window: OverlayWindow instance
        """
        self.overlay_window = overlay_window
        self.is_sharing = True
        self.notify_observers()

    def clear_overlay(self):
        """Clear overlay window"""
        self.overlay_window = None
        self.is_sharing = False
        self.is_resize_mode = False
        self.is_drawing_enabled = False
        self.notify_observers()

    # === Drawing State ===

    def set_pen_color(self, color: QColor):
        """Set pen color

        Args:
            color: New pen color
        """
        self.pen_color = color
        if self.user_id:
            self.update_participant_color(self.user_id, color)

    def set_alpha(self, alpha: float):
        """Set current alpha

        Args:
            alpha: Alpha value (0.0 - 1.0)
        """
        self.current_alpha = max(0.0, min(1.0, alpha))
        if self.user_id:
            self.update_participant_alpha(self.user_id, alpha)

    # === UI State ===

    def set_screen(self, screen: str):
        """Set current screen

        Args:
            screen: "start" or "main"
        """
        self.current_screen = screen
        self.notify_observers()

    def set_status(self, message: str):
        """Set status message

        Args:
            message: Status message
        """
        self.status_message = message
        self.notify_observers()
