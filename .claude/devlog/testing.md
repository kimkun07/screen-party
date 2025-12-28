# Task: Testing (초기 테스트 - 간단한 클릭 소통)

## 개요

**P1 단계**: 기본 인프라가 작동하는지 검증하기 위한 간단한 테스트 작성

이 단계에서는 복잡한 드로잉 기능이 아닌, **간단한 클릭 좌표 전송**만 구현하여 서버-클라이언트 통신이 제대로 작동하는지 확인합니다. 이후 기능을 추가할 때마다 테스트를 확장합니다.

## 목표 (P1 - 초기 단계)

- [ ] 서버 기본 유닛 테스트
- [ ] 클라이언트 기본 유닛 테스트
- [ ] 간단한 통합 테스트 (클릭 좌표 전송)
- [ ] CI/CD 파이프라인 (GitHub Actions)

## 상세 요구사항

### P1: 간단한 클릭 소통 테스트

**목적**: 복잡한 드로잉 전에 기본 통신이 작동하는지 검증

#### 구현할 기능
1. 게스트가 화면 클릭 → 서버로 좌표 전송
2. 서버가 모든 클라이언트에게 브로드캐스트
3. 호스트 화면에 클릭 위치 표시 (간단한 점)

```python
# 간단한 클릭 메시지 (P1)
{
  "type": "click",
  "user_id": "uuid-1234",
  "x": 100,
  "y": 200
}
```

#### 서버 유닛 테스트 (P1)
- `test_session.py`: 세션 생성, 조회
- `test_server.py`: 클릭 메시지 브로드캐스트
- `test_models.py`: 기본 데이터 모델

#### 클라이언트 유닛 테스트 (P1)
- `test_client.py`: WebSocket 연결 및 메시지 송수신
- `test_click_handler.py`: 클릭 이벤트 핸들링

#### 통합 테스트 (P1)
간단한 시나리오:
1. 호스트 세션 생성
2. 게스트 참여
3. 게스트가 클릭 (좌표 전송)
4. 호스트가 클릭 좌표 수신 확인

```python
import pytest
import asyncio
from screen_party_server import ScreenPartyServer
from screen_party_client.network.client import WebSocketClient

@pytest.mark.asyncio
async def test_simple_click_communication():
    """P1 테스트: 간단한 클릭 좌표 전송"""
    # 서버 시작
    server = ScreenPartyServer("localhost", 8765)
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.1)  # 서버 시작 대기

    # 호스트 연결
    host_client = WebSocketClient("ws://localhost:8765")
    await host_client.connect()
    await host_client.send_message({"type": "create_session", "host_name": "Host"})
    response = await host_client.receive_message()
    assert response["type"] == "session_created"
    session_id = response["session_id"]

    # 게스트 연결
    guest_client = WebSocketClient("ws://localhost:8765")
    await guest_client.connect()
    await guest_client.send_message({
        "type": "join_session",
        "session_id": session_id,
        "guest_name": "Guest"
    })
    response = await guest_client.receive_message()
    assert response["type"] == "join_success"

    # 게스트가 클릭 (좌표 전송)
    await guest_client.send_message({
        "type": "click",
        "x": 100,
        "y": 200
    })

    # 호스트가 클릭 좌표 수신
    click_msg = await host_client.receive_message()
    assert click_msg["type"] == "click"
    assert click_msg["x"] == 100
    assert click_msg["y"] == 200

    # 정리
    await host_client.close()
    await guest_client.close()
    server_task.cancel()
```

### P2 이후: 확장 테스트 (나중에 추가)

P2부터는 복잡한 기능 테스트를 추가합니다:
- `test_spline.py`: Spline 보간 로직
- `test_coordinate_mapper.py`: 좌표 변환
- `test_animator.py`: 페이드아웃 애니메이션
- 전체 드로잉 플로우 통합 테스트

### CI/CD 파이프라인
- GitHub Actions 워크플로우
- 모든 PR에서 테스트 자동 실행
- Python 3.11, 3.12 버전 테스트
- 테스트 실패 시 PR 병합 차단

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install Poetry
        run: curl -sSL https://install.python-poetry.org | python3 -
      - name: Install dependencies
        run: poetry install
      - name: Run tests
        run: poetry run pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 기술 결정

### pytest 사용
- 표준 Python 테스트 프레임워크
- pytest-asyncio로 비동기 테스트 지원
- pytest-cov로 커버리지 측정

### 테스트 커버리지 목표
- 80% 이상 (핵심 로직)
- GUI 코드는 제외 가능 (테스트 어려움)

## TODO

### P1: 초기 테스트 (지금 구현)
- [ ] test_session.py 작성 (세션 생성, 조회만)
- [ ] test_server.py 작성 (클릭 메시지 브로드캐스트)
- [ ] test_client.py 작성 (WebSocket 연결)
- [ ] test_integration.py 작성 (간단한 클릭 소통 시나리오)
- [ ] .github/workflows/test.yml 작성 (CI/CD)

### P2 이후: 확장 테스트 (나중에 추가)
- [ ] test_spline.py (Spline 보간)
- [ ] test_coordinate_mapper.py (좌표 변환)
- [ ] test_animator.py (페이드아웃)
- [ ] 드로잉 통합 테스트
- [ ] codecov 설정

## 클로드 코드 일기

_이 섹션은 작업 진행 시 업데이트됩니다._
