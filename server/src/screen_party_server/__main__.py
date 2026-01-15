"""Screen Party Server entry point"""

import asyncio
import os

from .server import ScreenPartyServer


def main():
    """서버 진입점"""
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8765"))

    server = ScreenPartyServer(host=host, port=port)
    asyncio.run(server.start())


if __name__ == "__main__":
    main()
