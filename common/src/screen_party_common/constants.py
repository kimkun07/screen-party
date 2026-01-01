"""공통 상수 정의"""

# 서버 설정
DEFAULT_PORT = 8765

# 세션 설정
DEFAULT_SESSION_TIMEOUT_MINUTES = 60
SESSION_ID_LENGTH = 6

# WebSocket 메시지 타입
MSG_TYPE_CREATE_SESSION = "create_session"
MSG_TYPE_SESSION_CREATED = "session_created"
MSG_TYPE_JOIN_SESSION = "join_session"
MSG_TYPE_GUEST_JOINED = "guest_joined"
MSG_TYPE_PING = "ping"
MSG_TYPE_PONG = "pong"
MSG_TYPE_ERROR = "error"
MSG_TYPE_SESSION_EXPIRED = "session_expired"

# 드로잉 메시지 타입 (향후 사용)
MSG_TYPE_LINE_START = "line_start"
MSG_TYPE_LINE_UPDATE = "line_update"
MSG_TYPE_LINE_END = "line_end"
MSG_TYPE_LINE_REMOVE = "line_remove"
