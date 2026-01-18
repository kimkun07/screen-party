"""Screen Party 실행 스크립트 래퍼

이 모듈은 uv run 명령어 진입점을 제공합니다.
실제 스크립트는 각 패키지의 scripts 디렉토리에 있습니다.
"""

import subprocess
import sys
import re
from pathlib import Path


# ============================================================================
# Client Commands
# ============================================================================


def client():
    """클라이언트 실행 (client/scripts/main.py)"""
    project_root = Path(__file__).parent.parent
    script_path = project_root / "client" / "scripts" / "main.py"

    # uv run --directory를 사용하여 client 환경에서 실행
    cmd = [
        "uv",
        "run",
        "--directory",
        str(project_root / "client"),
        "python",
        str(script_path),
    ]

    # 명령줄 인자 전달
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def package_client():
    """클라이언트 패키징 (client/scripts/package.py)"""
    project_root = Path(__file__).parent.parent
    script_path = project_root / "client" / "scripts" / "package.py"

    # uv run --directory를 사용하여 client 환경에서 실행
    cmd = [
        "uv",
        "run",
        "--directory",
        str(project_root / "client"),
        "python",
        str(script_path),
    ]

    # 명령줄 인자 전달
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


# ============================================================================
# Server Commands
# ============================================================================


def server():
    """서버 실행 (server/scripts/main.py)"""
    project_root = Path(__file__).parent.parent
    script_path = project_root / "server" / "scripts" / "main.py"

    # uv run --directory를 사용하여 server 환경에서 실행
    cmd = [
        "uv",
        "run",
        "--directory",
        str(project_root / "server"),
        "python",
        str(script_path),
    ]

    # 명령줄 인자 전달
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def publish_server():
    """서버 Docker 이미지 빌드 및 배포 (server/scripts/publish.py)"""
    project_root = Path(__file__).parent.parent
    script_path = project_root / "server" / "scripts" / "publish.py"

    # uv run --directory를 사용하여 server 환경에서 실행
    cmd = [
        "uv",
        "run",
        "--directory",
        str(project_root / "server"),
        "python",
        str(script_path),
    ]

    # 명령줄 인자 전달
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def dockerized_server():
    """로컬 테스트용 서버 실행 (server/scripts/dockerized_server.py)"""
    project_root = Path(__file__).parent.parent
    script_path = project_root / "server" / "scripts" / "dockerized_server.py"

    # uv run --directory를 사용하여 server 환경에서 실행
    cmd = [
        "uv",
        "run",
        "--directory",
        str(project_root / "server"),
        "python",
        str(script_path),
    ]

    # 명령줄 인자 전달
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


# ============================================================================
# Utility Commands
# ============================================================================


def format():
    """전체 workspace 코드 포맷팅"""
    root = Path(__file__).parent.parent
    workspaces = ["common", "server", "client"]

    failed = []

    for workspace in workspaces:
        workspace_path = root / workspace
        print(f"\n{'='*60}")
        print(f"Formatting {workspace}...")
        print(f"{'='*60}\n")

        # Ensure dev dependencies are installed
        subprocess.run(
            ["uv", "sync", "--directory", str(workspace_path), "--all-extras"],
            cwd=root,
            stdout=subprocess.DEVNULL,
        )

        result = subprocess.run(
            ["uv", "run", "--directory", str(workspace_path), "black", "src", "tests"],
            cwd=root,
        )

        if result.returncode != 0:
            failed.append(workspace)

    print(f"\n{'='*60}")
    print("Format Summary")
    print(f"{'='*60}")

    if failed:
        print(f"❌ Failed workspaces: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("✅ All workspaces formatted!")
        sys.exit(0)


def lint():
    """전체 workspace 린팅"""
    root = Path(__file__).parent.parent
    workspaces = ["common", "server", "client"]

    failed = []

    for workspace in workspaces:
        workspace_path = root / workspace
        print(f"\n{'='*60}")
        print(f"Linting {workspace}...")
        print(f"{'='*60}\n")

        # Ensure dev dependencies are installed
        subprocess.run(
            ["uv", "sync", "--directory", str(workspace_path), "--all-extras"],
            cwd=root,
            stdout=subprocess.DEVNULL,
        )

        result = subprocess.run(
            ["uv", "run", "--directory", str(workspace_path), "ruff", "check", "src", "tests"],
            cwd=root,
        )

        if result.returncode != 0:
            failed.append(workspace)

    print(f"\n{'='*60}")
    print("Lint Summary")
    print(f"{'='*60}")

    if failed:
        print(f"❌ Failed workspaces: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("✅ All workspaces passed linting!")
        sys.exit(0)


def test():
    """전체 workspace 테스트 실행 (unit + integration)"""

    def parse_pytest_output(output: str) -> tuple[bool, int, int]:
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

    root = Path(__file__).parent.parent
    workspaces = ["common", "server", "client"]

    results = {}

    for workspace in workspaces:
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
        success, passed, total = parse_pytest_output(result.stdout)
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
