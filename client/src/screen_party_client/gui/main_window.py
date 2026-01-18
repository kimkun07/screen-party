"""메인 윈도우 GUI"""

import asyncio
import logging
import sys
from typing import Optional

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QSettings

from ..network.client import WebSocketClient
from ..drawing.canvas_manager import CanvasManager
from ..network.message_handler import MessageHandler
from .state import AppState
from .ui_builder import UIBuilder
from .session_manager import SessionManager
from .overlay_manager import OverlayManager
from .drawing_handler import DrawingHandler

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

        # Application state (single source of truth)
        self.state = AppState()

        # Network client
        self.client: Optional[WebSocketClient] = None
        self.listen_task: Optional[asyncio.Task] = None

        # Canvas manager (created after UI init)
        self.canvas_manager: Optional[CanvasManager] = None

        # Message handler (created after canvas manager)
        self.message_handler: Optional[MessageHandler] = None

        # Helper classes
        self.ui_builder = UIBuilder(self)
        self.session_manager = SessionManager(self)
        self.overlay_manager = OverlayManager(self)
        self.drawing_handler = DrawingHandler(self)

        # UI 초기화
        self.init_ui()

        # State observer 등록 (UI 업데이트)
        self.state.add_observer(self._on_state_changed)

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
        self.ui_builder.create_start_screen()
        self.ui_builder.create_main_screen()

        # 시작 화면 표시
        self.show_start_screen()

    def _on_state_changed(self):
        """State 변경 시 호출되는 Observer 메서드

        이 메서드는 state가 변경될 때마다 호출되어 UI를 업데이트합니다.
        모든 UI 업데이트는 이 메서드에서 state를 읽어서 declarative하게 처리합니다.
        """
        self.update_ui_from_state()

    def update_ui_from_state(self):
        """State를 읽어서 모든 UI 요소를 업데이트

        이 메서드는 state를 읽어서 UI를 업데이트하는 유일한 장소입니다.
        비즈니스 로직에서는 state만 변경하고, UI는 이 메서드에서만 업데이트합니다.
        """
        # === 화면 전환 ===
        if self.state.current_screen == "main" and not self.main_scroll.isVisible():
            self._show_main_screen_ui()
        elif self.state.current_screen == "start" and not self.start_scroll.isVisible():
            self._show_start_screen_ui()

        # === 상태 메시지 ===
        if self.state.is_connected:
            self.status_label.setText(self.state.status_message)

        # === 참여자 정보 ===
        self.update_users_colors_display()

        # === 시작 화면 버튼 상태 ===
        self.create_button.setEnabled(self.state.start_buttons_enabled)
        self.join_button.setEnabled(
            self.state.start_buttons_enabled and len(self.session_input.text().strip()) > 0
        )
        self.server_input.setEnabled(self.state.start_buttons_enabled)
        self.session_input.setEnabled(self.state.start_buttons_enabled)

        # === 오버레이 생성/삭제 버튼 ===
        if self.state.overlay_created:
            self.setup_overlay_button.hide()
            self.overlay_control_widget.show()
            self.toggle_drawing_button.setEnabled(True)
            self.clear_drawings_button.setEnabled(True)
        else:
            self.overlay_control_widget.hide()
            self.setup_overlay_button.show()
            self.toggle_drawing_button.setEnabled(False)
            self.clear_drawings_button.setEnabled(False)

        # === 리사이즈 모드 버튼 ===
        if self.state.resize_mode_active:
            self.resize_overlay_button.setText("그림 영역 크기 조정 완료 (Enter)")
        else:
            self.resize_overlay_button.setText("그림 영역 크기 조정")

        # === 그리기 모드 버튼 ===
        if self.state.drawing_mode_active:
            self.toggle_drawing_button.setText("그리기 비활성화 (ESC로 비활성화)")
            self.toggle_drawing_button.setStyleSheet(
                """
                QPushButton {
                    border: 3px solid #4CAF50;
                    border-radius: 4px;
                }
                """
            )
        else:
            self.toggle_drawing_button.setText("그리기 활성화")
            self.toggle_drawing_button.setStyleSheet("")

    def show_start_screen(self):
        """시작 화면 표시 (상태 업데이트)"""
        self.state.set_screen("start")

    def _show_start_screen_ui(self):
        """시작 화면 UI 표시 (실제 UI 업데이트)"""
        self.start_scroll.show()
        self.main_scroll.hide()

    def show_main_screen(self):
        """메인 화면 표시 (상태 업데이트)"""
        self.state.set_screen("main")

    def _show_main_screen_ui(self):
        """메인 화면 UI 표시 (실제 UI 업데이트)"""
        self.start_scroll.hide()
        self.main_scroll.show()

        # 서버 주소와 세션 번호 표시
        self.server_info_label.setText(f"서버 주소: {self.state.server_url}")
        self.session_info_label.setText(f"세션 번호: {self.state.session_id}")

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
        self.state.set_status("서버 주소가 클립보드에 복사되었습니다")

    def copy_session_id(self):
        """세션 번호를 클립보드에 복사"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.state.session_id)
        self.state.set_status("세션 번호가 클립보드에 복사되었습니다")

    async def handle_message(self, message: dict):
        """서버로부터 받은 메시지 처리 (MessageHandler에 위임)

        Args:
            message: 수신한 메시지
        """
        if self.message_handler:
            await self.message_handler.handle_message(message)

    def set_start_status(self, status: str):
        """시작 화면 상태 메시지 설정

        Args:
            status: 상태 메시지
        """
        self.start_status_label.setText(status)
        logger.info(f"Start Status: {status}")

    def update_users_colors_display(self):
        """참여자별 색상 정보 UI 업데이트"""
        if not self.state.is_connected:
            self.users_colors_label.setText("")
            return

        # State에서 user_colors 가져오기
        user_colors = self.state.user_colors

        if not user_colors:
            self.users_colors_label.setText("")
            return

        # HTML로 색상 인디케이터 생성
        color_indicators = []
        for user_id, color in user_colors.items():
            # 자신인 경우 "나 (ID)"로 표시, 다른 사람은 ID 앞 8자리만 표시
            if user_id == self.state.user_id:
                user_label = f"나 ({user_id[:8]})"
            else:
                user_label = user_id[:8]
            # 색상 원 표시
            color_html = f'<span style="color: {color.name()};">●</span> {user_label}'
            color_indicators.append(color_html)

        # HTML 문자열로 조합
        display_text = "참여자: " + " | ".join(color_indicators)
        self.users_colors_label.setText(display_text)

    async def disconnect(self):
        """서버 연결 종료"""
        # 오버레이가 활성화되어 있으면 종료
        if self.state.is_sharing:
            self.overlay_manager.stop_overlay()

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

        # State 초기화
        self.state.set_disconnected()
        self.state.set_screen("start")
        self.state.set_start_buttons_enabled(True)

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
