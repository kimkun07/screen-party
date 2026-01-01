"""WebSocket 서버 유닛 테스트"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from screen_party_server.server import ScreenPartyServer
from screen_party_common import Session, Guest


@pytest.fixture
def server():
    """테스트용 서버 인스턴스"""
    return ScreenPartyServer(host="localhost", port=8765)


@pytest.fixture
def mock_websocket():
    """Mock WebSocket"""
    ws = AsyncMock()
    ws.remote_address = ("127.0.0.1", 12345)
    return ws


class TestScreenPartyServer:
    """ScreenPartyServer 테스트"""

    def test_server_initialization(self, server):
        """서버 초기화 테스트"""
        assert server.host == "localhost"
        assert server.port == 8765
        assert server.session_manager is not None
        assert len(server.clients) == 0
        assert len(server.websocket_to_user) == 0

    @pytest.mark.asyncio
    async def test_create_session(self, server, mock_websocket):
        """세션 생성 메시지 처리 테스트"""
        data = {
            "type": "create_session",
            "host_name": "TestHost"
        }

        user_id = await server.handle_create_session(mock_websocket, data)

        # 사용자 ID 생성 확인
        assert user_id is not None

        # 클라이언트 등록 확인
        assert user_id in server.clients
        assert server.clients[user_id] == mock_websocket
        assert server.websocket_to_user[mock_websocket] == user_id

        # 응답 전송 확인
        mock_websocket.send.assert_called_once()
        response = json.loads(mock_websocket.send.call_args[0][0])
        assert response["type"] == "session_created"
        assert "session_id" in response
        assert response["host_id"] == user_id
        assert response["host_name"] == "TestHost"

        # 세션 매니저에 세션 생성 확인
        session_id = response["session_id"]
        session = server.session_manager.get_session(session_id)
        assert session is not None
        assert session.host_id == user_id
        assert session.host_name == "TestHost"

    @pytest.mark.asyncio
    async def test_join_session(self, server, mock_websocket):
        """세션 참여 메시지 처리 테스트"""
        # 먼저 세션 생성
        session = server.session_manager.create_session("Host")
        host_ws = AsyncMock()
        server.clients[session.host_id] = host_ws
        server.websocket_to_user[host_ws] = session.host_id

        # 게스트 참여
        guest_ws = AsyncMock()
        data = {
            "type": "join_session",
            "session_id": session.session_id,
            "guest_name": "TestGuest"
        }

        user_id = await server.handle_join_session(guest_ws, data)

        # 사용자 ID 생성 확인
        assert user_id is not None

        # 클라이언트 등록 확인
        assert user_id in server.clients
        assert server.clients[user_id] == guest_ws
        assert server.websocket_to_user[guest_ws] == user_id

        # 게스트에게 응답 전송 확인
        guest_ws.send.assert_called()
        calls = [json.loads(call[0][0]) for call in guest_ws.send.call_args_list]
        join_response = next(msg for msg in calls if msg["type"] == "session_joined")
        assert join_response["session_id"] == session.session_id
        assert join_response["user_id"] == user_id
        assert join_response["guest_name"] == "TestGuest"

        # 호스트에게 알림 전송 확인
        host_ws.send.assert_called()
        host_calls = [json.loads(call[0][0]) for call in host_ws.send.call_args_list]
        guest_joined = next(msg for msg in host_calls if msg["type"] == "guest_joined")
        assert guest_joined["user_id"] == user_id
        assert guest_joined["guest_name"] == "TestGuest"

        # 세션에 게스트 추가 확인
        updated_session = server.session_manager.get_session(session.session_id)
        assert user_id in updated_session.guests

    @pytest.mark.asyncio
    async def test_join_nonexistent_session(self, server, mock_websocket):
        """존재하지 않는 세션 참여 시도 테스트"""
        data = {
            "type": "join_session",
            "session_id": "INVALID",
            "guest_name": "TestGuest"
        }

        user_id = await server.handle_join_session(mock_websocket, data)

        # 참여 실패 확인
        assert user_id is None

        # 에러 메시지 전송 확인
        mock_websocket.send.assert_called_once()
        response = json.loads(mock_websocket.send.call_args[0][0])
        assert response["type"] == "error"
        assert "not found" in response["message"].lower()

    @pytest.mark.asyncio
    async def test_ping_pong(self, server, mock_websocket):
        """핑/퐁 테스트"""
        await server.handle_ping(mock_websocket)

        mock_websocket.send.assert_called_once()
        response = json.loads(mock_websocket.send.call_args[0][0])
        assert response["type"] == "pong"

    @pytest.mark.asyncio
    async def test_broadcast(self, server):
        """브로드캐스트 테스트"""
        # 세션 생성
        session = server.session_manager.create_session("Host")

        # 호스트 WebSocket 등록
        host_ws = AsyncMock()
        server.clients[session.host_id] = host_ws
        server.websocket_to_user[host_ws] = session.host_id

        # 게스트 2명 추가
        guest1 = server.session_manager.add_guest(session.session_id, "Guest1")
        guest2 = server.session_manager.add_guest(session.session_id, "Guest2")

        guest1_ws = AsyncMock()
        guest2_ws = AsyncMock()
        server.clients[guest1.user_id] = guest1_ws
        server.clients[guest2.user_id] = guest2_ws
        server.websocket_to_user[guest1_ws] = guest1.user_id
        server.websocket_to_user[guest2_ws] = guest2.user_id

        # 브로드캐스트
        message = {"type": "test", "data": "hello"}
        await server.broadcast(session.session_id, message)

        # 모든 클라이언트가 메시지를 받았는지 확인
        host_ws.send.assert_called_once()
        guest1_ws.send.assert_called_once()
        guest2_ws.send.assert_called_once()

        # 메시지 내용 확인
        for ws in [host_ws, guest1_ws, guest2_ws]:
            response = json.loads(ws.send.call_args[0][0])
            assert response["type"] == "test"
            assert response["data"] == "hello"

    @pytest.mark.asyncio
    async def test_broadcast_exclude_user(self, server):
        """특정 사용자 제외 브로드캐스트 테스트"""
        # 세션 생성
        session = server.session_manager.create_session("Host")

        # 호스트 WebSocket 등록
        host_ws = AsyncMock()
        server.clients[session.host_id] = host_ws

        # 게스트 추가
        guest = server.session_manager.add_guest(session.session_id, "Guest1")
        guest_ws = AsyncMock()
        server.clients[guest.user_id] = guest_ws

        # 게스트 제외하고 브로드캐스트
        message = {"type": "test"}
        await server.broadcast(session.session_id, message, exclude_user_id=guest.user_id)

        # 호스트만 메시지를 받았는지 확인
        host_ws.send.assert_called_once()
        guest_ws.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_find_user_session(self, server):
        """사용자 세션 찾기 테스트"""
        # 세션 생성
        session = server.session_manager.create_session("Host")
        host_id = session.host_id

        # 게스트 추가
        guest = server.session_manager.add_guest(session.session_id, "Guest1")

        # 호스트 세션 찾기
        assert server.find_user_session(host_id) == session.session_id

        # 게스트 세션 찾기
        assert server.find_user_session(guest.user_id) == session.session_id

        # 존재하지 않는 사용자
        assert server.find_user_session("nonexistent") is None

    @pytest.mark.asyncio
    async def test_cleanup_client_host(self, server):
        """호스트 연결 종료 시 세션 만료 테스트"""
        # 세션 생성
        session = server.session_manager.create_session("Host")
        host_id = session.host_id

        # 호스트 WebSocket 등록
        host_ws = AsyncMock()
        server.clients[host_id] = host_ws
        server.websocket_to_user[host_ws] = host_id

        # 게스트 추가
        guest = server.session_manager.add_guest(session.session_id, "Guest1")
        guest_ws = AsyncMock()
        server.clients[guest.user_id] = guest_ws
        server.websocket_to_user[guest_ws] = guest.user_id

        # 호스트 정리
        await server.cleanup_client(host_id)

        # 세션 만료 확인
        updated_session = server.session_manager.get_session(session.session_id)
        assert updated_session is None or not updated_session.is_active

        # 클라이언트 제거 확인
        assert host_id not in server.clients
        assert host_ws not in server.websocket_to_user

        # 게스트에게 알림 전송 확인
        guest_ws.send.assert_called()
        calls = [json.loads(call[0][0]) for call in guest_ws.send.call_args_list]
        expired_msg = next(msg for msg in calls if msg["type"] == "session_expired")
        assert "Host disconnected" in expired_msg["message"]

    @pytest.mark.asyncio
    async def test_cleanup_client_guest(self, server):
        """게스트 연결 종료 시 세션 유지 테스트"""
        # 세션 생성
        session = server.session_manager.create_session("Host")
        host_id = session.host_id

        # 호스트 WebSocket 등록
        host_ws = AsyncMock()
        server.clients[host_id] = host_ws
        server.websocket_to_user[host_ws] = host_id

        # 게스트 추가
        guest = server.session_manager.add_guest(session.session_id, "Guest1")
        guest_ws = AsyncMock()
        server.clients[guest.user_id] = guest_ws
        server.websocket_to_user[guest_ws] = guest.user_id

        # 게스트 정리
        await server.cleanup_client(guest.user_id)

        # 세션 유지 확인
        updated_session = server.session_manager.get_session(session.session_id)
        assert updated_session is not None
        assert updated_session.is_active

        # 게스트 제거 확인
        assert guest.user_id not in updated_session.guests

        # 클라이언트 제거 확인
        assert guest.user_id not in server.clients
        assert guest_ws not in server.websocket_to_user

        # 호스트에게 알림 전송 확인
        host_ws.send.assert_called()
        calls = [json.loads(call[0][0]) for call in host_ws.send.call_args_list]
        left_msg = next(msg for msg in calls if msg["type"] == "guest_left")
        assert left_msg["user_id"] == guest.user_id

    @pytest.mark.asyncio
    async def test_send_error(self, server, mock_websocket):
        """에러 메시지 전송 테스트"""
        await server.send_error(mock_websocket, "Test error message")

        mock_websocket.send.assert_called_once()
        response = json.loads(mock_websocket.send.call_args[0][0])
        assert response["type"] == "error"
        assert response["message"] == "Test error message"

    @pytest.mark.asyncio
    async def test_handle_message_invalid_type(self, server, mock_websocket):
        """잘못된 메시지 타입 처리 테스트"""
        data = {"type": "invalid_type"}

        await server.handle_message(mock_websocket, data)

        # 에러 메시지 전송 확인
        mock_websocket.send.assert_called_once()
        response = json.loads(mock_websocket.send.call_args[0][0])
        assert response["type"] == "error"
        assert "Unknown message type" in response["message"]

    @pytest.mark.asyncio
    async def test_handle_message_missing_type(self, server, mock_websocket):
        """type 필드 누락 테스트"""
        data = {"some_field": "value"}

        await server.handle_message(mock_websocket, data)

        # 에러 메시지 전송 확인
        mock_websocket.send.assert_called_once()
        response = json.loads(mock_websocket.send.call_args[0][0])
        assert response["type"] == "error"
        assert "Missing 'type' field" in response["message"]

    @pytest.mark.asyncio
    async def test_drawing_message_not_authenticated(self, server, mock_websocket):
        """인증되지 않은 상태에서 드로잉 메시지 전송 테스트"""
        data = {
            "type": "line_start",
            "line_id": "line1",
            "color": "#FF0000"
        }

        await server.handle_message(mock_websocket, data)

        # 에러 메시지 전송 확인
        mock_websocket.send.assert_called_once()
        response = json.loads(mock_websocket.send.call_args[0][0])
        assert response["type"] == "error"
        assert "Not authenticated" in response["message"]

    @pytest.mark.asyncio
    async def test_drawing_message_broadcast(self, server):
        """드로잉 메시지 브로드캐스트 테스트"""
        # 세션 생성
        session = server.session_manager.create_session("Host")
        host_id = session.host_id

        # 호스트 WebSocket 등록
        host_ws = AsyncMock()
        server.clients[host_id] = host_ws
        server.websocket_to_user[host_ws] = host_id

        # 게스트 추가
        guest = server.session_manager.add_guest(session.session_id, "Guest1")
        guest_ws = AsyncMock()
        server.clients[guest.user_id] = guest_ws
        server.websocket_to_user[guest_ws] = guest.user_id

        # 게스트가 드로잉 메시지 전송
        data = {
            "type": "line_start",
            "line_id": "line1",
            "color": "#FF0000"
        }

        await server.handle_drawing_message(guest_ws, guest.user_id, data)

        # 호스트와 게스트 모두 메시지를 받았는지 확인
        host_ws.send.assert_called_once()
        guest_ws.send.assert_called_once()

        # 메시지 내용 확인
        for ws in [host_ws, guest_ws]:
            response = json.loads(ws.send.call_args[0][0])
            assert response["type"] == "line_start"
            assert response["line_id"] == "line1"
            assert response["color"] == "#FF0000"
