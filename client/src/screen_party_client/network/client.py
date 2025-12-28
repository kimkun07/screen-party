"""WebSocket 클라이언트"""

import json
import logging
from typing import Optional, Callable
import asyncio

import websockets
from websockets.asyncio.client import ClientConnection
from websockets.exceptions import ConnectionClosed, WebSocketException

logger = logging.getLogger(__name__)


class WebSocketClient:
    """Screen Party WebSocket 클라이언트"""

    def __init__(self, url: str = "ws://localhost:8765"):
        self.url = url
        self.websocket: Optional[ClientConnection] = None
        self.running = False
        self.message_handler: Optional[Callable] = None

    async def connect(self):
        """서버 연결"""
        try:
            self.websocket = await websockets.connect(self.url)
            self.running = True
            logger.info(f"Connected to {self.url}")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise

    async def disconnect(self):
        """서버 연결 종료"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            logger.info("Disconnected from server")

    async def send_message(self, message: dict):
        """메시지 전송

        Args:
            message: 전송할 메시지 (dict)
        """
        if not self.websocket:
            raise RuntimeError("Not connected to server")

        message_json = json.dumps(message)
        await self.websocket.send(message_json)
        logger.debug(f"Sent: {message}")

    async def receive_message(self) -> dict:
        """메시지 수신

        Returns:
            수신한 메시지 (dict)
        """
        if not self.websocket:
            raise RuntimeError("Not connected to server")

        message_json = await self.websocket.recv()
        message = json.loads(message_json)
        logger.debug(f"Received: {message}")
        return message

    async def listen(self):
        """메시지 수신 루프 (백그라운드 태스크용)"""
        try:
            while self.running and self.websocket:
                try:
                    message = await self.receive_message()
                    if self.message_handler:
                        await self.message_handler(message)
                except ConnectionClosed:
                    logger.info("Connection closed by server")
                    break
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    if self.running:
                        continue
                    else:
                        break
        finally:
            self.running = False

    def set_message_handler(self, handler: Callable):
        """메시지 핸들러 설정

        Args:
            handler: 메시지를 받았을 때 호출될 async 함수
        """
        self.message_handler = handler

    # Convenience methods for common operations
    async def create_session(self, host_name: str) -> dict:
        """세션 생성 요청

        Args:
            host_name: 호스트 이름

        Returns:
            서버 응답 메시지
        """
        await self.send_message({
            "type": "create_session",
            "host_name": host_name
        })
        return await self.receive_message()

    async def join_session(self, session_id: str, guest_name: str) -> dict:
        """세션 참여 요청

        Args:
            session_id: 세션 ID
            guest_name: 게스트 이름

        Returns:
            서버 응답 메시지
        """
        await self.send_message({
            "type": "join_session",
            "session_id": session_id,
            "guest_name": guest_name
        })
        return await self.receive_message()

    async def ping(self) -> dict:
        """핑 요청

        Returns:
            서버 응답 메시지 (pong)
        """
        await self.send_message({"type": "ping"})
        return await self.receive_message()
