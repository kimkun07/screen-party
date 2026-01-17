"""Screen Party 실행 스크립트 래퍼

이 모듈은 uv run 명령어 진입점을 제공합니다.
실제 스크립트는 각 패키지의 scripts 디렉토리에 있습니다.
"""

import asyncio
import os
import subprocess
import sys
import argparse
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
    """서버 실행"""
    # Add server/src to Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root / "server" / "src"))

    from screen_party_server.server import main as server_main

    parser = argparse.ArgumentParser(
        description="Screen Party WebSocket 서버",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  %(prog)s                           # 기본 설정으로 서버 시작 (0.0.0.0:8765)
  %(prog)s --host localhost          # localhost에서 서버 시작
  %(prog)s --port 9000               # 포트 9000으로 서버 시작
  %(prog)s --host 0.0.0.0 --port 80  # 모든 인터페이스, 포트 80

환경 변수:
  SCREEN_PARTY_HOST    서버 호스트 주소 (기본값: 0.0.0.0)
  SCREEN_PARTY_PORT    서버 포트 번호 (기본값: 8765)
        """,
    )

    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("SCREEN_PARTY_HOST", "0.0.0.0"),
        help="서버 호스트 주소 (기본값: 0.0.0.0)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("SCREEN_PARTY_PORT", "8765")),
        help="서버 포트 번호 (기본값: 8765)",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="자세한 로그 출력"
    )

    args = parser.parse_args()

    # 환경 변수 설정
    os.environ["SCREEN_PARTY_HOST"] = args.host
    os.environ["SCREEN_PARTY_PORT"] = str(args.port)

    # 서버 시작 메시지
    print("=" * 60)
    print("Screen Party 서버 시작".center(60))
    print("=" * 60)
    print(f"  호스트: {args.host}")
    print(f"  포트:   {args.port}")
    print(f"  URL:    ws://{args.host}:{args.port}")
    print("=" * 60)
    print()
    print("서버가 실행 중입니다. 종료하려면 Ctrl+C를 누르세요.")
    print()

    try:
        asyncio.run(server_main())
    except KeyboardInterrupt:
        print("\n서버 종료")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        sys.exit(1)


def publish_server():
    """서버 Docker 이미지 빌드 및 배포"""

    def run_command(cmd: list[str], description: str):
        """명령어 실행 및 결과 출력"""
        print(f"\n{'='*60}")
        print(f"📦 {description}")
        print(f"{'='*60}")
        print(f"$ {' '.join(cmd)}")
        print()

        result = subprocess.run(cmd, capture_output=False, text=True)

        if result.returncode != 0:
            print(f"\n❌ 실패: {description}")
            sys.exit(1)

        print(f"✅ 성공: {description}")
        return result

    parser = argparse.ArgumentParser(
        description="서버 Docker 이미지 빌드 및 Docker Hub 배포",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  uv run publish-server v0.1.0    # v0.1.0 태그로 빌드 및 배포
  uv run publish-server v0.2.0    # v0.2.0 태그로 빌드 및 배포

배포 과정:
  1. Docker 이미지 빌드
  2. v{version} 태그 지정
  3. latest 태그 추가
  4. Docker Hub에 푸시 (v{version})
  5. Docker Hub에 푸시 (latest)
        """,
    )

    parser.add_argument("version", help="버전 태그 (예: v0.1.0, v0.2.0)")

    parser.add_argument(
        "--skip-latest", action="store_true", help="latest 태그 푸시 건너뛰기"
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="실제로 실행하지 않고 명령어만 출력"
    )

    args = parser.parse_args()

    # 버전 검증 (v로 시작하는지)
    version = args.version
    if not version.startswith("v"):
        print(f"⚠️  경고: 버전이 'v'로 시작하지 않습니다: {version}")
        print(f"   'v{version}'를 사용하시겠습니까? (y/n)")
        if input().lower() == "y":
            version = f"v{version}"
        else:
            print("❌ 취소됨")
            sys.exit(1)

    # 프로젝트 루트 경로
    project_root = Path(__file__).parent.parent

    # Docker Hub 이미지 이름
    image_name = "kimkun07/screen-party-server"
    image_tag_version = f"{image_name}:{version}"
    image_tag_latest = f"{image_name}:latest"

    print("\n" + "=" * 60)
    print("🚀 서버 Docker 이미지 빌드 및 배포 시작")
    print("=" * 60)
    print(f"버전: {version}")
    print(f"이미지: {image_name}")
    print(f"태그: {version}, latest")
    print(f"프로젝트 루트: {project_root}")
    print("=" * 60)

    if args.dry_run:
        print("\n⚠️  DRY RUN 모드 - 실제로 실행되지 않습니다")

    # 1. Docker 이미지 빌드
    build_cmd = [
        "docker",
        "build",
        "--network=host",
        "-f",
        str(project_root / "server" / "Dockerfile"),
        "-t",
        image_tag_version,
        str(project_root),
    ]

    if not args.dry_run:
        run_command(build_cmd, f"Docker 이미지 빌드 ({version})")
    else:
        print(f"\n[DRY RUN] {' '.join(build_cmd)}")

    # 2. latest 태그 추가
    tag_cmd = ["docker", "tag", image_tag_version, image_tag_latest]

    if not args.dry_run:
        run_command(tag_cmd, "latest 태그 추가")
    else:
        print(f"[DRY RUN] {' '.join(tag_cmd)}")

    # 3. Docker Hub에 푸시 (버전 태그)
    push_version_cmd = ["docker", "push", image_tag_version]

    if not args.dry_run:
        run_command(push_version_cmd, f"Docker Hub 푸시 ({version})")
    else:
        print(f"[DRY RUN] {' '.join(push_version_cmd)}")

    # 4. Docker Hub에 푸시 (latest 태그)
    if not args.skip_latest:
        push_latest_cmd = ["docker", "push", image_tag_latest]

        if not args.dry_run:
            run_command(push_latest_cmd, "Docker Hub 푸시 (latest)")
        else:
            print(f"[DRY RUN] {' '.join(push_latest_cmd)}")
    else:
        print("\n⏭️  latest 태그 푸시 건너뛰기 (--skip-latest)")

    # 완료
    print("\n" + "=" * 60)
    print("🎉 배포 완료!")
    print("=" * 60)
    print(f"✅ 이미지: {image_tag_version}")
    if not args.skip_latest:
        print(f"✅ 이미지: {image_tag_latest}")
    print(f"\nDocker Hub: https://hub.docker.com/r/{image_name}")
    print("=" * 60)


def docker_server():
    """로컬 테스트용 서버 실행 (Docker Compose)"""
    root = Path(__file__).parent.parent
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
