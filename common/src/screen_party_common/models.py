"""데이터 모델 정의"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict


# 기본 색상 상수 (파스텔 핑크 - 첫 번째 프리셋)
DEFAULT_COLOR = "#FFB6C1"  # RGB(255, 182, 193)


@dataclass
class Participant:
    """참여자 정보"""

    user_id: str
    name: str
    color: str = DEFAULT_COLOR  # 펜 색상 (hex 형식)
    joined_at: datetime = field(default_factory=datetime.now)


@dataclass
class Session:
    """세션 정보"""

    session_id: str
    participants: Dict[str, Participant] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_active: bool = True

    def add_participant(self, participant: Participant) -> None:
        """참여자 추가"""
        self.participants[participant.user_id] = participant
        self.last_activity = datetime.now()

    def remove_participant(self, user_id: str) -> bool:
        """참여자 제거"""
        if user_id in self.participants:
            del self.participants[user_id]
            self.last_activity = datetime.now()
            return True
        return False

    def has_participants(self) -> bool:
        """참여자가 있는지 확인"""
        return len(self.participants) > 0

    def update_activity(self) -> None:
        """마지막 활동 시간 업데이트"""
        self.last_activity = datetime.now()
