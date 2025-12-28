# Task: Host Overlay (호스트 투명 오버레이)

## 개요

호스트가 게임 창 위에 투명 오버레이를 띄우는 기능

## 목표

- [ ] 실행 중인 창 목록 가져오기 (Windows/Linux)
- [ ] 창 선택 UI
- [ ] 투명 오버레이 창 생성
- [ ] 오버레이 위치/크기를 게임 창과 동기화
- [ ] 드로잉 렌더링 (다른 클라이언트가 그린 선 표시)
- [ ] 유닛 테스트 작성

## 상세 요구사항

### 창 목록 가져오기
- Windows: `pywin32` 라이브러리 사용
- Linux: `wmctrl` 또는 X11 라이브러리

```python
def get_window_list() -> List[WindowInfo]:
    """실행 중인 창 목록 반환"""
    # WindowInfo = namedtuple("WindowInfo", ["title", "handle", "rect"])
```

### 창 선택 UI
```
┌─────────────────────────────┐
│   게임 창 선택              │
├─────────────────────────────┤
│ [x] League of Legends       │
│ [ ] Steam                   │
│ [ ] Discord                 │
│                             │
│         [확인]              │
└─────────────────────────────┘
```

### 투명 오버레이 창
- Qt::FramelessWindowHint: 창 테두리 제거
- Qt::WindowStaysOnTopHint: 항상 최상위
- Qt::Tool: 작업 표시줄에 표시 안 함
- setAttribute(Qt.WA_TranslucentBackground): 투명 배경
- 마우스 이벤트 통과 (클릭이 아래 게임 창으로 전달)

```python
class OverlayWindow(QWidget):
    def __init__(self, game_window_rect: QRect):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(game_window_rect)
```

### 드로잉 렌더링
- QPainter로 곡선 그리기
- 페이드아웃 애니메이션 (alpha 값 조정)
- 선 데이터 구조:
  ```python
  @dataclass
  class Line:
      line_id: str
      user_id: str
      color: QColor
      points: List[QPointF]
      alpha: float  # 0.0 ~ 1.0
  ```

## 기술 결정

### 크로스 플랫폼 창 관리
- Windows: `pywin32` (`pip install pywin32`)
- Linux: `python-xlib` (`pip install python-xlib`)
- 플랫폼별 구현을 추상화 클래스로 분리

### 마우스 이벤트 통과
- Qt::WA_TransparentForMouseEvents 속성 사용
- 드로잉은 보이지만 클릭은 아래 게임 창으로 전달

## TODO

- [ ] WindowManager 클래스 구현 (utils/window_manager.py)
- [ ] 창 선택 다이얼로그 구현 (gui/window_selector.py)
- [ ] OverlayWindow 클래스 구현 (gui/overlay.py)
- [ ] 드로잉 렌더링 로직 (QPainter)
- [ ] 창 위치/크기 동기화 (타이머로 주기적 체크)
- [ ] 유닛 테스트 작성 (test_overlay.py)

## 클로드 코드 일기

_이 섹션은 작업 진행 시 업데이트됩니다._
