# Task: Server Core (WebSocket 서버 기본 구조)

## 개요

WebSocket 서버 기본 구조 및 메시지 라우팅 시스템

## 목표

- [ ] WebSocket 서버 초기화 (asyncio + websockets)
- [ ] 클라이언트 연결/해제 처리
- [ ] 메시지 수신 및 라우팅
- [ ] 브로드캐스트 시스템 (세션 내 모든 클라이언트에게 전송)
- [ ] 에러 처리 및 로깅
- [ ] 유닛 테스트 작성

## 상세 요구사항

### 서버 구조
```python
class ScreenPartyServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.session_manager = SessionManager()
        self.clients: Dict[str, WebSocketServerProtocol] = {}

    async def start(self):
        """서버 시작"""

    async def handle_client(self, websocket: WebSocketServerProtocol):
        """클라이언트 연결 처리"""

    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """메시지 라우팅"""

    async def broadcast(self, session_id: str, message: dict, exclude_user_id: str = None):
        """세션 내 브로드캐스트"""
```

### 메시지 타입
- `create_session`: 세션 생성 (호스트)
- `join_session`: 세션 참여 (게스트)
- `line_start`: 선 시작
- `line_update`: 선 업데이트
- `line_end`: 선 종료
- `line_remove`: 선 삭제
- `ping`/`pong`: 연결 유지

### 에러 처리
- WebSocket 연결 실패
- 잘못된 메시지 형식
- 존재하지 않는 세션
- 권한 없는 작업 (예: 게스트가 세션 삭제 시도)

### 포트 설정
- 기본 포트: 8765
- 환경 변수로 변경 가능 (`SCREEN_PARTY_PORT`)

## 기술 결정

### websockets 라이브러리 사용
```python
import asyncio
import websockets
from websockets.server import WebSocketServerProtocol

async def main():
    server = ScreenPartyServer(host="0.0.0.0", port=8765)
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
```

### JSON 메시지 포맷
- 모든 메시지는 JSON 형식
- `type` 필드로 메시지 종류 구분
- 에러 응답: `{"type": "error", "message": "..."}`

## TODO

- [x] ScreenPartyServer 클래스 구현 (server.py)
- [x] 메시지 핸들러 함수들 구현
- [x] 브로드캐스트 로직 구현
- [x] 에러 처리 및 로깅
- [x] CLI 진입점 (main 함수)
- [x] 유닛 테스트 작성 (test_server.py)
- [ ] 간단한 테스트 클라이언트 작성 (수동 테스트용 - P1에서 진행)

## 클로드 코드 일기

### 2025-12-28 - WebSocket 서버 구현 완료

**상태**: 🟡 준비중 → ✅ 완료

**진행 내용**:
- ✅ `server/src/screen_party_server/server.py` 생성
  - `ScreenPartyServer` 클래스 구현
  - WebSocket 연결 관리 (clients dict, websocket_to_user 역매핑)
  - 메시지 핸들러:
    - `handle_create_session`: 세션 생성 (호스트)
    - `handle_join_session`: 세션 참여 (게스트)
    - `handle_ping`: 핑/퐁
    - `handle_drawing_message`: 드로잉 메시지 브로드캐스트
  - 브로드캐스트 시스템 (세션 내 모든 클라이언트에게 전송, exclude 옵션)
  - 클라이언트 정리 로직 (호스트 disconnection 시 세션 만료, 게스트 disconnection 시 알림)
  - 에러 처리 및 로깅 (logging 모듈)
  - CLI 진입점 (main 함수, 환경 변수 지원)
- ✅ `server/tests/test_server.py` 생성
  - 15개 유닛 테스트 작성
  - 모든 테스트 통과 (15/15 in 0.08s)
- ✅ websockets 14.x 최신 API 사용 (ServerConnection)

**테스트 결과**:
```
test_server.py::TestScreenPartyServer::test_server_initialization PASSED
test_server.py::TestScreenPartyServer::test_create_session PASSED
test_server.py::TestScreenPartyServer::test_join_session PASSED
test_server.py::TestScreenPartyServer::test_join_nonexistent_session PASSED
test_server.py::TestScreenPartyServer::test_ping_pong PASSED
test_server.py::TestScreenPartyServer::test_broadcast PASSED
test_server.py::TestScreenPartyServer::test_broadcast_exclude_user PASSED
test_server.py::TestScreenPartyServer::test_find_user_session PASSED
test_server.py::TestScreenPartyServer::test_cleanup_client_host PASSED
test_server.py::TestScreenPartyServer::test_cleanup_client_guest PASSED
test_server.py::TestScreenPartyServer::test_send_error PASSED
test_server.py::TestScreenPartyServer::test_handle_message_invalid_type PASSED
test_server.py::TestScreenPartyServer::test_handle_message_missing_type PASSED
test_server.py::TestScreenPartyServer::test_drawing_message_not_authenticated PASSED
test_server.py::TestScreenPartyServer::test_drawing_message_broadcast PASSED

15 passed in 0.08s
```

**주요 결정사항**:
- websockets 14.x 최신 API 사용 (`websockets.asyncio.server.ServerConnection`)
- 환경 변수 지원: `SCREEN_PARTY_HOST`, `SCREEN_PARTY_PORT`
- 기본 포트: 8765
- 세션 cleanup 태스크는 서버 시작 시 자동으로 백그라운드 실행
- 호스트 disconnection 시 먼저 알림 전송 후 세션 만료 (게스트가 알림을 받을 수 있도록)

**다음 단계**:
P0 마지막 task:
1. client-core: PyQt6 GUI 기본 구조 및 WebSocket 클라이언트

P1 tasks (서버 완료 후):
1. testing: 간단한 클릭 소통 테스트 (수동 테스트 클라이언트 포함)
2. server-deployment: Docker 이미지

---

> **다음 Claude Code에게**:
> - 서버 실행: `uv run python server/main.py`
> - 환경 변수로 호스트/포트 변경 가능
> - SessionManager cleanup task는 자동으로 백그라운드 실행됨
> - websockets 14.x 사용 (legacy API deprecated)
