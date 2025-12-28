# Task: Fade Animation (페이드아웃 애니메이션)

## 개요

선이 그려진 후 2초 유지 → 1초 동안 페이드아웃하여 사라지는 애니메이션

## 목표

- [ ] 선 종료 시 타이머 시작
- [ ] 2초 대기 후 페이드아웃 시작
- [ ] 1초 동안 alpha 값 1.0 → 0.0으로 감소
- [ ] 완전히 투명해지면 선 삭제
- [ ] 유닛 테스트 작성

## 상세 요구사항

### 타임라인
```
0s          2s          3s
│───────────│───────────│
 그리는 중    유지       페이드아웃
             (alpha=1.0) (alpha: 1.0→0.0)
                                 └─ 삭제
```

### Line 데이터 구조 확장
```python
@dataclass
class Line:
    line_id: str
    user_id: str
    color: QColor
    points: List[QPointF]
    is_drawing: bool  # 그리는 중인지
    alpha: float  # 0.0 ~ 1.0
    end_time: Optional[datetime]  # 선이 종료된 시각
    fade_start_time: Optional[datetime]  # 페이드 시작 시각
```

### 애니메이션 로직
```python
class LineAnimator:
    def __init__(self, line: Line):
        self.line = line
        self.hold_duration = 2.0  # 초
        self.fade_duration = 1.0  # 초

    def update(self, current_time: datetime):
        """프레임마다 호출되어 alpha 값 업데이트"""
        if not self.line.end_time:
            return  # 아직 그리는 중

        elapsed = (current_time - self.line.end_time).total_seconds()

        if elapsed < self.hold_duration:
            # 유지 단계
            self.line.alpha = 1.0
        elif elapsed < self.hold_duration + self.fade_duration:
            # 페이드아웃 단계
            fade_progress = (elapsed - self.hold_duration) / self.fade_duration
            self.line.alpha = 1.0 - fade_progress
        else:
            # 완전히 사라짐
            self.line.alpha = 0.0
            return True  # 삭제 신호

        return False
```

### 렌더링 시 alpha 적용
```python
def paintEvent(self, event: QPaintEvent):
    painter = QPainter(self)

    for line in self.lines.values():
        color = QColor(line.color)
        color.setAlphaF(line.alpha)  # alpha 적용

        pen = QPen(color, 3)
        painter.setPen(pen)
        # ... 그리기
```

### QTimer로 주기적 업데이트
- 60 FPS로 업데이트 (16ms마다)
- 모든 선의 alpha 값 갱신
- alpha = 0.0인 선 삭제

## 기술 결정

### 유지 시간: 2초
- 너무 짧으면 빠르게 사라져서 정보 손실
- 너무 길면 화면이 지저분해짐
- 2초가 적절한 균형

### 페이드 시간: 1초
- 부드러운 전환 효과
- 사용자가 선이 사라지는 것을 인지할 수 있음

## TODO

- [ ] LineAnimator 클래스 구현 (drawing/animator.py)
- [ ] Line 데이터 구조 확장 (end_time, fade_start_time 추가)
- [ ] QTimer로 주기적 업데이트 (16ms)
- [ ] alpha 값 적용하여 렌더링
- [ ] alpha = 0.0인 선 자동 삭제
- [ ] 유닛 테스트 작성 (test_animator.py)

## 클로드 코드 일기

_이 섹션은 작업 진행 시 업데이트됩니다._
