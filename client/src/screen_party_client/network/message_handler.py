"""Message handler - processes server messages"""

import logging
from typing import Dict, Any, Callable, Awaitable

from PyQt6.QtGui import QColor
from screen_party_common import MessageType

from ..gui.state import AppState
from ..drawing.canvas_manager import CanvasManager

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handles incoming WebSocket messages and updates state

    This class separates message handling logic from the UI,
    making the code more testable and maintainable.
    """

    def __init__(
        self,
        state: AppState,
        canvas_manager: CanvasManager,
        disconnect_callback: Callable[[], Awaitable[None]],
    ):
        """Initialize message handler

        Args:
            state: Application state
            canvas_manager: Canvas manager
            disconnect_callback: Async function to call on disconnect
        """
        self.state = state
        self.canvas_manager = canvas_manager
        self.disconnect_callback = disconnect_callback

    async def handle_message(self, message: Dict[str, Any]):
        """Handle incoming message from server

        Args:
            message: Message dictionary
        """
        msg_type = message.get("type")
        logger.info(f"Received message: {msg_type}")

        if msg_type in ("guest_joined", "participant_joined"):
            await self._handle_participant_joined(message)
        elif msg_type in ("guest_left", "participant_left"):
            await self._handle_participant_left(message)
        elif msg_type == "session_expired":
            await self._handle_session_expired(message)
        elif msg_type == "error":
            await self._handle_error(message)
        elif msg_type == MessageType.DRAWING_START.value:
            await self._handle_drawing_start(message)
        elif msg_type == MessageType.DRAWING_UPDATE.value:
            await self._handle_drawing_update(message)
        elif msg_type == MessageType.DRAWING_END.value:
            await self._handle_drawing_end(message)
        elif msg_type == MessageType.COLOR_CHANGE.value:
            await self._handle_color_change(message)

    # === Participant Messages ===

    async def _handle_participant_joined(self, message: Dict[str, Any]):
        """Handle participant joined message"""
        participant_name = message.get("guest_name") or message.get("participant_name", "Participant")
        user_id = message.get("user_id")
        color_str = message.get("color", "#FF0000")

        if user_id:
            color = QColor(color_str)
            # Update state (this will notify observers)
            self.state.add_participant(user_id, color, alpha=1.0)
            # Update canvases
            self.canvas_manager.add_participant(user_id, color, alpha=1.0)
            logger.info(f"Added participant {user_id} with color {color_str}")

        self.state.set_status(f"{participant_name} joined the session")

    async def _handle_participant_left(self, message: Dict[str, Any]):
        """Handle participant left message"""
        participant_name = message.get("guest_name") or message.get("participant_name", "Participant")
        user_id = message.get("user_id")

        if user_id:
            # Update state
            self.state.remove_participant(user_id)
            # Update canvases
            self.canvas_manager.remove_participant(user_id)
            logger.info(f"Removed participant {user_id}")

        self.state.set_status(f"{participant_name} left the session")

    # === Session Messages ===

    async def _handle_session_expired(self, message: Dict[str, Any]):
        """Handle session expired message"""
        reason = message.get("message", "Session expired")
        self.state.set_status(f"Session expired: {reason}")
        await self.disconnect_callback()

    async def _handle_error(self, message: Dict[str, Any]):
        """Handle error message"""
        error_msg = message.get("message", "Unknown error")
        self.state.set_status(f"Error: {error_msg}")
        logger.error(f"Server error: {error_msg}")

    # === Drawing Messages ===

    async def _handle_drawing_start(self, message: Dict[str, Any]):
        """Handle drawing start message"""
        line_id = message.get("line_id")
        user_id = message.get("user_id")

        if line_id and user_id and user_id != self.state.user_id:
            self.canvas_manager.handle_drawing_start(line_id, user_id, message)

    async def _handle_drawing_update(self, message: Dict[str, Any]):
        """Handle drawing update message"""
        line_id = message.get("line_id")
        user_id = message.get("user_id")

        if line_id and user_id and user_id != self.state.user_id:
            self.canvas_manager.handle_drawing_update(line_id, user_id, message)

    async def _handle_drawing_end(self, message: Dict[str, Any]):
        """Handle drawing end message"""
        line_id = message.get("line_id")
        user_id = message.get("user_id")

        if line_id and user_id and user_id != self.state.user_id:
            self.canvas_manager.handle_drawing_end(line_id, user_id)

    async def _handle_color_change(self, message: Dict[str, Any]):
        """Handle color change message"""
        user_id = message.get("user_id")
        color_str = message.get("color", "#FF0000")
        alpha = message.get("alpha", 1.0)

        if user_id:
            color = QColor(color_str)
            # Update state
            self.state.update_participant_color(user_id, color)
            self.state.update_participant_alpha(user_id, alpha)
            # Update canvases
            self.canvas_manager.update_participant_color(user_id, color)
            self.canvas_manager.update_participant_alpha(user_id, alpha)
            logger.info(f"User {user_id} changed color to {color_str}, alpha to {alpha:.2f}")
