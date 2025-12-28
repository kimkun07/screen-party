# Task: Color System (색상 설정 시스템)

## 개요

각 게스트별로 펜 색상을 설정하여 누가 그린 선인지 구분

## 목표

- [ ] 색상 팔레트 UI
- [ ] 색상 변경 기능
- [ ] 색상 정보 서버 동기화
- [ ] 기존 선과 새 선의 색상 구분
- [ ] 유닛 테스트 작성

## 상세 요구사항

### 색상 팔레트
- 미리 정의된 8가지 색상 제공
- 색상 버튼 클릭으로 변경

```
┌─────────────────────────────┐
│ 펜 색상:                    │
│ [🔴] [🔵] [🟢] [🟡]       │
│ [🟣] [🟠] [⚪] [⚫]       │
└─────────────────────────────┘
```

### 기본 색상 팔레트
```python
DEFAULT_COLORS = [
    "#FF0000",  # Red
    "#0000FF",  # Blue
    "#00FF00",  # Green
    "#FFFF00",  # Yellow
    "#FF00FF",  # Magenta
    "#FF8000",  # Orange
    "#FFFFFF",  # White
    "#000000",  # Black
]
```

### 색상 변경 로직
- 색상 변경 시 이후 그린 선만 새 색상 적용
- 이미 그린 선은 기존 색상 유지
- 서버에 `color_change` 메시지 전송

```json
{
  "type": "color_change",
  "user_id": "uuid-1234",
  "color": "#FF0000"
}
```

### User 데이터 구조
```python
@dataclass
class User:
    user_id: str
    name: str
    color: str  # HEX 색상 코드
    is_host: bool
```

### 색상 저장
- 세션 내에서 유지
- 로컬 저장소에 기본 색상 저장 (`~/.screen-party/config.json`)
- 다음 세션에서 동일한 색상 사용

## 기술 결정

### 커스텀 RGB vs 팔레트
- 초기 버전은 팔레트만 제공
- 향후 커스텀 RGB 선택 기능 추가 가능 (QColorDialog)

### 색상 충돌
- 여러 게스트가 같은 색상 선택 가능 (제한 없음)
- 필요 시 자동 색상 할당 기능 추가 가능

## TODO

- [ ] 색상 팔레트 UI 구현 (gui/color_palette.py)
- [ ] User 데이터 구조에 color 필드 추가
- [ ] 색상 변경 핸들러
- [ ] 서버 메시지 포맷 업데이트 (color_change)
- [ ] 로컬 저장소에 기본 색상 저장/불러오기
- [ ] 유닛 테스트 작성 (test_color.py)

## 클로드 코드 일기

_이 섹션은 작업 진행 시 업데이트됩니다._
