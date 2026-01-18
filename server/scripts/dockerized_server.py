"""Docker 이미지로 서버 실행

로컬 테스트용 Docker 이미지로 서버 실행 스크립트입니다.
"""

import argparse
import subprocess
import sys
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

DEFAULT_PORT = 8765
IMAGE_NAME = "screen-party-server:local"
CONTAINER_NAME = "screen-party-server-test"

# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Run Screen Party server in Docker")
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Host port to expose (default: {DEFAULT_PORT})"
    )
    args = parser.parse_args()

    scripts_dir = Path(__file__).parent
    server_dir = scripts_dir.parent
    root_dir = server_dir.parent

    dockerfile = server_dir / "Dockerfile"

    if not dockerfile.exists():
        print(f"❌ Error: {dockerfile} not found")
        sys.exit(1)

    # 1. 빌드 실행
    print(f"🔨 Building Docker image...")

    build_cmd = [
        "docker", "build",
        "--network=host",
        "-f", str(dockerfile),      # Dockerfile 위치 지정
        "-t", IMAGE_NAME,           # 이미지 태그 지정
        str(root_dir)               # 빌드 컨텍스트 (이 위치의 .dockerignore가 사용됨)
    ]

    build_result = subprocess.run(build_cmd)

    if build_result.returncode != 0:
        print("❌ Build failed")
        sys.exit(build_result.returncode)

    # 2. 컨테이너 실행
    print(f"🚀 Running container: {IMAGE_NAME}")
    print(f"   Network: host (포트 {args.port}에서 리스닝)")

    # 기존에 실행 중인 동일 이름의 컨테이너가 있다면 삭제
    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], stderr=subprocess.DEVNULL)

    run_cmd = [
        "docker", "run", "--rm",
        "--name", CONTAINER_NAME,
        "--network", "host",
        # "-p", f"{args.port}:8765", # 잘 작동하지 않아서 network host 사용함.
        IMAGE_NAME,
        "uv", "run", "--no-sync", "--directory", "/app/server", "server",
        "--host", "0.0.0.0",
        "--port", str(args.port)
    ]

    result = subprocess.run(run_cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()