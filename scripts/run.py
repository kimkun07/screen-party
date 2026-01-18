"""Screen Party 실행 스크립트 래퍼

이 모듈은 uv run 명령어 진입점을 제공합니다.
실제 스크립트는 각 패키지의 scripts 디렉토리에 있습니다.
"""

import subprocess
import sys
import re
from pathlib import Path


# ============================================================================
# Configuration Data
# ============================================================================

# 단일 스크립트 실행 설정
SCRIPT_CONFIGS = {
    "client": {
        "package": "client",
        "script": "scripts/main.py",
        "description": "클라이언트 실행",
    },
    "package_client": {
        "package": "client",
        "script": "scripts/package.py",
        "description": "클라이언트 패키징",
    },
    "server": {
        "package": "server",
        "script": "scripts/main.py",
        "description": "서버 실행",
    },
    "publish_server": {
        "package": "server",
        "script": "scripts/publish.py",
        "description": "서버 Docker 이미지 빌드 및 배포",
    },
    "dockerized_server": {
        "package": "server",
        "script": "scripts/dockerized_server.py",
        "description": "로컬 테스트용 서버 실행",
    },
}

# Workspace 도구 설정
WORKSPACE_TOOLS = {
    "format": {
        "command": ["black", "src", "tests"],
        "title": "Formatting",
        "summary_title": "Format Summary",
        "success_msg": "✅ All workspaces formatted!",
        "fail_prefix": "❌ Failed workspaces:",
    },
    "lint": {
        "command": ["ruff", "check", "src", "tests"],
        "title": "Linting",
        "summary_title": "Lint Summary",
        "success_msg": "✅ All workspaces passed linting!",
        "fail_prefix": "❌ Failed workspaces:",
    },
}

# Workspace 목록
WORKSPACES = ["common", "server", "client", "integration"]


# ============================================================================
# Common Functions
# ============================================================================


def _run_script(package: str, script: str):
    """공통 스크립트 실행 로직"""
    project_root = Path(__file__).parent.parent
    script_path = project_root / package / script

    cmd = [
        "uv",
        "run",
        "--directory",
        str(project_root / package),
        "python",
        str(script_path),
    ]

    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def _run_workspace_tool(tool_config: dict):
    """공통 workspace 도구 실행 로직"""
    root = Path(__file__).parent.parent
    failed = []

    for workspace in WORKSPACES:
        workspace_path = root / workspace
        print(f"\n{'='*60}")
        print(f"{tool_config['title']} {workspace}...")
        print(f"{'='*60}\n")

        # Ensure dev dependencies are installed
        subprocess.run(
            ["uv", "sync", "--directory", str(workspace_path), "--all-extras"],
            cwd=root,
            stdout=subprocess.DEVNULL,
        )

        result = subprocess.run(
            ["uv", "run", "--directory", str(workspace_path)] + tool_config["command"],
            cwd=root,
        )

        if result.returncode != 0:
            failed.append(workspace)

    print(f"\n{'='*60}")
    print(tool_config["summary_title"])
    print(f"{'='*60}")

    if failed:
        print(f"{tool_config['fail_prefix']} {', '.join(failed)}")
        sys.exit(1)
    else:
        print(tool_config["success_msg"])
        sys.exit(0)


# ============================================================================
# Client Commands
# ============================================================================


def client():
    """클라이언트 실행 (client/scripts/main.py)"""
    config = SCRIPT_CONFIGS["client"]
    _run_script(config["package"], config["script"])


def package_client():
    """클라이언트 패키징 (client/scripts/package.py)"""
    config = SCRIPT_CONFIGS["package_client"]
    _run_script(config["package"], config["script"])


# ============================================================================
# Server Commands
# ============================================================================


def server():
    """서버 실행 (server/scripts/main.py)"""
    config = SCRIPT_CONFIGS["server"]
    _run_script(config["package"], config["script"])


def publish_server():
    """서버 Docker 이미지 빌드 및 배포 (server/scripts/publish.py)"""
    config = SCRIPT_CONFIGS["publish_server"]
    _run_script(config["package"], config["script"])


def dockerized_server():
    """로컬 테스트용 서버 실행 (server/scripts/dockerized_server.py)"""
    config = SCRIPT_CONFIGS["dockerized_server"]
    _run_script(config["package"], config["script"])


# ============================================================================
# Utility Commands
# ============================================================================


def format():
    """전체 workspace 코드 포맷팅"""
    _run_workspace_tool(WORKSPACE_TOOLS["format"])


def lint():
    """전체 workspace 린팅"""
    _run_workspace_tool(WORKSPACE_TOOLS["lint"])


def _parse_pytest_output(output: str) -> tuple[bool, int, int]:
    """pytest 출력을 파싱하여 성공 여부, 패스 개수, 총 테스트 개수를 반환"""
    # "no tests ran" 체크
    if "no tests ran" in output.lower():
        return True, 0, 0

    # "X passed in Y.YYs" 패턴 찾기
    passed_match = re.search(r"(\d+) passed", output)
    failed_match = re.search(r"(\d+) failed", output)

    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    total = passed + failed

    success = failed == 0

    return success, passed, total


def test():
    """전체 workspace 테스트 실행 (unit + integration)"""
    root = Path(__file__).parent.parent
    results = {}

    for workspace in WORKSPACES:
        workspace_path = root / workspace
        print(f"\n{'='*60}")
        print(f"Running tests in {workspace}...")
        print(f"{'='*60}\n")

        result = subprocess.run(
            ["uv", "run", "--directory", str(workspace_path), "pytest"],
            cwd=root,
            capture_output=True,
            text=True,
        )

        # 출력 표시
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        # 결과 파싱
        success, passed, total = _parse_pytest_output(result.stdout)
        results[workspace] = (success, passed, total)

    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")

    all_success = True
    for workspace, (success, passed, total) in results.items():
        status = "✅" if success else "❌"
        if total == 0:
            print(f"{status} {workspace:10s}: no tests")
        else:
            print(f"{status} {workspace:10s}: {passed}/{total} passed")

        if not success:
            all_success = False

    print(f"{'='*60}")

    if all_success:
        sys.exit(0)
    else:
        sys.exit(1)
