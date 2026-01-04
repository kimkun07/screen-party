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
import zipfile
from pathlib import Path
from datetime import datetime


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


def create_readme(version: str, output_path: Path):
    """README.txt 파일 생성"""
    readme_content = f"""Screen Party v{version.lstrip('v')} - Windows Client

실시간 화면 드로잉 공유 애플리케이션

## 사용 방법

1. ScreenParty.exe 실행
2. Host Mode 또는 Guest Mode 선택
3. 서버에 연결하여 드로잉 시작

## 명령줄 옵션

기본 실행:
    ScreenParty.exe

특정 서버 연결:
    ScreenParty.exe --server ws://192.168.1.100:8765

전체 화면 모드:
    ScreenParty.exe --fullscreen

도움말:
    ScreenParty.exe --help

## 시스템 요구사항

- Windows 10 이상
- 인터넷 연결 (서버 접속 시)

## 문제 해결

### 바이러스 백신 오탐
일부 바이러스 백신 프로그램에서 오탐할 수 있습니다.
안전한 프로그램이며, 필요 시 예외 처리를 추가해주세요.

### 실행 오류
- Visual C++ Redistributable 설치 확인
- Windows 방화벽 설정 확인

## 라이선스

MIT License

## 문의

GitHub: https://github.com/your-username/screen-party

빌드 날짜: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    output_path.write_text(readme_content, encoding='utf-8')
    print(f"✅ README.txt 생성 완료: {output_path}")


def create_zip(version: str, dist_dir: Path, output_dir: Path):
    """ZIP 압축 파일 생성"""
    zip_filename = f"ScreenParty-{version}-windows.zip"
    zip_path = output_dir / zip_filename

    # 기존 ZIP 파일 삭제
    if zip_path.exists():
        zip_path.unlink()

    print(f"\n{'='*60}")
    print(f"📦 ZIP 압축 생성: {zip_filename}")
    print(f"{'='*60}")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # ScreenParty.exe 추가
        exe_path = dist_dir / "ScreenParty.exe"
        if exe_path.exists():
            zipf.write(exe_path, "ScreenParty.exe")
            print(f"  ✅ ScreenParty.exe")
        else:
            print(f"  ❌ ScreenParty.exe not found!")
            sys.exit(1)

        # README.txt 추가
        readme_path = dist_dir / "README.txt"
        if readme_path.exists():
            zipf.write(readme_path, "README.txt")
            print(f"  ✅ README.txt")

    # 파일 크기 확인
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"\n✅ ZIP 생성 완료: {zip_path}")
    print(f"   크기: {size_mb:.2f} MB")

    return zip_path


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
  2. PyInstaller 실행 (client.spec)
  3. README.txt 생성
  4. ZIP 압축 (ScreenParty-v0.1.0-windows.zip)
  5. GitHub Release 안내

주의:
  - Windows에서 실행해야 합니다
  - PyInstaller가 설치되어 있어야 합니다 (uv sync --all-groups)
        """
    )

    parser.add_argument(
        "version",
        help="버전 태그 (예: v0.1.0, v0.2.0)"
    )

    parser.add_argument(
        "--skip-clean",
        action="store_true",
        help="기존 빌드 정리 건너뛰기"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제로 실행하지 않고 명령어만 출력"
    )

    args = parser.parse_args()

    # 버전 검증 (v로 시작하는지)
    version = args.version
    if not version.startswith('v'):
        print(f"⚠️  경고: 버전이 'v'로 시작하지 않습니다: {version}")
        print(f"   'v{version}'를 사용하시겠습니까? (y/n)")
        response = input().lower()
        if response == 'y':
            version = f'v{version}'
        else:
            print("❌ 취소됨")
            sys.exit(1)

    # 프로젝트 루트 경로
    project_root = Path(__file__).parent.parent
    spec_file = project_root / "client" / "client.spec"
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"

    print("\n" + "="*60)
    print("🚀 클라이언트 앱 패키징 시작 (PyInstaller)")
    print("="*60)
    print(f"버전: {version}")
    print(f"프로젝트 루트: {project_root}")
    print(f"Spec 파일: {spec_file}")
    print("="*60)

    if args.dry_run:
        print("\n⚠️  DRY RUN 모드 - 실제로 실행되지 않습니다")

    # 1. 기존 빌드 정리
    if not args.skip_clean:
        if not args.dry_run:
            if build_dir.exists():
                print(f"\n🗑️  기존 build/ 디렉토리 삭제...")
                shutil.rmtree(build_dir)
            if dist_dir.exists():
                print(f"🗑️  기존 dist/ 디렉토리 삭제...")
                shutil.rmtree(dist_dir)
            print("✅ 빌드 정리 완료")
        else:
            print(f"\n[DRY RUN] 기존 빌드 정리")

    # 2. PyInstaller 실행
    # Windows에서는 python -m PyInstaller 사용
    pyinstaller_cmd = [
        sys.executable,  # Python 인터프리터 경로
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]

    if not args.dry_run:
        run_command(pyinstaller_cmd, "PyInstaller 실행", cwd=project_root)
    else:
        print(f"\n[DRY RUN] {' '.join(pyinstaller_cmd)}")

    # 3. 결과물 확인
    if not args.dry_run:
        exe_path = dist_dir / "ScreenParty.exe"
        if not exe_path.exists():
            print(f"\n❌ 빌드 실패: {exe_path} 파일이 생성되지 않았습니다")
            sys.exit(1)

        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n✅ 실행 파일 생성 완료: {exe_path}")
        print(f"   크기: {size_mb:.2f} MB")

    # 4. README.txt 생성
    if not args.dry_run:
        readme_path = dist_dir / "README.txt"
        create_readme(version, readme_path)
    else:
        print(f"\n[DRY RUN] README.txt 생성")

    # 5. ZIP 압축
    if not args.dry_run:
        zip_path = create_zip(version, dist_dir, project_root)
    else:
        print(f"\n[DRY RUN] ZIP 압축: ScreenParty-{version}-windows.zip")

    # 완료
    print("\n" + "="*60)
    print("🎉 패키징 완료!")
    print("="*60)
    if not args.dry_run:
        print(f"✅ 실행 파일: {dist_dir / 'ScreenParty.exe'}")
        print(f"✅ ZIP 파일: {zip_path}")
        print(f"\n📤 GitHub Release 배포 방법:")
        print(f"   1. GitHub 레포지토리 → Releases → Create a new release")
        print(f"   2. Tag: {version}")
        print(f"   3. Title: Screen Party {version}")
        print(f"   4. {zip_path.name} 파일 업로드")
        print(f"\n또는 GitHub CLI 사용:")
        print(f"   gh release create {version} {zip_path.name} --title \"Screen Party {version}\"")
    print("="*60)


if __name__ == "__main__":
    main()
