"""Docker 이미지 빌드 및 배포 스크립트

서버 Docker 이미지를 빌드하고 Docker Hub에 배포합니다.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
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
    project_root = Path(__file__).parent.parent.parent

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


if __name__ == "__main__":
    main()
