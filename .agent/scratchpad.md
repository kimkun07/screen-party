# Scripts Reorganization - REVERTED & REFINED

## Goal
Reorganize script files to follow the established client pattern:
- Client: client/scripts/main.py, client/scripts/package.py
- Server: server/scripts/main.py, server/scripts/dockerized_server.py, server/scripts/publish.py
- Root: scripts/run.py (minimal wrapper to call package scripts)

## Summary
Ralph는 이전 통합 방식이 마음에 들지 않음. 클라이언트처럼 각 패키지가 자체 scripts 디렉토리를 가지는 방식으로 재구성.

✅ **완료**: server/scripts 디렉토리 생성 및 3개 스크립트 분리
- server/scripts/main.py (서버 실행)
- server/scripts/dockerized_server.py (Docker Compose)
- server/scripts/publish.py (Docker 빌드/배포)

✅ **변경사항**:
- server.py: main() 함수 제거 (ScreenPartyServer 클래스만 유지)
- __main__.py: scripts.main.main() 호출하도록 변경
- scripts/run.py: 각 서버 함수가 server/scripts의 스크립트 호출
- Dockerfile: PYTHONPATH에 /app/server 추가

✅ **테스트**: 120개 테스트 모두 통과

## Tasks

### Phase 1: Create server/scripts directory structure ✅
[x] Create server/scripts/ directory
[x] Create server/scripts/__init__.py
[x] Create server/scripts/main.py (server execution logic)
[x] Create server/scripts/dockerized_server.py (Docker Compose)
[x] Create server/scripts/publish.py (Docker build & publish)

### Phase 2: Move server main logic to scripts/main.py ✅
[x] Move __main__.py main() logic to server/scripts/main.py
[x] Move server.py main() logic to server/scripts/main.py (existed)
[x] Keep server.py as ScreenPartyServer class only (removed main())
[x] Keep __main__.py minimal (imports scripts.main.main)
[x] Update imports and references

### Phase 3: Simplify root scripts/run.py ✅
[x] Update server() to call server/scripts/main.py
[x] Update docker_server() to call server/scripts/dockerized_server.py
[x] Update publish_server() to call server/scripts/publish.py
[x] Keep format/lint/test functions in run.py (workspace-level)
[x] Remove unused imports (asyncio, os, argparse)

### Phase 4: Update Dockerfile ✅
[x] Keep CMD as "python -m screen_party_server" (works via __main__.py)
[x] Update PYTHONPATH to include /app/server
[x] Add comment explaining flow

### Phase 5: Testing ✅
[x] Run all tests (uv run test) - 120 tests pass
[x] Test server locally (uv run server --help) - works
[x] Test python -m screen_party_server --help - works
[x] Verify all commands work

## Current Structure
```
client/
└── scripts/
    ├── main.py            # Client execution
    └── package.py         # PyInstaller build

server/
├── src/screen_party_server/
│   ├── __main__.py        # Entry point (calls server.main())
│   └── server.py          # ScreenPartyServer class + main()
└── Dockerfile             # Uses "python -m screen_party_server"

scripts/
└── run.py                 # All server logic embedded here
```

## Target Structure
```
client/
└── scripts/
    ├── main.py            # Client execution ✅
    └── package.py         # PyInstaller build ✅

server/
├── scripts/
│   ├── __init__.py        # NEW
│   ├── main.py            # NEW - server execution (from __main__.py + server.main())
│   ├── dockerized_server.py  # NEW - Docker Compose
│   └── publish.py         # NEW - Docker build & publish
├── src/screen_party_server/
│   ├── __main__.py        # Minimal (call scripts.main)
│   └── server.py          # ScreenPartyServer class only (no main())
└── Dockerfile             # Uses server/scripts/main.py

scripts/
└── run.py                 # Minimal wrapper (calls client/server scripts)
    ├── client()           # → client/scripts/main.py
    ├── package_client()   # → client/scripts/package.py
    ├── server()           # → server/scripts/main.py
    ├── docker_server()    # → server/scripts/dockerized_server.py
    ├── publish_server()   # → server/scripts/publish.py
    ├── format()           # Keep in run.py (workspace-level)
    ├── lint()             # Keep in run.py (workspace-level)
    └── test()             # Keep in run.py (workspace-level)
```

## Commands After Reorganization
- `uv run client` - Run client
- `uv run package-client` - Package client
- `uv run server` - Run server locally
- `uv run publish-server` - Build & publish server Docker image
- `uv run docker-server` - Run server with Docker Compose
- `uv run format` - Format all code
- `uv run lint` - Lint all code
- `uv run test` - Run all tests (including integration)

## Results

### Files Changed
- **Deleted**: 6 script files (run_server.py, publish_server.py, docker_server.py, format_all.py, lint_all.py, test_all.py)
- **Modified**: run.py (added all functionality), pyproject.toml (updated entry points), package.py (simplified), README.md (updated documentation)
- **Net change**: -6 files, +449 lines in run.py, -655 lines removed from old scripts, -124 lines from package.py

### Testing
- ✅ All 120 tests pass (29 server, 91 client, 0 common)
- ✅ `uv run format` tested and working
- ✅ `uv run lint` tested and working
- ✅ `uv run server --help` tested and working
- ✅ `uv run test` tested and working

### Documentation
- ✅ README.md updated with comprehensive commands section
- ✅ Package workflow documentation updated
- ✅ All command entry points verified in pyproject.toml

### Commits
1. `e5b39ba` - [scripts] 모든 스크립트를 run.py로 통합
2. `1b2a827` - [scripts] package.py 간소화 - README/ZIP 생성 제거
3. `a745947` - [scripts] README.md 업데이트 - 명령어 섹션 추가
4. `43ef46f` - [scripts] scratchpad 업데이트 - 작업 완료 상태 기록

### Next Steps
- Phase 5 (integration tests) deferred - requires more domain knowledge
- Ready to merge to main branch
- All requested tasks completed
