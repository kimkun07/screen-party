# Screen Party

디스코드 화면공유와 함께 사용해서 실시간으로 그림을 그리는 도구

TO WRITE - [스크린샷 첨부]

## 사용 가이드

### 1. 버전 확인

[Releases 페이지](https://github.com/kimkun07/screen-party/releases)에서 사용할 릴리즈를 선택합니다.

- 각 릴리즈마다 호환되는 서버/클라이언트 버전이 명시되어 있습니다.
- 릴리즈 페이지에 표시된 정확한 버전을 사용하세요.

### 2. 서버 준비 (셀프 호스팅)

Docker로 서버를 실행합니다. **릴리즈 페이지에 명시된 서버 버전**을 사용합니다.

```bash
# v1.0.0 릴리즈의 서버 실행 예시
docker run -d -p 8765:8765 kimkun07/screen-party-server:v1.0.0
```

또는 Docker Compose 사용:

```yaml
services:
  screen-party-server:
    image: kimkun07/screen-party-server:v1.0.0  # 릴리즈에 명시된 버전 사용
    ports:
      - "8765:8765"
    restart: unless-stopped
```

```bash
docker compose up -d
```

### 3. 클라이언트 설치

**Windows 실행 파일 다운로드**

1. [Releases 페이지](https://github.com/kimkun07/screen-party/releases)에서 선택한 릴리즈의 `ScreenParty.exe` 다운로드
2. `ScreenParty.exe` 실행

### 4. 호스트: 세션 생성 및 화면공유

1. **Screen Party 실행**
2. **서버 주소 입력 및 세션 생성**
   - 서버 주소 입력 (예: `ws://localhost:8765` 또는 `ws://서버IP:8765`)
   - "세션 생성" 버튼 클릭
   - 메인 화면 진입
3. **세션 코드 복사**
   - 메인 화면에서 6자리 세션 코드 표시 (예: `ABC123`)
   - "복사" 버튼으로 세션 코드 복사
   [TO WRITE - 스크린샷 첨부]
   - Discord 채팅에 세션 코드 공유
4. **그림 영역 생성**
   - "그림 영역 생성" 버튼 클릭
   - 투명 오버레이가 나타나면 드래그로 크기 및 위치 조정
   - "그림 영역 크기 조정 완료" 버튼 클릭 또는 `Enter` 키로 완료
   [TO WRITE - 스크린샷 첨부]
5. **화면공유 시작**
   - Discord에서 게임 창 화면공유 시작

### 5. 게스트: 세션 참여

1. **Screen Party 실행**
2. **서버 주소, 세션 코드 입력 및 세션 참여**
   - 호스트와 동일한 서버 주소 입력 (예: `ws://서버IP:8765`)
   - 호스트가 공유한 세션 코드 입력 (예: `ABC123`)
   - "세션 참여" 버튼 클릭
   - 메인 화면 진입
3. **그림 영역 설정**
   - "그림 영역 생성" 버튼 클릭
   - Discord 화면공유의 게임 영역에 맞춰 드래그로 크기 조정
   - "그림 영역 크기 조정 완료" 버튼 클릭 또는 `Enter` 키로 완료

### 6. 드로잉 기능

- **그리기 활성화/비활성화**: "그리기 활성화" 버튼 클릭 (또는 `ESC` 키로 비활성화)
- **그리기**: 그리기 활성화 상태에서 마우스 왼쪽 버튼 드래그
- **색상 변경**: 메인 화면의 색상 팔레트에서 색상 선택
- **자동 페이드**: 그린 선은 2초 후 1초 동안 페이드아웃됨

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

#### 3단계: 개발 시작 전 스크립트 실행

TO-WRITE 예전 스크립트라서 업데이트 필요. 이제 다른 manual-scripts 스크립트들도 추가하기

**WSL 터미널에서 동기화 스크립트 실행**:

Windows에서 클라이언트를 테스트하려면 WSL 프로젝트를 Windows로 동기화해야 합니다.
```bash
# WSL (devcontainer 또는 Ubuntu 터미널)
./scripts/start_mirror.sh /mnt/d/Data/Develop/screen-party-mirrored
```

> **팁**:
> - 이 스크립트는 WSL의 파일 변경을 감지하여 자동으로 Windows로 복사합니다
> - **백그라운드에서 계속 실행**되어야 하므로, 별도 터미널 탭에서 실행하세요
> - Ctrl + C로 종료 가능
> - 한 번 실행하면 모든 파일 변경이 자동으로 동기화됩니다


TO-WRITE: 아래 내용 최신 내용 확인하고 간소화. 섹션 이름도 잘 짓기
**윈도우 알림**:

이 프로젝트는 **Windows 네이티브 알림**을 통해 Claude Code의 작업 상태를 실시간으로 전달합니다.

1. **dev-notify-bridge** (Windows 알림 브릿지):
   - Windows에서 `npx dev-notify-bridge --port 6789`를 실행해야 함
   - devcontainer의 `localhost:6789`에서 POST 요청을 받아 Windows 알림 표시

2. **Claude Code Hooks** (`.claude/claude-config/settings.json`):

3. **notify-to-windows.sh 스크립트** (`.claude/notify-to-windows.sh`):
   - Claude Code hooks에서 호출됨
   - WSL의 기본 게이트웨이 IP를 동적으로 가져와서 Windows 호스트에 연결
   - `http://<WINDOWS_HOST_IP>:6789/notify`로 POST 요청 전송
   - Windows에서 네이티브 알림 표시

**환경 구성**:
- WSL Docker가 **rootful 모드**로 설치되어야 함 (rootless 모드는 네트워크 격리 발생)
- devcontainer의 `network_mode: host` 설정으로 WSL의 localhost와 네트워크 공유
- 자세한 내용은 `.claude/devlog/dev-environment.md` 참조
  
**수동 테스트**:
```bash
# devcontainer 또는 WSL에서
./.claude/notify-to-windows.sh --title "Test" --message "This is a test notification" --sound true
```

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

#### 5단계: 사용 가능한 명령어

모든 스크립트는 `uv run` 명령어로 실행합니다:

**클라이언트 명령어**:
```bash
uv run client                    # 클라이언트 실행
uv run package-client <version>  # 클라이언트 패키징 (Windows만 가능)
```

**서버 명령어**:
```bash
uv run server                    # 서버 실행 (로컬)
uv run docker-server             # Docker Compose로 서버 실행
uv run publish-server <version>  # Docker 이미지 빌드 및 Docker Hub 배포
```

**개발 도구**:
```bash
uv run format                    # 전체 코드베이스 포맷팅 (Black)
uv run lint                      # 전체 코드베이스 린팅 (Ruff)
uv run test                      # 전체 테스트 실행 (pytest)
```

모든 명령어는 `--help` 옵션으로 자세한 도움말을 볼 수 있습니다:
```bash
uv run server --help
uv run publish-server --help
uv run package-client --help
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
2. version_info.txt 생성 (Windows 버전 정보)
3. PyInstaller 실행 (client.spec 기반)
4. 임시 파일 정리

결과물:
- `dist/ScreenParty.exe` - 실행 파일 (단일 파일, ~100-200MB)

**GitHub Release 배포**:

```bash
# GitHub CLI 사용
gh release create v0.1.0 dist/ScreenParty.exe --title "Screen Party v0.1.0"

# 또는 수동으로:
# 1. GitHub 레포지토리 → Releases → Create a new release
# 2. Tag: v0.1.0
# 3. Title: Screen Party v0.1.0
# 4. dist/ScreenParty.exe 파일 업로드
```

---

**개발 시작일**: 2025-12-28
