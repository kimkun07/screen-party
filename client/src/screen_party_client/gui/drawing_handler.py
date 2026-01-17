"""드로잉/캔버스 관련 메서드 (색상/투명도 변경, 드로잉 시그널 처리)"""

import asyncio
import logging
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QColor

from screen_party_common import DrawingEndMessage, ColorChangeMessage
from ..drawing import DrawingCanvas

if TYPE_CHECKING:
    from .main_window import MainWindow

logger = logging.getLogger(__name__)


class DrawingHandler:
    """드로잉/캔버스 로직을 담당하는 헬퍼 클래스"""

    def __init__(self, window: "MainWindow"):
        self.window = window

    def _connect_drawing_signals(self, canvas: DrawingCanvas):
        """DrawingCanvas 시그널 연결

        Args:
            canvas: 연결할 캔버스
        """
        canvas.drawing_started.connect(self._on_drawing_started)
        canvas.drawing_updated.connect(self._on_drawing_updated)
        canvas.drawing_ended.connect(self._on_drawing_ended)

    def _on_drawing_started(self, line_id: str, user_id: str, data: dict):
        """드로잉 시작 시그널 처리"""
        asyncio.create_task(self._send_drawing_message(data))

    def _on_drawing_updated(self, line_id: str, user_id: str, data: dict):
        """드로잉 업데이트 시그널 처리"""
        asyncio.create_task(self._send_drawing_message(data))

    def _on_drawing_ended(self, line_id: str, user_id: str):
        """드로잉 종료 시그널 처리"""
        msg = DrawingEndMessage(
            line_id=line_id,
            user_id=user_id,
        )
        asyncio.create_task(self._send_drawing_message(msg.to_dict()))

    async def _send_drawing_message(self, data: dict):
        """드로잉 메시지를 서버로 전송"""
        if self.window.client and self.window.state.is_connected:
            try:
                await self.window.client.send_message(data)
            except Exception as e:
                logger.error(f"Failed to send drawing message: {e}")

    async def _send_color_change(self, data: dict):
        """색상 변경 메시지를 서버로 전송"""
        if self.window.client and self.window.state.is_connected:
            try:
                await self.window.client.send_message(data)
            except Exception as e:
                logger.error(f"Failed to send color change message: {e}")

    def set_pen_color(self, color: QColor):
        """펜 색상 변경 (신규 곡선에만 적용)

        Args:
            color: 새로운 펜 색상
        """
        # Canvas 색상 변경
        self.window.canvas_manager.main_canvas.set_pen_color(color)

        # State 업데이트
        self.window.state.set_pen_color(color)
        self.window.state.set_status(f"색상 변경: RGB({color.red()}, {color.green()}, {color.blue()})")
        logger.info(f"Pen color changed to RGB({color.red()}, {color.green()}, {color.blue()})")

        # 서버에 색상 변경 알림 (알파값 포함)
        if self.window.client and self.window.state.is_connected and self.window.state.user_id:
            msg = ColorChangeMessage(
                user_id=self.window.state.user_id,
                color=color.name(),
                alpha=self.window.state.current_alpha,
            )
            asyncio.create_task(self._send_color_change(msg.to_dict()))

    def on_alpha_changed(self, value: int, label: QLabel):
        """투명도 슬라이더 변경 시 호출

        Args:
            value: 슬라이더 값 (0~100)
            label: 업데이트할 라벨
        """
        alpha = value / 100.0

        # Canvas 알파 변경
        self.window.canvas_manager.main_canvas.set_pen_alpha(alpha)

        # State 업데이트
        self.window.state.set_alpha(alpha)
        label.setText(f"투명도: {value}%")
        logger.info(f"Pen alpha changed to {alpha:.2f}")

        # 서버에 알파값 변경 알림 (현재 색상과 함께 전송)
        if self.window.client and self.window.state.is_connected and self.window.state.user_id:
            current_color = self.window.canvas_manager.main_canvas.pen_color
            msg = ColorChangeMessage(
                user_id=self.window.state.user_id,
                color=current_color.name(),
                alpha=alpha,
            )
            asyncio.create_task(self._send_color_change(msg.to_dict()))
