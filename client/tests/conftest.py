"""pytest configuration for client tests"""

import os
import sys


def pytest_configure(config):
    """Set up environment for headless GUI testing

    Only use offscreen mode on Linux without DISPLAY (e.g., devcontainer, CI).
    Windows and macOS can run GUI tests normally.
    """
    # Linux headless 환경에서만 offscreen 사용
    # (DISPLAY 환경변수가 없거나 CI 환경)
    if sys.platform.startswith('linux'):
        if not os.environ.get('DISPLAY') or os.environ.get('CI'):
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
