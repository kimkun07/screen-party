"""세션 관리"""

import asyncio
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

from .models import Guest, Session


class SessionManager:
    """세션 생성, 조회, 만료 관리"""

    def __init__(self, session_timeout_minutes: int = 60):
        """
        Args:
            session_timeout_minutes: 세션 만료 시간 (분), 기본 60분
        """
        self.sessions: Dict[str, Session] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self._cleanup_task: Optional[asyncio.Task] = None

    def _generate_session_id(self) -> str:
        """
        6자리 세션 ID 생성 (대문자 + 숫자)

        Returns:
            6자리 세션 ID (예: ABC123)
        """
        chars = string.ascii_uppercase + string.digits
        max_retries = 10

        for _ in range(max_retries):
            session_id = "".join(random.choices(chars, k=6))
            if session_id not in self.sessions:
                return session_id

        # 최대 재시도 초과 시 예외 발생 (매우 드문 경우)
        raise RuntimeError("세션 ID 생성 실패: 최대 재시도 초과")

    def create_session(self, host_name: str) -> Session:
        """
        새 세션 생성

        Args:
            host_name: 호스트 이름

        Returns:
            생성된 Session 객체
        """
        session_id = self._generate_session_id()
        host_id = str(uuid.uuid4())

        session = Session(
            session_id=session_id,
            host_id=host_id,
            host_name=host_name,
        )

        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        세션 조회

        Args:
            session_id: 세션 ID

        Returns:
            Session 객체 또는 None (존재하지 않거나 비활성)
        """
        session = self.sessions.get(session_id)
        if session and session.is_active:
            return session
        return None

    def add_guest(self, session_id: str, guest_name: str) -> Optional[Guest]:
        """
        세션에 게스트 추가

        Args:
            session_id: 세션 ID
            guest_name: 게스트 이름

        Returns:
            생성된 Guest 객체 또는 None (세션이 존재하지 않으면)
        """
        session = self.get_session(session_id)
        if not session:
            return None

        guest = Guest(
            user_id=str(uuid.uuid4()),
            name=guest_name,
        )

        session.add_guest(guest)
        return guest

    def remove_guest(self, session_id: str, user_id: str) -> bool:
        """
        세션에서 게스트 제거

        Args:
            session_id: 세션 ID
            user_id: 게스트 user_id

        Returns:
            성공 여부
        """
        session = self.get_session(session_id)
        if not session:
            return False

        return session.remove_guest(user_id)

    def expire_session(self, session_id: str) -> None:
        """
        세션 만료 처리

        Args:
            session_id: 세션 ID
        """
        if session_id in self.sessions:
            self.sessions[session_id].is_active = False

    def delete_session(self, session_id: str) -> bool:
        """
        세션 삭제

        Args:
            session_id: 세션 ID

        Returns:
            성공 여부
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def cleanup_expired_sessions(self) -> int:
        """
        만료된 세션 정리

        Returns:
            삭제된 세션 수
        """
        now = datetime.now()
        expired_sessions = []

        for session_id, session in self.sessions.items():
            # 비활성 세션 또는 타임아웃된 세션
            if not session.is_active or (now - session.last_activity) > self.session_timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.sessions[session_id]

        return len(expired_sessions)

    async def start_cleanup_task(self, interval_minutes: int = 5) -> None:
        """
        백그라운드 cleanup 태스크 시작

        Args:
            interval_minutes: 정리 주기 (분), 기본 5분
        """
        if self._cleanup_task and not self._cleanup_task.done():
            return  # 이미 실행 중

        async def cleanup_loop():
            while True:
                await asyncio.sleep(interval_minutes * 60)
                deleted_count = self.cleanup_expired_sessions()
                if deleted_count > 0:
                    print(f"[SessionManager] {deleted_count}개 만료된 세션 정리")

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    def stop_cleanup_task(self) -> None:
        """백그라운드 cleanup 태스크 중지"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
