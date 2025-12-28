# Task: Client Core (클라이언트 기본 GUI 및 연결)

## 개요

PyQt6 기반 클라이언트 GUI 및 WebSocket 연결 관리

## 목표

- [ ] PyQt6 메인 윈도우 구현
- [ ] 모드 선택 UI (Host/Guest)
- [ ] WebSocket 클라이언트 연결 관리
- [ ] 비동기 처리 (asyncio + PyQt6 통합)
- [ ] 기본 에러 처리 및 사용자 피드백
- [ ] 유닛 테스트 작성

## 상세 요구사항

### 메인 윈도우 구조
```
┌─────────────────────────────┐
│   Screen Party              │
├─────────────────────────────┤
│                             │
│   [Host Mode]               │
│                             │
│   [Guest Mode]              │
│                             │
└─────────────────────────────┘
```

### Host Mode 플로우
1. "Host Mode" 버튼 클릭
2. 서버 연결 (WebSocket)
3. `create_session` 메시지 전송
4. 세션 ID 받아서 표시
5. "게임 창 선택" 버튼 활성화

### Guest Mode 플로우
1. "Guest Mode" 버튼 클릭
2. 세션 ID 입력 다이얼로그 표시
3. 서버 연결 (WebSocket)
4. `join_session` 메시지 전송
5. 성공 시 "영역 설정" 버튼 활성화

### asyncio + PyQt6 통합
- `qasync` 라이브러리 사용
- asyncio 이벤트 루프를 PyQt6 이벤트 루프와 통합
- WebSocket 연결을 비동기로 처리

```python
import asyncio
import sys
from qasync import QEventLoop
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)
loop = QEventLoop(app)
asyncio.set_event_loop(loop)

# 메인 윈도우 실행
window = MainWindow()
window.show()

with loop:
    loop.run_forever()
```

## 기술 결정

### qasync 사용
- PyQt6의 이벤트 루프와 asyncio 통합
- WebSocket 연결을 GUI 스레드와 분리하지 않고도 비동기 처리 가능
- 의존성: `qasync`

### WebSocket 클라이언트
```python
import websockets

class WebSocketClient:
    def __init__(self, url: str):
        self.url = url
        self.websocket = None

    async def connect(self):
        self.websocket = await websockets.connect(self.url)

    async def send_message(self, message: dict):
        await self.websocket.send(json.dumps(message))

    async def receive_message(self) -> dict:
        message = await self.websocket.recv()
        return json.loads(message)
```

## TODO

- [ ] MainWindow 클래스 구현 (gui/main_window.py)
- [ ] WebSocketClient 클래스 구현 (network/client.py)
- [ ] Host Mode UI 및 로직
- [ ] Guest Mode UI 및 로직
- [ ] qasync 통합 (main.py)
- [ ] 에러 처리 및 사용자 피드백
- [ ] 유닛 테스트 작성 (test_main_window.py, test_client.py)

## 클로드 코드 일기

_이 섹션은 작업 진행 시 업데이트됩니다._
