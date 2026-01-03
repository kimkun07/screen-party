#!/usr/bin/env python3
"""Screen Party 클라이언트 실행 스크립트

Usage:
    uv run client [options]

Example:
    uv run client
    uv run client --server ws://localhost:8765
    uv run client --server wss://your-server.com
"""

import sys
import os
import asyncio
import argparse

# client/src를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "client", "src"))

from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop
from screen_party_client.gui.main_window import MainWindow


def parse_args():
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(
        description="Screen Party 클라이언트 (PyQt6 GUI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  %(prog)s                              # 기본 서버에 연결 (ws://localhost:8765)
  %(prog)s --server ws://192.168.1.10   # 특정 서버에 연결
  %(prog)s --server ws://example.com:9000  # 외부 서버에 연결

환경 변수:
  SCREEN_PARTY_SERVER    서버 WebSocket URL (기본값: ws://localhost:8765)
        """
    )

    parser.add_argument(
        "--server",
        type=str,
        default=os.getenv("SCREEN_PARTY_SERVER", "ws://localhost:8765"),
        help="서버 WebSocket URL (기본값: ws://localhost:8765)"
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

    # 환경 변수 설정
    os.environ["SCREEN_PARTY_SERVER"] = args.server

    # 클라이언트 시작 메시지
    print("=" * 60)
    print("Screen Party 클라이언트 시작".center(60))
    print("=" * 60)
    print(f"  서버 URL: {args.server}")
    print("=" * 60)
    print()

    # PyQt6 애플리케이션 생성
    app = QApplication(sys.argv)

    # asyncio 이벤트 루프와 PyQt6 통합
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 메인 윈도우 생성
    window = MainWindow(server_url=args.server)

    if args.fullscreen:
        window.showFullScreen()
    else:
        window.show()

    # 이벤트 루프 실행
    with loop:
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            print("\n클라이언트 종료")
        except Exception as e:
            print(f"\n오류 발생: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
