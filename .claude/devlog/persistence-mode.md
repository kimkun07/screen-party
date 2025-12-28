# Task: Persistence Mode (장시간 그림 모드)

## 개요

선이 자동으로 사라지지 않고 화면에 유지되는 모드 (전략 브리핑용)

## 목표

- [ ] 장시간 모드 토글 UI
- [ ] 모드별 선 구분 (일반 vs 장시간)
- [ ] 장시간 모드 선은 페이드아웃 비활성화
- [ ] 수동 삭제 기능 (ESC 키)
- [ ] 유닛 테스트 작성

## 상세 요구사항

### UI
- 체크박스 또는 토글 버튼: "장시간 모드"
- 활성화 시 이후 그린 선은 자동으로 사라지지 않음
- 비활성화 시 이전처럼 페이드아웃 작동

```
┌─────────────────────────────┐
│ [ ] 장시간 모드 (Shift+P)  │
└─────────────────────────────┘
```

### Line 데이터 구조 확장
```python
@dataclass
class Line:
    # ... 기존 필드
    is_persistent: bool  # 장시간 모드 여부
```

### 페이드아웃 로직 수정
```python
def update(self, current_time: datetime):
    if self.line.is_persistent:
        # 장시간 모드 선은 페이드아웃 안 함
        self.line.alpha = 1.0
        return False

    # 기존 페이드아웃 로직
    # ...
```

### 수동 삭제 (ESC 키)
- ESC 키를 누르면 자신이 그린 선만 삭제
- 다른 사람이 그린 선은 유지
- 삭제 시 서버에 `line_remove` 메시지 전송

```python
def keyPressEvent(self, event: QKeyEvent):
    if event.key() == Qt.Key.Key_Escape:
        # 자신이 그린 선만 필터링
        my_lines = [
            line_id for line_id, line in self.lines.items()
            if line.user_id == self.my_user_id
        ]
        # 삭제
        for line_id in my_lines:
            self.remove_line(line_id)
            self.send_line_remove(line_id)
```

### 서버 메시지
```json
// 선 시작 메시지에 is_persistent 추가
{
  "type": "line_start",
  "line_id": "uuid-5678",
  "user_id": "uuid-1234",
  "color": "#FF0000",
  "is_persistent": true,  // 추가
  "start_point": {"x": 100, "y": 200}
}
```

## 기술 결정

### 모드 저장
- 세션 내에서 유지 (재접속 시 초기화)
- 필요시 로컬 저장소에 기본값 저장 가능

### 단축키
- Shift+P: 장시간 모드 토글
- ESC: 자신이 그린 선 모두 삭제

## TODO

- [ ] 장시간 모드 UI 추가 (체크박스)
- [ ] Line 데이터 구조에 is_persistent 필드 추가
- [ ] 페이드아웃 로직 수정 (is_persistent 체크)
- [ ] ESC 키 핸들러 구현
- [ ] 서버 메시지 포맷 업데이트
- [ ] 유닛 테스트 작성 (test_persistence.py)

## 클로드 코드 일기

_이 섹션은 작업 진행 시 업데이트됩니다._
