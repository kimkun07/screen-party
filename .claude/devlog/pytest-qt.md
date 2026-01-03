# Task: pytest-qt GUI 자동화 테스트 설정

## 개요

PyQt6 GUI를 headless 환경(devcontainer)에서 자동화 테스트하기 위한 pytest-qt 설정

## 목표

- [x] pytest-qt, pytest-xvfb 설치
- [x] devcontainer에서 GUI 테스트 실행 가능하도록 시스템 의존성 설치
- [x] pytest 설정 (pyproject.toml)
- [x] GUI 테스트 작성 및 검증

## 설정 과정

### 1. Python 의존성 추가

#### 루트 pyproject.toml
```toml
[dependency-groups]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "pytest-qt>=4.4.0",        # 추가
    "pytest-xvfb>=3.0.0",      # 추가
    "black>=24.0.0",
    "ruff>=0.8.0",
]
```

#### client/pyproject.toml
```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "pytest-qt>=4.4.0",        # 추가
    "pytest-xvfb>=3.0.0",      # 추가
]
```

**이유**:
- `pytest-qt`: PyQt/PySide GUI 테스트를 위한 pytest 플러그인
- `pytest-xvfb`: X Window System이 없는 환경에서 가상 디스플레이 제공

### 2. 시스템 의존성 설치 (devcontainer)

pytest-qt를 사용하려면 여러 시스템 라이브러리가 필요합니다. 다음과 같은 에러가 순차적으로 발생했습니다:

#### 에러 1: libGL.so.1 missing
```
ImportError: libGL.so.1: cannot open shared object file: No such file or directory
```

**해결**:
```bash
apt-get install -y xvfb libgl1 libglib2.0-0 libdbus-1-3
```

#### 에러 2: libxkbcommon.so.0 missing
```
ImportError: libxkbcommon.so.0: cannot open shared object file: No such file or directory
```

**해결**:
```bash
apt-get install -y libxkbcommon0 libxkbcommon-x11-0 libxcb-icccm4 \
    libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0
```

#### 에러 3: libEGL.so.1 missing
```
ImportError: libEGL.so.1: cannot open shared object file: No such file or directory
```

**해결**:
```bash
apt-get install -y libegl1 libdbus-1-3 libfontconfig1
```

#### 전체 설치 명령어 (한 번에)
```bash
apt-get update && apt-get install -y \
    xvfb \
    libgl1 \
    libglib2.0-0 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libegl1 \
    libfontconfig1
```

### 3. pytest 설정 (pyproject.toml)

#### 루트 pyproject.toml에 추가
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["server/tests", "client/tests", "common/tests"]
qt_api = "pyqt6"  # 사용할 Qt API 지정
markers = [
    "gui: marks tests that require GUI (deselect with '-m \"not gui\"')"
]
```

**주의**: `qt_api` 설정은 pytest-qt에서 사용하지만, pytest가 "Unknown config option" 경고를 표시합니다. 이는 무시해도 됩니다.

### 4. 테스트 파일 작성 시 주의사항

#### pytest_plugins 설정 (실패한 방법)
```python
# ❌ 이렇게 하면 안 됨
pytest_plugins = ["pytest_qt"]  # ModuleNotFoundError 발생
```

pytest-qt는 자동으로 로드되므로 명시적으로 로드할 필요 없습니다.

#### GUI 테스트 마커
```python
# ✅ 올바른 방법
import pytest

pytestmark = pytest.mark.gui  # 파일 전체를 GUI 테스트로 마킹
```

#### qtbot fixture 사용
```python
def test_something(qtbot):
    """qtbot은 pytest-qt가 자동으로 제공하는 fixture"""
    window = MainWindow()
    qtbot.addWidget(window)  # 위젯을 qtbot에 추가
    window.show()  # 반드시 show() 호출 필요

    assert window.isVisible()
```

**주의**: `qtbot.addWidget()`만으로는 위젯이 보이지 않습니다. `window.show()`를 명시적으로 호출해야 `isVisible()`이 True가 됩니다.

### 5. 테스트 실행 방법

#### offscreen 모드로 실행 (권장)
```bash
QT_QPA_PLATFORM=offscreen uv run pytest client/tests/test_main_window_gui.py -v
```

**이유**: devcontainer에는 X Window System이 없으므로 offscreen 플랫폼을 사용해야 합니다.

#### 특정 테스트만 실행
```bash
QT_QPA_PLATFORM=offscreen uv run pytest client/tests/test_main_window_gui.py::TestStartScreen -v
```

#### GUI 테스트 제외하고 실행
```bash
uv run pytest -m "not gui"
```

### 6. 주요 API

#### qtbot.addWidget()
```python
qtbot.addWidget(window)  # 테스트 종료 시 자동으로 정리됨
```

#### qtbot.mouseClick()
```python
from PyQt6.QtCore import Qt
qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
```

#### qtbot.keyClicks()
```python
qtbot.keyClicks(line_edit, "ABC123")  # 텍스트 입력 시뮬레이션
```

#### QApplication.clipboard()
```python
from PyQt6.QtWidgets import QApplication
clipboard = QApplication.clipboard()
assert clipboard.text() == "expected_text"
```

## 문제 해결

### 문제 1: pytest-qt가 import되지 않음
```
ImportError: Error importing plugin "pytest_qt": No module named 'pytest_qt'
```

**원인**: uv.lock이 업데이트되지 않음

**해결**:
```bash
uv lock && uv sync --all-groups
```

### 문제 2: isVisible()이 항상 False
```python
window = MainWindow()
qtbot.addWidget(window)
assert window.start_widget.isVisible()  # ❌ AssertionError
```

**원인**: 위젯이 show()되지 않음

**해결**:
```python
window = MainWindow()
qtbot.addWidget(window)
window.show()  # ✅ 추가
assert window.start_widget.isVisible()  # ✅ 통과
```

### 문제 3: 시스템 라이브러리 없음
```
ImportError: libXXX.so.1: cannot open shared object file
```

**원인**: PyQt6가 필요로 하는 시스템 라이브러리 미설치

**해결**: 위의 "시스템 의존성 설치" 섹션 참고

## 테스트 결과

### 작성된 테스트
- **총 17개 테스트**
- **100% 통과** ✅

| 카테고리 | 테스트 수 | 파일 |
|---------|----------|------|
| 시작 화면 | 6개 | `test_main_window_gui.py::TestStartScreen` |
| 메인 화면 | 3개 | `test_main_window_gui.py::TestMainScreen` |
| UI 상태 | 3개 | `test_main_window_gui.py::TestUIState` |
| 상태 메시지 | 3개 | `test_main_window_gui.py::TestStatusMessages` |
| 화면 전환 | 2개 | `test_main_window_gui.py::TestScreenTransition` |

### 실행 결과
```
============================= test session starts ==============================
platform linux -- Python 3.13.5, pytest-9.0.2, pluggy-1.6.0
PyQt6 6.10.1 -- Qt runtime 6.10.1 -- Qt compiled 6.10.0
plugins: qt-4.5.0, xvfb-3.1.1, cov-7.0.0, asyncio-1.3.0
collecting ... collected 17 items

client/tests/test_main_window_gui.py::TestStartScreen::test_initial_state PASSED
client/tests/test_main_window_gui.py::TestStartScreen::test_server_input_default_value PASSED
client/tests/test_main_window_gui.py::TestStartScreen::test_server_input_custom_value PASSED
client/tests/test_main_window_gui.py::TestStartScreen::test_session_input_enables_join_button PASSED
client/tests/test_main_window_gui.py::TestStartScreen::test_session_input_empty_disables_join_button PASSED
client/tests/test_main_window_gui.py::TestStartScreen::test_create_button_enabled_by_default PASSED
client/tests/test_main_window_gui.py::TestMainScreen::test_show_main_screen PASSED
client/tests/test_main_window_gui.py::TestMainScreen::test_copy_server_address PASSED
client/tests/test_main_window_gui.py::TestMainScreen::test_copy_session_id PASSED
client/tests/test_main_window_gui.py::TestUIState::test_disable_start_buttons PASSED
client/tests/test_main_window_gui.py::TestUIState::test_enable_start_buttons PASSED
client/tests/test_main_window_gui.py::TestUIState::test_enable_start_buttons_without_session PASSED
client/tests/test_main_window_gui.py::TestStatusMessages::test_set_start_status PASSED
client/tests/test_main_window_gui.py::TestStatusMessages::test_set_status_when_connected PASSED
client/tests/test_main_window_gui.py::TestStatusMessages::test_set_status_when_not_connected PASSED
client/tests/test_main_window_gui.py::TestScreenTransition::test_show_start_screen PASSED
client/tests/test_main_window_gui.py::TestScreenTransition::test_show_main_screen_updates_labels PASSED

============================== 17 passed in 0.10s ==============================
```

## 클로드 코드 일기

### 2026-01-03 - pytest-qt 설정 완료

**상태**: 🟡 준비중 → 🟢 진행중 → ✅ 완료

**진행 내용**:
- ✅ pytest-qt, pytest-xvfb 의존성 추가
- ✅ devcontainer에서 필요한 시스템 라이브러리 설치
  - libGL, libEGL, libxkbcommon 등
- ✅ pytest 설정 (qt_api, markers)
- ✅ GUI 테스트 17개 작성 및 모두 통과
- ✅ offscreen 모드로 headless 환경에서 실행 성공

**발견한 문제점**:
1. `pytest_plugins = ["pytest_qt"]` 사용 시 ModuleNotFoundError 발생
   - 해결: pytest-qt는 자동으로 로드되므로 제거
2. `qtbot.addWidget()` 후에도 `isVisible()` False
   - 해결: `window.show()` 명시적 호출 필요
3. 여러 시스템 라이브러리 누락
   - 해결: libGL, libEGL, libxkbcommon 등 설치

**주요 결정사항**:
- QT_QPA_PLATFORM=offscreen으로 실행
- GUI 테스트에 `@pytest.mark.gui` 마커 추가
- 모든 테스트에서 `window.show()` 명시적 호출

**테스트 결과**:
- ✅ **17/17 테스트 통과** (100%)
- ✅ devcontainer에서 GUI 테스트 실행 가능
- ✅ CI/CD 통합 가능

**다음 단계**:
- GitHub Actions에서 GUI 테스트 실행 (선택사항)
- 더 많은 GUI 인터랙션 테스트 추가 (드로잉, 네트워크 등)

---

> **다음 Claude Code에게**:
> - pytest-qt 설정은 이 문서 참고
> - 반드시 시스템 라이브러리 설치 필요 (libGL, libEGL, libxkbcommon 등)
> - 테스트 실행 시 `QT_QPA_PLATFORM=offscreen` 환경 변수 필수
> - `qtbot.addWidget()` 후 반드시 `window.show()` 호출
> - `pytest_plugins`는 사용하지 말 것 (자동 로드됨)
