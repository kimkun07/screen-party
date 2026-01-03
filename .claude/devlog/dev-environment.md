# Task: Development Environment Setup

## 개요

개발 및 테스트 환경 구성 - devcontainer에서 Claude Code 개발, Windows 호스트에서 클라이언트 앱 테스트

## 목표

- [x] devcontainer에서 Claude Code 개발 환경 완성
- [x] Windows 호스트에서 PyQt6 클라이언트 테스트 환경 구성
- [x] WSL과 Windows 호스트 간 원활한 파일 접근 설정

## 환경 구조

```
WSL2 (Ubuntu 24.04) - 원본 레포지토리
  ├── Docker Engine 설치됨
  ├── /home/simelvia/Develop-WSL/screen-party (원본)
  │   └── devcontainer (Claude Code yolo 모드)
  └── /mnt/d/data/develop/screen-party (Windows 드라이브 마운트)

Windows 호스트 (윈도우 앱 테스트)
  └── D:\Data\Develop\screen-party-mirrored (symlink → WSL 원본)
      └── .venv-windows (Python 가상환경)
```

### 파일 구조 설명

1. **원본 레포지토리**: `/home/simelvia/Develop-WSL/screen-party` (WSL)
   - screen-party 레포지토리를 WSL에서 먼저 생성
   - devcontainer에서 Claude Code 개발 진행

2. **Windows symlink**: `D:\Data\Develop\screen-party-mirrored`
   - WSL 원본에 대한 심볼릭 링크 (디렉토리)
   - 생성 명령어: `mklink /d D:\Data\Develop\screen-party-mirrored \\wsl.localhost\Ubuntu-24.04\home\simelvia\Develop-WSL\screen-party`
   - Windows에서 PyQt6 앱 테스트용

### 역할 분리

- **Windows 호스트**: PyQt6 클라이언트 앱 실행 및 테스트
- **WSL2**: Docker Engine 제공, 원본 레포지토리 관리
- **devcontainer**: Claude Code를 이용한 개발, 서버 실행, 테스트

## TODO

- [x] 파일 구조 결정 (WSL 원본 + Windows symlink)
- [x] devcontainer IS_SANDBOX 환경변수 자동 설정
- [x] .venv 자동 생성 및 의존성 설치
- [x] CLAUDE_CONFIG_DIR 설정 (인증 영속성)
- [x] HAPPY_HOME_DIR 설정 (Happy Coder 인증 영속성)
- [x] postCreate.sh pip 설치 에러 수정 (editable 패키지)
- [x] 컨테이너 재빌드 및 테스트
- [x] Windows 호스트에서 Python 가상환경 구성 완료
- [x] Windows symlink에서 venv 정상 작동 확인
- [x] 클라이언트 테스트 워크플로우 확립
- [x] .venv-linux → .venv 마이그레이션

## 클로드 코드 일기

### 2025-12-30 - Happy Coder 인증 영속성 및 pip 설치 문제 해결

**상태**: 🟢 진행중 → ✅ 완료

**작업 내용**:

1. **HAPPY_HOME_DIR 환경변수 발견 및 설정** ✅
   - happy-coder 소스 코드 분석 (`/usr/local/share/nvm/versions/node/v24.12.0/lib/node_modules/happy-coder/dist/`)
   - `types-CgkAW-7c.mjs` 파일에서 환경변수 로직 발견:
     ```javascript
     if (process.env.HAPPY_HOME_DIR) {
       this.happyHomeDir = expandedPath;
     } else {
       this.happyHomeDir = join(homedir(), ".happy");  // 기본값
     }
     ```
   - `devcontainer.json`에 `HAPPY_HOME_DIR=/workspaces/screen-party/.claude/happy-config` 추가
   - Claude Code의 `CLAUDE_CONFIG_DIR`과 동일한 방식으로 인증 영속성 확보

2. **.gitignore 업데이트** ✅
   - `.claude/happy-config/` 추가 (Happy Coder 인증 정보 제외)
   - `access.key`, `settings.json` 등이 git에 포함되지 않도록 보호

3. **기존 인증 정보 마이그레이션** ✅
   - `~/.happy/` → `/workspaces/screen-party/.claude/happy-config/` 복사
   - `access.key`, `settings.json`, `daemon.state.json` 등 이동
   - `happy doctor` 명령으로 새 경로 확인 완료

4. **postCreate.sh pip 설치 에러 수정** ✅
   - **문제**: `client/requirements.txt`에 `-e ../server` 상대 경로가 있었음
   - **원인**: postCreate.sh가 `/workspaces/screen-party`에서 실행되므로 `../server`는 존재하지 않는 경로
   - **해결**:
     - `postCreate.sh`에 `pip install -e /workspaces/screen-party/server` 추가 (절대 경로)
     - `client/requirements.txt`에서 `-e ../server` 제거
   - **결과**: postCreate.sh 정상 실행 확인 (에러 없음)

5. **서버 테스트 실행 확인** ✅
   - `pytest` 실행: 29/29 테스트 통과 (1.14초)
   - 세션 관리 테스트 14개 ✅
   - WebSocket 서버 테스트 15개 ✅
   - 클라이언트 테스트는 아직 작성되지 않음 (예상된 상태)

**주요 파일 변경**:
- `.devcontainer/devcontainer.json`:
  - `HAPPY_HOME_DIR` 환경변수 추가
- `.devcontainer/postCreate.sh`:
  - `pip install -e /workspaces/screen-party/server` 추가 (절대 경로)
- `client/requirements.txt`:
  - `-e ../server` 제거
- `.gitignore`:
  - `.claude/happy-config/` 추가

**검증 완료**:
- ✅ postCreate.sh 에러 없이 실행 완료
- ✅ happy-coder 새 설정 경로 인식 (`happy doctor`로 확인)
- ✅ 서버 테스트 29개 모두 통과
- ✅ server 패키지 editable 모드 설치 성공

**다음 단계**:
- devcontainer 재빌드로 전체 프로세스 검증
- Windows 호스트 테스트 환경 구성

---

### 2025-12-30 - devcontainer 설정 완료

**상태**: 🟢 진행중 → ✅ 완료

**작업 내용**:

1. **IS_SANDBOX 환경변수 자동 설정** ✅
   - `devcontainer.json`에 `containerEnv` 추가
   - `IS_SANDBOX=1` 자동 설정
   - 매번 `IS_SANDBOX=1 claude` 입력 불필요

2. **.venv 자동 생성** ✅
   - `postCreate.sh` 업데이트
   - 컨테이너 생성 시 `.venv` 자동 생성
   - 모든 의존성 자동 설치 (pip, dev, server, client)
   - `python.defaultInterpreterPath` → `.venv` 설정

3. **CLAUDE_CONFIG_DIR 설정** ✅
   - `.claude/claude-config/` 디렉토리 사용 (프로젝트 내부)
   - `CLAUDE_CONFIG_DIR=/workspaces/screen-party/.claude/claude-config` 설정
   - 별도 마운트 불필요 (프로젝트 디렉토리가 이미 마운트됨)
   - 컨테이너 재시작 시에도 Claude 인증 유지

4. **.gitignore 업데이트** ✅
   - `.venv` 추가
   - `.venv-windows` 추가
   - `.claude/claude-config/` 추가 (인증 정보 제외)

**주요 파일 변경**:
- `.devcontainer/devcontainer.json`:
  - `containerEnv` 추가 (IS_SANDBOX, CLAUDE_CONFIG_DIR)
  - `python.defaultInterpreterPath` 변경 (.venv)
  - ~~`mounts` 제거 (불필요 - 프로젝트 내부 디렉토리 사용)~~
- `.devcontainer/postCreate.sh`:
  - `.claude/claude-config/` 디렉토리 생성
  - `.venv` 생성 로직 추가
  - 의존성 자동 설치 추가
- `.gitignore`:
  - 가상환경 패턴 추가 (.venv, .venv-windows)
  - Claude 인증 디렉토리 추가 (.claude/claude-config/)

**테스트 필요**:
- [x] 컨테이너 재빌드 후 `.venv` 정상 생성 확인
- [x] `claude` 명령어 (IS_SANDBOX 없이) 정상 작동 확인
- [x] Claude 인증 영속성 확인 (재시작 후에도 유지)

---

### 2025-12-30 - 환경 구성 시도 및 문제점 파악

**상태**: 🟢 진행중

**환경 구성 목적**:
- **devcontainer**: Claude Code yolo 모드로 서버/클라이언트 개발
- **Windows 호스트**: Windows 네이티브 PyQt6 앱 테스트

**시도한 내용**:

1. **Windows 호스트에서 가상환경 활성화** ✅ 성공
   ```powershell
   D:\Data\Develop\screen-party-mirrored> .\.venv-windows\Scripts\Activate.ps1
   ```
   - Windows에서 직접 venv 사용 가능 확인

2. **WSL 경로에서 가상환경 활성화** ❌ 실패
   ```powershell
   \\wsl.localhost\Ubuntu-24.04\home\simelvia\Develop-WSL\screen-party> .\.venv-windows\Scripts\Activate.ps1
   ```
   - WSL 파일시스템을 Windows에서 접근하는 경로에서 실패

3. **/mnt 마운트 방식** ❌ 실패
   ```
   /mnt/d/data/develop/screen-party
   ```
   - WSL에서 devcontainer 생성 시 Docker를 Windows 환경에서 찾으려 함
   - Docker Desktop의 WSL2 통합 문제로 추정

**발견된 문제**:

1. **Docker 경로 문제**:
   - WSL에 Docker Engine이 설치되어 있으나, VS Code가 Windows Docker Desktop을 찾으려 함
   - /mnt/d 경로에서 devcontainer 생성 시 경로 혼선 발생

2. **파일 접근 문제**:
   - Windows에서 WSL 파일시스템 접근 시 성능 및 권한 문제 가능성
   - .venv-windows가 WSL 경로에서 작동하지 않음

**파일 구조 확인**:
- ✅ 원본 레포지토리: `/home/simelvia/Develop-WSL/screen-party` (WSL)
- ✅ Windows symlink: `D:\Data\Develop\screen-party-mirrored` (`mklink /d` 사용)
- ✅ symlink를 통해 파일 동기화 불필요 (실시간 반영)

**고려사항**:

1. **Docker 설정**:
   - Docker Desktop WSL2 통합 확인 필요
   - 또는 WSL 네이티브 Docker 사용 방향 검토

2. **symlink 제약사항**:
   - Windows에서 symlink 접근 시 성능 이슈 가능성
   - .venv-windows가 symlink 경로에서 정상 작동하는지 확인 필요
   - 일부 도구가 symlink를 정상적으로 처리하지 못할 수 있음

**다음 단계**:

1. Docker Desktop WSL2 통합 상태 확인
2. devcontainer를 WSL 파일시스템에서만 사용하도록 제한
3. Windows symlink에서 .venv-windows 정상 작동 확인

**블로커**:
- Docker 경로 혼선 문제 해결 필요

---

> **다음 Claude Code에게**:
>
> **환경 구조**:
> - WSL에서 devcontainer 개발, Windows에서 클라이언트 테스트하는 이중 환경
> - **파일 구조**: WSL 원본 (`/home/simelvia/Develop-WSL/screen-party`) ← Windows symlink (`D:\Data\Develop\screen-party-mirrored`)
> - symlink로 연결되어 있으므로 별도 동기화 불필요
>
> **devcontainer 설정 완료**:
> - ✅ `IS_SANDBOX=1` 자동 설정됨 (매번 입력 불필요)
> - ✅ `.venv` 자동 생성 및 의존성 설치
> - ✅ `CLAUDE_CONFIG_DIR=.claude/claude-config` (프로젝트 내부, 인증 영속성)
> - Python 인터프리터: `.venv/bin/python` 사용
> - **중요**: `.claude/claude-config/`는 git에 포함되지 않음 (인증 정보)
>
> **주의사항**:
> - Docker는 WSL2 Docker Desktop 통합 사용
> - /mnt 마운트 경로는 devcontainer 생성 시 문제 있음 → WSL 네이티브 경로 사용
> - Windows 테스트 환경은 사용자가 직접 구성 중 → devcontainer 개발에 집중
