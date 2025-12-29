#!/usr/bin/env python3
"""Screen Party 서버 실행 스크립트"""

import sys
import os

# server/src를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "server", "src"))

# 서버 실행
from screen_party_server.server import main
import asyncio

if __name__ == "__main__":
    print("=" * 50)
    print("Screen Party 서버 시작")
    print("=" * 50)
    print(f"주소: {os.getenv('SCREEN_PARTY_HOST', '0.0.0.0')}")
    print(f"포트: {os.getenv('SCREEN_PARTY_PORT', '8765')}")
    print("=" * 50)
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n서버 종료")
