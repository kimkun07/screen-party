"""메인 윈도우 GUI"""

import asyncio
import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QInputDialog, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ..network.client import WebSocketClient

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Screen Party 메인 윈도우"""

    # Signals
    session_created = pyqtSignal(str, str)  # session_id, host_id
    session_joined = pyqtSignal(str, str)   # session_id, user_id
    error_occurred = pyqtSignal(str)        # error_message

    def __init__(self, server_url: str = "ws://localhost:8765"):
        super().__init__()
        self.server_url = server_url
        self.client: Optional[WebSocketClient] = None
        self.session_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.is_host = False
        self.listen_task: Optional[asyncio.Task] = None

        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Screen Party")
        self.setGeometry(100, 100, 400, 300)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_widget.setLayout(layout)

        # Title
        title = QLabel("Screen Party")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(40)

        # Host mode button
        self.host_button = QPushButton("Host Mode")
        self.host_button.setMinimumHeight(50)
        self.host_button.clicked.connect(lambda: asyncio.create_task(self.on_host_mode()))
        layout.addWidget(self.host_button)

        layout.addSpacing(20)

        # Guest mode button
        self.guest_button = QPushButton("Guest Mode")
        self.guest_button.setMinimumHeight(50)
        self.guest_button.clicked.connect(lambda: asyncio.create_task(self.on_guest_mode()))
        layout.addWidget(self.guest_button)

        layout.addSpacing(40)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Session info label
        self.session_info_label = QLabel("")
        self.session_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        session_font = QFont()
        session_font.setPointSize(14)
        session_font.setBold(True)
        self.session_info_label.setFont(session_font)
        layout.addWidget(self.session_info_label)

        layout.addStretch()

    async def on_host_mode(self):
        """호스트 모드 시작"""
        try:
            self.set_status("Connecting to server...")
            self.disable_buttons()

            # WebSocket 클라이언트 생성 및 연결
            self.client = WebSocketClient(self.server_url)
            self.client.set_message_handler(self.handle_message)
            await self.client.connect()

            # 세션 생성 요청
            self.set_status("Creating session...")
            response = await self.client.create_session("Host")

            if response.get("type") == "session_created":
                self.session_id = response["session_id"]
                self.user_id = response["host_id"]
                self.is_host = True

                self.set_status("Session created!")
                self.session_info_label.setText(f"Session ID: {self.session_id}")

                # Listen 태스크 시작
                self.listen_task = asyncio.create_task(self.client.listen())

                # 성공 다이얼로그
                QMessageBox.information(
                    self,
                    "Session Created",
                    f"Session ID: {self.session_id}\n\nShare this ID with guests!"
                )

                self.session_created.emit(self.session_id, self.user_id)

            elif response.get("type") == "error":
                raise RuntimeError(response.get("message", "Unknown error"))

        except Exception as e:
            logger.error(f"Host mode failed: {e}", exc_info=True)
            self.set_status(f"Error: {e}")
            self.error_occurred.emit(str(e))
            QMessageBox.critical(self, "Error", f"Failed to create session:\n{e}")
            self.enable_buttons()
            if self.client:
                await self.client.disconnect()
                self.client = None

    async def on_guest_mode(self):
        """게스트 모드 시작"""
        try:
            # 세션 ID 입력
            session_id, ok = QInputDialog.getText(
                self,
                "Join Session",
                "Enter Session ID:"
            )

            if not ok or not session_id:
                return

            session_id = session_id.strip().upper()

            self.set_status("Connecting to server...")
            self.disable_buttons()

            # WebSocket 클라이언트 생성 및 연결
            self.client = WebSocketClient(self.server_url)
            self.client.set_message_handler(self.handle_message)
            await self.client.connect()

            # 세션 참여 요청
            self.set_status(f"Joining session {session_id}...")
            response = await self.client.join_session(session_id, "Guest")

            if response.get("type") == "session_joined":
                self.session_id = response["session_id"]
                self.user_id = response["user_id"]
                self.is_host = False

                self.set_status("Joined session!")
                self.session_info_label.setText(f"Session ID: {self.session_id}")

                # Listen 태스크 시작
                self.listen_task = asyncio.create_task(self.client.listen())

                # 성공 다이얼로그
                QMessageBox.information(
                    self,
                    "Session Joined",
                    f"Successfully joined session: {self.session_id}"
                )

                self.session_joined.emit(self.session_id, self.user_id)

            elif response.get("type") == "error":
                raise RuntimeError(response.get("message", "Unknown error"))

        except Exception as e:
            logger.error(f"Guest mode failed: {e}", exc_info=True)
            self.set_status(f"Error: {e}")
            self.error_occurred.emit(str(e))
            QMessageBox.critical(self, "Error", f"Failed to join session:\n{e}")
            self.enable_buttons()
            if self.client:
                await self.client.disconnect()
                self.client = None

    async def handle_message(self, message: dict):
        """서버로부터 받은 메시지 처리

        Args:
            message: 수신한 메시지
        """
        msg_type = message.get("type")
        logger.info(f"Received message: {msg_type}")

        if msg_type == "guest_joined":
            guest_name = message.get("guest_name", "Guest")
            self.set_status(f"{guest_name} joined the session")

        elif msg_type == "guest_left":
            guest_name = message.get("guest_name", "Guest")
            self.set_status(f"{guest_name} left the session")

        elif msg_type == "session_expired":
            reason = message.get("message", "Session expired")
            self.set_status(f"Session expired: {reason}")
            QMessageBox.warning(self, "Session Expired", reason)
            await self.disconnect()

        elif msg_type == "error":
            error_msg = message.get("message", "Unknown error")
            self.set_status(f"Error: {error_msg}")
            logger.error(f"Server error: {error_msg}")

    def set_status(self, status: str):
        """상태 메시지 설정

        Args:
            status: 상태 메시지
        """
        self.status_label.setText(status)
        logger.info(f"Status: {status}")

    def disable_buttons(self):
        """버튼 비활성화"""
        self.host_button.setEnabled(False)
        self.guest_button.setEnabled(False)

    def enable_buttons(self):
        """버튼 활성화"""
        self.host_button.setEnabled(True)
        self.guest_button.setEnabled(True)

    async def disconnect(self):
        """서버 연결 종료"""
        if self.listen_task:
            self.listen_task.cancel()
            try:
                await self.listen_task
            except asyncio.CancelledError:
                pass
            self.listen_task = None

        if self.client:
            await self.client.disconnect()
            self.client = None

        self.session_id = None
        self.user_id = None
        self.is_host = False
        self.session_info_label.setText("")
        self.enable_buttons()

    def closeEvent(self, event):
        """윈도우 종료 시 호출"""
        if self.client:
            # 비동기 disconnect를 동기적으로 실행
            loop = asyncio.get_event_loop()
            loop.create_task(self.disconnect())
        event.accept()
