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
- [x] test_session.py 작성 (세션 생성, 조회만) - ✅ 14개 테스트
- [x] test_server.py 작성 (클릭 메시지 브로드캐스트) - ✅ 15개 테스트
- [x] test_integration.py 작성 (서버-호스트-게스트 간 양방향 통신) - ✅ 3개 테스트
- [ ] test_client.py 작성 (WebSocket 클라이언트 유닛 테스트)
- [ ] .github/workflows/test.yml 작성 (CI/CD)

### P2 이후: 확장 테스트 (나중에 추가)
- [ ] test_spline.py (Spline 보간)
- [ ] test_coordinate_mapper.py (좌표 변환)
- [ ] test_animator.py (페이드아웃)
- [ ] 드로잉 통합 테스트
- [ ] codecov 설정

## 클로드 코드 일기

### 2025-12-28 - 서버 유닛 테스트 완료

**상태**: 🟡 준비중 → 🟢 진행중

**진행 내용**:
- ✅ test_session.py 작성 완료 (14개 테스트)
  - 세션 ID 생성 및 중복 방지
  - 세션 CRUD 작업
  - 게스트 추가/제거
  - 세션 만료 및 cleanup
  - 백그라운드 cleanup 태스크
  - 세션 활동 시간 업데이트
- ✅ test_server.py 작성 완료 (15개 테스트)
  - 서버 초기화
  - 세션 생성/참여
  - 핑/퐁
  - 브로드캐스트 (일반, 특정 사용자 제외)
  - 사용자 세션 찾기
  - 클라이언트 정리 (호스트/게스트)
  - 에러 처리
  - 드로잉 메시지 처리
- ✅ pytest 설정 완료 (pyproject.toml)
  - asyncio_mode = "auto"
  - testpaths = ["server/tests", "client/tests"]

**테스트 결과**:
- ✅ **29/29 테스트 통과** (100%)
- 실행 시간: 1.09초
- Python 3.13.5, pytest 8.3.4
- pytest-asyncio 사용

**주요 결정사항**:
- AsyncMock 사용: WebSocket 연결을 Mock으로 대체
- pytest.mark.asyncio: 비동기 테스트 지원
- 각 테스트는 독립적으로 실행 가능
- 서버 테스트에서는 실제 WebSocket 서버를 띄우지 않음 (유닛 테스트)

**미구현/다음 단계**:
- [ ] test_client.py 작성 (클라이언트 WebSocket 연결)
- [ ] test_integration.py 작성 (실제 서버-클라이언트 통합 테스트)
- [ ] GitHub Actions CI/CD 설정
- [ ] 커버리지 측정 및 리포트

**커버리지**:
- 아직 측정 안 함 (pytest-cov 설치되어 있음)
- 다음 명령어로 측정 가능: `pytest --cov=server/src --cov-report=term-missing`

---

### 2026-01-01 - 통합 테스트 완료 및 드로잉 메시지 브로드캐스트 수정

**상태**: 🟢 진행중

**진행 내용**:
- ✅ test_integration.py 작성 완료 (3개 테스트)
  - 호스트 세션 생성 + 게스트 2명 참여 + 양방향 통신 (드로잉 메시지)
  - 게스트 나가기 → 호스트가 guest_left 알림 수신
  - 호스트 나가기 → 게스트가 session_expired 알림 수신
- ✅ 서버 코드 버그 수정
  - `handle_drawing_message`에서 브로드캐스트 시 **송신자를 제외**하도록 수정
  - 기존: `await self.broadcast(session_id, data)`
  - 수정: `await self.broadcast(session_id, data, exclude_user_id=user_id)`
- ✅ 서버 유닛 테스트 수정
  - `test_drawing_message_broadcast`: 송신자가 자신의 메시지를 받지 않도록 테스트 변경
- ✅ 패키지 __init__.py 수정
  - `screen_party_server/__init__.py`에 ScreenPartyServer export 추가
  - `screen_party_client/__init__.py`에 WebSocketClient export 추가

**테스트 결과**:
- ✅ **유닛 테스트 29개 통과** (1.07초)
- ✅ **통합 테스트 3개 통과** (1.95초)
- ✅ **총 32개 테스트 100% 통과**

**주요 결정사항**:
- 통합 테스트는 `tests/` 디렉토리에 별도로 관리
- pytest 실행: `uv run pytest` (유닛 테스트만), `uv run pytest tests/test_integration.py` (통합 테스트)
- 드로잉 메시지는 송신자에게 에코백하지 않음 (다른 참여자에게만 브로드캐스트)

**다음 단계**:
- [ ] test_client.py 작성 (클라이언트 WebSocket 유닛 테스트)
- [ ] CI/CD 설정 (GitHub Actions)
- [ ] 커버리지 측정 (`pytest --cov`)

---

> **다음 Claude Code에게**:
> - **통합 테스트 완료**: 서버-호스트-게스트 간 실시간 양방향 통신 검증됨
> - 드로잉 메시지는 송신자를 제외하고 브로드캐스트됨 (중요!)
> - 통합 테스트 실행: `uv run pytest tests/test_integration.py -v`
> - 전체 테스트 실행: `uv run pytest && uv run pytest tests/test_integration.py`
> - client-core는 구현되어 있지만 **유닛 테스트가 아직 없음** (test_client.py 필요)
