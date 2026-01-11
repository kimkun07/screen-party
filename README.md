# Screen Party

실시간 화면 드로잉 공유 애플리케이션 - 게임 브리핑을 위한 협업 도구

## 프로젝트 개요

**Screen Party**는 호스트가 게임 화면 위에 투명 오버레이를 띄우고, 게스트들이 디스코드 화면공유를 보면서 실시간으로 그림을 그려 전략을 공유할 수 있는 협업 도구입니다.

### 주요 기능

- **실시간 드로잉**: 게스트가 그린 선이 모든 참여자 화면에 즉시 표시
- **부드러운 곡선**: 베지어 커브 피팅으로 자연스러운 드로잉
- **자동 페이드아웃**: 2초 유지 후 1초 동안 투명하게 사라짐 (파라미터 조절 가능)
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

- **WSL (Ubuntu)**: 프로젝트 저장소 위치, docker engine 설치, devcontainer 실행
- **devcontainer (Linux)**: 개발 진행: 클로드 코드를 --dangerously-skip-permissions 모드로 실행하기 위한 환경
- **Windows**: 클라이언트 GUI (PyQt6) 테스트

### 환경 구성 방법

#### 1단계: WSL에 프로젝트 클론

```bash
# WSL (Ubuntu) 터미널에서
cd ~
git clone https://github.com/your-username/screen-party.git
cd screen-party
```

#### 2단계: VS Code에서 devcontainer 열기

**devcontainer의 Git Credential 제거**

devcontainer 내부에서 Github 레포지토리를 변경하지 못하도록 로그인 정보를 제거합니다.

1. Windows에서 VS Code 실행
2. VS Code 설정 열기 (`Ctrl + ,`)
3. "dev containers" 검색
4. **Dev > Containers: Copy Git Config** → `false`로 설정
5. **Dev > Containers: Git Credential Helper Config Location** → `none`으로 설정

**devcontainer 열기**
1. Command Palette → `Dev Containers: Open Folder in Container...`
2. WSL 경로 선택: `\\wsl$\Ubuntu\home\username\screen-party`
3. devcontainer가 자동으로 빌드되고 실행됨

**자동 설정 내용** (`.devcontainer/postCreate.sh`):
- uv 설치
- `.venv` 가상환경 생성
- `uv sync --all-groups`로 모든 의존성 설치
- bashrc에 가상환경 자동 활성화 추가

#### 3단계: WSL → Windows 실시간 동기화 설정

Windows에서 클라이언트를 테스트하려면 WSL 프로젝트를 Windows로 동기화해야 합니다.

**WSL 터미널에서 동기화 스크립트 실행**:

```bash
# WSL (devcontainer 또는 Ubuntu 터미널)
./scripts/start_mirror.sh /mnt/d/Data/Develop/screen-party-mirrored
```

> **팁**:
> - 이 스크립트는 WSL의 파일 변경을 감지하여 자동으로 Windows로 복사합니다
> - **백그라운드에서 계속 실행**되어야 하므로, 별도 터미널 탭에서 실행하세요
> - Ctrl + C로 종료 가능
> - 한 번 실행하면 모든 파일 변경이 자동으로 동기화됩니다

#### 4단계: Windows에 uv 및 가상환경 설치

```powershell
# PowerShell
# 1. uv 설치
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. 동기화된 디렉토리로 이동
cd D:\Data\Develop\screen-party-mirrored

# 3. Windows용 가상환경 생성
uv venv

# 4. 가상환경 활성화
.venv\Scripts\activate.ps1

# 5. 의존성 설치
uv sync --all-groups
```

> **참고**:
> - WSL의 `.venv`와 Windows의 `.venv`는 별도로 관리됩니다

#### 5단계: 개발 워크플로우

**서버 실행** (devcontainer에서):
```bash
# 기본 실행
uv run server

# 도움말 보기
uv run server --help

# 커스텀 호스트/포트
uv run server --host localhost --port 9000
```

**클라이언트 실행** (Windows에서):

> **참고**: 동기화 스크립트(`start_mirror.sh`)가 실행 중이어야 WSL의 최신 변경사항이 반영됩니다.

```powershell
# PowerShell
cd D:\Data\Develop\screen-party-mirrored

# 1. 가상환경 활성화
.venv\Scripts\activate.ps1

# 2. 클라이언트 실행
uv run client
```

**테스트 실행** (devcontainer에서):
```bash
# 유닛 테스트 (서버 + 클라이언트)
uv run pytest

# 통합 테스트
uv run pytest integration/tests/test_integration.py -v

# 서버 테스트만 실행
uv run pytest server/tests/ -v

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

**서버 Docker 배포**

프로젝트 루트에서 `uv run publish-server` 명령어를 사용하여 자동으로 빌드 및 배포:

```bash
uv run publish-server v0.1.0          # v0.1.0 태그로 빌드 및 배포
uv run publish-server v0.2.0          # v0.2.0 태그로 빌드 및 배포

# 도움말 보기
uv run publish-server --help

# Dry-run 모드 (실제로 실행하지 않고 명령어만 확인)
uv run publish-server v0.1.0 --dry-run

# latest 태그 푸시 건너뛰기
uv run publish-server v0.1.0 --skip-latest
```

`publish-server` 스크립트가 자동으로 다음 작업을 수행합니다:
1. Docker 이미지 빌드
2. 버전 태그 지정 (예: v0.1.0)
3. latest 태그 추가
4. Docker Hub에 푸시 (v0.1.0 + latest)

**클라이언트 앱 패키징 (Windows)**

PyInstaller를 사용하여 Windows 실행 파일(.exe)을 생성합니다.

> **중요**: Windows 환경에서만 실행 가능합니다.

```powershell
# Windows PowerShell
cd D:\Data\Develop\screen-party-mirrored
.\.venv\Scripts\activate.ps1

# 클라이언트 패키징
uv run package-client v0.1.0

# 도움말 보기
uv run package-client --help

# Dry-run 모드 (실제로 실행하지 않고 명령어만 확인)
uv run package-client v0.1.0 --dry-run
```

`package-client` 스크립트가 자동으로 다음 작업을 수행합니다:
1. 기존 빌드 정리 (build/, dist/)
2. PyInstaller 실행 (client.spec 기반)
3. README.txt 생성
4. ZIP 압축 (ScreenParty-v0.1.0-windows.zip)

결과물:
- `dist/ScreenParty.exe` - 실행 파일 (단일 파일, ~100-200MB)
- `ScreenParty-v0.1.0-windows.zip` - 배포용 ZIP 파일

**GitHub Release 배포**:

```bash
# GitHub CLI 사용
gh release create v0.1.0 ScreenParty-v0.1.0-windows.zip --title "Screen Party v0.1.0"

# 또는 수동으로:
# 1. GitHub 레포지토리 → Releases → Create a new release
# 2. Tag: v0.1.0
# 3. Title: Screen Party v0.1.0
# 4. ZIP 파일 업로드
```

**주의사항**:
- 바이러스 백신 프로그램에서 오탐할 수 있습니다 (PyInstaller 특성)
- 사용자에게 예외 처리 안내 필요
- 실행 파일 크기가 큼 (PyQt6, numpy, scipy 포함)


---

**개발 시작일**: 2025-12-28
