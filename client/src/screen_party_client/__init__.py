"""Screen Party Client - PyQt6 기반 실시간 드로잉 클라이언트"""

__version__ = "0.1.0"

from .network.client import WebSocketClient

__all__ = ["WebSocketClient"]
