# Screen Party - 프로젝트 전체 진행 상황

> 이 문서는 screen-party 프로젝트의 전체 진행 상황을 관리합니다.
> 클로드 코드는 작업 시작 시 이 파일을 먼저 읽고 어떤 task를 진행해야 할지 확인합니다.

## 프로젝트 개요

**screen-party**는 실시간 화면 드로잉 공유 애플리케이션입니다.

### 핵심 시나리오

1. **연결 및 준비**
   - 호스트: 프로그램 실행 → 6자리 세션 번호 발급 → 게임 창 선택 → 투명 오버레이 생성
   - 게스트: 세션 번호 입력 → 접속 → 디스코드 화면에서 게임 영역 지정 (좌표 매핑)

2. **실시간 드로잉**
   - 게스트가 마우스로 그림 → Spline으로 변환 → 실시간 전송
   - 모든 참여자 화면에 매끄러운 곡선 표시
   - 페이드아웃: 마우스를 떼면 2초 유지 → 1초 동안 투명하게 사라짐

3. **고급 기능**
   - 장시간 모드: 선이 사라지지 않고 유지 (전략 브리핑용)
   - 개별 초기화: ESC 키로 자신이 그린 선만 제거
   - 색상 구분: 각 게스트별 펜 색상 설정
   - 창 관리 동기화: 호스트가 게임 최소화 시 오버레이도 숨김

### 기술 스택

- **언어**: Python 3.13+
- **패키지 관리**: uv (workspace 기반 monorepo)
- **개발환경**: devcontainer (VS Code)
- **서버**: WebSocket (asyncio, websockets 라이브러리)
- **클라이언트 GUI**: PyQt6 (크로스 플랫폼 지원)
- **드로잉**: scipy (Spline 보간), PyQt6 QPainter
- **테스트**: pytest, pytest-asyncio, pytest-cov
- **코드 품질**: black, ruff, pyright
- **배포**:
  - 서버: Docker 이미지 (uv 기반)
  - 클라이언트: PyInstaller (Windows .exe, Linux AppImage/Binary)

## Task 진행 상황

| 우선순위 | Task | 상태 | 설명 | 의존성 |
|---------|------|------|------|--------|
| P0 | project-structure | ✅ 완료 | uv workspace monorepo 구조 설정 + devcontainer | - |
| P0 | session-management | ✅ 완료 | 세션 생성/관리 (6자리 코드) | project-structure |
| P0 | server-core | ✅ 완료 | WebSocket 서버 기본 구조 | project-structure, session-management |
| P0 | client-core | ✅ 완료 | 클라이언트 기본 GUI 및 연결 (통합 테스트 완료) | project-structure |
| P1 | testing | 🟢 진행중 | 유닛 테스트 (서버 29개) + 통합 테스트 (3개) 완료 | server-core, client-core |
| P1 | server-deployment | ✅ 완료 | Docker 이미지 및 배포 | server-core, testing |
| P1 | client-deployment | 🟡 준비중 | 클라이언트 실행 파일 빌드 | client-core, testing |
| P2 | host-overlay | 🟡 준비중 | 호스트 투명 오버레이 | client-core, testing |
| P2 | guest-calibration | 🟡 준비중 | 게스트 영역 설정 (좌표 매핑) | client-core, testing |
| P2 | drawing-engine | 🟡 준비중 | 실시간 드로잉 (Spline) | server-core, client-core, testing |
| P2 | fade-animation | 🟡 준비중 | 페이드아웃 애니메이션 | drawing-engine |
| P3 | persistence-mode | 🟡 준비중 | 장시간 그림 모드 | drawing-engine |
| P3 | color-system | 🟡 준비중 | 색상 설정 시스템 | drawing-engine |
| P3 | window-sync | 🟡 준비중 | 창 관리 동기화 | host-overlay |

### 상태 범례

- 🔴 **차단됨** (Blocked): 다른 작업이 완료되어야 진행 가능
- 🟡 **준비중** (Not Started): 아직 시작 안 함
- 🟢 **진행중** (In Progress): 현재 작업 중
- ✅ **완료** (Completed): 작업 완료
- ⏸️ **보류** (On Hold): 임시로 중단

## Task 의존성 다이어그램

```
[project-structure] (P0)
    ├─> [session-management] (P0)
    │       └─> [server-core] (P0)
    │               └─> [testing] (P1) ← 간단한 클릭 소통 테스트
    │                       ├─> [server-deployment] (P1)
    │                       ├─> [drawing-engine] (P2)
    │                       │       ├─> [fade-animation] (P2)
    │                       │       ├─> [persistence-mode] (P3)
    │                       │       └─> [color-system] (P3)
    │                       ├─> [host-overlay] (P2)
    │                       │       └─> [window-sync] (P3)
    │                       └─> [guest-calibration] (P2)
    │
    └─> [client-core] (P0)
            └─> [testing] (P1)
                    └─> [client-deployment] (P1)
```

## 프로젝트 구조

```
screen-party/
├── pyproject.toml              # uv workspace 루트
├── uv.lock                     # 의존성 잠금 파일
├── common/                     # 공통 패키지
│   ├── pyproject.toml
│   ├── src/
│   │   └── screen_party_common/
│   │       ├── __init__.py
│   │       ├── models.py       # Session, Guest
│   │       └── constants.py    # 공통 상수
│   └── tests/
├── server/
│   ├── pyproject.toml          # 서버 의존성
│   ├── Dockerfile              # 서버 Docker 이미지 (uv 기반)
│   ├── src/
│   │   └── screen_party_server/
│   │       ├── __init__.py
│   │       ├── server.py       # WebSocket 서버
│   │       ├── session.py      # 세션 관리
│   │       └── utils.py
│   └── tests/
│       ├── test_server.py
│       └── test_session.py
├── client/
│   ├── pyproject.toml          # 클라이언트 의존성
│   ├── src/
│   │   └── screen_party_client/
│   │       ├── __init__.py
│   │       ├── main.py         # GUI 진입점
│   │       ├── gui/
│   │       │   ├── main_window.py
│   │       │   ├── overlay.py  # 투명 오버레이
│   │       │   └── calibration.py
│   │       ├── network/
│   │       │   └── client.py   # WebSocket 클라이언트
│   │       ├── drawing/
│   │       │   ├── engine.py   # 드로잉 엔진
│   │       │   └── spline.py   # Spline 변환
│   │       └── utils.py
│   └── tests/
│       ├── test_overlay.py
│       └── test_drawing.py
├── docker-compose.yml          # 로컬 테스트용
├── .gitignore
├── README.md
└── .claude/
    ├── CLAUDE.md
    └── devlog/
        └── ...
```

## 프로토콜 설계 (초안)

### WebSocket 메시지 포맷

```json
// 세션 생성 (호스트 → 서버)
{
  "type": "create_session",
  "host_name": "Player1",
  "screen_resolution": {"width": 1920, "height": 1080}
}

// 세션 생성 응답 (서버 → 호스트)
{
  "type": "session_created",
  "session_id": "ABC123",
  "host_id": "uuid-1234"
}

// 세션 참여 (게스트 → 서버)
{
  "type": "join_session",
  "session_id": "ABC123",
  "guest_name": "Player2"
}

// 선 시작 (게스트 → 서버)
{
  "type": "line_start",
  "line_id": "uuid-5678",
  "user_id": "uuid-1234",
  "color": "#FF0000",
  "start_point": {"x": 100, "y": 200}
}

// 선 업데이트 (게스트 → 서버)
{
  "type": "line_update",
  "line_id": "uuid-5678",
  "points": [
    {"x": 100, "y": 200, "t": 0.0},
    {"x": 105, "y": 205, "t": 0.1},
    {"x": 110, "y": 215, "t": 0.2}
  ]
}

// 선 종료 (게스트 → 서버)
{
  "type": "line_end",
  "line_id": "uuid-5678"
}

// 선 삭제 (자동/수동) (서버 → 모든 클라이언트)
{
  "type": "line_remove",
  "line_id": "uuid-5678",
  "fade_duration": 1.0  // 초 (0이면 즉시 삭제)
}
```

## 주요 기술 결정

### 1. GUI 프레임워크: PyQt6

**선택 이유**:
- 크로스 플랫폼 지원 (Windows, Linux, macOS)
- 투명 오버레이 창 지원 (Qt::WindowStaysOnTopHint, Qt::FramelessWindowHint)
- 고성능 드로잉 (QPainter, QGraphicsScene)
- 창 관리 API (window geometry, focus events)

**대안**:
- ~~Tkinter~~: 투명 오버레이 지원 부족
- ~~Kivy~~: 데스크톱 앱에 과한 복잡도

### 2. 클라이언트 배포: PyInstaller

**선택 이유**:
- 단일 실행 파일 생성 (--onefile 옵션)
- PyQt6 지원
- Windows .exe 및 Linux binary 생성 가능

**대안**:
- ~~py2exe~~: Windows 전용
- ~~cx_Freeze~~: PyQt6 호환성 이슈

### 3. Spline 보간: scipy.interpolate

**선택 이유**:
- `scipy.interpolate.make_interp_spline()` 사용
- 부드러운 곡선 생성 (cubic spline)
- 적은 포인트로도 매끄러운 결과

### 4. WebSocket 라이브러리: websockets

**선택 이유**:
- asyncio 기반 비동기 처리
- 간단한 API
- Python 표준 라이브러리와 호환성 좋음

## 블로커 및 주요 질문

### 해결됨
- ✅ GUI 프레임워크 선택: PyQt6
- ✅ 클라이언트 배포 방법: PyInstaller
- ✅ Spline 라이브러리: scipy.interpolate

### 미해결
- ❓ 세션 ID 생성 알고리즘: 단순 6자리 랜덤? 충돌 방지 어떻게?
- ❓ 네트워크 타임아웃 정책: 몇 초 동안 업데이트 없으면 선 제거?
- ❓ 최대 동시 접속자 수 제한: 무제한? 아니면 제한 (예: 10명)?
- ❓ 색상 팔레트: 미리 정의된 색상? 커스텀 RGB?

## 최근 업데이트

### 2026-01-01 - 서버 배포 완료 (Docker)

**작업 내용**:
- ✅ feature/server-deployment 브랜치 생성
- ✅ Dockerfile 보안 개선: 비 root 유저 추가 (appuser, UID 1000)
- ✅ devcontainer.json에 docker-in-docker feature 추가
- ✅ devcontainer rebuild 완료
- ✅ Docker 이미지 빌드 테스트 성공
- ✅ docker-compose로 서버 실행 테스트 성공
- ✅ 클라이언트 연결 및 세션 생성 테스트 성공

**테스트 결과**:
- ✅ Docker 이미지 빌드 성공 (screen-party-server:latest)
- ✅ 서버 정상 실행 (0.0.0.0:8765)
- ✅ 클라이언트 WebSocket 연결 성공
- ✅ 세션 생성 API 정상 동작

**주요 개선사항**:
- Dockerfile 보안 강화 (비 root 유저)
- Multi-stage build로 이미지 최적화
- uv 기반 의존성 관리

**완료 상태**:
- ✅ **P1 server-deployment Task 완료**
- 프로덕션 배포 준비 완료

---

### 2026-01-01 - 통합 테스트 완료 및 P0 완성

**작업 내용**:
- ✅ 통합 테스트 작성 완료 (tests/test_integration.py)
  - 호스트 세션 생성 + 게스트 2명 참여 + 양방향 통신 테스트
  - 게스트/호스트 나가기 시나리오 테스트
- ✅ 서버 드로잉 메시지 브로드캐스트 수정
  - 송신자를 제외하고 브로드캐스트하도록 수정
  - `server.py:202` `exclude_user_id=user_id` 추가
- ✅ 서버 유닛 테스트 수정 (test_drawing_message_broadcast)
- ✅ 패키지 export 추가 (__init__.py)
- ✅ README.md 업데이트
  - devcontainer Git credential 설정 방법 추가
  - devcontainer 사용 이유를 "YOLO 모드 실행"으로 명확화

**테스트 결과**:
- ✅ **유닛 테스트 29개 통과** (server 15개 + session 14개)
- ✅ **통합 테스트 3개 통과** (서버-호스트-게스트 간 양방향 통신)
- ✅ **총 32개 테스트 100% 통과**

**주요 결정사항**:
- **P0 Task 완료**: project-structure, session-management, server-core, client-core 모두 완료
- 통합 테스트로 실제 통신 검증 완료
- 다음 단계: P1 (testing CI/CD 추가, server/client deployment) 또는 P2 (드로잉 기능 구현)

**다음 단계**:
1. P1 완성: CI/CD, Docker 배포, 클라이언트 빌드
2. P2 시작: host-overlay (투명 오버레이), guest-calibration (좌표 매핑)
3. P2 진행: drawing-engine (Spline 드로잉)

---

### 2025-12-30 - uv Workspace로 마이그레이션

**작업 내용**:
- ✅ pip monorepo → uv workspace 마이그레이션 완료
- ✅ common/ 패키지 생성 (Session, Guest 모델 분리)
- ✅ server/client에서 common 참조하도록 변경
- ✅ Dockerfile 작성 (uv 기반 multi-stage build)
- ✅ uv sync로 의존성 관리 (uv.lock)
- ✅ pytest 29개 테스트 모두 통과

**주요 변경사항**:
- 패키지 관리자: pip → uv
- 공통 코드: server에서 common/으로 분리
- Docker: server/Dockerfile에서 uv 사용
- 의존성: uv.lock으로 잠금

**다음 단계**:
1. Dockerfile 빌드 테스트
2. devcontainer.json에 uv 추가

---

### 2025-12-28 - 개발환경을 pip monorepo로 전환 (레거시)

**작업 내용**:
- ✅ Poetry 제거 및 pip 기반 monorepo로 전환
- ✅ devcontainer 설정 추가 (.devcontainer/devcontainer.json)
  - Python 3.13 이미지 사용
  - VS Code 확장 프로그램 자동 설치
  - Git 설정 자동화
- ✅ requirements.txt 파일들 생성
  - `server/requirements.txt`: websockets, pytest-asyncio
  - `client/requirements.txt`: PyQt6, websockets, scipy, numpy, qasync
  - `dev-requirements.txt`: black, ruff, pytest 등
- ✅ pyproject.toml 간소화 (도구 설정만)

**주요 결정**:
- Poetry → pip: 더 간단하고 표준적인 의존성 관리
- devcontainer: 팀원 간 개발환경 통일
- Python 3.13.5 사용

**다음 단계**:
1. client-core 완성 (테스트 작성)
2. 통합 테스트 작성

---

### 2025-12-28 - 클라이언트 기본 구조 구현

**작업 내용**:
- ✅ MainWindow 클래스 구현 (276 lines)
  - PyQt6 기반 GUI (Host/Guest 모드)
  - 세션 ID 표시 및 입력
  - PyQt Signal/Slot 이벤트 처리
- ✅ WebSocketClient 클래스 구현 (137 lines)
  - websockets 14.x 비동기 연결
  - JSON 메시지 송수신
  - 에러 처리 및 로깅
- ✅ Host/Guest 모드 플로우 구현

**주요 결정**:
- qasync로 asyncio와 PyQt6 통합
- Signal/Slot으로 UI 업데이트

**다음 단계**:
1. 클라이언트 유닛 테스트 작성
2. 서버-클라이언트 통합 테스트
3. 투명 오버레이 창 구현 (host-overlay)

---

### 2025-12-28 - 서버 유닛 테스트 완료

**작업 내용**:
- ✅ test_session.py (14개 테스트)
- ✅ test_server.py (15개 테스트)
- ✅ pytest 설정 (pyproject.toml)

**테스트 결과**:
- ✅ 29/29 테스트 통과 (100%)
- 실행 시간: 1.09초

**다음 단계**:
1. 클라이언트 테스트 작성
2. 통합 테스트 작성
3. CI/CD 설정 (GitHub Actions)

---

### 2025-12-28 - P0 server-core 완료

**작업 내용**:
- ✅ ScreenPartyServer 클래스 구현 (server.py)
  - WebSocket 연결 관리 (clients, websocket_to_user)
  - 메시지 핸들러 (create_session, join_session, ping, drawing_message)
  - 브로드캐스트 시스템 (exclude 옵션 지원)
  - 클라이언트 정리 로직 (호스트/게스트 disconnection)
  - 에러 처리 및 로깅
  - CLI 진입점 (환경 변수 지원)
- ✅ 유닛 테스트 15개 작성 및 통과

**테스트 결과**:
- 15/15 tests passed in 0.08s

**주요 결정**:
- websockets 14.x 최신 API 사용 (ServerConnection)
- 기본 포트: 8765 (환경 변수로 변경 가능)
- 호스트 disconnection 시 세션 만료 전 알림 전송

**다음 단계**:
1. client-core: PyQt6 GUI 및 WebSocket 클라이언트

### 2025-12-28 - P0 session-management 완료

**작업 내용**:
- ✅ Session, Guest 데이터 모델 정의 (models.py)
- ✅ SessionManager 클래스 구현 (session.py)
  - 6자리 세션 ID 생성 (대문자+숫자, 최대 10회 재시도)
  - 세션 CRUD 작업 (create, get, add_guest, remove_guest, expire, delete)
  - 타임아웃 처리 (기본 60분)
  - 백그라운드 cleanup 태스크 (5분마다)
- ✅ 유닛 테스트 작성 (14개 테스트, 모두 통과)

**테스트 결과**:
- 14/14 tests passed in 1.06s

**주요 결정**:
- 세션 ID: 36^6 = 2.1B 조합으로 충돌 확률 극히 낮음
- 백그라운드 cleanup: asyncio task로 자동 실행

**다음 단계**:
1. server-core: WebSocket 서버 구현 (SessionManager 통합)
2. client-core: PyQt6 GUI 기본 구조

### 2025-12-28 - P0 project-structure 완료

**작업 내용**:
- ✅ Python 3.13.4 설치 (pyenv)
- ✅ Poetry 2.2.1 설치
- ✅ Poetry monorepo 구조 생성
  - 루트, server, client 각각 독립 pyproject.toml
  - server: websockets 14.2
  - client: PyQt6, scipy, numpy, qasync
- ✅ 의존성 설치 및 import 테스트 성공

**주요 결정**:
- PyInstaller는 Python 3.13 미지원으로 P1까지 보류

**다음 단계**:
1. session-management: 6자리 세션 ID 생성
2. server-core: WebSocket 서버 구현
3. client-core: PyQt6 GUI 기본 구조

### 2025-12-28 - 프로젝트 초기 설정

**작업 내용**:
- CLAUDE.md 업데이트 (screen-party 프로젝트용)
- devlog 디렉토리 구조 생성 (14개 task)
- main.md 작성 (프로젝트 개요, Task 목록, 우선순위)
- 우선순위 재조정 (테스트/배포 → P1)

---

## Quick Start 가이드

### 1. uv 설치 및 의존성 설치

```bash
# uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
export PATH="$HOME/.local/bin:$PATH"

# 의존성 설치
uv sync --all-groups
```

### 2. 개발 명령어

```bash
# 서버 실행
uv run python server/main.py

# 클라이언트 실행
uv run python client/main.py

# 테스트 실행
uv run pytest server/tests/ -v

# 코드 포맷팅
uv run black server/ client/ common/

# 린팅
uv run ruff check server/ client/ common/
```

### 3. Docker 사용

```bash
# 서버 이미지 빌드 및 실행
docker build -f server/Dockerfile -t screen-party-server:latest .
docker run -p 8765:8765 screen-party-server:latest

# docker-compose 사용
docker-compose up
```

자세한 내용은 루트 README.md 및 각 패키지의 README.md를 참고하세요.

---

## 다음 클로드 코드 세션을 위한 가이드

### 시작 시 읽어야 할 파일 (순서대로)
1. `.claude/devlog/main.md` (이 파일)
2. `.claude/CLAUDE.md` (프로젝트 규칙)
3. 현재 작업 중인 task의 devlog 파일

### 작업 완료 시 체크리스트
- [ ] 해당 task devlog 업데이트 (TODO 체크, 일기 작성)
- [ ] main.md의 Task 상태 업데이트 (🟡 → 🟢 → ✅)
- [ ] main.md의 "최근 업데이트" 섹션에 항목 추가
- [ ] 커밋 메시지 형식 확인: `[task] 한글 설명`
