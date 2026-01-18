"""통합 테스트: 서버-참여자 간 양방향 통신"""

import asyncio
import pytest

from screen_party_server import ScreenPartyServer
from screen_party_client import WebSocketClient


@pytest.mark.asyncio
async def test_three_participants_session():
    """
    시나리오:
    1. 서버 시작
    2. 참여자1이 세션 생성
    3. 참여자2 참여
    4. 참여자3 참여
    5. 모든 참여자가 서로 정보 수신 확인
    """
    # 1. 서버 시작
    server = ScreenPartyServer("localhost", 8765)
    server_task = asyncio.create_task(server.start())

    # 서버가 완전히 시작될 때까지 대기
    await asyncio.sleep(0.5)

    try:
        # 2. 참여자1 연결 및 세션 생성
        participant1_client = WebSocketClient("ws://localhost:8765")
        await participant1_client.connect()

        response = await participant1_client.create_session("Participant_1")
        assert response["type"] == "session_created"
        assert "session_id" in response
        assert response["host_name"] == "Participant_1"

        session_id = response["session_id"]
        _ = response["host_id"]  # 응답 검증

        print(f"✓ 참여자1 세션 생성 성공: {session_id}")

        # 3. 참여자2 연결 및 세션 참여
        participant2_client = WebSocketClient("ws://localhost:8765")
        await participant2_client.connect()

        response = await participant2_client.join_session(session_id, "Participant_2")
        assert response["type"] == "session_joined"
        assert response["session_id"] == session_id
        assert response["guest_name"] == "Participant_2"
        assert response["host_name"] == "Participant_1"

        participant2_id = response["user_id"]

        print(f"✓ 참여자2 참여 성공: {participant2_id}")

        # 참여자1은 participant_joined 메시지를 받아야 함
        participant1_notification = await participant1_client.receive_message()
        assert participant1_notification["type"] == "participant_joined"
        assert participant1_notification["user_id"] == participant2_id
        assert participant1_notification["participant_name"] == "Participant_2"

        print("✓ 참여자1이 참여자2 참여 알림 수신")

        # 4. 참여자3 연결 및 세션 참여
        participant3_client = WebSocketClient("ws://localhost:8765")
        await participant3_client.connect()

        response = await participant3_client.join_session(session_id, "Participant_3")
        assert response["type"] == "session_joined"
        assert response["session_id"] == session_id
        assert response["guest_name"] == "Participant_3"

        participant3_id = response["user_id"]

        print(f"✓ 참여자3 참여 성공: {participant3_id}")

        # 참여자1과 참여자2는 participant_joined 메시지를 받아야 함
        participant1_notification2 = await participant1_client.receive_message()
        assert participant1_notification2["type"] == "participant_joined"
        assert participant1_notification2["user_id"] == participant3_id
        assert participant1_notification2["participant_name"] == "Participant_3"

        participant2_notification = await participant2_client.receive_message()
        assert participant2_notification["type"] == "participant_joined"
        assert participant2_notification["user_id"] == participant3_id
        assert participant2_notification["participant_name"] == "Participant_3"

        print("✓ 참여자1과 참여자2가 참여자3 참여 알림 수신")

        # 5. 양방향 통신 테스트 - 참여자2가 메시지 전송
        test_message_from_participant2 = {
            "type": "line_start",
            "line_id": "line-001",
            "color": "#FF0000",
            "x": 100,
            "y": 200,
        }

        await participant2_client.send_message(test_message_from_participant2)

        # 참여자1과 참여자3이 메시지를 받아야 함 (참여자2 자신은 받지 않음)
        participant1_msg = await participant1_client.receive_message()
        assert participant1_msg["type"] == "line_start"
        assert participant1_msg["line_id"] == "line-001"
        assert participant1_msg["color"] == "#FF0000"
        assert participant1_msg["x"] == 100
        assert participant1_msg["y"] == 200

        participant3_msg = await participant3_client.receive_message()
        assert participant3_msg["type"] == "line_start"
        assert participant3_msg["line_id"] == "line-001"

        print("✓ 참여자2 → 참여자1, 참여자3 메시지 전송 성공")

        # 6. 양방향 통신 테스트 - 참여자3이 메시지 전송
        test_message_from_participant3 = {
            "type": "line_update",
            "line_id": "line-002",
            "points": [{"x": 10, "y": 20}, {"x": 30, "y": 40}],
        }

        await participant3_client.send_message(test_message_from_participant3)

        # 참여자1과 참여자2가 메시지를 받아야 함
        participant1_msg2 = await participant1_client.receive_message()
        assert participant1_msg2["type"] == "line_update"
        assert participant1_msg2["line_id"] == "line-002"

        participant2_msg2 = await participant2_client.receive_message()
        assert participant2_msg2["type"] == "line_update"
        assert participant2_msg2["line_id"] == "line-002"

        print("✓ 참여자3 → 참여자1, 참여자2 메시지 전송 성공")

        # 7. 핑/퐁 테스트
        pong = await participant1_client.ping()
        assert pong["type"] == "pong"

        pong = await participant2_client.ping()
        assert pong["type"] == "pong"

        pong = await participant3_client.ping()
        assert pong["type"] == "pong"

        print("✓ 모든 참여자 핑/퐁 성공")

        print("\n✅ 통합 테스트 성공: 서버-참여자 간 양방향 통신 확인")

    finally:
        # 정리
        await participant1_client.disconnect()
        await participant2_client.disconnect()
        await participant3_client.disconnect()

        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_participant_leaves_session():
    """
    시나리오:
    1. 참여자1이 세션 생성
    2. 참여자2 참여
    3. 참여자2 나가기
    4. 참여자1이 participant_left 알림 수신
    """
    # 서버 시작
    server = ScreenPartyServer("localhost", 8766)
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.5)

    try:
        # 참여자1 연결
        participant1_client = WebSocketClient("ws://localhost:8766")
        await participant1_client.connect()
        response = await participant1_client.create_session("Participant_1")
        session_id = response["session_id"]

        # 참여자2 연결
        participant2_client = WebSocketClient("ws://localhost:8766")
        await participant2_client.connect()
        response = await participant2_client.join_session(session_id, "Participant_2")
        participant2_id = response["user_id"]

        # 참여자1이 participant_joined 수신
        await participant1_client.receive_message()

        # 참여자2 연결 종료
        await participant2_client.disconnect()
        await asyncio.sleep(0.2)

        # 참여자1이 participant_left 알림을 받아야 함
        notification = await participant1_client.receive_message()
        assert notification["type"] == "participant_left"
        assert notification["user_id"] == participant2_id
        assert notification["participant_name"] == "Participant_2"

        print("✅ 참여자 나가기 알림 정상 수신")

    finally:
        await participant1_client.disconnect()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_session_creator_disconnects():
    """
    시나리오:
    1. 참여자1이 세션 생성
    2. 참여자2 참여
    3. 참여자1 나가기
    4. 참여자2가 participant_left 알림 수신
    """
    # 서버 시작
    server = ScreenPartyServer("localhost", 8767)
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.5)

    try:
        # 참여자1 연결
        participant1_client = WebSocketClient("ws://localhost:8767")
        await participant1_client.connect()
        response = await participant1_client.create_session("Participant_1")
        session_id = response["session_id"]
        participant1_id = response["host_id"]

        # 참여자2 연결
        participant2_client = WebSocketClient("ws://localhost:8767")
        await participant2_client.connect()
        await participant2_client.join_session(session_id, "Participant_2")

        # 참여자1이 participant_joined 수신
        await participant1_client.receive_message()

        # 참여자1 연결 종료
        await participant1_client.disconnect()
        await asyncio.sleep(0.2)

        # 참여자2가 participant_left 알림을 받아야 함
        notification = await participant2_client.receive_message()
        assert notification["type"] == "participant_left"
        assert notification["user_id"] == participant1_id
        assert notification["participant_name"] == "Participant_1"

        print("✅ 세션 생성자 나가기 시 participant_left 알림 정상 수신")

    finally:
        await participant2_client.disconnect()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_complete_drawing_flow():
    """
    시나리오:
    1. 참여자1이 세션 생성
    2. 참여자2 참여
    3. 참여자2가 완전한 드로잉 흐름 수행 (line_start → line_update → line_end)
    4. 참여자1이 모든 드로잉 메시지를 순서대로 수신
    """
    # 서버 시작
    server = ScreenPartyServer("localhost", 8768)
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.5)

    try:
        # 참여자1 연결
        participant1_client = WebSocketClient("ws://localhost:8768")
        await participant1_client.connect()
        response = await participant1_client.create_session("Participant_1")
        session_id = response["session_id"]

        # 참여자2 연결
        participant2_client = WebSocketClient("ws://localhost:8768")
        await participant2_client.connect()
        await participant2_client.join_session(session_id, "Participant_2")

        # 참여자1이 participant_joined 수신
        await participant1_client.receive_message()

        # 참여자2가 드로잉 시작
        line_id = "test-line-001"
        line_start_msg = {
            "type": "line_start",
            "line_id": line_id,
            "color": "#FF0000",
            "x": 100,
            "y": 200,
        }
        await participant2_client.send_message(line_start_msg)

        # 참여자1이 line_start 수신
        participant1_msg = await participant1_client.receive_message()
        assert participant1_msg["type"] == "line_start"
        assert participant1_msg["line_id"] == line_id
        assert participant1_msg["color"] == "#FF0000"
        assert participant1_msg["x"] == 100
        assert participant1_msg["y"] == 200
        print("✓ 참여자1이 line_start 수신")

        # 참여자2가 드로잉 업데이트 (여러 점 추가)
        line_update_msg = {
            "type": "line_update",
            "line_id": line_id,
            "points": [
                {"x": 110, "y": 210},
                {"x": 120, "y": 220},
                {"x": 130, "y": 230},
            ],
        }
        await participant2_client.send_message(line_update_msg)

        # 참여자1이 line_update 수신
        participant1_msg = await participant1_client.receive_message()
        assert participant1_msg["type"] == "line_update"
        assert participant1_msg["line_id"] == line_id
        assert len(participant1_msg["points"]) == 3
        assert participant1_msg["points"][0]["x"] == 110
        print("✓ 참여자1이 line_update 수신")

        # 참여자2가 드로잉 종료
        line_end_msg = {
            "type": "line_end",
            "line_id": line_id,
        }
        await participant2_client.send_message(line_end_msg)

        # 참여자1이 line_end 수신
        participant1_msg = await participant1_client.receive_message()
        assert participant1_msg["type"] == "line_end"
        assert participant1_msg["line_id"] == line_id
        print("✓ 참여자1이 line_end 수신")

        print("✅ 완전한 드로잉 흐름 테스트 성공 (start → update → end)")

    finally:
        await participant1_client.disconnect()
        await participant2_client.disconnect()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_color_change_broadcast():
    """
    시나리오:
    1. 참여자1이 세션 생성
    2. 참여자2, 참여자3 참여
    3. 참여자2가 색상 변경
    4. 참여자1과 참여자3이 색상 변경 메시지 수신 (참여자2 본인도 수신)
    """
    # 서버 시작
    server = ScreenPartyServer("localhost", 8769)
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.5)

    try:
        # 참여자1 연결
        participant1_client = WebSocketClient("ws://localhost:8769")
        await participant1_client.connect()
        response = await participant1_client.create_session("Participant_1")
        session_id = response["session_id"]

        # 참여자2 연결
        participant2_client = WebSocketClient("ws://localhost:8769")
        await participant2_client.connect()
        response = await participant2_client.join_session(session_id, "Participant_2")
        participant2_id = response["user_id"]

        # 참여자1이 participant_joined 수신
        await participant1_client.receive_message()

        # 참여자3 연결
        participant3_client = WebSocketClient("ws://localhost:8769")
        await participant3_client.connect()
        await participant3_client.join_session(session_id, "Participant_3")

        # 참여자1과 참여자2가 participant_joined 수신
        await participant1_client.receive_message()
        await participant2_client.receive_message()

        # 참여자2가 색상 변경
        color_change_msg = {
            "type": "color_change",
            "color": "#00FF00",  # 초록색
        }
        await participant2_client.send_message(color_change_msg)

        # 참여자1이 color_change 메시지 수신
        participant1_msg = await participant1_client.receive_message()
        assert participant1_msg["type"] == "color_change"
        assert participant1_msg["color"] == "#00FF00"
        print("✓ 참여자1이 색상 변경 메시지 수신")

        # 참여자2 본인도 color_change 메시지 수신 (서버가 송신자 포함하여 브로드캐스트)
        participant2_msg = await participant2_client.receive_message()
        assert participant2_msg["type"] == "color_change"
        assert participant2_msg["color"] == "#00FF00"
        print("✓ 참여자2(송신자)도 색상 변경 메시지 수신")

        # 참여자3이 color_change 메시지 수신
        participant3_msg = await participant3_client.receive_message()
        assert participant3_msg["type"] == "color_change"
        assert participant3_msg["color"] == "#00FF00"
        print("✓ 참여자3이 색상 변경 메시지 수신")

        print("✅ 색상 변경 브로드캐스트 테스트 성공")

    finally:
        await participant1_client.disconnect()
        await participant2_client.disconnect()
        await participant3_client.disconnect()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
