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

# client/src를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "client", "src"))

from PyQt6.QtWidgets import QApplication
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

    # PyQt6 애플리케이션 생성
    app = QApplication(sys.argv)

    # asyncio 이벤트 루프와 PyQt6 통합
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 메인 윈도우 생성
    window = MainWindow()

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
