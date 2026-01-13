"""세션 관리 유닛 테스트"""

import asyncio
from datetime import datetime, timedelta

import pytest

from screen_party_common import Participant, Session
from screen_party_server.session import SessionManager


def test_session_id_generation():
    """세션 ID 생성 테스트"""
    manager = SessionManager()
    session, participant = manager.create_session("TestParticipant")

    # 6자리 확인
    assert len(session.session_id) == 6
    # 대문자 + 숫자만 포함
    assert session.session_id.isalnum()
    assert session.session_id.isupper()


def test_session_id_uniqueness():
    """세션 ID 중복 방지 테스트"""
    manager = SessionManager()
    session_ids = set()

    # 100개 세션 생성
    for i in range(100):
        session, _ = manager.create_session(f"Participant{i}")
        session_ids.add(session.session_id)

    # 모두 고유해야 함
    assert len(session_ids) == 100


def test_create_session():
    """세션 생성 테스트"""
    manager = SessionManager()
    session, participant = manager.create_session("TestParticipant")

    assert session.session_id is not None
    assert participant.user_id is not None
    assert participant.name == "TestParticipant"
    assert session.is_active is True
    assert len(session.participants) == 1
    assert participant.user_id in session.participants


def test_get_session():
    """세션 조회 테스트"""
    manager = SessionManager()
    session, _ = manager.create_session("TestParticipant")

    # 존재하는 세션
    retrieved = manager.get_session(session.session_id)
    assert retrieved is not None
    assert retrieved.session_id == session.session_id

    # 존재하지 않는 세션
    assert manager.get_session("INVALID") is None


def test_add_participant():
    """참여자 추가 테스트"""
    manager = SessionManager()
    session, first_participant = manager.create_session("FirstParticipant")

    # 참여자 추가
    participant = manager.add_participant(session.session_id, "SecondParticipant")
    assert participant is not None
    assert participant.name == "SecondParticipant"
    assert participant.user_id is not None

    # 세션에 참여자가 추가되었는지 확인
    retrieved_session = manager.get_session(session.session_id)
    assert len(retrieved_session.participants) == 2
    assert participant.user_id in retrieved_session.participants


def test_add_multiple_participants():
    """여러 참여자 추가 테스트"""
    manager = SessionManager()
    session, first_participant = manager.create_session("FirstParticipant")

    # 여러 참여자 추가
    participant2 = manager.add_participant(session.session_id, "SecondParticipant")
    participant3 = manager.add_participant(session.session_id, "ThirdParticipant")
    participant4 = manager.add_participant(session.session_id, "FourthParticipant")

    retrieved_session = manager.get_session(session.session_id)
    assert len(retrieved_session.participants) == 4


def test_remove_participant():
    """참여자 제거 테스트"""
    manager = SessionManager()
    session, first_participant = manager.create_session("FirstParticipant")

    # 참여자 추가
    participant = manager.add_participant(session.session_id, "SecondParticipant")

    # 참여자 제거
    result = manager.remove_participant(session.session_id, participant.user_id)
    assert result is True

    # 세션에서 참여자가 제거되었는지 확인
    retrieved_session = manager.get_session(session.session_id)
    assert len(retrieved_session.participants) == 1


def test_remove_nonexistent_participant():
    """존재하지 않는 참여자 제거 시도"""
    manager = SessionManager()
    session, _ = manager.create_session("TestParticipant")

    # 존재하지 않는 참여자 제거
    result = manager.remove_participant(session.session_id, "invalid_user_id")
    assert result is False


def test_expire_session():
    """세션 만료 테스트"""
    manager = SessionManager()
    session, _ = manager.create_session("TestParticipant")

    # 세션 만료
    manager.expire_session(session.session_id)

    # 만료된 세션은 조회되지 않음
    retrieved = manager.get_session(session.session_id)
    assert retrieved is None


def test_delete_session():
    """세션 삭제 테스트"""
    manager = SessionManager()
    session, _ = manager.create_session("TestParticipant")

    # 세션 삭제
    result = manager.delete_session(session.session_id)
    assert result is True

    # 삭제된 세션은 조회되지 않음
    retrieved = manager.get_session(session.session_id)
    assert retrieved is None


def test_cleanup_expired_sessions():
    """만료된 세션 정리 테스트"""
    manager = SessionManager(session_timeout_minutes=0)  # 즉시 만료

    # 세션 생성
    session1, _ = manager.create_session("Participant1")
    session2, _ = manager.create_session("Participant2")

    # 활동 시간을 과거로 설정
    session1.last_activity = datetime.now() - timedelta(minutes=1)
    session2.last_activity = datetime.now() - timedelta(minutes=1)

    # cleanup 실행
    deleted_count = manager.cleanup_expired_sessions()
    assert deleted_count == 2
    assert len(manager.sessions) == 0


def test_cleanup_keeps_active_sessions():
    """활성 세션은 유지되는지 테스트"""
    manager = SessionManager(session_timeout_minutes=60)

    # 세션 생성
    session1, _ = manager.create_session("Participant1")
    session2, _ = manager.create_session("Participant2")

    # cleanup 실행 (아직 만료 안 됨)
    deleted_count = manager.cleanup_expired_sessions()
    assert deleted_count == 0
    assert len(manager.sessions) == 2


@pytest.mark.asyncio
async def test_background_cleanup_task():
    """백그라운드 cleanup 태스크 테스트"""
    manager = SessionManager(session_timeout_minutes=0)

    # 세션 생성
    session, _ = manager.create_session("TestParticipant")
    session.last_activity = datetime.now() - timedelta(minutes=1)

    # cleanup 태스크 시작 (테스트용으로 짧은 주기)
    await manager.start_cleanup_task(interval_minutes=0.01)

    # 잠깐 대기
    await asyncio.sleep(1)

    # 중지
    manager.stop_cleanup_task()

    # 세션이 정리되었는지 확인
    assert len(manager.sessions) == 0


def test_session_activity_update():
    """세션 활동 시간 업데이트 테스트"""
    session = Session(session_id="TEST01")
    participant = Participant(user_id="user123", name="TestParticipant")
    session.add_participant(participant)

    original_time = session.last_activity

    # 약간 대기
    import time

    time.sleep(0.01)

    # 활동 업데이트
    session.update_activity()

    assert session.last_activity > original_time
