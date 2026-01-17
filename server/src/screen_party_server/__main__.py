"""Screen Party Server entry point

python -m screen_party_server 호출 시 진입점.
실제 로직은 server/scripts/main.py에 있습니다.
"""

import sys
from pathlib import Path

# server/scripts를 Python path에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "server"))

# 이제 scripts.main을 import 가능
from scripts.main import main  # noqa: E402

if __name__ == "__main__":
    main()
