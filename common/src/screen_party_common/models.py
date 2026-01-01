"""데이터 모델 정의"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict


@dataclass
class Guest:
    """게스트 정보"""

    user_id: str
    name: str
    joined_at: datetime = field(default_factory=datetime.now)


@dataclass
class Session:
    """세션 정보"""

    session_id: str
    host_id: str
    host_name: str
    guests: Dict[str, Guest] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_active: bool = True

    def add_guest(self, guest: Guest) -> None:
        """게스트 추가"""
        self.guests[guest.user_id] = guest
        self.last_activity = datetime.now()

    def remove_guest(self, user_id: str) -> bool:
        """게스트 제거"""
        if user_id in self.guests:
            del self.guests[user_id]
            self.last_activity = datetime.now()
            return True
        return False

    def update_activity(self) -> None:
        """마지막 활동 시간 업데이트"""
        self.last_activity = datetime.now()
