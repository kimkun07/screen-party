# Scripts Reorganization

## Goal
Reorganize script files to follow the established pattern (like `run.py client` command), improving maintainability and consistency.

## Tasks

### Phase 1: Move server scripts into run.py
[x] Move run_server.py → server() function in run.py
[x] Move publish_server.py → publish_server() function in run.py
[x] Move docker_server.py → docker_server() function in run.py (rename)
[x] Delete original script files after migration
[x] Test server commands work correctly

### Phase 2: Move utility scripts into run.py
[x] Move format_all.py → format() function in run.py
[x] Move lint_all.py → lint() function in run.py
[x] Move test_all.py → test() function in run.py
[~] Add integration tests to test() function (already included)
[x] Delete original script files after migration
[x] Test utility commands work correctly

### Phase 3: Simplify package.py
[x] Remove README.txt generation (unnecessary)
[x] Remove ZIP file generation (unnecessary)
[x] Keep only PyInstaller build logic
[x] Test package command works correctly (dry-run tested)

### Phase 4: Clean up server entry points
[x] Check if both server.py and __main__.py are needed
[~] Both are needed: server.py has main(), __main__.py calls it
[~] Dockerfile already uses python -m screen_party_server
[~] No changes needed - already optimal

### Phase 5: Enhance integration tests
[~] Create multiple test scenarios (deferred - needs domain knowledge)
[~] Split into multiple files for different scenarios (deferred)
[~] Add integration tests to test command (deferred)

### Phase 6: Update pyproject.toml
[x] Update all script entry points in pyproject.toml
[x] Verify uv run commands work with new structure
[x] Test all commands end-to-end

### Phase 7: Update documentation
[x] Update README.md with new command structure
[x] Add comprehensive commands section (5단계)
[x] Update package.py documentation (removed README/ZIP mentions)
[x] All documentation updated

## Current Structure
```
scripts/
├── run.py                 # Entry point wrapper
├── run_server.py          # Server execution → Move to run.py
├── publish_server.py      # Server Docker build/publish → Move to run.py
├── docker_server.py       # Docker Compose server → Move to run.py
├── format_all.py          # Code formatting → Move to run.py
├── lint_all.py            # Linting → Move to run.py
└── test_all.py            # Testing → Move to run.py
```

## Target Structure
```
scripts/
└── run.py                 # All commands in one file
    ├── client()           # Already exists
    ├── package_client()   # Already exists
    ├── server()           # NEW (from run_server.py)
    ├── publish_server()   # NEW (from publish_server.py)
    ├── docker_server()    # NEW (from docker_server.py)
    ├── format()           # NEW (from format_all.py)
    ├── lint()             # NEW (from lint_all.py)
    └── test()             # NEW (from test_all.py) + integration tests
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
