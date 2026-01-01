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

- **언어**: Python 3.13+
- **패키지 관리**: uv (workspace 기반 monorepo)
- **GUI**: PyQt6
- **서버**: WebSocket (asyncio + websockets)
- **드로잉**: scipy (Spline 보간), QPainter
- **테스트**: pytest, pytest-asyncio, pytest-cov
- **배포**:
  - 서버: Docker (uv 기반 multi-stage build)
  - 클라이언트: PyInstaller (예정)

## 프로젝트 구조

```
screen-party/
├── pyproject.toml              # uv workspace 루트
├── uv.lock                     # 의존성 잠금 파일
├── common/                     # 공통 패키지
│   └── src/screen_party_common/
│       ├── models.py           # Session, Guest
│       └── constants.py        # 공통 상수
├── server/
│   ├── Dockerfile              # 서버 Docker 이미지
│   ├── src/screen_party_server/
│   │   ├── server.py           # WebSocket 서버
│   │   └── session.py          # 세션 관리
│   └── tests/
├── client/
│   ├── src/screen_party_client/
│   │   ├── main.py             # GUI 진입점
│   │   ├── gui/                # PyQt6 GUI
│   │   ├── network/            # WebSocket 클라이언트
│   │   └── drawing/            # 드로잉 엔진 (예정)
│   └── tests/
├── docker-compose.yml          # 로컬 테스트용
└── .claude/
    ├── CLAUDE.md               # Claude Code 가이드
    └── devlog/                 # 개발 진행 상황
```

## 개발 환경

### 현재 개발 환경 구성

이 프로젝트는 다음과 같은 **하이브리드 환경**에서 개발하고 있습니다:

- **WSL (Ubuntu)**: 프로젝트 저장소 위치, devcontainer 실행
- **devcontainer (Linux)**: YOLO 모드로 실행하기 위한 환경 (PyQt6 headless 실행 가능)
- **Windows**: 클라이언트 GUI (PyQt6) 테스트 환경

**devcontainer를 사용하는 이유**:
- **YOLO 모드 실행**: PyQt6를 headless 환경에서 실행하여 GUI 없이도 테스트 가능
- **일관된 개발 환경**: 팀원 간 동일한 Python 버전 및 패키지 환경 보장
- **Linux 환경**: 서버 개발 및 Docker 이미지 빌드에 최적화된 환경

### 환경 구성 방법

#### 1단계: WSL에 프로젝트 클론

```bash
# WSL (Ubuntu) 터미널에서
cd ~
git clone https://github.com/your-username/screen-party.git
cd screen-party
```

#### 2단계: VS Code에서 devcontainer 열기

1. Windows에서 VS Code 실행
2. `F1` → `Dev Containers: Open Folder in Container...`
3. WSL 경로 선택: `\\wsl$\Ubuntu\home\username\screen-party`
4. devcontainer가 자동으로 빌드되고 실행됨

**자동 설정 내용** (`.devcontainer/postCreate.sh`):
- uv 설치
- `.venv` 가상환경 생성
- `uv sync --all-groups`로 모든 의존성 설치
- bashrc에 가상환경 자동 활성화 추가

**Git Credential 설정** (devcontainer에서 Git 인증이 안 될 경우):

devcontainer 내부에서는 GitHub 로그인 credential이 없어야 합니다.
VS Code 설정을 변경하여 credential helper를 사용하지 않도록 설정합니다:

1. VS Code 설정 열기 (`Ctrl + ,`)
2. "dev containers" 검색
3. **Dev > Containers: Copy Git Config** → `false`로 설정
4. **Dev > Containers: Git Credential Helper Config Location** → `none`으로 설정
5. devcontainer 재시작

#### 3단계: Windows에서 프로젝트 심볼릭 링크 생성

Windows에서 클라이언트를 실행하려면 WSL 경로 대신 **로컬 경로**가 필요합니다.

```powershell
# PowerShell (관리자 권한)
# D:\Data\Develop 디렉토리에 심볼릭 링크 생성
mklink /D "D:\Data\Develop\screen-party-mirrored" "\\wsl$\Ubuntu\home\username\screen-party"
```

> **중요**: `\\wsl$` 경로에서 직접 uv를 실행했을 때 **실패**했습니다.
> Windows 드라이브(C:, D: 등)에 심볼릭 링크를 만든 뒤, 절대 경로로 실행했을 때 성공했습니다.

#### 4단계: Windows에 uv 및 가상환경 설치

```powershell
# PowerShell (관리자 권한)

# 1. uv 설치
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. 심볼릭 링크 경로로 이동
cd D:\Data\Develop\screen-party-mirrored

# 3. Windows용 가상환경 생성
C:\Users\YourUsername\.local\bin\uv.exe venv venv-windows

# 4. 가상환경 활성화
D:\Data\Develop\screen-party-mirrored\venv-windows\Scripts\activate.ps1

# 5. 의존성 설치
C:\Users\YourUsername\.local\bin\uv.exe sync --active --all-groups
```

**가상환경 활성화 오류 시**:
```powershell
# PowerShell 실행 정책 변경
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 5단계: 개발 워크플로우

**서버 실행** (devcontainer에서):
```bash
# devcontainer 터미널에서
uv run python -m screen_party_server.server
```

**클라이언트 실행** (Windows에서):
```powershell
# PowerShell
cd D:\Data\Develop\screen-party-mirrored
D:\Data\Develop\screen-party-mirrored\venv-windows\Scripts\activate.ps1
C:\Users\YourUsername\.local\bin\uv.exe run --active python -m screen_party_client.gui.main_window
```

**테스트 실행** (devcontainer에서):
```bash
# 모든 테스트 실행
uv run pytest

# 서버 테스트만 실행
uv run pytest server/tests/ -v

# 클라이언트 테스트만 실행
uv run pytest client/tests/ -v

# 커버리지 포함
uv run pytest --cov=server --cov=client
```

**코드 품질 검사** (devcontainer에서):
```bash
# Black (포맷팅)
uv run black server/ client/ common/

# Ruff (린팅)
uv run ruff check server/ client/ common/
```

#### 6단계: 배포 워크플로우

**서버 Docker 이미지 (작성 예정)**

**클라이언트 앱 (작성 예정)**


---

**개발 시작일**: 2025-12-28
