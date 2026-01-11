"""
메시지 타입 및 프로토콜 정의

클라이언트-서버 간 통신에 사용되는 모든 메시지 타입과 구조를 정의합니다.
"""

from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Tuple
from enum import Enum


class MessageType(str, Enum):
    """메시지 타입 정의 (클라이언트-서버 공통)"""

    # === Session Management ===
    CREATE_SESSION = "create_session"
    JOIN_SESSION = "join_session"
    SESSION_CREATED = "session_created"
    SESSION_JOINED = "session_joined"
    GUEST_JOINED = "guest_joined"
    GUEST_LEFT = "guest_left"
    SESSION_EXPIRED = "session_expired"

    # === Communication ===
    PING = "ping"
    PONG = "pong"
    ERROR = "error"

    # === Drawing ===
    DRAWING_START = "drawing_start"
    DRAWING_UPDATE = "drawing_update"
    DRAWING_END = "drawing_end"
    COLOR_CHANGE = "color_change"


# 카테고리별 메시지 타입 그룹 (문자열 값으로 비교)
DRAWING_MESSAGE_TYPES = {
    MessageType.DRAWING_START.value,
    MessageType.DRAWING_UPDATE.value,
    MessageType.DRAWING_END.value,
    MessageType.COLOR_CHANGE.value,
    # Legacy support (기존 "line_*" 메시지 타입)
    "line_start",
    "line_update",
    "line_end",
    "line_remove",
}

SESSION_MESSAGE_TYPES = {
    MessageType.CREATE_SESSION.value,
    MessageType.JOIN_SESSION.value,
    MessageType.SESSION_CREATED.value,
    MessageType.SESSION_JOINED.value,
    MessageType.GUEST_JOINED.value,
    MessageType.GUEST_LEFT.value,
    MessageType.SESSION_EXPIRED.value,
}

# 인증 불필요한 public 메시지
PUBLIC_MESSAGE_TYPES = {
    MessageType.CREATE_SESSION.value,
    MessageType.JOIN_SESSION.value,
    MessageType.PING.value,
}

# 인증 필요한 authenticated 메시지
AUTHENTICATED_MESSAGE_TYPES = DRAWING_MESSAGE_TYPES


# === 메시지 데이터 클래스 ===


@dataclass
class BaseMessage:
    """기본 메시지 클래스"""

    type: MessageType

    def to_dict(self) -> Dict[str, Any]:
        """dict로 변환 (JSON 직렬화용)

        Returns:
            JSON 직렬화 가능한 dict
        """
        data = asdict(self)
        # MessageType enum을 문자열로 변환
        if "type" in data and isinstance(data["type"], MessageType):
            data["type"] = data["type"].value
        # tuple을 list로 변환 (JSON 직렬화)
        data = self._convert_tuples_to_lists(data)
        return data

    def _convert_tuples_to_lists(self, obj):
        """재귀적으로 tuple을 list로 변환"""
        if isinstance(obj, tuple):
            return list(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_tuples_to_lists(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_tuples_to_lists(item) for item in obj]
        return obj


@dataclass
class DrawingStartMessage(BaseMessage):
    """드로잉 시작 메시지

    Attributes:
        line_id: 라인 고유 ID
        user_id: 사용자 ID
        color: 펜 색상 (hex 형식, 예: "#FF0000")
        start_point: 시작 점 (x, y)
    """

    line_id: str
    user_id: str
    color: str
    start_point: Tuple[float, float]
    type: MessageType = field(default=MessageType.DRAWING_START, init=False)


@dataclass
class DrawingUpdateMessage(BaseMessage):
    """드로잉 업데이트 메시지 (Delta Update)

    Attributes:
        line_id: 라인 고유 ID
        user_id: 사용자 ID
        new_finalized_segments: 새로 확정된 베지어 세그먼트 리스트
        current_raw_points: 현재 raw 점들
    """

    line_id: str
    user_id: str
    new_finalized_segments: List[Dict[str, Any]]
    current_raw_points: List[Tuple[float, float]]
    type: MessageType = field(default=MessageType.DRAWING_UPDATE, init=False)


@dataclass
class DrawingEndMessage(BaseMessage):
    """드로잉 종료 메시지

    Attributes:
        line_id: 라인 고유 ID
        user_id: 사용자 ID
    """

    line_id: str
    user_id: str
    type: MessageType = field(default=MessageType.DRAWING_END, init=False)


@dataclass
class ColorChangeMessage(BaseMessage):
    """색상 변경 메시지

    Attributes:
        user_id: 사용자 ID
        color: 새로운 펜 색상 (hex 형식, 예: "#FF0000")
        alpha: 투명도 (0.0 ~ 1.0, 기본값 1.0)
    """

    user_id: str
    color: str
    alpha: float = 1.0
    type: MessageType = field(default=MessageType.COLOR_CHANGE, init=False)
