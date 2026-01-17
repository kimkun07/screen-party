"""세션 관리 (생성/참여) 관련 메서드"""

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor
from screen_party_common.models import DEFAULT_COLOR

from ..network.client import WebSocketClient

if TYPE_CHECKING:
    from .main_window import MainWindow

logger = logging.getLogger(__name__)


class SessionManager:
    """세션 생성/참여 로직을 담당하는 헬퍼 클래스"""

    def __init__(self, window: "MainWindow"):
        self.window = window

    async def on_create_session(self):
        """세션 생성 (호스트)"""
        try:
            server_url = self.window.server_input.text().strip()
            if not server_url:
                self.window.set_start_status("오류: 서버 주소를 입력해주세요")
                return

            logger.info("=" * 60)
            logger.info("SESSION CREATION STARTED")
            logger.info(f"Server URL: {server_url}")
            logger.info("=" * 60)

            self.window.set_start_status("서버에 연결 중...")
            self.window.state.set_start_buttons_enabled(False)

            # WebSocket 클라이언트 생성 및 연결
            logger.info("Step 1: Creating WebSocket client...")
            self.window.client = WebSocketClient(server_url)
            self.window.client.set_message_handler(self.window.handle_message)

            logger.info("Step 2: Connecting to server...")
            await self.window.client.connect()
            logger.info("Step 2: ✓ Connection established")

            # 세션 생성 요청
            self.window.set_start_status("세션 생성 중...")
            logger.info("Step 3: Requesting session creation...")
            response = await self.window.client.create_session("Host")
            logger.info(f"Step 3: ✓ Received response: {response}")

            if response.get("type") == "session_created":
                session_id = response["session_id"]
                user_id = response["host_id"]

                logger.info("✓ Session created successfully!")
                logger.info(f"  Session ID: {session_id}")
                logger.info(f"  Host ID: {user_id}")

                # State 업데이트
                self.window.state.set_connected(session_id, user_id, server_url)

                # Canvas Manager에 user_id 설정
                self.window.canvas_manager.set_user_id(user_id)

                # 참여자 정보 초기화
                participants = response.get("participants", [])
                self.window.state.initialize_participants(participants)
                for participant in participants:
                    pid = participant.get("user_id")
                    color_str = participant.get("color", DEFAULT_COLOR)
                    if pid:
                        self.window.canvas_manager.add_participant(pid, QColor(color_str), alpha=1.0)
                logger.info(f"Initialized participants with {len(participants)} users")

                # 서버 주소 저장
                self.window.settings.setValue("server_url", server_url)
                logger.info(f"Server URL saved to settings: {server_url}")

                self.window.session_created.emit(session_id, user_id)

                # Listen 태스크 시작 (QTimer로 지연시켜 이벤트 루프 블록 방지)
                QTimer.singleShot(100, self.window._start_listen_task)

                # 메인 화면으로 전환
                self.window.show_main_screen()
                logger.info("=" * 60)

            elif response.get("type") == "error":
                error_msg = response.get("message", "Unknown error")
                logger.error(f"✗ Server returned error: {error_msg}")
                raise RuntimeError(error_msg)

        except Exception as e:
            logger.error(f"Session creation failed: {e}", exc_info=True)
            self.window.set_start_status(f"오류: {e}")
            self.window.error_occurred.emit(str(e))
            self.window.state.set_start_buttons_enabled(True)
            if self.window.client:
                await self.window.client.disconnect()
                self.window.client = None

    async def on_join_session(self):
        """세션 참여 (게스트)"""
        try:
            server_url = self.window.server_input.text().strip()
            session_id = self.window.session_input.text().strip().upper()

            if not server_url:
                self.window.set_start_status("오류: 서버 주소를 입력해주세요")
                return

            if not session_id:
                self.window.set_start_status("오류: 세션 번호를 입력해주세요")
                return

            logger.info("=" * 60)
            logger.info("SESSION JOIN STARTED")
            logger.info(f"Server URL: {server_url}")
            logger.info(f"Session ID: {session_id}")
            logger.info("=" * 60)

            self.window.set_start_status("서버에 연결 중...")
            self.window.state.set_start_buttons_enabled(False)

            # WebSocket 클라이언트 생성 및 연결
            logger.info("Step 1: Creating WebSocket client...")
            self.window.client = WebSocketClient(server_url)
            self.window.client.set_message_handler(self.window.handle_message)

            logger.info("Step 2: Connecting to server...")
            await self.window.client.connect()
            logger.info("Step 2: ✓ Connection established")

            # 세션 참여 요청
            self.window.set_start_status(f"세션 {session_id}에 참여 중...")
            logger.info(f"Step 3: Requesting to join session {session_id}...")
            response = await self.window.client.join_session(session_id, "Guest")
            logger.info(f"Step 3: ✓ Received response: {response}")

            if response.get("type") == "session_joined":
                session_id = response["session_id"]
                user_id = response["user_id"]

                logger.info("✓ Successfully joined session!")
                logger.info(f"  Session ID: {session_id}")
                logger.info(f"  User ID: {user_id}")

                # State 업데이트
                self.window.state.set_connected(session_id, user_id, server_url)

                # Canvas Manager에 user_id 설정
                self.window.canvas_manager.set_user_id(user_id)

                # 참여자 정보 초기화
                participants = response.get("participants", [])
                self.window.state.initialize_participants(participants)
                for participant in participants:
                    pid = participant.get("user_id")
                    color_str = participant.get("color", DEFAULT_COLOR)
                    if pid:
                        self.window.canvas_manager.add_participant(pid, QColor(color_str), alpha=1.0)
                logger.info(f"Initialized participants with {len(participants)} users")

                # 서버 주소 저장
                self.window.settings.setValue("server_url", server_url)
                logger.info(f"Server URL saved to settings: {server_url}")

                self.window.session_joined.emit(session_id, user_id)

                # Listen 태스크 시작 (QTimer로 지연시켜 이벤트 루프 블록 방지)
                QTimer.singleShot(100, self.window._start_listen_task)

                # 메인 화면으로 전환
                self.window.show_main_screen()
                logger.info("=" * 60)

            elif response.get("type") == "error":
                error_msg = response.get("message", "Unknown error")
                logger.error(f"✗ Server returned error: {error_msg}")
                raise RuntimeError(error_msg)

        except Exception as e:
            logger.error(f"Session join failed: {e}", exc_info=True)
            self.window.set_start_status(f"오류: {e}")
            self.window.error_occurred.emit(str(e))
            self.window.state.set_start_buttons_enabled(True)
            if self.window.client:
                await self.window.client.disconnect()
                self.window.client = None
