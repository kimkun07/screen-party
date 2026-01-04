#!/usr/bin/env python3
"""
전체 workspace 테스트 실행 스크립트
각 workspace (common, server, client)에서 pytest를 실행합니다.
"""

import subprocess
import sys
import re
from pathlib import Path


def parse_pytest_output(output: str) -> tuple[bool, int, int]:
    """
    pytest 출력을 파싱하여 성공 여부, 패스 개수, 총 테스트 개수를 반환합니다.

    Returns:
        (success, passed, total)
    """
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


def main():
    """모든 workspace에서 테스트 실행"""
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


if __name__ == "__main__":
    main()
