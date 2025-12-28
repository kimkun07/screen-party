# Task: Project Structure (Poetry Monorepo)

## 개요

Poetry monorepo 구조 설정 - 루트와 server/client 디렉토리에 각각 독립적인 pyproject.toml 생성

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

### 2025-12-28 - Poetry Monorepo 구조 완성

**상태**: 🟡 준비중 → ✅ 완료

**진행 내용**:
- ✅ Python 3.13.4 설치 및 pyenv 설정
- ✅ Poetry 2.2.1 설치
- ✅ 루트 pyproject.toml 작성 (package-mode = false)
- ✅ server/ 디렉토리 구조 생성
  - pyproject.toml (websockets 14.2 포함)
  - src/screen_party_server/__init__.py
  - tests/__init__.py
  - README.md
- ✅ client/ 디렉토리 구조 생성
  - pyproject.toml (PyQt6, scipy, numpy, qasync 포함)
  - src/screen_party_client/__init__.py
  - tests/__init__.py
  - README.md
- ✅ 각 패키지 의존성 설치 성공
- ✅ Import 테스트 성공

**주요 결정사항**:
- Python 버전: 3.13.4 (최신 안정 버전)
- PyInstaller: Python 3.13 미지원으로 P1 client-deployment까지 보류
- 루트는 workspace 역할만 (package-mode = false)

**테스트 결과**:
- ✅ server import 성공 (version 0.1.0)
- ✅ client import 성공 (version 0.1.0)

**다음 단계**:
P0 나머지 task 진행:
1. session-management: 6자리 세션 ID 생성
2. server-core: WebSocket 서버 구현
3. client-core: PyQt6 GUI 기본 구조

---

> **다음 Claude Code에게**:
> - server/client는 각각 독립적인 virtualenv를 가집니다
> - 작업 시 `cd server && poetry run ...` 또는 `cd client && poetry run ...` 사용
> - PyInstaller는 나중에 Python 3.13 지원 버전이 나오면 추가하세요
