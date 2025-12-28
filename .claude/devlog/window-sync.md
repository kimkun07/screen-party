# Task: Window Sync (창 관리 동기화)

## 개요

호스트가 게임 창을 최소화/복원하면 오버레이도 자동으로 숨김/표시

## 목표

- [ ] 게임 창 상태 감지 (최소화, 복원, 이동, 크기 변경)
- [ ] 오버레이 창 동기화
- [ ] 주기적 체크 (타이머)
- [ ] 유닛 테스트 작성

## 상세 요구사항

### 게임 창 상태 감지
- Windows: `IsIconic()`, `GetWindowRect()` API
- Linux: X11 속성 확인

```python
class WindowMonitor:
    def __init__(self, window_handle):
        self.window_handle = window_handle

    def is_minimized(self) -> bool:
        """창이 최소화되었는지 확인"""

    def get_rect(self) -> QRect:
        """창의 현재 위치/크기 반환"""

    def is_visible(self) -> bool:
        """창이 보이는지 확인"""
```

### 오버레이 동기화 로직
```python
def sync_overlay(self):
    """게임 창과 오버레이 동기화"""
    if not self.game_window:
        return

    # 최소화 상태 확인
    if self.window_monitor.is_minimized():
        self.overlay.hide()
        return
    else:
        self.overlay.show()

    # 위치/크기 동기화
    rect = self.window_monitor.get_rect()
    if rect != self.overlay.geometry():
        self.overlay.setGeometry(rect)
```

### 주기적 체크
- QTimer로 100ms마다 체크
- 너무 빠르면 CPU 부하, 너무 느리면 지연 발생
- 100ms가 적절한 균형

```python
self.sync_timer = QTimer()
self.sync_timer.timeout.connect(self.sync_overlay)
self.sync_timer.start(100)  # 100ms
```

### 창 이벤트 처리 (선택 사항)
- Windows: `SetWinEventHook()` 사용하여 창 이벤트 직접 수신
- 더 효율적이지만 구현 복잡도 증가
- 초기 버전은 타이머 방식으로 충분

## 기술 결정

### 타이머 vs 이벤트 후킹
- 초기 버전: 타이머 (100ms)
- 향후 개선: 이벤트 후킹 (성능 최적화)

### 크로스 플랫폼 지원
- Windows: `pywin32` 라이브러리
- Linux: `python-xlib` 라이브러리
- 플랫폼별 구현 분리

## TODO

- [ ] WindowMonitor 클래스 구현 (utils/window_monitor.py)
- [ ] 플랫폼별 구현 (Windows, Linux)
- [ ] 오버레이 동기화 로직
- [ ] QTimer 설정 (100ms)
- [ ] 게임 창이 닫히면 오버레이도 닫기
- [ ] 유닛 테스트 작성 (test_window_sync.py)

## 클로드 코드 일기

_이 섹션은 작업 진행 시 업데이트됩니다._
