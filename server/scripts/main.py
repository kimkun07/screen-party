"""Screen Party 서버 실행 스크립트

서버를 실행하는 메인 진입점입니다.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path


def main():
    """서버 실행"""
    # Add server/src to Python path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root / "server" / "src"))

    from screen_party_server.server import ScreenPartyServer

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
        server = ScreenPartyServer(host=args.host, port=args.port)
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\n서버 종료")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
