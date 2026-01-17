"""메인 윈도우 GUI"""

import asyncio
import logging
import sys
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QInputDialog, QHBoxLayout, QLineEdit,
    QApplication, QGroupBox, QSlider, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSettings
from PyQt6.QtGui import QFont, QColor

from screen_party_common import MessageType, DrawingEndMessage, ColorChangeMessage
from ..network.client import WebSocketClient
from ..drawing import DrawingCanvas
from .constants import PRESET_COLORS, get_default_pen_color

logger = logging.getLogger(__name__)


def get_version() -> str:
    """실행 파일의 버전 정보를 가져옵니다.

    PyInstaller로 빌드된 exe 파일의 Windows 버전 정보를 읽습니다.
    개발 환경에서는 "-dev"를 반환합니다.
    """
    # PyInstaller로 빌드된 경우 (frozen 상태)
    if getattr(sys, "frozen", False):
        try:
            import win32api

            exe_path = sys.executable
            info = win32api.GetFileVersionInfo(exe_path, "\\")
            ms = info["FileVersionMS"]
            ls = info["FileVersionLS"]
            major = win32api.HIWORD(ms)
            minor = win32api.LOWORD(ms)
            patch = win32api.HIWORD(ls)
            return f"{major}.{minor}.{patch}"
        except Exception:
            return "unknown"

    # 개발 환경
    return "-dev"


class MainWindow(QMainWindow):
    """Screen Party 메인 윈도우"""

    # Signals
    session_created = pyqtSignal(str, str)  # session_id, host_id
    session_joined = pyqtSignal(str, str)  # session_id, user_id
    error_occurred = pyqtSignal(str)  # error_message

    def __init__(self):
        super().__init__()

        # QSettings 초기화 (로컬 저장소)
        self.settings = QSettings("ScreenParty", "Client")

        self.client: Optional[WebSocketClient] = None
        self.session_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.is_host = False  # Deprecated: kept for backward compatibility
        self.listen_task: Optional[asyncio.Task] = None

        # UI 상태
        self.is_connected = False

        # 오버레이 상태
        self.is_sharing = False
        self.overlay_window = None

        # 현재 알파값 추적 (0.0 ~ 1.0)
        self.current_alpha = 1.0

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
        # 스크롤 영역 생성
        self.start_scroll = QScrollArea()
        self.start_scroll.setWidgetResizable(True)
        self.start_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

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
        # QSettings에서 저장된 서버 주소 불러오기
        saved_server = self.settings.value("server_url", "")
        self.server_input.setText(saved_server)
        self.server_input.setPlaceholderText("ws://localhost:8765")
        start_layout.addWidget(self.server_input)

        start_layout.addSpacing(20)

        # 세션 생성 / 세션 참여 (두 column 배치, 1:1 비율)
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)

        # 세션 생성 column (왼쪽)
        create_column = QVBoxLayout()
        create_label = QLabel("새 세션")
        create_label_font = QFont()
        create_label_font.setPointSize(14)
        create_label_font.setBold(True)
        create_label.setFont(create_label_font)
        create_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        create_column.addWidget(create_label)
        create_column.addSpacing(10)

        self.create_button = QPushButton("세션 생성")
        self.create_button.setMinimumHeight(50)
        self.create_button.clicked.connect(
            lambda: asyncio.create_task(self.on_create_session()))
        create_column.addWidget(self.create_button)
        create_column.addStretch()  # 아래쪽 공간 채우기

        columns_layout.addLayout(create_column, 1)  # stretch factor = 1

        # 세션 참여 column (오른쪽)
        join_column = QVBoxLayout()
        join_label = QLabel("기존 세션 참여")
        join_label_font = QFont()
        join_label_font.setPointSize(14)
        join_label_font.setBold(True)
        join_label.setFont(join_label_font)
        join_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        join_column.addWidget(join_label)
        join_column.addSpacing(10)

        session_label = QLabel("세션 번호:")
        join_column.addWidget(session_label)

        self.session_input = QLineEdit()
        self.session_input.setPlaceholderText("세션 번호 입력")
        self.session_input.textChanged.connect(self.on_session_input_changed)
        join_column.addWidget(self.session_input)

        join_column.addSpacing(5)  # 입력과 버튼 사이 간격

        self.join_button = QPushButton("접속")
        self.join_button.setMinimumHeight(50)
        self.join_button.setEnabled(False)
        self.join_button.clicked.connect(
            lambda: asyncio.create_task(self.on_join_session()))
        join_column.addWidget(self.join_button)

        columns_layout.addLayout(join_column, 1)  # stretch factor = 1

        start_layout.addLayout(columns_layout)

        start_layout.addSpacing(20)

        # Status label
        self.start_status_label = QLabel("")
        self.start_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        start_layout.addWidget(self.start_status_label)

        start_layout.addStretch()

        # 스크롤 영역에 위젯 설정
        self.start_scroll.setWidget(self.start_widget)
        self.main_layout.addWidget(self.start_scroll)

    def create_main_screen(self):
        """메인 화면 생성"""
        # 스크롤 영역 생성
        self.main_scroll = QScrollArea()
        self.main_scroll.setWidgetResizable(True)
        self.main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

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

        main_screen_layout.addSpacing(20)

        # Status label (상단에 배치)
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_screen_layout.addWidget(self.status_label)

        main_screen_layout.addSpacing(20)

        # ===== 그림 영역 설정 섹션 (통합) =====
        overlay_group = QGroupBox("그림 영역 설정")
        self.overlay_group_layout = QVBoxLayout()
        overlay_group.setLayout(self.overlay_group_layout)

        # 초기 상태: 그림 영역 생성 버튼
        self.setup_overlay_button = QPushButton("그림 영역 생성")
        self.setup_overlay_button.setMinimumHeight(45)
        self.setup_overlay_button.clicked.connect(self.toggle_overlay)
        self.overlay_group_layout.addWidget(self.setup_overlay_button)

        # 생성 후 상태: 크기 조정 + 삭제 버튼 (8:2 비율)
        self.overlay_control_widget = QWidget()
        overlay_control_layout = QHBoxLayout()
        overlay_control_layout.setContentsMargins(0, 0, 0, 0)
        overlay_control_layout.setSpacing(10)
        self.overlay_control_widget.setLayout(overlay_control_layout)

        self.resize_overlay_button = QPushButton("그림 영역 크기 조정")
        self.resize_overlay_button.setMinimumHeight(40)
        self.resize_overlay_button.clicked.connect(self.toggle_resize_mode)
        overlay_control_layout.addWidget(self.resize_overlay_button, 8)  # 80%

        self.delete_overlay_button = QPushButton("삭제")
        self.delete_overlay_button.setMinimumHeight(40)
        self.delete_overlay_button.clicked.connect(self.stop_overlay)
        overlay_control_layout.addWidget(self.delete_overlay_button, 2)  # 20%

        self.overlay_group_layout.addWidget(self.overlay_control_widget)
        self.overlay_control_widget.hide()  # 초기에는 숨김

        # 그리기 활성화/비활성화 버튼
        self.toggle_drawing_button = QPushButton("그리기 활성화")
        self.toggle_drawing_button.setMinimumHeight(40)
        self.toggle_drawing_button.setEnabled(False)
        self.toggle_drawing_button.clicked.connect(self.toggle_drawing_mode)
        self.overlay_group_layout.addWidget(self.toggle_drawing_button)

        # 색상 팔레트 (프리셋 색상 버튼들)
        palette_label = QLabel("색상:")
        self.overlay_group_layout.addWidget(palette_label)

        palette_layout = QHBoxLayout()
        self.color_buttons = []

        for color in PRESET_COLORS:
            btn = QPushButton()
            btn.setFixedSize(40, 40)  # 정사각형 버튼
            # 기본 색상과 hover/pressed 효과를 모두 정의하여 Qt 기본 피드백 제공
            base_r, base_g, base_b = color.red(), color.green(), color.blue()
            hover_r = min(255, int(base_r * 1.1))  # 10% 밝게
            hover_g = min(255, int(base_g * 1.1))
            hover_b = min(255, int(base_b * 1.1))
            pressed_r = max(0, int(base_r * 0.9))  # 10% 어둡게
            pressed_g = max(0, int(base_g * 0.9))
            pressed_b = max(0, int(base_b * 0.9))
            btn.setStyleSheet(
                f"QPushButton {{"
                f"  background-color: rgb({base_r}, {base_g}, {base_b}); "
                f"  border: 2px solid #888; "
                f"  border-radius: 4px;"
                f"}}"
                f"QPushButton:hover {{"
                f"  background-color: rgb({hover_r}, {hover_g}, {hover_b}); "
                f"  border: 2px solid #AAA;"
                f"}}"
                f"QPushButton:pressed {{"
                f"  background-color: rgb({pressed_r}, {pressed_g}, {pressed_b}); "
                f"  border: 2px solid #666;"
                f"}}"
            )
            btn.clicked.connect(lambda checked, c=color: self.set_pen_color(c))
            palette_layout.addWidget(btn)
            self.color_buttons.append(btn)

        self.overlay_group_layout.addLayout(palette_layout)

        # Alpha 슬라이더
        alpha_label = QLabel("투명도: 100%")
        self.overlay_group_layout.addWidget(alpha_label)

        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setMinimum(0)
        self.alpha_slider.setMaximum(100)
        self.alpha_slider.setValue(100)
        self.alpha_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.alpha_slider.setTickInterval(10)
        self.alpha_slider.valueChanged.connect(
            lambda value: self.on_alpha_changed(value, alpha_label)
        )
        self.overlay_group_layout.addWidget(self.alpha_slider)

        # 그림 모두 지우기 버튼
        self.clear_drawings_button = QPushButton("그림 모두 지우기")
        self.clear_drawings_button.setMinimumHeight(40)
        self.clear_drawings_button.setEnabled(False)
        self.clear_drawings_button.clicked.connect(self.clear_overlay_drawings)
        self.overlay_group_layout.addWidget(self.clear_drawings_button)

        main_screen_layout.addWidget(overlay_group)

        main_screen_layout.addSpacing(15)

        # ===== 참여자 섹션 =====
        participants_group = QGroupBox("참여자")
        participants_layout = QVBoxLayout()
        participants_group.setLayout(participants_layout)

        self.users_colors_label = QLabel("연결 대기 중...")
        self.users_colors_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        participants_layout.addWidget(self.users_colors_label)

        main_screen_layout.addWidget(participants_group)

        main_screen_layout.addSpacing(15)

        # ===== 정보 섹션 =====
        info_group = QGroupBox("정보")
        info_layout = QVBoxLayout()
        info_group.setLayout(info_layout)

        # 서버 주소 표시 + 복사 버튼
        server_info_layout = QHBoxLayout()
        self.server_info_label = QLabel("")
        server_info_layout.addWidget(self.server_info_label)
        self.copy_server_button = QPushButton("복사")
        self.copy_server_button.setMaximumWidth(60)
        self.copy_server_button.clicked.connect(self.copy_server_address)
        server_info_layout.addWidget(self.copy_server_button)
        info_layout.addLayout(server_info_layout)

        # 세션 번호 표시 + 복사 버튼
        session_info_layout = QHBoxLayout()
        self.session_info_label = QLabel("")
        session_info_layout.addWidget(self.session_info_label)
        self.copy_session_button = QPushButton("복사")
        self.copy_session_button.setMaximumWidth(60)
        self.copy_session_button.clicked.connect(self.copy_session_id)
        session_info_layout.addWidget(self.copy_session_button)
        info_layout.addLayout(session_info_layout)

        # 세션 나가기 버튼
        self.leave_session_button = QPushButton("세션 나가기")
        self.leave_session_button.setMinimumHeight(40)
        self.leave_session_button.clicked.connect(lambda: asyncio.create_task(self.disconnect()))
        info_layout.addWidget(self.leave_session_button)

        # 사용법 링크 + 버전 정보
        footer_layout = QHBoxLayout()
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        github_label = QLabel('<a href="https://github.com/kimkun07/screen-party">사용법 (GitHub)</a>')
        github_label.setOpenExternalLinks(True)
        footer_layout.addWidget(github_label)

        version_label = QLabel(f"v{get_version()}")
        version_label.setStyleSheet("color: gray;")
        footer_layout.addWidget(version_label)

        info_layout.addLayout(footer_layout)

        main_screen_layout.addWidget(info_group)

        main_screen_layout.addStretch()

        # 스크롤 영역에 위젯 설정
        self.main_scroll.setWidget(self.main_widget)
        self.main_layout.addWidget(self.main_scroll)

        # Drawing Canvas 생성 (오버레이용으로만 사용)
        self.drawing_canvas = DrawingCanvas(
            parent=self.main_widget,
            user_id=None,  # 세션 연결 시 설정
            pen_color=get_default_pen_color(),  # 첫 번째 프리셋 색상 (파스텔 핑크)
            pen_width=3,
        )
        self.drawing_canvas.hide()  # 화면에 표시하지 않음

        # Drawing Canvas 시그널 연결
        self._connect_drawing_signals()

    def show_start_screen(self):
        """시작 화면 표시"""
        self.start_scroll.show()
        self.main_scroll.hide()

    def show_main_screen(self):
        """메인 화면 표시"""
        self.start_scroll.hide()
        self.main_scroll.show()

        # 서버 주소와 세션 번호 표시
        server_url = self.server_input.text()
        self.server_info_label.setText(f"서버 주소: {server_url}")
        self.session_info_label.setText(f"세션 번호: {self.session_id}")

        # 참여자 색상 정보 표시
        self.update_users_colors_display()

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
                self.set_start_status("오류: 서버 주소를 입력해주세요")
                return

            logger.info("=" * 60)
            logger.info("SESSION CREATION STARTED")
            logger.info(f"Server URL: {server_url}")
            logger.info("=" * 60)

            self.set_start_status("서버에 연결 중...")
            self.disable_start_buttons()

            # WebSocket 클라이언트 생성 및 연결
            logger.info("Step 1: Creating WebSocket client...")
            self.client = WebSocketClient(server_url)
            self.client.set_message_handler(self.handle_message)

            logger.info("Step 2: Connecting to server...")
            await self.client.connect()
            logger.info("Step 2: ✓ Connection established")

            # 세션 생성 요청
            self.set_start_status("세션 생성 중...")
            logger.info("Step 3: Requesting session creation...")
            response = await self.client.create_session("Host")
            logger.info(f"Step 3: ✓ Received response: {response}")

            if response.get("type") == "session_created":
                self.session_id = response["session_id"]
                self.user_id = response["host_id"]
                self.is_host = True
                self.is_connected = True

                logger.info(f"✓ Session created successfully!")
                logger.info(f"  Session ID: {self.session_id}")
                logger.info(f"  Host ID: {self.user_id}")

                # DrawingCanvas에 user_id 설정
                self.drawing_canvas.set_user_id(self.user_id)

                # 참여자 정보로 user_colors 초기화
                participants = response.get("participants", [])
                for participant in participants:
                    user_id = participant.get("user_id")
                    color_str = participant.get("color", "#FF0000")
                    if user_id:
                        color = QColor(color_str)
                        self.drawing_canvas.user_colors[user_id] = color
                        self.drawing_canvas.user_alphas[user_id] = 1.0
                logger.info(f"Initialized user_colors with {len(participants)} participants")

                # 서버 주소 저장
                self.settings.setValue("server_url", server_url)
                logger.info(f"Server URL saved to settings: {server_url}")

                self.session_created.emit(self.session_id, self.user_id)

                # Listen 태스크 시작 (QTimer로 지연시켜 이벤트 루프 블록 방지)
                QTimer.singleShot(100, self._start_listen_task)

                # 메인 화면으로 전환
                self.show_main_screen()
                logger.info("=" * 60)

            elif response.get("type") == "error":
                error_msg = response.get("message", "Unknown error")
                logger.error(f"✗ Server returned error: {error_msg}")
                raise RuntimeError(error_msg)

        except Exception as e:
            logger.error(f"Session creation failed: {e}", exc_info=True)
            self.set_start_status(f"오류: {e}")
            self.error_occurred.emit(str(e))
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
                self.set_start_status("오류: 서버 주소를 입력해주세요")
                return

            if not session_id:
                self.set_start_status("오류: 세션 번호를 입력해주세요")
                return

            logger.info("=" * 60)
            logger.info("SESSION JOIN STARTED")
            logger.info(f"Server URL: {server_url}")
            logger.info(f"Session ID: {session_id}")
            logger.info("=" * 60)

            self.set_start_status("서버에 연결 중...")
            self.disable_start_buttons()

            # WebSocket 클라이언트 생성 및 연결
            logger.info("Step 1: Creating WebSocket client...")
            self.client = WebSocketClient(server_url)
            self.client.set_message_handler(self.handle_message)

            logger.info("Step 2: Connecting to server...")
            await self.client.connect()
            logger.info("Step 2: ✓ Connection established")

            # 세션 참여 요청
            self.set_start_status(f"세션 {session_id}에 참여 중...")
            logger.info(f"Step 3: Requesting to join session {session_id}...")
            response = await self.client.join_session(session_id, "Guest")
            logger.info(f"Step 3: ✓ Received response: {response}")

            if response.get("type") == "session_joined":
                self.session_id = response["session_id"]
                self.user_id = response["user_id"]
                self.is_host = False
                self.is_connected = True

                logger.info(f"✓ Successfully joined session!")
                logger.info(f"  Session ID: {self.session_id}")
                logger.info(f"  User ID: {self.user_id}")

                # DrawingCanvas에 user_id 설정
                self.drawing_canvas.set_user_id(self.user_id)

                # 참여자 정보로 user_colors 초기화
                participants = response.get("participants", [])
                for participant in participants:
                    user_id = participant.get("user_id")
                    color_str = participant.get("color", "#FF0000")
                    if user_id:
                        color = QColor(color_str)
                        self.drawing_canvas.user_colors[user_id] = color
                        self.drawing_canvas.user_alphas[user_id] = 1.0
                logger.info(f"Initialized user_colors with {len(participants)} participants")

                # 서버 주소 저장
                self.settings.setValue("server_url", server_url)
                logger.info(f"Server URL saved to settings: {server_url}")

                self.session_joined.emit(self.session_id, self.user_id)

                # Listen 태스크 시작 (QTimer로 지연시켜 이벤트 루프 블록 방지)
                QTimer.singleShot(100, self._start_listen_task)

                # 메인 화면으로 전환
                self.show_main_screen()
                logger.info("=" * 60)

            elif response.get("type") == "error":
                error_msg = response.get("message", "Unknown error")
                logger.error(f"✗ Server returned error: {error_msg}")
                raise RuntimeError(error_msg)

        except Exception as e:
            logger.error(f"Session join failed: {e}", exc_info=True)
            self.set_start_status(f"오류: {e}")
            self.error_occurred.emit(str(e))
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

    async def _send_color_change(self, data: dict):
        """색상 변경 메시지를 서버로 전송"""
        if self.client and self.is_connected:
            try:
                await self.client.send_message(data)
            except Exception as e:
                logger.error(f"Failed to send color change message: {e}")

    async def handle_message(self, message: dict):
        """서버로부터 받은 메시지 처리

        Args:
            message: 수신한 메시지
        """
        msg_type = message.get("type")
        logger.info(f"Received message: {msg_type}")

        if msg_type == "guest_joined" or msg_type == "participant_joined":
            participant_name = message.get("guest_name") or message.get("participant_name", "Participant")
            user_id = message.get("user_id")
            color_str = message.get("color", "#FF0000")

            # 참여자 색상 정보 추가
            if user_id:
                color = QColor(color_str)
                self.drawing_canvas.user_colors[user_id] = color
                self.drawing_canvas.user_alphas[user_id] = 1.0
                # 오버레이가 있으면 오버레이에도 추가
                if self.is_sharing and self.overlay_window:
                    self.overlay_window.get_canvas().user_colors[user_id] = color
                    self.overlay_window.get_canvas().user_alphas[user_id] = 1.0
                logger.info(f"Added participant {user_id} with color {color_str}")
                # UI 업데이트
                self.update_users_colors_display()

            self.set_status(f"{participant_name} joined the session")

        elif msg_type == "guest_left" or msg_type == "participant_left":
            participant_name = message.get("guest_name") or message.get("participant_name", "Participant")
            user_id = message.get("user_id")

            # 참여자 색상 정보 제거
            if user_id:
                if user_id in self.drawing_canvas.user_colors:
                    del self.drawing_canvas.user_colors[user_id]
                if user_id in self.drawing_canvas.user_alphas:
                    del self.drawing_canvas.user_alphas[user_id]
                # 오버레이가 있으면 오버레이에서도 제거
                if self.is_sharing and self.overlay_window:
                    if user_id in self.overlay_window.get_canvas().user_colors:
                        del self.overlay_window.get_canvas().user_colors[user_id]
                    if user_id in self.overlay_window.get_canvas().user_alphas:
                        del self.overlay_window.get_canvas().user_alphas[user_id]
                logger.info(f"Removed participant {user_id}")
                # UI 업데이트
                self.update_users_colors_display()

            self.set_status(f"{participant_name} left the session")

        elif msg_type == "session_expired":
            reason = message.get("message", "Session expired")
            self.set_status(f"Session expired: {reason}")
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
                self.drawing_canvas.handle_drawing_start(
                    line_id, user_id, message)
                # 오버레이가 있으면 오버레이에도 전달
                if self.is_sharing and self.overlay_window:
                    self.overlay_window.get_canvas().handle_drawing_start(line_id, user_id, message)

        elif msg_type == MessageType.DRAWING_UPDATE.value:
            line_id = message.get("line_id")
            user_id = message.get("user_id")
            if line_id and user_id and user_id != self.user_id:
                self.drawing_canvas.handle_drawing_update(
                    line_id, user_id, message)
                # 오버레이가 있으면 오버레이에도 전달
                if self.is_sharing and self.overlay_window:
                    self.overlay_window.get_canvas().handle_drawing_update(line_id, user_id, message)

        elif msg_type == MessageType.DRAWING_END.value:
            line_id = message.get("line_id")
            user_id = message.get("user_id")
            if line_id and user_id and user_id != self.user_id:
                self.drawing_canvas.handle_drawing_end(line_id, user_id)
                # 오버레이가 있으면 오버레이에도 전달
                if self.is_sharing and self.overlay_window:
                    self.overlay_window.get_canvas().handle_drawing_end(line_id, user_id)

        elif msg_type == MessageType.COLOR_CHANGE.value:
            user_id = message.get("user_id")
            color_str = message.get("color", "#FF0000")
            alpha = message.get("alpha", 1.0)
            if user_id:
                # DrawingCanvas의 user_colors 및 user_alphas 업데이트
                color = QColor(color_str)
                self.drawing_canvas.user_colors[user_id] = color
                self.drawing_canvas.user_alphas[user_id] = alpha
                # 오버레이가 있으면 오버레이에도 업데이트
                if self.is_sharing and self.overlay_window:
                    self.overlay_window.get_canvas().user_colors[user_id] = color
                    self.overlay_window.get_canvas().user_alphas[user_id] = alpha
                # UI 업데이트
                self.update_users_colors_display()
                logger.info(f"User {user_id} changed color to {color_str}, alpha to {alpha:.2f}")

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

    # ========== 색상 설정 메서드 ==========

    def set_pen_color(self, color: QColor):
        """펜 색상 변경 (신규 곡선에만 적용)

        Args:
            color: 새로운 펜 색상
        """
        self.drawing_canvas.set_pen_color(color)
        self.set_status(f"색상 변경: RGB({color.red()}, {color.green()}, {color.blue()})")
        logger.info(f"Pen color changed to RGB({color.red()}, {color.green()}, {color.blue()})")

        # UI 업데이트
        self.update_users_colors_display()

        # 서버에 색상 변경 알림 (알파값 포함)
        if self.client and self.is_connected and self.user_id:
            msg = ColorChangeMessage(
                user_id=self.user_id,
                color=color.name(),
                alpha=self.current_alpha,
            )
            asyncio.create_task(self._send_color_change(msg.to_dict()))

    def on_alpha_changed(self, value: int, label: QLabel):
        """투명도 슬라이더 변경 시 호출

        Args:
            value: 슬라이더 값 (0~100)
            label: 업데이트할 라벨
        """
        alpha = value / 100.0
        self.current_alpha = alpha
        self.drawing_canvas.set_pen_alpha(alpha)
        label.setText(f"투명도: {value}%")
        logger.info(f"Pen alpha changed to {alpha:.2f}")

        # 서버에 알파값 변경 알림 (현재 색상과 함께 전송)
        if self.client and self.is_connected and self.user_id:
            current_color = self.drawing_canvas.pen_color
            msg = ColorChangeMessage(
                user_id=self.user_id,
                color=current_color.name(),
                alpha=alpha,
            )
            asyncio.create_task(self._send_color_change(msg.to_dict()))

    def update_users_colors_display(self):
        """참여자별 색상 정보 UI 업데이트"""
        if not self.is_connected or not self.drawing_canvas:
            self.users_colors_label.setText("")
            return

        # DrawingCanvas의 user_colors에서 정보 가져오기
        user_colors = self.drawing_canvas.user_colors

        if not user_colors:
            self.users_colors_label.setText("")
            return

        # HTML로 색상 인디케이터 생성
        color_indicators = []
        for user_id, color in user_colors.items():
            # 자신인 경우 "나 (ID)"로 표시, 다른 사람은 ID 앞 8자리만 표시
            if user_id == self.user_id:
                user_label = f"나 ({user_id[:8]})"
            else:
                user_label = user_id[:8]
            # 색상 원 표시
            color_html = f'<span style="color: {color.name()};">●</span> {user_label}'
            color_indicators.append(color_html)

        # HTML 문자열로 조합
        display_text = "참여자: " + " | ".join(color_indicators)
        self.users_colors_label.setText(display_text)

    # ========== 오버레이 모드 메서드 ==========

    def toggle_overlay(self):
        """그림 영역 생성 (버튼에서 호출)"""
        self.create_overlay()

    def create_overlay(self):
        """그림 영역 생성"""
        from .overlay_window import OverlayWindow

        try:
            # 오버레이 윈도우 생성
            self.overlay_window = OverlayWindow(
                user_id=self.user_id,
                pen_color=get_default_pen_color(),  # 첫 번째 프리셋 색상 (파스텔 핑크)
            )

            # DrawingCanvas 시그널 연결
            canvas = self.overlay_window.get_canvas()
            canvas.drawing_started.connect(self._on_drawing_started)
            canvas.drawing_updated.connect(self._on_drawing_updated)
            canvas.drawing_ended.connect(self._on_drawing_ended)

            # 메인 캔버스의 user_colors를 오버레이 캔버스에 복사
            canvas.user_colors = self.drawing_canvas.user_colors.copy()
            canvas.user_alphas = self.drawing_canvas.user_alphas.copy()

            # 오버레이 시그널 연결
            self.overlay_window.drawing_mode_changed.connect(
                self.on_drawing_mode_changed)

            # UI 상태 전환: 생성 버튼 숨기고 컨트롤 위젯 표시
            self.setup_overlay_button.hide()
            self.overlay_control_widget.show()
            self.toggle_drawing_button.setEnabled(True)
            self.clear_drawings_button.setEnabled(True)

            self.set_status("그림 영역이 생성되었습니다. 크기를 조정하세요.")

            # 창 표시
            self.overlay_window.show()

            # 상태 업데이트
            self.is_sharing = True

            # 즉시 리사이즈 모드 활성화
            self.overlay_window.set_resize_mode(True)
            self.resize_overlay_button.setText("그림 영역 크기 조정 완료 (Enter)")

            logger.info("Overlay created and resize mode enabled")

        except Exception as e:
            logger.error(f"Failed to create overlay: {e}", exc_info=True)
            self.set_status(f"오류: 그림 영역 생성 실패: {e}")
            self.stop_overlay()

    def stop_overlay(self):
        """그림 영역 삭제"""
        if self.overlay_window:
            try:
                self.overlay_window.close()
            except Exception as e:
                logger.error(f"Error closing overlay: {e}")
            self.overlay_window = None

        # UI 상태 전환: 컨트롤 위젯 숨기고 생성 버튼 표시
        self.overlay_control_widget.hide()
        self.setup_overlay_button.show()

        # 버튼 상태 리셋
        self.is_sharing = False
        self.resize_overlay_button.setText("그림 영역 크기 조정")
        self.toggle_drawing_button.setEnabled(False)
        self.toggle_drawing_button.setText("그리기 활성화")
        self.clear_drawings_button.setEnabled(False)

        self.set_status("그림 영역이 삭제되었습니다")

        logger.info("Overlay stopped")

    def toggle_resize_mode(self):
        """그림 영역 크기 조정 토글"""
        if self.overlay_window:
            current = self.overlay_window.is_resize_mode()
            self.overlay_window.set_resize_mode(not current)

            # Update button text
            if not current:
                self.resize_overlay_button.setText("그림 영역 크기 조정 완료 (Enter)")
                self.set_status("크기 조정 모드: 창 테두리를 드래그하여 조정하세요 (Enter로 완료)")
                logger.info("Resize mode enabled")
            else:
                self.resize_overlay_button.setText("그림 영역 크기 조정")
                self.set_status("그림 영역 준비 완료. 그리기 활성화 버튼을 누르세요")
                logger.info("Resize mode disabled")

    def toggle_drawing_mode(self):
        """그리기 모드 토글"""
        if self.overlay_window:
            current = self.overlay_window.is_drawing_enabled()
            self.overlay_window.set_drawing_enabled(not current)

    def on_drawing_mode_changed(self, enabled: bool):
        """그리기 모드 변경 핸들러"""
        if enabled:
            self.toggle_drawing_button.setText("그리기 비활성화 (ESC로 비활성화)")
            # 테두리에 불빛 효과 추가 (배경색 없음)
            self.toggle_drawing_button.setStyleSheet(
                """
                QPushButton {
                    border: 3px solid #4CAF50;
                    border-radius: 4px;
                }
                """
            )
            self.set_status("그리기 활성화됨 (ESC 키로 비활성화 가능)")
            logger.info("Drawing mode enabled")
        else:
            self.toggle_drawing_button.setText("그리기 활성화")
            # 일반 스타일로 되돌리기
            self.toggle_drawing_button.setStyleSheet("")
            self.set_status("그리기 비활성화됨 (클릭이 아래로 전달됨)")
            logger.info("Drawing mode disabled")

    def clear_overlay_drawings(self):
        """그림 모두 지우기"""
        if self.overlay_window:
            self.overlay_window.get_canvas().clear_all_drawings()
            self.set_status("모든 그림이 지워졌습니다")
            logger.info("All drawings cleared")

    # ================================================================

    async def disconnect(self):
        """서버 연결 종료"""
        # 오버레이가 활성화되어 있으면 종료
        if self.is_sharing:
            self.stop_overlay()

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
