"""WebSocket 서버 구현"""

import asyncio
import json
import logging
import os
from typing import Dict, Optional, Set
from datetime import datetime

import websockets
from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosed

from .session import SessionManager
from screen_party_common import Guest

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ScreenPartyServer:
    """Screen Party WebSocket 서버"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.session_manager = SessionManager()
        # user_id -> websocket 매핑
        self.clients: Dict[str, ServerConnection] = {}
        # websocket -> user_id 역매핑 (빠른 조회용)
        self.websocket_to_user: Dict[ServerConnection, str] = {}

    async def start(self):
        """서버 시작"""
        # 백그라운드 cleanup 태스크 시작
        cleanup_task = asyncio.create_task(
            self.session_manager.start_cleanup_task(interval_minutes=5)
        )

        logger.info(f"Starting Screen Party server on {self.host}:{self.port}")

        async with websockets.serve(self.handle_client, self.host, self.port):
            await asyncio.Future()  # run forever

    async def handle_client(self, websocket: ServerConnection):
        """클라이언트 연결 처리"""
        user_id = None
        try:
            logger.info(f"New client connected: {websocket.remote_address}")

            async for message in websocket:
                try:
                    data = json.loads(message)
                    user_id = await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    await self.send_error(websocket, "Invalid JSON format")
                except Exception as e:
                    logger.error(f"Error handling message: {e}", exc_info=True)
                    await self.send_error(websocket, str(e))

        except ConnectionClosed:
            logger.info(f"Client disconnected: {websocket.remote_address}")
        finally:
            # 연결 종료 시 정리
            if user_id:
                await self.cleanup_client(user_id)

    async def handle_message(self, websocket: ServerConnection, data: dict) -> Optional[str]:
        """메시지 라우팅 및 처리

        Returns:
            user_id (if this client has one)
        """
        msg_type = data.get("type")

        if not msg_type:
            await self.send_error(websocket, "Missing 'type' field")
            return None

        # 현재 클라이언트의 user_id 조회
        user_id = self.websocket_to_user.get(websocket)

        # 메시지 타입별 라우팅
        if msg_type == "create_session":
            user_id = await self.handle_create_session(websocket, data)
        elif msg_type == "join_session":
            user_id = await self.handle_join_session(websocket, data)
        elif msg_type == "ping":
            await self.handle_ping(websocket)
        elif msg_type in ("line_start", "line_update", "line_end", "line_remove"):
            if user_id:
                await self.handle_drawing_message(websocket, user_id, data)
            else:
                await self.send_error(websocket, "Not authenticated")
        else:
            await self.send_error(websocket, f"Unknown message type: {msg_type}")

        return user_id

    async def handle_create_session(self, websocket: ServerConnection, data: dict) -> str:
        """세션 생성 처리 (호스트)"""
        host_name = data.get("host_name", "Host")

        # 세션 생성
        session = self.session_manager.create_session(host_name=host_name)
        host_id = session.host_id

        # 클라이언트 등록
        self.clients[host_id] = websocket
        self.websocket_to_user[websocket] = host_id

        logger.info(f"Session created: {session.session_id} by {host_name} ({host_id})")

        # 응답 전송
        await websocket.send(
            json.dumps(
                {
                    "type": "session_created",
                    "session_id": session.session_id,
                    "host_id": host_id,
                    "host_name": host_name,
                }
            )
        )

        return host_id

    async def handle_join_session(self, websocket: ServerConnection, data: dict) -> str:
        """세션 참여 처리 (게스트)"""
        session_id = data.get("session_id")
        guest_name = data.get("guest_name", "Guest")

        if not session_id:
            await self.send_error(websocket, "Missing session_id")
            return None

        # 세션 조회
        session = self.session_manager.get_session(session_id)
        if not session:
            await self.send_error(websocket, f"Session not found: {session_id}")
            return None

        if not session.is_active:
            await self.send_error(websocket, f"Session is not active: {session_id}")
            return None

        # 세션에 게스트 추가 (Guest 객체를 반환함)
        guest = self.session_manager.add_guest(session_id, guest_name)
        if not guest:
            await self.send_error(websocket, "Failed to join session")
            return None

        guest_id = guest.user_id

        # 클라이언트 등록
        self.clients[guest_id] = websocket
        self.websocket_to_user[websocket] = guest_id

        logger.info(f"Guest {guest_name} ({guest_id}) joined session {session_id}")

        # 게스트에게 응답 전송
        await websocket.send(
            json.dumps(
                {
                    "type": "session_joined",
                    "session_id": session_id,
                    "user_id": guest_id,
                    "guest_name": guest_name,
                    "host_name": session.host_name,
                }
            )
        )

        # 세션 내 다른 클라이언트들에게 알림
        await self.broadcast(
            session_id,
            {"type": "guest_joined", "user_id": guest_id, "guest_name": guest_name},
            exclude_user_id=guest_id,
        )

        return guest_id

    async def handle_ping(self, websocket: ServerConnection):
        """핑 처리"""
        await websocket.send(json.dumps({"type": "pong"}))

    async def handle_drawing_message(self, websocket: ServerConnection, user_id: str, data: dict):
        """드로잉 메시지 처리 (line_start, line_update, line_end, line_remove)"""
        # 사용자가 속한 세션 찾기
        session_id = self.find_user_session(user_id)

        if not session_id:
            await self.send_error(websocket, "Not in any session")
            return

        # 세션 활동 업데이트
        session = self.session_manager.get_session(session_id)
        if session:
            session.last_activity = datetime.now()

        # 세션 내 모든 클라이언트에게 브로드캐스트 (송신자 제외)
        await self.broadcast(session_id, data, exclude_user_id=user_id)

    async def broadcast(
        self, session_id: str, message: dict, exclude_user_id: Optional[str] = None
    ):
        """세션 내 모든 클라이언트에게 메시지 브로드캐스트

        Args:
            session_id: 세션 ID
            message: 전송할 메시지 (dict)
            exclude_user_id: 제외할 사용자 ID (optional)
        """
        # sessions dict에서 직접 가져오기 (is_active 체크 안 함)
        session = self.session_manager.sessions.get(session_id)
        if not session:
            return

        # 세션 내 모든 사용자 ID 수집
        user_ids = {session.host_id}
        user_ids.update(session.guests.keys())

        # 제외할 사용자 제거
        if exclude_user_id:
            user_ids.discard(exclude_user_id)

        # 메시지 전송
        message_json = json.dumps(message)
        for user_id in user_ids:
            websocket = self.clients.get(user_id)
            if websocket:
                try:
                    await websocket.send(message_json)
                except ConnectionClosed:
                    logger.warning(f"Failed to send to {user_id}: connection closed")

    async def send_error(self, websocket: ServerConnection, message: str):
        """에러 메시지 전송"""
        logger.warning(f"Sending error: {message}")
        try:
            await websocket.send(json.dumps({"type": "error", "message": message}))
        except ConnectionClosed:
            logger.warning("Failed to send error: connection closed")

    def find_user_session(self, user_id: str) -> Optional[str]:
        """사용자가 속한 세션 ID 찾기"""
        for session_id, session in self.session_manager.sessions.items():
            if session.host_id == user_id or user_id in session.guests:
                return session_id
        return None

    async def cleanup_client(self, user_id: str):
        """클라이언트 연결 종료 시 정리"""
        logger.info(f"Cleaning up client: {user_id}")

        # 세션 찾기 (직접 sessions dict에서 찾기 - is_active 체크 안 함)
        session_id = None
        session = None
        for sid, sess in self.session_manager.sessions.items():
            if sess.host_id == user_id or user_id in sess.guests:
                session_id = sid
                session = sess
                break

        if session_id and session:
            # 호스트가 나간 경우 세션 만료
            if session.host_id == user_id:
                logger.info(f"Host left, expiring session: {session_id}")

                # 먼저 게스트들에게 알림 (세션 만료 전에)
                await self.broadcast(
                    session_id, {"type": "session_expired", "message": "Host disconnected"}
                )

                # 그 다음 세션 만료
                self.session_manager.expire_session(session_id)
            # 게스트가 나간 경우
            else:
                guest = session.guests.get(user_id)
                if guest:
                    self.session_manager.remove_guest(session_id, user_id)
                    logger.info(f"Guest {guest.name} left session {session_id}")

                    # 세션 내 다른 클라이언트들에게 알림
                    await self.broadcast(
                        session_id,
                        {"type": "guest_left", "user_id": user_id, "guest_name": guest.name},
                    )

        # 클라이언트 제거
        websocket = self.clients.pop(user_id, None)
        if websocket:
            self.websocket_to_user.pop(websocket, None)


async def main():
    """서버 진입점"""
    host = os.getenv("SCREEN_PARTY_HOST", "0.0.0.0")
    port = int(os.getenv("SCREEN_PARTY_PORT", "8765"))

    server = ScreenPartyServer(host=host, port=port)
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
