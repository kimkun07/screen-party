#!/usr/bin/env python3
"""
전체 workspace 린팅 스크립트
각 workspace (common, server, client)에서 ruff를 실행합니다.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """모든 workspace에서 ruff 실행"""
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


if __name__ == "__main__":
    main()
