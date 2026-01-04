"""Screen Party Client 실행 진입점"""

import sys
import asyncio
import logging

from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from .gui.main_window import MainWindow

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """메인 함수"""
    # QApplication 생성
    app = QApplication(sys.argv)

    # qasync 이벤트 루프 설정
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # MainWindow 생성 및 표시
    window = MainWindow()
    window.show()

    logger.info("Screen Party Client started")

    # 이벤트 루프 실행
    with loop:
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Client interrupted by user")
        finally:
            sys.exit(0)


if __name__ == "__main__":
    main()
