"""Docker 이미지로 서버 실행

로컬 테스트용 Docker 이미지로 서버 실행 스크립트입니다.
"""

import subprocess
import sys
from pathlib import Path

def main():
    scripts_dir = Path(__file__).parent
    server_dir = scripts_dir.parent
    root_dir = server_dir.parent

    dockerfile = server_dir / "Dockerfile"
    image_name = "screen-party-server:local"

    if not dockerfile.exists():
        print(f"❌ Error: {dockerfile} not found")
        sys.exit(1)

    # 1. 빌드 실행
    print(f"🔨 Building Docker image...")
    build_result = subprocess.run([
        "docker", "build",
        "--network=host",
        "-f", str(dockerfile),      # Dockerfile 위치 지정
        "-t", image_name,           # 이미지 태그 지정
        str(root_dir)               # 빌드 컨텍스트 (이 위치의 .dockerignore가 사용됨)
    ])

    if build_result.returncode != 0:
        print("❌ Build failed")
        sys.exit(build_result.returncode)

    # 2. 컨테이너 실행
    print(f"🚀 Running container: {image_name}...")
    
    # 기존에 실행 중인 동일 이름의 컨테이너가 있다면 삭제
    subprocess.run(["docker", "rm", "-f", "screen-party-server-test"], stderr=subprocess.DEVNULL)

    run_cmd = [
        "docker", "run", "--rm",
        "--name", "screen-party-server-test",
        # "--network", "host",         # 실행 시에도 호스트 네트워크 사용 (필요시)
        "-p", "8765:8765",         # network=host를 안 쓸 경우 포트 매핑 필요
        image_name
    ]

    result = subprocess.run(run_cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()