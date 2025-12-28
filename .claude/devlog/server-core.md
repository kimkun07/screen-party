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

- [ ] ScreenPartyServer 클래스 구현 (server.py)
- [ ] 메시지 핸들러 함수들 구현
- [ ] 브로드캐스트 로직 구현
- [ ] 에러 처리 및 로깅
- [ ] CLI 진입점 (main 함수)
- [ ] 유닛 테스트 작성 (test_server.py)
- [ ] 간단한 테스트 클라이언트 작성 (수동 테스트용)

## 클로드 코드 일기

_이 섹션은 작업 진행 시 업데이트됩니다._
