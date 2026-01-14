"""Screen Party 실행 스크립트 래퍼

이 모듈은 uv run 명령어 진입점을 제공합니다.
실제 스크립트는 각 패키지의 scripts 디렉토리에 있습니다.
"""

import subprocess
import sys
from pathlib import Path


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
