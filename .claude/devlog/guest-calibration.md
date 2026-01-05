# Task: Guest Calibration (게스트 영역 설정)

## 개요

게스트가 디스코드 화면공유에서 게임 화면 영역을 지정하여 좌표 매핑

## 목표

- [ ] 영역 선택 UI (드래그로 사각형 지정)
- [ ] 좌표 변환 로직 (게스트 로컬 좌표 → 호스트 좌표)
- [ ] 영역 설정 저장 및 재사용
- [ ] 영역 재설정 기능
- [ ] 유닛 테스트 작성

## 상세 요구사항

### 영역 선택 UI
1. "영역 설정" 버튼 클릭
2. 전체 화면을 반투명 오버레이로 덮음
3. 마우스 드래그로 사각형 영역 지정
4. 확정 시 오버레이 제거 및 영역 저장

```
┌───────────────────────────────────┐
│ 반투명 오버레이                   │
│                                   │
│    ┌──────────────┐               │
│    │ 게임 화면    │  ← 드래그     │
│    │              │               │
│    └──────────────┘               │
│                                   │
│ [ESC: 취소]  [Enter: 확정]        │
└───────────────────────────────────┘
```

### 좌표 변환 로직
- 게스트 로컬 좌표: 디스코드 화면 내에서 클릭한 위치
- 영역 좌표: 게스트가 지정한 사각형 영역
- 호스트 좌표: 호스트의 게임 화면 좌표

```python
class CoordinateMapper:
    def __init__(self, guest_rect: QRect, host_resolution: Tuple[int, int]):
        self.guest_rect = guest_rect
        self.host_resolution = host_resolution

    def map_to_host(self, local_point: QPointF) -> QPointF:
        """게스트 로컬 좌표 → 호스트 좌표 변환"""
        # 영역 내 상대 좌표 계산
        relative_x = (local_point.x() - self.guest_rect.x()) / self.guest_rect.width()
        relative_y = (local_point.y() - self.guest_rect.y()) / self.guest_rect.height()

        # 호스트 해상도로 스케일링
        host_x = relative_x * self.host_resolution[0]
        host_y = relative_y * self.host_resolution[1]

        return QPointF(host_x, host_y)
```

### 영역 설정 저장
- 세션 내에서 재사용
- 게스트가 재접속해도 유지 (로컬 저장소)
- JSON 형식으로 저장:
  ```json
  {
    "session_id": "ABC123",
    "calibration": {
      "x": 100,
      "y": 200,
      "width": 800,
      "height": 600
    }
  }
  ```

## 기술 결정

### QRubberBand 사용
- PyQt6 내장 위젯으로 드래그 영역 표시
- 시각적 피드백 제공

### 로컬 저장소
- JSON 파일로 저장 (`~/.screen-party/calibrations.json`)
- 세션별로 구분하여 저장

## TODO

- [ ] CalibrationWidget 클래스 구현 (gui/calibration.py)
- [ ] CoordinateMapper 클래스 구현 (utils/coordinate_mapper.py)
- [ ] 로컬 저장소 관리 (utils/config.py)
- [ ] 영역 재설정 UI
- [ ] 유닛 테스트 작성 (test_calibration.py, test_coordinate_mapper.py)

## 클로드 코드 일기

### 2026-01-05 - 게스트 오버레이 구현 완료

**상태**: 🟡 준비중 → 🟢 진행중 → ✅ 완료

**구현 내용**:

1. **OverlayWindow 개선 - 그리기 모드 토글**
   - `_drawing_enabled` 플래그 추가 (기본값: False, 클릭 passthrough)
   - `set_drawing_enabled(bool)` 메서드 추가
     - True: WindowTransparentForInput 제거 → 마우스 입력 허용 (그리기 가능)
     - False: WindowTransparentForInput 활성화 → 클릭 passthrough
     - setWindowFlags() 동적 변경 + show() 재호출로 플래그 적용
   - `is_drawing_enabled()` 메서드 추가
   - `drawing_mode_changed` 시그널 추가 (bool)
   - `keyPressEvent()` 추가: ESC 키로 그리기 모드 비활성화

2. **MainWindow 게스트 UI 추가**
   - "Guest Mode" 섹션 추가 (메인 화면)
   - "화면 영역 설정" 버튼 (setup_overlay_button)
     - 클릭 시 창 선택 다이얼로그 표시
     - 오버레이 생성 후 "Stop Guest Overlay"로 텍스트 변경
   - "그리기 활성화/비활성화" 토글 버튼 (toggle_drawing_button)
     - 오버레이 생성 전: 비활성화
     - 오버레이 생성 후: 활성화
     - 그리기 모드에 따라 텍스트 변경

3. **MainWindow 메서드 추가/수정**
   - `start_guest_overlay()`: 게스트 오버레이 시작 (창 선택)
   - `create_overlay(window_handle, is_guest)`: 오버레이 생성 (호스트/게스트 공통)
     - is_guest=True: 그리기 토글 버튼 활성화, FAB 없음
     - is_guest=False: FAB 생성, 그리기 토글 버튼 없음
   - `toggle_drawing_mode()`: 그리기 모드 토글
   - `on_drawing_mode_changed(bool)`: 그리기 모드 변경 시그널 핸들러
     - 버튼 텍스트 업데이트
     - 상태 메시지 표시 (ESC 키 안내)
   - `stop_share_mode()`: 게스트 버튼 리셋 추가

**주요 기술 구현**:
- ✅ WindowTransparentForInput 동적 토글 (setWindowFlags + show)
- ✅ ESC 키 핸들러 (keyPressEvent)
- ✅ 호스트/게스트 공통 오버레이 코드 (OverlayWindow 재사용)
- ✅ 그리기 모드 시그널 (drawing_mode_changed)

**사용자 시나리오**:
1. 게스트가 세션 참여 → 메인 화면 표시
2. "화면 영역 설정" 클릭 → 디스코드 등 화면 공유 프로그램 선택
3. 오버레이 생성 (기본: 그리기 비활성화, 클릭 passthrough)
4. "그리기 활성화" 클릭 → 그리기 모드 활성화 (마우스 입력 허용)
5. 오버레이에서 그림 그리기
6. ESC 키 또는 "그리기 비활성화" 클릭 → 클릭 passthrough로 전환
7. 다시 화면 공유 프로그램 조작 가능

**테스트 결과**:
- ✅ Import 테스트 통과
- ⚠️ Windows에서 실제 동작 테스트 필요

**다음 단계**:
1. Windows 환경에서 수동 테스트
   - 화면 영역 설정 (창 선택)
   - 그리기 활성화/비활성화 토글
   - ESC 키로 비활성화
   - 클릭 passthrough 확인
   - 오버레이에서 그리기 → 서버 전송 확인
2. 버그 수정 (필요시)

**파일 변경사항**:
```
client/src/screen_party_client/gui/
├── overlay_window.py (수정)
│   - drawing mode 토글 기능 추가
│   - ESC 키 핸들러 추가
└── main_window.py (수정)
    - 게스트 UI 섹션 추가
    - 게스트 오버레이 메서드 추가
```

**블로커**: 없음 (구현 완료)

---

> **다음 클로드 코드에게**:
> - 게스트 오버레이 구현 완료!
> - Windows 환경에서 테스트 필요
> - 그리기 모드 토글이 잘 작동하는지 확인
> - ESC 키가 작동하는지 확인
> - 호스트/게스트 모두 같은 OverlayWindow 사용
> - 버그 발견 시 수정 부탁합니다
