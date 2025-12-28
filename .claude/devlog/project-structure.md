# Task: Project Structure (Poetry Monorepo)

## 개요

Poetry monorepo 구조 설정 - 루트와 server/client 디렉토리에 각각 독립적인 pyproject.toml 생성

## 목표

- [x] 루트 pyproject.toml 생성 (workspace 설정)
- [ ] server/ 디렉토리 구조 및 pyproject.toml 생성
- [ ] client/ 디렉토리 구조 및 pyproject.toml 생성
- [ ] .gitignore 파일 생성 (Python 프로젝트용)
- [ ] 기본 README.md 생성
- [ ] Poetry 설치 및 의존성 초기화

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

- [ ] 루트 pyproject.toml 작성
- [ ] server 디렉토리 구조 생성
- [ ] client 디렉토리 구조 생성
- [ ] .gitignore 작성
- [ ] Poetry 의존성 설치 확인 (`poetry install`)
- [ ] 각 패키지 import 테스트

## 클로드 코드 일기

_이 섹션은 작업 진행 시 업데이트됩니다._
