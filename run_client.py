#!/usr/bin/env python3
"""Screen Party 클라이언트 실행 스크립트"""

import sys
import os
import asyncio

# client/src를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "client", "src"))

from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop
from screen_party_client.gui.main_window import MainWindow

def main():
    """클라이언트 진입점"""
    print("=" * 50)
    print("Screen Party 클라이언트 시작")
    print("=" * 50)
    print(f"서버 URL: {os.getenv('SCREEN_PARTY_SERVER', 'ws://localhost:8765')}")
    print("=" * 50)
    print()

    # PyQt6 애플리케이션 생성
    app = QApplication(sys.argv)

    # asyncio 이벤트 루프와 PyQt6 통합
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 메인 윈도우 생성
    server_url = os.getenv("SCREEN_PARTY_SERVER", "ws://localhost:8765")
    window = MainWindow(server_url=server_url)
    window.show()

    # 이벤트 루프 실행
    with loop:
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            print("\n클라이언트 종료")

if __name__ == "__main__":
    main()
