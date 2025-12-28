# Task: Project Structure (pip Monorepo)

## 개요

pip 기반 monorepo 구조 설정 - requirements.txt로 의존성 관리, devcontainer로 개발환경 통일

## 목표

- [x] 루트 pyproject.toml 생성 (workspace 설정)
- [x] server/ 디렉토리 구조 및 pyproject.toml 생성
- [x] client/ 디렉토리 구조 및 pyproject.toml 생성
- [x] .gitignore 파일 생성 (Python 프로젝트용)
- [x] 기본 README.md 생성
- [x] Poetry 설치 및 의존성 초기화

## 상세 요구사항

### 루트 pyproject.toml
- Python 버전: 3.11+
- Poetry workspace 설정으로 server, client 연결
- 공통 개발 도구: pytest, black, ruff 등

### server/pyproject.toml
- 패키지명: screen-party-server
- 의존성:
  - websockets (WebSocket 서버)
  - asyncio (표준 라이브러리지만 명시)
- 개발 의존성:
  - pytest
  - pytest-asyncio

### client/pyproject.toml
- 패키지명: screen-party-client
- 의존성:
  - PyQt6 (GUI)
  - websockets (WebSocket 클라이언트)
  - scipy (Spline 보간)
  - numpy
- 개발 의존성:
  - pytest
  - PyInstaller (배포용)

### 디렉토리 구조
```
screen-party/
├── pyproject.toml
├── poetry.lock
├── server/
│   ├── pyproject.toml
│   ├── src/
│   │   └── screen_party_server/
│   │       └── __init__.py
│   └── tests/
│       └── __init__.py
├── client/
│   ├── pyproject.toml
│   ├── src/
│   │   └── screen_party_client/
│   │       └── __init__.py
│   └── tests/
│       └── __init__.py
└── .gitignore
```

## 참고 자료

- Poetry workspace: https://python-poetry.org/docs/managing-dependencies/#path-dependencies
- Poetry 설치: `curl -sSL https://install.python-poetry.org | python3 -`

## TODO

- [x] 루트 pyproject.toml 작성
- [x] server 디렉토리 구조 생성
- [x] client 디렉토리 구조 생성
- [x] .gitignore 작성
- [x] Poetry 의존성 설치 확인 (`poetry install`)
- [x] 각 패키지 import 테스트

## 클로드 코드 일기

### 2025-12-28 - pip Monorepo로 전환 완료

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

> **다음 Claude Code에게**:
> - Poetry는 제거되었습니다. pip와 requirements.txt를 사용하세요
> - devcontainer에서 작업하면 모든 의존성이 자동으로 설치됩니다
> - 테스트 실행: `pytest` (루트에서)
> - 개발 도구: black, ruff (pyproject.toml에 설정됨)
