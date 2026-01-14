#!/usr/bin/env python3
"""Screen Party 클라이언트 실행 스크립트

Usage:
    uv run client [options]

Example:
    uv run client
    uv run client --fullscreen
"""

import sys
import os
import asyncio
import argparse
import logging
from pathlib import Path

# client/src를 Python path에 추가
client_dir = Path(__file__).parent.parent
sys.path.insert(0, str(client_dir / "src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from qasync import QEventLoop
from screen_party_client.gui.main_window import MainWindow

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def get_resource_path(relative_path: str) -> str:
    """리소스 파일 경로 찾기 (개발/배포 환경 모두 지원)

    Args:
        relative_path: 리소스 파일의 상대 경로 (예: "assets/ScreenParty-Logo.ico")

    Returns:
        리소스 파일의 절대 경로 (문자열)
    """
    # PyInstaller로 패키징된 경우
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
        resource_path = os.path.join(base_path, relative_path)
        logger.info(f"PyInstaller mode - Resource path: {resource_path}")
        return resource_path

    # 개발 환경: client 디렉토리 기준
    # __file__은 client/scripts/main.py
    # client 디렉토리는 1단계 위
    base_path = Path(__file__).parent.parent
    resource_path = base_path / relative_path
    logger.info(f"Development mode - Resource path: {resource_path}")
    return str(resource_path)


def parse_args():
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(
        description="Screen Party 클라이언트 (PyQt6 GUI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  %(prog)s                    # 클라이언트 시작 (저장된 서버 주소 사용)
  %(prog)s --fullscreen       # 전체 화면 모드로 시작

참고:
  서버 주소는 GUI에서 직접 입력하고, 자동으로 저장됩니다.
        """
    )

    parser.add_argument(
        "--fullscreen",
        action="store_true",
        help="전체 화면 모드로 시작"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="자세한 로그 출력"
    )

    return parser.parse_args()


def main():
    """클라이언트 진입점"""
    args = parse_args()

    # verbose 모드 처리
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")

    # 클라이언트 시작 메시지
    print("=" * 60)
    print("Screen Party 클라이언트 시작".center(60))
    print("=" * 60)
    print()

    logger.info("Starting Screen Party Client...")

    # Windows에서 작업 표시줄 아이콘이 제대로 표시되도록 AppUserModelID 설정
    if sys.platform == 'win32':
        try:
            import ctypes
            # AppUserModelID를 설정하여 작업 표시줄에서 Python 기본 아이콘 대신 앱 아이콘 사용
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('ScreenParty.Client.1.0')
            logger.info("Windows AppUserModelID set")
        except Exception as e:
            logger.warning(f"Failed to set AppUserModelID: {e}")

    # PyQt6 애플리케이션 생성
    app = QApplication(sys.argv)
    app.setApplicationName("Screen Party")

    # 애플리케이션 아이콘 설정 (작업 표시줄 아이콘)
    app_icon = None
    try:
        icon_path = get_resource_path("assets/ScreenParty-Logo.ico")
        logger.info(f"Looking for icon at: {icon_path}")

        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            if not app_icon.isNull():
                app.setWindowIcon(app_icon)
                logger.info(f"✓ Application icon set successfully: {icon_path}")
            else:
                logger.warning(f"✗ Icon loaded but is null: {icon_path}")
        else:
            logger.warning(f"✗ Icon file not found: {icon_path}")
    except Exception as e:
        logger.error(f"✗ Failed to set application icon: {e}", exc_info=True)

    # asyncio 이벤트 루프와 PyQt6 통합
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 메인 윈도우 생성
    window = MainWindow()

    # MainWindow에도 명시적으로 아이콘 설정
    if app_icon and not app_icon.isNull():
        window.setWindowIcon(app_icon)
        logger.info("✓ MainWindow icon set")

    if args.fullscreen:
        window.showFullScreen()
    else:
        window.show()

    # 이벤트 루프 실행
    with loop:
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Client interrupted by user")
            print("\n클라이언트 종료")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            print(f"\n오류 발생: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
