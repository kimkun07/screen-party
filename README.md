# Screen Party

실시간 화면 드로잉 공유 애플리케이션 - 게임 브리핑을 위한 협업 도구

## 프로젝트 개요

**Screen Party**는 호스트가 게임 화면 위에 투명 오버레이를 띄우고, 게스트들이 디스코드 화면공유를 보면서 실시간으로 그림을 그려 전략을 공유할 수 있는 협업 도구입니다.

### 주요 기능

- **실시간 드로잉**: 게스트가 그린 선이 모든 참여자 화면에 즉시 표시
- **부드러운 곡선**: Spline 보간으로 자연스러운 드로잉
- **자동 페이드아웃**: 2초 유지 후 1초 동안 투명하게 사라짐
- **장시간 모드**: 전략 브리핑용으로 선이 유지되는 모드
- **색상 구분**: 각 게스트별 펜 색상 설정 가능
- **좌표 매핑**: 디스코드 화면에서 게임 영역 지정으로 정확한 위치 동기화

## 사용 시나리오

### 1. 호스트 (방장) 준비
1. Screen Party 실행
2. "Host Mode" 선택
3. 6자리 세션 번호 발급 (예: ABC123)
4. 디스코드 채팅에 세션 번호 공유
5. 게임 창 선택 → 투명 오버레이 생성

### 2. 게스트 (참여자) 참여
1. Screen Party 실행
2. "Guest Mode" 선택
3. 세션 번호 입력 (예: ABC123)
4. 디스코드 화면공유에서 게임 영역 지정 (드래그)
5. 마우스로 드로잉 시작

### 3. 실시간 협업
- 게스트가 그린 선이 호스트 화면 및 다른 게스트 화면에 실시간 표시
- 2초 후 자동으로 페이드아웃하여 화면 깨끗하게 유지
- 장시간 모드로 전환하여 전략 설명 가능
- ESC 키로 자신이 그린 선만 삭제 가능

## 기술 스택

- **언어**: Python 3.11+
- **GUI**: PyQt6
- **서버**: WebSocket (asyncio + websockets)
- **드로잉**: scipy (Spline 보간), QPainter
- **패키지 관리**: Poetry (monorepo)
- **배포**:
  - 서버: Docker
  - 클라이언트: PyInstaller (Windows .exe, Linux binary)

## 프로젝트 상태

현재 기획 및 초기 설정 단계입니다.

### 진행 상황

자세한 개발 진행 상황은 [`.claude/devlog/main.md`](.claude/devlog/main.md)를 참고하세요.

| 우선순위 | Task | 상태 |
|---------|------|------|
| P0 | Project Structure | 🟡 준비중 |
| P0 | Session Management | 🟡 준비중 |
| P0 | Server Core | 🟡 준비중 |
| P0 | Client Core | 🟡 준비중 |
| P1 | Testing (간단한 클릭 소통) | 🟡 준비중 |
| P1 | Server Deployment | 🟡 준비중 |
| P1 | Client Deployment | 🟡 준비중 |
| P2 | Host Overlay | 🟡 준비중 |
| P2 | Guest Calibration | 🟡 준비중 |
| P2 | Drawing Engine | 🟡 준비중 |
| P2 | Fade Animation | 🟡 준비중 |
| P3 | Persistence Mode | 🟡 준비중 |
| P3 | Color System | 🟡 준비중 |
| P3 | Window Sync | 🟡 준비중 |

## 프로젝트 구조 (예정)

```
screen-party/
├── pyproject.toml              # 루트 monorepo 설정
├── server/
│   ├── pyproject.toml
│   ├── src/
│   │   └── screen_party_server/
│   │       ├── server.py       # WebSocket 서버
│   │       ├── session.py      # 세션 관리
│   │       └── models.py       # 데이터 모델
│   └── tests/
├── client/
│   ├── pyproject.toml
│   ├── src/
│   │   └── screen_party_client/
│   │       ├── main.py         # GUI 진입점
│   │       ├── gui/            # PyQt6 GUI
│   │       ├── network/        # WebSocket 클라이언트
│   │       └── drawing/        # 드로잉 엔진, Spline
│   └── tests/
├── Dockerfile                  # 서버 Docker 이미지
├── docker-compose.yml          # 로컬 테스트용
└── .claude/
    ├── CLAUDE.md               # Claude Code 가이드
    └── devlog/                 # 개발 진행 상황
        ├── main.md
        ├── project-structure.md
        └── ...
```

## 개발 가이드

이 프로젝트는 **task & devlog 시스템**을 사용하여 개발 작업을 관리합니다.

### Claude Code로 작업하기

1. `.claude/devlog/main.md` 읽기 (프로젝트 전체 개요)
2. `.claude/CLAUDE.md` 읽기 (프로젝트 규칙 및 가이드)
3. 해당 task의 devlog 파일 읽기 (예: `project-structure.md`)
4. 작업 진행 및 devlog 업데이트
5. 커밋 메시지 형식: `[task] 한글 설명`

### 로컬 개발 (예정)

```bash
# Poetry 설치
curl -sSL https://install.python-poetry.org | python3 -

# 의존성 설치
poetry install

# 서버 실행
cd server
poetry run python -m screen_party_server.server

# 클라이언트 실행
cd client
poetry run python -m screen_party_client.main
```

## 라이선스

TBD

## 기여

TBD

---

**개발 시작일**: 2025-12-28
