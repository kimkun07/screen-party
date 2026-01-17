#!/usr/bin/env python3
"""클라이언트 앱 패키징 스크립트 (PyInstaller)

Usage:
    uv run package-client <version>

Example:
    uv run package-client v0.1.0
    uv run package-client v0.2.0
"""

import subprocess
import sys
import argparse
import shutil
from pathlib import Path


def parse_version(version: str) -> tuple[int, int, int, int]:
    """버전 문자열을 튜플로 변환 (예: v0.1.0 -> (0, 1, 0, 0))"""
    # v 접두사 제거
    ver = version.lstrip("v")
    parts = ver.split(".")

    # 최대 4개의 숫자로 분리 (major, minor, patch, build)
    nums = []
    for part in parts[:4]:
        try:
            nums.append(int(part))
        except ValueError:
            nums.append(0)

    # 4개로 맞추기
    while len(nums) < 4:
        nums.append(0)

    return tuple(nums[:4])


def create_version_info(version: str, output_path: Path):
    """Windows 버전 정보 파일 생성 (version_info.txt)"""
    ver_tuple = parse_version(version)
    ver_str = version.lstrip("v")

    content = f"""# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    filevers={ver_tuple},
    prodvers={ver_tuple},
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [
            StringStruct(u'CompanyName', u'Screen Party'),
            StringStruct(u'FileDescription', u'Screen Party - Real-time Drawing Overlay'),
            StringStruct(u'FileVersion', u'{ver_str}'),
            StringStruct(u'InternalName', u'ScreenParty'),
            StringStruct(u'LegalCopyright', u'MIT License'),
            StringStruct(u'OriginalFilename', u'ScreenParty.exe'),
            StringStruct(u'ProductName', u'Screen Party'),
            StringStruct(u'ProductVersion', u'{ver_str}'),
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""

    output_path.write_text(content, encoding="utf-8")
    print(f"✅ version_info.txt 생성 완료: {output_path}")


def run_command(cmd: list[str], description: str, cwd=None):
    """명령어 실행 및 결과 출력"""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"{'='*60}")
    print(f"$ {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, capture_output=False, text=True, cwd=cwd)

    if result.returncode != 0:
        print(f"\n❌ 실패: {description}")
        sys.exit(1)

    print(f"✅ 성공: {description}")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="클라이언트 앱 패키징 (PyInstaller)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  uv run package-client v0.1.0    # v0.1.0 버전 패키징
  uv run package-client v0.2.0    # v0.2.0 버전 패키징

패키징 과정:
  1. 기존 빌드 정리 (build/, dist/)
  2. version_info.txt 생성 (버전 정보)
  3. PyInstaller 실행 (client.spec)
  4. 임시 version_info.txt 삭제
  5. 결과물 확인 (dist/ScreenParty.exe)

주의:
  - Windows에서 실행해야 합니다
  - PyInstaller가 설치되어 있어야 합니다 (uv sync --all-groups)
        """,
    )

    parser.add_argument("version", help="버전 태그 (예: v0.1.0, v0.2.0)")

    parser.add_argument(
        "--skip-clean", action="store_true", help="기존 빌드 정리 건너뛰기"
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
        response = input().lower()
        if response == "y":
            version = f"v{version}"
        else:
            print("❌ 취소됨")
            sys.exit(1)

    # 프로젝트 루트 경로 (client/scripts/package.py 기준)
    client_dir = Path(__file__).parent.parent
    project_root = client_dir.parent
    spec_file = client_dir / "client.spec"
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    version_info_file = client_dir / "version_info.txt"

    print("\n" + "=" * 60)
    print("🚀 클라이언트 앱 패키징 시작 (PyInstaller)")
    print("=" * 60)
    print(f"버전: {version}")
    print(f"프로젝트 루트: {project_root}")
    print(f"Spec 파일: {spec_file}")
    print("=" * 60)

    if args.dry_run:
        print("\n⚠️  DRY RUN 모드 - 실제로 실행되지 않습니다")

    # 1. 기존 빌드 정리
    if not args.skip_clean:
        if not args.dry_run:
            if build_dir.exists():
                print("\n🗑️  기존 build/ 디렉토리 삭제...")
                shutil.rmtree(build_dir)
            if dist_dir.exists():
                print("🗑️  기존 dist/ 디렉토리 삭제...")
                shutil.rmtree(dist_dir)
            print("✅ 빌드 정리 완료")
        else:
            print("\n[DRY RUN] 기존 빌드 정리")

    # 2. version_info.txt 생성
    if not args.dry_run:
        create_version_info(version, version_info_file)
    else:
        print("\n[DRY RUN] version_info.txt 생성")

    # 3. PyInstaller 실행
    pyinstaller_cmd = [
        "uv",
        "run",
        "--directory",
        str(client_dir),
        "pyinstaller",
        "--clean",
        "--noconfirm",
        str(spec_file),
    ]

    if not args.dry_run:
        run_command(pyinstaller_cmd, "PyInstaller 실행", cwd=project_root)
    else:
        print(f"\n[DRY RUN] {' '.join(pyinstaller_cmd)}")

    # 4. 임시 version_info.txt 삭제
    if not args.dry_run and version_info_file.exists():
        version_info_file.unlink()
        print("🗑️  임시 version_info.txt 삭제 완료")

    # 5. 결과물 확인
    if not args.dry_run:
        exe_path = dist_dir / "ScreenParty.exe"
        if not exe_path.exists():
            print(f"\n❌ 빌드 실패: {exe_path} 파일이 생성되지 않았습니다")
            sys.exit(1)

        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n✅ 실행 파일 생성 완료: {exe_path}")
        print(f"   크기: {size_mb:.2f} MB")

    # 완료
    print("\n" + "=" * 60)
    print("🎉 패키징 완료!")
    print("=" * 60)
    if not args.dry_run:
        print(f"✅ 실행 파일: {dist_dir / 'ScreenParty.exe'}")
        print("\n📤 배포 방법:")
        print(f"   1. GitHub Releases에서 {version} 태그로 릴리즈 생성")
        print(f"   2. dist/ScreenParty.exe 파일 업로드")
    print("=" * 60)


if __name__ == "__main__":
    main()
