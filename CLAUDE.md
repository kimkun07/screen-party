# Claude Code 사용 가이드 - screen-party 프로젝트

## 개요

이 문서는 Claude Code가 screen-party 프로젝트에서 효과적으로 작업하기 위한 가이드입니다.

**screen-party**는 실시간 화면 드로잉 공유 애플리케이션입니다:
- 호스트가 게임 화면에 투명 오버레이를 띄움
- 게스트들이 디스코드 화면공유를 보면서 실시간으로 그림을 그림
- 모든 참여자가 동시에 드로잉을 보며 협업 가능

## ⚠️ 중요 주의사항

### 보안: 배포된 서버 도메인 관리

**배포된 서버 도메인을 절대 코드나 문서에 직접 적지 마세요!**

- ✅ **올바른 방법**: `.env.secret` 파일에만 저장
- ❌ **잘못된 방법**: README.md, devlog, 코드에 직접 작성

**규칙**:
1. 배포된 서버 URL은 **`.env.secret` 파일에만** 저장
2. `.env.secret` 파일은 `.gitignore`에 포함되어 Git에 커밋되지 않음
3. `.env.example` 파일에 예시 형식만 제공
4. README나 devlog에서는 "`.env.secret` 파일 참조"라고만 명시
5. 코드에서 환경 변수로 읽어서 사용

**예시**:
```bash
# .env.secret 파일 내용 (로컬에만 존재)
DEPLOYED_SERVER_URL=wss://your-actual-server-domain.com

# 사용 방법
export DEPLOYED_SERVER_URL=$(grep DEPLOYED_SERVER_URL .env.secret | cut -d'=' -f2)
uv run python client/main.py --server $DEPLOYED_SERVER_URL
```

**이유**: 배포된 서버 도메인은 보안상 민감한 정보이며, 공개 레포지토리에 노출되면 안 됩니다.

### README.md 수정 시 주의사항

**Windows 클라이언트 실행 방법을 절대 변경하지 마세요!**

README의 "클라이언트 실행 (Windows에서)" 섹션에는 다음과 같은 **필수** 사항이 있습니다:

1. **가상환경을 먼저 activate해야 함**
   ```powershell
   D:\Data\Develop\screen-party-mirrored\.venv-windows\Scripts\activate.ps1
   ```

2. **uv는 절대 경로로 실행해야 함**
   ```powershell
   C:\Users\YourUsername\.local\bin\uv.exe run --active python client/main.py
   ```

3. **`--active` 옵션이 필수**
   - `uv run --active`를 사용해야 함
   - activate된 환경을 사용하기 위해 필요
   - 이 옵션 없이 상대 경로로 실행하면 에러 발생

4. **심볼릭 링크 경로에서 실행해야 함**
   - `\\wsl$` 경로에서 직접 실행 시 실패
   - `D:\Data\Develop\screen-party-mirrored`에서 실행해야 함

**이유**: Windows에서 WSL 프로젝트를 사용할 때의 환경 제약 사항입니다. 이를 무시하고 간단하게 변경하면 실행이 실패합니다.

### 기술 스택

- **언어**: Python 3.13+
- **패키지 관리**: uv (workspace 기반 monorepo)
- **개발환경**: devcontainer (VS Code)
- **서버**: WebSocket (asyncio, websockets 14.x+)
- **클라이언트**: PyQt6 (GUI), qasync (비동기 통합)
- **테스트**: pytest, pytest-asyncio, pytest-cov
- **코드 품질**: black, ruff, pyright
- **배포**: Docker (서버, uv 기반), PyInstaller (클라이언트)

## 프로젝트 구조

screen-party 프로젝트는 **여러 개의 독립적인 Task로 구성**되어 있습니다.

### Task 기반 구조

각 Task는:
- **독립적인 목표**를 가지고 있음
- **독립적인 devlog 파일**로 추적됨 (`.claude/devlog/[task-name].md`)
- **독립적으로 완료** 가능
- **의존성**이 있을 수 있음 (main.md의 Task 의존성 참조)

### 현재 Task 목록

```
screen-party/
├── CLAUDE.md                   # 이 문서
├── .devcontainer/              # devcontainer 설정
│   └── devcontainer.json
├── pyproject.toml              # uv workspace 루트
├── uv.lock                     # 의존성 잠금 파일
├── common/                     # 공통 패키지
│   ├── pyproject.toml
│   ├── src/
│   │   └── screen_party_common/
│   │       ├── models.py       # Session, Guest
│   │       └── constants.py    # 공통 상수
│   └── tests/
├── server/                     # 서버 코드
│   ├── pyproject.toml
│   ├── Dockerfile              # 서버 Docker 이미지 (uv 기반)
│   ├── src/
│   └── tests/
├── client/                     # 클라이언트 코드
│   ├── pyproject.toml
│   ├── src/
│   └── tests/
├── docker-compose.yml          # 로컬 테스트용
└── .claude/
    └── devlog/                 # Task 진행 상황 추적
        ├── main.md                     # 전체 프로젝트 진행 상황 (시작점)
        ├── project-structure.md        # Task: uv workspace + devcontainer
        ├── session-management.md       # Task: 세션 관리 시스템
        ├── server-core.md              # Task: WebSocket 서버
        ├── client-core.md              # Task: 클라이언트 기본 구조 (PyQt6)
        ├── host-overlay.md             # Task: 호스트 투명 오버레이
        ├── guest-calibration.md        # Task: 게스트 영역 설정
        ├── drawing-engine.md           # Task: 실시간 드로잉 엔진
        ├── fade-animation.md           # Task: 페이드아웃 애니메이션
        ├── persistence-mode.md         # Task: 장시간 그림 모드
        ├── color-system.md             # Task: 색상 설정 시스템
        ├── window-sync.md              # Task: 창 관리 동기화
        ├── testing.md                  # Task: 유닛 테스트
        ├── server-deployment.md        # Task: 서버 Docker 배포
        └── client-deployment.md        # Task: 클라이언트 배포
```

### Task 이름 규칙

- **구조/설정**: `project-structure`
- **핵심 컴포넌트**: `server-core`, `client-core`
- **기능 기반**: `session-management`, `drawing-engine`, `fade-animation`
- **배포**: `server-deployment`, `client-deployment`
- **품질 보증**: `testing`

## 커밋 메시지 형식

screen-party 프로젝트는 **Task 기반 커밋 메시지 형식**을 사용합니다.

### 형식

```
[task] 한글 설명
```

### 예시

```bash
[project-structure] Poetry monorepo 초기 설정
[server-core] WebSocket 서버 기본 구조 구현
[drawing-engine] Spline 변환 로직 추가
[testing] 세션 관리 유닛 테스트 작성
```

### 규칙

1. **Task 이름**: 대괄호 `[]` 안에 task 이름 작성 (영문, 소문자, 하이픈)
2. **설명**: 한글로 명확하게 작성
3. **간결함**: 한 줄로 요약 (상세 내용은 body에 작성)
4. **접두사 금지**: `fix:`, `feat:`, `chore:` 등의 conventional commits 접두사 사용하지 않음
   - ❌ `fix: [task] 버그 수정`
   - ✅ `[task] 버그 수정`

### 특수 케이스

- **여러 Task 동시 수정**: 각 Task를 별도 대괄호로 명시
  ```
  [github-action] [devlog] deploy.yml 에러 처리 수정 및 devlog 업데이트
  [nginx-conf-generator] [github-action] 설정 파일 생성 및 워크플로우 연동
  ```

- **프로젝트 전체 설정**: `[project]` 사용
  ```
  [project] .gitignore 업데이트
  [project] README 초안 작성
  ```

- **Claude 관련 설정**: `[claude]` 사용
  ```
  [claude] CLAUDE.md 구조 설명 추가
  [claude] devlog 시스템 개선
  ```

- **자동 생성 커밋**: 예외적으로 `chore:` 접두사 사용 (GitHub Actions 자동 커밋)
  ```
  chore: regenerate nginx configs
  ```

## devlog 시스템

monoserver 프로젝트는 **devlog 시스템**을 사용하여 개발 작업을 관리합니다.

### devlog 디렉토리 구조

```
.claude/
├── claude.md              # 이 문서 (Claude Code 가이드)
└── devlog/
    ├── main.md            # 프로젝트 전체 진행 상황 (시작점)
    ├── nginx-conf-generator.md
    ├── github-action.md
    ├── google-compute-engine.md
    └── install-guide.md
```

### 새로운 Task 시작 프로세스

사용자가 새로운 Task를 시작하고 싶을 때 (예: Docker rootless 설정, 새로운 기능 추가 등):

1. **새로운 devlog 파일 생성**
   - `.claude/devlog/` 디렉토리에 task 이름으로 파일 생성 (예: `docker-rootless.md`)
   - 템플릿 구조 사용:
     - 개요
     - 목표
     - TODO 리스트
     - 클로드 코드 일기 섹션

2. **main.md 업데이트**
   - Task 진행 상황 테이블에 새 항목 추가
   - 우선순위 설정 (P0, P1, P2 등)
   - 상태를 🟡 준비중 또는 🟢 진행중으로 설정
   - Task 의존성 다이어그램 업데이트 (필요시)

3. **작업 수행**
   - 새로 생성한 devlog 파일의 TODO를 따라 진행
   - 진행 상황을 devlog에 기록

4. **CLAUDE.md 업데이트 (필요시)**
   - 새로운 프로세스나 규칙이 발견되면 이 문서 업데이트
   - 다음 Claude Code가 동일한 프로세스를 따르도록 명시

### 기존 Task 작업 시작 프로세스

Claude Code가 monoserver 프로젝트에서 기존 Task를 작업할 때 다음 순서를 따릅니다:

1. **`.claude/devlog/main.md` 읽기**
   - 프로젝트 전체 개요 파악
   - 현재 진행 상황 확인
   - 다음에 해야 할 작업 확인
   - Task 우선순위 및 의존성 파악

2. **해당 Task 파일 읽기**
   - Task 설명 및 요구사항 이해
   - TODO 리스트 확인
   - 이전 Claude Code가 남긴 일기 읽기

3. **작업 수행**
   - TODO 리스트에 따라 작업 진행
   - 문제가 발생하면 해결 시도 및 기록
   - 테스트 및 검증

4. **devlog 업데이트**
   - TODO 리스트 체크
   - "클로드 코드 일기" 섹션에 작업 내용 기록:
     - 진행한 내용
     - 성공한 부분
     - 실패한 부분 및 원인
     - 다음 단계 제안
     - 다음 Claude Code를 위한 조언

5. **main.md 업데이트**
   - Task 상태 변경 (🟡 → 🟢 → ✅)
   - 최근 업데이트 섹션에 작업 내용 기록

### 상태 아이콘

- 🔴 **차단됨** (Blocked): 다른 작업이 완료되어야 진행 가능
- 🟡 **준비중** (Not Started): 아직 시작 안 함
- 🟢 **진행중** (In Progress): 현재 작업 중
- ✅ **완료** (Completed): 작업 완료
- ⏸️ **보류** (On Hold): 임시로 중단

### 클로드 코드 일기 작성 가이드

"클로드 코드 일기"는 가장 중요한 섹션입니다. 다음 Claude Code 세션이 이 내용을 읽고 어디서부터 시작해야 할지 알 수 있습니다.

**좋은 일기 예시**:
```markdown
### 2025-12-26 - Nginx Config Generator 구현

**상태**: 🟡 준비중 → 🟢 진행중

**진행 내용**:
- scripts/generate-nginx-configs.ts 파일 생성
- js-yaml 라이브러리로 compose.yaml 파싱 성공
- hello 서비스에 대한 .conf 파일 생성 테스트 성공

**다음 단계**:
1. 모든 서비스에 대해 반복 로직 작성
2. pnpm 스크립트에 추가

**고려사항**:
- 포트 번호는 수동으로 지정하는 게 더 명확함

**블로커**: 없음

**테스트 결과**:
- ✅ compose.yaml 파싱 성공
- ✅ hello.conf 생성 성공

---

> 다음 클로드 코드에게:
> - fs/promises를 사용해서 비동기로 파일 쓰기 하세요
> - 에러 처리를 철저히 하세요
```

**나쁜 일기 예시** (피해야 함):
```markdown
### 2025-12-26 - 작업함

**진행 내용**:
- 코드 작성

**다음 단계**:
- 테스트

> 다음 클로드 코드에게:
> - 열심히 하세요
```

## 작업 우선순위

### P0 (Foundation - 필수 기반 작업)
1. `project-structure.md` - Poetry monorepo 구조 설정
2. `session-management.md` - 세션 생성/관리 (6자리 코드)
3. `server-core.md` - WebSocket 서버 기본 구조
4. `client-core.md` - 클라이언트 기본 GUI 및 연결

### P1 (Testing & Deployment - 테스트 및 배포 인프라)
5. `testing.md` - 유닛 테스트 (간단한 클릭 소통 테스트)
6. `server-deployment.md` - Docker 이미지 및 배포
7. `client-deployment.md` - 클라이언트 실행 파일 빌드

### P2 (Core Features - 핵심 기능)
8. `host-overlay.md` - 호스트 투명 오버레이 (게임 창 선택)
9. `guest-calibration.md` - 게스트 영역 설정 (좌표 매핑)
10. `drawing-engine.md` - 실시간 드로잉 엔진 (Spline 변환)
11. `fade-animation.md` - 페이드아웃 애니메이션 (2초 대기 → 1초 페이드)

### P3 (Advanced Features - 고급 기능)
12. `persistence-mode.md` - 장시간 그림 모드
13. `color-system.md` - 색상 설정 시스템
14. `window-sync.md` - 창 관리 동기화

## 마무리 체크리스트

작업을 마치기 전에:
- [ ] TODO 리스트 업데이트
- [ ] "클로드 코드 일기" 작성 (구체적으로!)
- [ ] 테스트 결과 기록
- [ ] 다음 Claude Code를 위한 조언 작성
- [ ] main.md의 Task 상태 업데이트
- [ ] main.md의 "최근 업데이트" 섹션에 항목 추가
- [ ] **커밋 메시지 형식 확인**: `[task] 한글 설명` 형식 준수

---

**이 devlog 시스템을 사용하면 Claude Code 세션 간에 컨텍스트가 유지됩니다.**
