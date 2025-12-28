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

_이 섹션은 작업 진행 시 업데이트됩니다._
