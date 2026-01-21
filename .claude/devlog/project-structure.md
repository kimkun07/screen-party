# Task: Project Structure (uv Workspace)

## 개요

uv workspace 기반 monorepo 구조 설정 - 공통 패키지 분리, uv.lock으로 의존성 관리, devcontainer로 개발환경 통일

## 목표

- [x] 루트 pyproject.toml 생성 (uv workspace 설정)
- [x] common/ 디렉토리 구조 및 pyproject.toml 생성
- [x] server/ 디렉토리 구조 및 pyproject.toml 생성
- [x] client/ 디렉토리 구조 및 pyproject.toml 생성
- [x] .gitignore 파일 생성 (Python 프로젝트용)
- [x] 기본 README.md 생성
- [x] uv 설치 및 의존성 초기화

## 상세 요구사항

### 루트 pyproject.toml
- Python 버전: 3.13+
- uv workspace 설정으로 common, server, client 연결
- 공통 개발 도구: pytest, black, ruff 등 (dependency-groups)

### common/pyproject.toml
- 패키지명: screen-party-common
- 의존성: 없음 (순수 Python 데이터 모델)

### server/pyproject.toml
- 패키지명: screen-party-server
- 의존성:
  - websockets (WebSocket 서버)
  - screen-party-common (workspace 의존성)
- 개발 의존성:
  - pytest
  - pytest-asyncio
  - pytest-cov

### client/pyproject.toml
- 패키지명: screen-party-client
- 의존성:
  - PyQt6 (GUI)
  - websockets (WebSocket 클라이언트)
  - scipy (Spline 보간)
  - numpy
  - qasync (PyQt6 + asyncio 통합)
  - screen-party-common (workspace 의존성)
- 개발 의존성:
  - pytest
  - pytest-asyncio
  - pytest-cov

### 디렉토리 구조
```
screen-party/
├── pyproject.toml          # uv workspace 설정
├── uv.lock
├── common/                 # 공통 패키지
│   ├── pyproject.toml
│   ├── src/
│   │   └── screen_party_common/
│   │       ├── __init__.py
│   │       ├── models.py
│   │       └── constants.py
│   └── tests/
├── server/
│   ├── pyproject.toml
│   ├── src/
│   │   └── screen_party_server/
│   │       └── __init__.py
│   └── tests/
├── client/
│   ├── pyproject.toml
│   ├── src/
│   │   └── screen_party_client/
│   │       └── __init__.py
│   └── tests/
├── Dockerfile              # 서버 Docker 이미지 (uv 기반)
└── .gitignore
```

## 참고 자료

- uv 공식 문서: https://docs.astral.sh/uv/
- uv workspace: https://docs.astral.sh/uv/concepts/workspaces/
- uv 설치: `curl -LsSf https://astral.sh/uv/install.sh | sh`

## TODO

- [x] uv 설치
- [x] 루트 pyproject.toml 작성 (workspace 설정)
- [x] common 디렉토리 구조 생성
- [x] server 디렉토리 구조 생성
- [x] client 디렉토리 구조 생성
- [x] .gitignore 작성
- [x] uv sync로 의존성 설치 확인
- [x] 각 패키지 import 테스트
- [x] Dockerfile 작성 (uv 기반)

## 클로드 코드 일기

### 2025-12-30 - uv Workspace로 마이그레이션 완료

**상태**: ✅ 완료

**진행 내용**:
- ✅ uv 0.9.20 설치
- ✅ 루트 pyproject.toml 생성 (uv workspace 설정)
- ✅ common/ 패키지 생성
  - `models.py`: Session, Guest 데이터 모델
  - `constants.py`: 공통 상수 (포트, 타임아웃 등)
- ✅ server/client pyproject.toml을 uv workspace 멤버로 변경
- ✅ server 코드에서 common import로 변경
- ✅ Dockerfile 작성 (uv 기반 multi-stage build)
- ✅ uv sync로 의존성 설치 (모든 workspace 멤버)
- ✅ 기존 pip 파일 삭제 (requirements.txt, venv)
- ✅ pytest 29개 테스트 모두 통과

**주요 결정사항**:
- pip → uv: 더 빠르고 현대적인 패키지 관리자
- 공통 패키지 분리: server와 client 모두에서 참조 가능
- uv workspace: workspace 멤버 간 자동 의존성 해결
- Dockerfile: uv sync 사용, multi-stage build로 최적화

**새로운 구조**:
```
screen-party/
├── pyproject.toml              # uv workspace 루트
├── uv.lock                     # 의존성 잠금 파일
├── common/                     # 공통 패키지
│   └── src/screen_party_common/
│       ├── models.py           # Session, Guest
│       └── constants.py        # 공통 상수
├── server/
│   └── src/screen_party_server/
├── client/
│   └── src/screen_party_client/
└── Dockerfile                  # uv 기반 서버 이미지
```

**의존성 관리**:
- `uv sync`: 모든 workspace 멤버 설치
- `uv sync --all-groups`: dev 의존성 포함
- `uv run pytest`: 테스트 실행

**테스트 결과**:
- ✅ server/tests: 29/29 통과 (1.11초)
- ✅ common import 성공
- ✅ workspace 멤버 간 의존성 해결 성공

**다음 단계**:
1. Dockerfile 빌드 테스트
2. client 코드에서 common 사용 (필요시)
3. devcontainer.json에 uv 추가

---

### 2025-12-28 - pip Monorepo로 전환 완료 (레거시)

**상태**: ✅ 완료 → ✅ 업데이트 완료

**진행 내용**:
- ✅ Poetry 제거 및 pip 기반 monorepo로 전환
- ✅ devcontainer 설정 추가 (.devcontainer/devcontainer.json)
  - Python 3.13 이미지 사용
  - 필요한 VS Code 확장 프로그램 자동 설치
  - Git 설정 자동화
- ✅ requirements.txt 파일들 생성
  - `server/requirements.txt`: websockets, pytest-asyncio
  - `client/requirements.txt`: PyQt6, websockets, scipy, numpy, qasync
  - `dev-requirements.txt`: black, ruff, pytest 등 개발 도구
  - `pip-requirements.txt`: 루트 의존성
- ✅ pyproject.toml 간소화 (도구 설정만 유지)
  - black, ruff, pytest, pyright 설정

**주요 결정사항**:
- Poetry → pip: 더 간단하고 표준적인 의존성 관리
- devcontainer: 팀원 간 개발환경 통일
- Python 버전: 3.13.5 (devcontainer)
- 모든 의존성을 requirements.txt로 관리

**테스트 결과**:
- ✅ pytest 29개 테스트 모두 통과
- ✅ 서버/클라이언트 import 성공

**다음 단계**:
1. client-core: PyQt6 GUI 완성
2. testing: 통합 테스트 작성

---

### 2025-12-28 - devcontainer 권한 문제 해결

**상태**: ✅ 해결 완료

**문제**:
- devcontainer에서 생성된 파일이 uid 100999로 소유됨
- 호스트(WSL2)에서 파일 읽기 권한 없음 (permission denied)

**해결 방법**:
1. **호스트에서 파일 소유권 변경**:
   ```bash
   sudo chown -R $USER:$USER /home/simelvia/Develop-WSL/screen-party
   ```

2. **devcontainer를 root 사용자로 실행**:
   - `.devcontainer/devcontainer.json`에 `"remoteUser": "root"` 추가
   - 이렇게 하면 컨테이너에서 모든 파일에 접근 가능

3. **postCreateCommand 분리**:
   - `.devcontainer/postCreate.sh` 스크립트로 분리하여 관리 용이

**결과**:
- ✅ 호스트(WSL2)와 devcontainer 양쪽 모두에서 파일 편집 가능
- ✅ 권한 충돌 없이 개발 가능

---

### 2025-12-28 - Poetry Monorepo 구조 완성 (레거시)

**상태**: 🟡 준비중 → ✅ 완료 → ⏸️ Poetry 제거됨

**진행 내용**:
- ✅ Python 3.13.4 설치 및 pyenv 설정
- ✅ Poetry 2.2.1 설치
- ✅ Poetry monorepo 구조 생성
- ⚠️ 이후 pip monorepo로 전환 (상단 참조)

---

## Quick Start 가이드

### 1. uv 설치

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# PATH 추가
export PATH="$HOME/.local/bin:$PATH"
```

### 2. 의존성 설치

```bash
# 프로젝트 루트에서
uv sync --all-groups
```

### 3. 서버 실행

```bash
# 기본 실행
uv run python server/main.py

# 환경 변수 지정
SERVER_PORT=9000 uv run python server/main.py
```

### 4. 클라이언트 실행

```bash
uv run python client/main.py
```

### 5. 테스트

```bash
# 모든 테스트
uv run pytest

# 서버만
uv run pytest server/tests/ -v

# 커버리지 포함
uv run pytest --cov=server --cov=client
```

### 6. Docker 배포

```bash
# 이미지 빌드
docker build -f server/Dockerfile -t screen-party-server:latest .

# 실행
docker run -p 8765:8765 screen-party-server:latest

# docker-compose 사용
docker-compose up
```

### 7. 이미지 배포

```bash
# Docker Hub
docker tag screen-party-server:latest your-username/screen-party-server:latest
docker push your-username/screen-party-server:latest

# GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker tag screen-party-server:latest ghcr.io/your-username/screen-party-server:latest
docker push ghcr.io/your-username/screen-party-server:latest
```

### 8. 클라이언트 배포 (예정)

> **참고**: PyInstaller는 Python 3.13 미지원. Python 3.12 환경에서 빌드하세요.

```bash
# Windows .exe
pyinstaller --onefile --windowed client/src/screen_party_client/gui/main_window.py

# Linux binary
pyinstaller --onefile client/src/screen_party_client/gui/main_window.py
```

---

> **다음 Claude Code에게**:
> - **패키지 관리자**: uv를 사용합니다 (Poetry와 pip는 제거됨)
> - **의존성 설치**: `uv sync --all-groups`
> - **테스트 실행**: `uv run pytest server/tests/ -v`
> - **서버 실행**: `uv run python server/main.py`
> - **클라이언트 실행**: `uv run python client/main.py`
> - **공통 패키지**: common/에 Session, Guest 모델 및 상수 정의
> - **workspace 구조**: common, server, client 모두 독립 패키지
> - **Docker**: server/Dockerfile에서 uv 기반 multi-stage build 사용
> - **배포**: Docker Hub 또는 GitHub Container Registry에 푸시
