"""Docker Compose로 서버 실행

로컬 테스트용 Docker Compose 서버 실행 스크립트입니다.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """로컬 테스트용 서버 실행 (Docker Compose)"""
    root = Path(__file__).parent.parent.parent
    compose_file = root / "server" / "docker-compose.yml"

    if not compose_file.exists():
        print(f"❌ Error: {compose_file} not found")
        sys.exit(1)

    print(f"Starting local server with {compose_file}...")

    result = subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "up", "--build"],
        cwd=root,
    )

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
