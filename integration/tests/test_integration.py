"""통합 테스트: 서버-호스트-게스트 간 양방향 통신"""

import asyncio
import pytest

from screen_party_server import ScreenPartyServer
from screen_party_client import WebSocketClient


@pytest.mark.asyncio
async def test_host_creates_session_and_two_guests_join():
    """
    시나리오:
    1. 서버 시작
    2. 호스트가 세션 생성
    3. 게스트1 참여
    4. 게스트2 참여
    5. 호스트와 게스트들이 서로 정보 수신 확인
    """
    # 1. 서버 시작
    server = ScreenPartyServer("localhost", 8765)
    server_task = asyncio.create_task(server.start())

    # 서버가 완전히 시작될 때까지 대기
    await asyncio.sleep(0.5)

    try:
        # 2. 호스트 연결 및 세션 생성
        host_client = WebSocketClient("ws://localhost:8765")
        await host_client.connect()

        response = await host_client.create_session("Host_Player")
        assert response["type"] == "session_created"
        assert "session_id" in response
        assert response["host_name"] == "Host_Player"

        session_id = response["session_id"]
        _ = response["host_id"]  # host_id 사용하지 않지만 응답 검증

        print(f"✓ 호스트 세션 생성 성공: {session_id}")

        # 3. 게스트1 연결 및 세션 참여
        guest1_client = WebSocketClient("ws://localhost:8765")
        await guest1_client.connect()

        response = await guest1_client.join_session(session_id, "Guest_1")
        assert response["type"] == "session_joined"
        assert response["session_id"] == session_id
        assert response["guest_name"] == "Guest_1"
        assert response["host_name"] == "Host_Player"

        guest1_id = response["user_id"]

        print(f"✓ 게스트1 참여 성공: {guest1_id}")

        # 호스트는 guest_joined 메시지를 받아야 함
        host_notification = await host_client.receive_message()
        assert host_notification["type"] == "guest_joined"
        assert host_notification["user_id"] == guest1_id
        assert host_notification["guest_name"] == "Guest_1"

        print("✓ 호스트가 게스트1 참여 알림 수신")

        # 4. 게스트2 연결 및 세션 참여
        guest2_client = WebSocketClient("ws://localhost:8765")
        await guest2_client.connect()

        response = await guest2_client.join_session(session_id, "Guest_2")
        assert response["type"] == "session_joined"
        assert response["session_id"] == session_id
        assert response["guest_name"] == "Guest_2"

        guest2_id = response["user_id"]

        print(f"✓ 게스트2 참여 성공: {guest2_id}")

        # 호스트와 게스트1은 guest_joined 메시지를 받아야 함
        host_notification2 = await host_client.receive_message()
        assert host_notification2["type"] == "guest_joined"
        assert host_notification2["user_id"] == guest2_id
        assert host_notification2["guest_name"] == "Guest_2"

        guest1_notification = await guest1_client.receive_message()
        assert guest1_notification["type"] == "guest_joined"
        assert guest1_notification["user_id"] == guest2_id
        assert guest1_notification["guest_name"] == "Guest_2"

        print("✓ 호스트와 게스트1이 게스트2 참여 알림 수신")

        # 5. 양방향 통신 테스트 - 게스트1이 메시지 전송
        test_message_from_guest1 = {
            "type": "line_start",
            "line_id": "line-001",
            "color": "#FF0000",
            "x": 100,
            "y": 200
        }

        await guest1_client.send_message(test_message_from_guest1)

        # 호스트와 게스트2가 메시지를 받아야 함 (게스트1 자신은 받지 않음)
        host_msg = await host_client.receive_message()
        assert host_msg["type"] == "line_start"
        assert host_msg["line_id"] == "line-001"
        assert host_msg["color"] == "#FF0000"
        assert host_msg["x"] == 100
        assert host_msg["y"] == 200

        guest2_msg = await guest2_client.receive_message()
        assert guest2_msg["type"] == "line_start"
        assert guest2_msg["line_id"] == "line-001"

        print("✓ 게스트1 → 호스트, 게스트2 메시지 전송 성공")

        # 6. 양방향 통신 테스트 - 게스트2가 메시지 전송
        test_message_from_guest2 = {
            "type": "line_update",
            "line_id": "line-002",
            "points": [{"x": 10, "y": 20}, {"x": 30, "y": 40}]
        }

        await guest2_client.send_message(test_message_from_guest2)

        # 호스트와 게스트1이 메시지를 받아야 함
        host_msg2 = await host_client.receive_message()
        assert host_msg2["type"] == "line_update"
        assert host_msg2["line_id"] == "line-002"

        guest1_msg2 = await guest1_client.receive_message()
        assert guest1_msg2["type"] == "line_update"
        assert guest1_msg2["line_id"] == "line-002"

        print("✓ 게스트2 → 호스트, 게스트1 메시지 전송 성공")

        # 7. 핑/퐁 테스트
        pong = await host_client.ping()
        assert pong["type"] == "pong"

        pong = await guest1_client.ping()
        assert pong["type"] == "pong"

        pong = await guest2_client.ping()
        assert pong["type"] == "pong"

        print("✓ 모든 클라이언트 핑/퐁 성공")

        print("\n✅ 통합 테스트 성공: 서버-호스트-게스트 간 양방향 통신 확인")

    finally:
        # 정리
        await host_client.disconnect()
        await guest1_client.disconnect()
        await guest2_client.disconnect()

        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_guest_leaves_session():
    """
    시나리오:
    1. 호스트 세션 생성
    2. 게스트 참여
    3. 게스트 나가기
    4. 호스트가 guest_left 알림 수신
    """
    # 서버 시작
    server = ScreenPartyServer("localhost", 8766)
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.5)

    try:
        # 호스트 연결
        host_client = WebSocketClient("ws://localhost:8766")
        await host_client.connect()
        response = await host_client.create_session("Host")
        session_id = response["session_id"]

        # 게스트 연결
        guest_client = WebSocketClient("ws://localhost:8766")
        await guest_client.connect()
        response = await guest_client.join_session(session_id, "Guest")
        guest_id = response["user_id"]

        # 호스트가 guest_joined 수신
        await host_client.receive_message()

        # 게스트 연결 종료
        await guest_client.disconnect()
        await asyncio.sleep(0.2)

        # 호스트가 guest_left 알림을 받아야 함
        notification = await host_client.receive_message()
        assert notification["type"] == "guest_left"
        assert notification["user_id"] == guest_id
        assert notification["guest_name"] == "Guest"

        print("✅ 게스트 나가기 알림 정상 수신")

    finally:
        await host_client.disconnect()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_host_disconnects_expires_session():
    """
    시나리오:
    1. 호스트 세션 생성
    2. 게스트 참여
    3. 호스트 나가기
    4. 게스트가 session_expired 알림 수신
    """
    # 서버 시작
    server = ScreenPartyServer("localhost", 8767)
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.5)

    try:
        # 호스트 연결
        host_client = WebSocketClient("ws://localhost:8767")
        await host_client.connect()
        response = await host_client.create_session("Host")
        session_id = response["session_id"]

        # 게스트 연결
        guest_client = WebSocketClient("ws://localhost:8767")
        await guest_client.connect()
        await guest_client.join_session(session_id, "Guest")

        # 호스트가 guest_joined 수신
        await host_client.receive_message()

        # 호스트 연결 종료
        await host_client.disconnect()
        await asyncio.sleep(0.2)

        # 게스트가 session_expired 알림을 받아야 함
        notification = await guest_client.receive_message()
        assert notification["type"] == "session_expired"
        assert "Host disconnected" in notification["message"]

        print("✅ 호스트 나가기 시 세션 만료 알림 정상 수신")

    finally:
        await guest_client.disconnect()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
