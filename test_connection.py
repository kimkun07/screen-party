#!/usr/bin/env python3
"""서버-클라이언트 연결 테스트 (CLI 버전)"""

import sys
import os
import asyncio
import json

# client/src를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "client", "src"))

from screen_party_client.network.client import WebSocketClient


async def test_host_mode():
    """호스트 모드 테스트"""
    print("\n" + "=" * 50)
    print("호스트 모드 테스트")
    print("=" * 50)

    server_url = os.getenv("SCREEN_PARTY_SERVER", "ws://localhost:8765")
    client = WebSocketClient(server_url)

    try:
        # 서버 연결
        print(f"서버 연결 중: {server_url}")
        await client.connect()
        print("✅ 서버 연결 성공!")

        # 세션 생성 요청
        print("\n세션 생성 요청 중...")
        await client.send_message({
            "type": "create_session",
            "host_name": "TestHost"
        })

        # 응답 받기
        response = await asyncio.wait_for(client.receive_message(), timeout=5.0)
        print(f"✅ 응답 받음: {json.dumps(response, indent=2, ensure_ascii=False)}")

        if response.get("type") == "session_created":
            session_id = response.get("session_id")
            host_id = response.get("host_id")
            print(f"\n🎉 세션 생성 성공!")
            print(f"   세션 코드: {session_id}")
            print(f"   호스트 ID: {host_id}")
            return session_id
        else:
            print(f"❌ 세션 생성 실패: {response}")
            return None

    except asyncio.TimeoutError:
        print("❌ 타임아웃: 서버 응답 없음")
        return None
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        return None
    finally:
        await client.disconnect()


async def test_guest_mode(session_id: str):
    """게스트 모드 테스트"""
    print("\n" + "=" * 50)
    print("게스트 모드 테스트")
    print("=" * 50)

    server_url = os.getenv("SCREEN_PARTY_SERVER", "ws://localhost:8765")
    client = WebSocketClient(server_url)

    try:
        # 서버 연결
        print(f"서버 연결 중: {server_url}")
        await client.connect()
        print("✅ 서버 연결 성공!")

        # 세션 참여 요청
        print(f"\n세션 참여 요청 중 (세션 코드: {session_id})...")
        await client.send_message({
            "type": "join_session",
            "session_id": session_id,
            "guest_name": "TestGuest"
        })

        # 응답 받기
        response = await asyncio.wait_for(client.receive_message(), timeout=5.0)
        print(f"✅ 응답 받음: {json.dumps(response, indent=2, ensure_ascii=False)}")

        if response.get("type") == "session_joined":
            user_id = response.get("user_id")
            print(f"\n🎉 세션 참여 성공!")
            print(f"   사용자 ID: {user_id}")
            return True
        else:
            print(f"❌ 세션 참여 실패: {response}")
            return False

    except asyncio.TimeoutError:
        print("❌ 타임아웃: 서버 응답 없음")
        return False
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        return False
    finally:
        await client.disconnect()


async def test_ping():
    """핑 테스트"""
    print("\n" + "=" * 50)
    print("핑/퐁 테스트")
    print("=" * 50)

    server_url = os.getenv("SCREEN_PARTY_SERVER", "ws://localhost:8765")
    client = WebSocketClient(server_url)

    try:
        print(f"서버 연결 중: {server_url}")
        await client.connect()
        print("✅ 서버 연결 성공!")

        print("\n핑 전송 중...")
        await client.send_message({"type": "ping"})

        response = await asyncio.wait_for(client.receive_message(), timeout=5.0)
        print(f"✅ 응답 받음: {json.dumps(response, indent=2, ensure_ascii=False)}")

        if response.get("type") == "pong":
            print("🎉 핑/퐁 성공!")
            return True
        else:
            print(f"❌ 예상치 못한 응답: {response}")
            return False

    except asyncio.TimeoutError:
        print("❌ 타임아웃: 서버 응답 없음")
        return False
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        return False
    finally:
        await client.disconnect()


async def test_full_session():
    """전체 세션 테스트 (호스트와 게스트 동시 연결)"""
    print("\n" + "=" * 60)
    print("전체 세션 테스트 (호스트 + 게스트)")
    print("=" * 60)

    server_url = os.getenv("SCREEN_PARTY_SERVER", "ws://localhost:8765")

    # 호스트 클라이언트
    host_client = WebSocketClient(server_url)
    # 게스트 클라이언트
    guest_client = WebSocketClient(server_url)

    try:
        # 1. 호스트 연결 및 세션 생성
        print("\n[호스트] 서버 연결 중...")
        await host_client.connect()
        print("✅ [호스트] 서버 연결 성공!")

        print("\n[호스트] 세션 생성 중...")
        await host_client.send_message({
            "type": "create_session",
            "host_name": "TestHost"
        })

        response = await asyncio.wait_for(host_client.receive_message(), timeout=5.0)
        print(f"✅ [호스트] 응답: {json.dumps(response, indent=2, ensure_ascii=False)}")

        if response.get("type") != "session_created":
            print("❌ 세션 생성 실패")
            return False

        session_id = response.get("session_id")
        print(f"\n🎉 세션 생성 성공! 코드: {session_id}")

        # 2. 게스트 연결 및 세션 참여
        print("\n[게스트] 서버 연결 중...")
        await guest_client.connect()
        print("✅ [게스트] 서버 연결 성공!")

        print(f"\n[게스트] 세션 참여 중 (코드: {session_id})...")
        await guest_client.send_message({
            "type": "join_session",
            "session_id": session_id,
            "guest_name": "TestGuest"
        })

        # 게스트 응답 받기
        guest_response = await asyncio.wait_for(guest_client.receive_message(), timeout=5.0)
        print(f"✅ [게스트] 응답: {json.dumps(guest_response, indent=2, ensure_ascii=False)}")

        if guest_response.get("type") != "session_joined":
            print("❌ 게스트 참여 실패")
            return False

        # 호스트도 guest_joined 메시지를 받아야 함
        host_notification = await asyncio.wait_for(host_client.receive_message(), timeout=5.0)
        print(f"✅ [호스트] 알림: {json.dumps(host_notification, indent=2, ensure_ascii=False)}")

        print("\n🎉 게스트 참여 성공!")
        print(f"   게스트 ID: {guest_response.get('user_id')}")

        # 3. 간단한 메시지 테스트
        print("\n[게스트] 드로잉 메시지 전송 테스트...")
        await guest_client.send_message({
            "type": "line_start",
            "line_id": "test-line-1",
            "color": "#FF0000"
        })

        # 호스트가 메시지를 받아야 함
        drawing_msg = await asyncio.wait_for(host_client.receive_message(), timeout=5.0)
        print(f"✅ [호스트] 드로잉 메시지 받음: {json.dumps(drawing_msg, indent=2, ensure_ascii=False)}")

        if drawing_msg.get("type") == "line_start":
            print("🎉 드로잉 메시지 브로드캐스트 성공!")
            return True
        else:
            print("❌ 드로잉 메시지 전달 실패")
            return False

    except asyncio.TimeoutError:
        print("❌ 타임아웃: 서버 응답 없음")
        return False
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await guest_client.disconnect()
        await host_client.disconnect()


async def main():
    """메인 테스트"""
    print("\n" + "=" * 60)
    print("Screen Party 서버-클라이언트 연결 테스트")
    print("=" * 60)

    # 1. 핑 테스트
    ping_ok = await test_ping()
    if not ping_ok:
        print("\n❌ 핑 테스트 실패. 서버가 실행 중인지 확인하세요.")
        print("   서버 실행: python server/main.py")
        return

    # 2. 전체 세션 테스트
    session_ok = await test_full_session()
    if not session_ok:
        print("\n❌ 세션 테스트 실패")
        return

    # 최종 결과
    print("\n" + "=" * 60)
    print("✅ 모든 테스트 통과!")
    print("=" * 60)
    print("\n서버-클라이언트 연결이 정상적으로 작동합니다.")
    print("\nGUI 클라이언트는 로컬 머신에서 실행하세요:")
    print("  1. 이 저장소를 로컬에 clone")
    print("  2. uv sync --all-groups")
    print("  3. SCREEN_PARTY_SERVER=ws://<서버IP>:8765 uv run python client/main.py")
    print("\n또는 터미널 2개를 열어서:")
    print("  터미널 1: uv run python server/main.py")
    print("  터미널 2 (로컬): uv run python client/main.py")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n테스트 중단")
