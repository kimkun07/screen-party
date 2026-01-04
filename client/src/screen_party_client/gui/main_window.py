"""메인 윈도우 GUI"""

import asyncio
import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QInputDialog, QMessageBox, QHBoxLayout, QLineEdit,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from screen_party_common import MessageType, DrawingEndMessage
from ..network.client import WebSocketClient
from ..drawing import DrawingCanvas

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Screen Party 메인 윈도우"""

    # Signals
    session_created = pyqtSignal(str, str)  # session_id, host_id
    session_joined = pyqtSignal(str, str)  # session_id, user_id
    error_occurred = pyqtSignal(str)  # error_message

    def __init__(self, server_url: str = "ws://localhost:8765"):
        super().__init__()
        self.default_server_url = server_url
        self.client: Optional[WebSocketClient] = None
        self.session_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.is_host = False
        self.listen_task: Optional[asyncio.Task] = None

        # UI 상태
        self.is_connected = False

        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Screen Party")
        self.setGeometry(100, 100, 500, 400)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_widget.setLayout(self.main_layout)

        # 시작 화면과 메인 화면 생성
        self.create_start_screen()
        self.create_main_screen()

        # 시작 화면 표시
        self.show_start_screen()

    def create_start_screen(self):
        """시작 화면 생성"""
        self.start_widget = QWidget()
        start_layout = QVBoxLayout()
        start_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.start_widget.setLayout(start_layout)

        # Title
        title = QLabel("Screen Party")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        start_layout.addWidget(title)

        start_layout.addSpacing(40)

        # 서버 주소 입력
        server_label = QLabel("서버 주소:")
        start_layout.addWidget(server_label)
        self.server_input = QLineEdit()
        self.server_input.setText(self.default_server_url)
        self.server_input.setPlaceholderText("ws://localhost:8765")
        start_layout.addWidget(self.server_input)

        start_layout.addSpacing(20)

        # 세션 번호 입력 + 접속 버튼 (가로 레이아웃)
        session_label = QLabel("세션 번호:")
        start_layout.addWidget(session_label)

        session_layout = QHBoxLayout()
        self.session_input = QLineEdit()
        self.session_input.setPlaceholderText("세션 번호 입력")
        self.session_input.textChanged.connect(self.on_session_input_changed)
        session_layout.addWidget(self.session_input)

        self.join_button = QPushButton("접속")
        self.join_button.setMinimumHeight(40)
        self.join_button.setEnabled(False)
        self.join_button.clicked.connect(lambda: asyncio.create_task(self.on_join_session()))
        session_layout.addWidget(self.join_button)

        start_layout.addLayout(session_layout)

        start_layout.addSpacing(20)

        # 세션 생성 버튼
        self.create_button = QPushButton("세션 생성")
        self.create_button.setMinimumHeight(50)
        self.create_button.clicked.connect(lambda: asyncio.create_task(self.on_create_session()))
        start_layout.addWidget(self.create_button)

        start_layout.addSpacing(20)

        # Status label
        self.start_status_label = QLabel("")
        self.start_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        start_layout.addWidget(self.start_status_label)

        start_layout.addStretch()

        self.main_layout.addWidget(self.start_widget)

    def create_main_screen(self):
        """메인 화면 생성"""
        self.main_widget = QWidget()
        main_screen_layout = QVBoxLayout()
        main_screen_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_widget.setLayout(main_screen_layout)

        # Title
        title = QLabel("Screen Party")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_screen_layout.addWidget(title)

        main_screen_layout.addSpacing(30)

        # 서버 주소 표시 + 복사 버튼
        server_info_layout = QHBoxLayout()
        self.server_info_label = QLabel("")
        server_info_layout.addWidget(self.server_info_label)
        self.copy_server_button = QPushButton("복사")
        self.copy_server_button.clicked.connect(self.copy_server_address)
        server_info_layout.addWidget(self.copy_server_button)
        main_screen_layout.addLayout(server_info_layout)

        main_screen_layout.addSpacing(10)

        # 세션 번호 표시 + 복사 버튼
        session_info_layout = QHBoxLayout()
        self.session_info_label = QLabel("")
        session_info_layout.addWidget(self.session_info_label)
        self.copy_session_button = QPushButton("복사")
        self.copy_session_button.clicked.connect(self.copy_session_id)
        session_info_layout.addWidget(self.copy_session_button)
        main_screen_layout.addLayout(session_info_layout)

        main_screen_layout.addSpacing(30)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_screen_layout.addWidget(self.status_label)

        main_screen_layout.addSpacing(20)

        # Drawing Canvas
        self.drawing_canvas = DrawingCanvas(
            parent=self.main_widget,
            user_id=None,  # 세션 연결 시 설정
            pen_color=QColor(255, 0, 0),
            pen_width=3,
        )
        self.drawing_canvas.setMinimumSize(600, 400)
        main_screen_layout.addWidget(self.drawing_canvas)

        # Drawing Canvas 시그널 연결
        self._connect_drawing_signals()

        main_screen_layout.addStretch()

        self.main_layout.addWidget(self.main_widget)

    def show_start_screen(self):
        """시작 화면 표시"""
        self.start_widget.show()
        self.main_widget.hide()

    def show_main_screen(self):
        """메인 화면 표시"""
        self.start_widget.hide()
        self.main_widget.show()

        # 서버 주소와 세션 번호 표시
        server_url = self.server_input.text()
        self.server_info_label.setText(f"서버 주소: {server_url}")
        self.session_info_label.setText(f"세션 번호: {self.session_id}")

    def on_session_input_changed(self, text: str):
        """세션 번호 입력 변경 시 호출"""
        self.join_button.setEnabled(len(text.strip()) > 0)

    def copy_server_address(self):
        """서버 주소를 클립보드에 복사"""
        clipboard = QApplication.clipboard()
        server_url = self.server_input.text()
        clipboard.setText(server_url)
        self.set_status("서버 주소가 클립보드에 복사되었습니다")

    def copy_session_id(self):
        """세션 번호를 클립보드에 복사"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.session_id)
        self.set_status("세션 번호가 클립보드에 복사되었습니다")

    async def on_create_session(self):
        """세션 생성 (호스트)"""
        try:
            server_url = self.server_input.text().strip()
            if not server_url:
                QMessageBox.warning(self, "입력 오류", "서버 주소를 입력해주세요")
                return

            self.set_start_status("서버에 연결 중...")
            self.disable_start_buttons()

            # WebSocket 클라이언트 생성 및 연결
            self.client = WebSocketClient(server_url)
            self.client.set_message_handler(self.handle_message)
            await self.client.connect()

            # 세션 생성 요청
            self.set_start_status("세션 생성 중...")
            response = await self.client.create_session("Host")

            if response.get("type") == "session_created":
                self.session_id = response["session_id"]
                self.user_id = response["host_id"]
                self.is_host = True
                self.is_connected = True

                # DrawingCanvas에 user_id 설정
                self.drawing_canvas.set_user_id(self.user_id)

                # 클립보드에 (서버주소, 세션번호) 복사
                clipboard = QApplication.clipboard()
                clipboard_text = f"({server_url}, {self.session_id})"
                clipboard.setText(clipboard_text)

                self.set_start_status(f"세션 생성 완료! 클립보드에 복사됨")

                self.session_created.emit(self.session_id, self.user_id)

                # Listen 태스크 시작 (QTimer로 지연시켜 이벤트 루프 블록 방지)
                QTimer.singleShot(100, self._start_listen_task)

                # 메인 화면으로 전환
                QTimer.singleShot(500, self.show_main_screen)

            elif response.get("type") == "error":
                raise RuntimeError(response.get("message", "Unknown error"))

        except Exception as e:
            logger.error(f"Session creation failed: {e}", exc_info=True)
            self.set_start_status(f"오류: {e}")
            self.error_occurred.emit(str(e))
            QMessageBox.critical(self, "오류", f"세션 생성 실패:\n{e}")
            self.enable_start_buttons()
            if self.client:
                await self.client.disconnect()
                self.client = None

    async def on_join_session(self):
        """세션 참여 (게스트)"""
        try:
            server_url = self.server_input.text().strip()
            session_id = self.session_input.text().strip().upper()

            if not server_url:
                QMessageBox.warning(self, "입력 오류", "서버 주소를 입력해주세요")
                return

            if not session_id:
                QMessageBox.warning(self, "입력 오류", "세션 번호를 입력해주세요")
                return

            self.set_start_status("서버에 연결 중...")
            self.disable_start_buttons()

            # WebSocket 클라이언트 생성 및 연결
            self.client = WebSocketClient(server_url)
            self.client.set_message_handler(self.handle_message)
            await self.client.connect()

            # 세션 참여 요청
            self.set_start_status(f"세션 {session_id}에 참여 중...")
            response = await self.client.join_session(session_id, "Guest")

            if response.get("type") == "session_joined":
                self.session_id = response["session_id"]
                self.user_id = response["user_id"]
                self.is_host = False
                self.is_connected = True

                # DrawingCanvas에 user_id 설정
                self.drawing_canvas.set_user_id(self.user_id)

                self.set_start_status(f"세션 참여 성공!")

                self.session_joined.emit(self.session_id, self.user_id)

                # Listen 태스크 시작 (QTimer로 지연시켜 이벤트 루프 블록 방지)
                QTimer.singleShot(100, self._start_listen_task)

                # 메인 화면으로 전환
                QTimer.singleShot(500, self.show_main_screen)

            elif response.get("type") == "error":
                raise RuntimeError(response.get("message", "Unknown error"))

        except Exception as e:
            logger.error(f"Session join failed: {e}", exc_info=True)
            self.set_start_status(f"오류: {e}")
            self.error_occurred.emit(str(e))
            QMessageBox.critical(self, "오류", f"세션 참여 실패:\n{e}")
            self.enable_start_buttons()
            if self.client:
                await self.client.disconnect()
                self.client = None

    def _connect_drawing_signals(self):
        """DrawingCanvas 시그널 연결"""
        self.drawing_canvas.drawing_started.connect(self._on_drawing_started)
        self.drawing_canvas.drawing_updated.connect(self._on_drawing_updated)
        self.drawing_canvas.drawing_ended.connect(self._on_drawing_ended)

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
        if self.client and self.is_connected:
            try:
                await self.client.send_message(data)
            except Exception as e:
                logger.error(f"Failed to send drawing message: {e}")

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

        # 드로잉 메시지 처리
        elif msg_type == MessageType.DRAWING_START.value:
            line_id = message.get("line_id")
            user_id = message.get("user_id")
            if line_id and user_id and user_id != self.user_id:
                self.drawing_canvas.handle_drawing_start(line_id, user_id, message)

        elif msg_type == MessageType.DRAWING_UPDATE.value:
            line_id = message.get("line_id")
            user_id = message.get("user_id")
            if line_id and user_id and user_id != self.user_id:
                self.drawing_canvas.handle_drawing_update(line_id, user_id, message)

        elif msg_type == MessageType.DRAWING_END.value:
            line_id = message.get("line_id")
            user_id = message.get("user_id")
            if line_id and user_id and user_id != self.user_id:
                self.drawing_canvas.handle_drawing_end(line_id, user_id)

    def set_status(self, status: str):
        """메인 화면 상태 메시지 설정

        Args:
            status: 상태 메시지
        """
        if self.is_connected:
            self.status_label.setText(status)
        logger.info(f"Status: {status}")

    def set_start_status(self, status: str):
        """시작 화면 상태 메시지 설정

        Args:
            status: 상태 메시지
        """
        self.start_status_label.setText(status)
        logger.info(f"Start Status: {status}")

    def disable_start_buttons(self):
        """시작 화면 버튼 비활성화"""
        self.create_button.setEnabled(False)
        self.join_button.setEnabled(False)
        self.server_input.setEnabled(False)
        self.session_input.setEnabled(False)

    def enable_start_buttons(self):
        """시작 화면 버튼 활성화"""
        self.create_button.setEnabled(True)
        self.join_button.setEnabled(len(self.session_input.text().strip()) > 0)
        self.server_input.setEnabled(True)
        self.session_input.setEnabled(True)

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
        self.is_connected = False
        self.show_start_screen()
        self.enable_start_buttons()

    def _start_listen_task(self):
        """Listen 태스크 시작 (QTimer 콜백용)"""
        if self.client:
            self.listen_task = asyncio.ensure_future(self.client.listen())
            logger.info("Listen task started")

    def closeEvent(self, event):
        """윈도우 종료 시 호출"""
        if self.client:
            # 비동기 disconnect를 동기적으로 실행
            loop = asyncio.get_event_loop()
            loop.create_task(self.disconnect())
        event.accept()
