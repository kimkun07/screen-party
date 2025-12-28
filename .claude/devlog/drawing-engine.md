# Task: Drawing Engine (실시간 드로잉 엔진)

## 개요

실시간 드로잉 및 Spline 변환 시스템

## 목표

- [ ] 마우스 입력 캡처 (게스트)
- [ ] Spline 보간으로 부드러운 곡선 생성
- [ ] 실시간 서버 전송 (배치 처리)
- [ ] 드로잉 렌더링 (모든 클라이언트)
- [ ] 선 데이터 관리 (추가/업데이트/삭제)
- [ ] 유닛 테스트 작성

## 상세 요구사항

### 마우스 입력 캡처
- 마우스 버튼 down: 선 시작
- 마우스 move: 점 추가
- 마우스 버튼 up: 선 종료

```python
class DrawingCanvas(QWidget):
    def mousePressEvent(self, event: QMouseEvent):
        """선 시작"""

    def mouseMoveEvent(self, event: QMouseEvent):
        """점 추가"""

    def mouseReleaseEvent(self, event: QMouseEvent):
        """선 종료"""
```

### Spline 보간
- scipy.interpolate.make_interp_spline 사용
- 입력: 원시 마우스 포인트 (N개)
- 출력: 부드러운 Spline 포인트 (M개, M > N)

```python
from scipy.interpolate import make_interp_spline
import numpy as np

def smooth_points(points: List[QPointF], num_samples: int = 100) -> List[QPointF]:
    """Spline 보간으로 부드러운 곡선 생성"""
    if len(points) < 3:
        return points  # 3개 미만이면 보간 불가

    x = np.array([p.x() for p in points])
    y = np.array([p.y() for p in points])
    t = np.linspace(0, 1, len(points))

    # Cubic spline
    spline_x = make_interp_spline(t, x, k=3)
    spline_y = make_interp_spline(t, y, k=3)

    # 샘플링
    t_new = np.linspace(0, 1, num_samples)
    x_new = spline_x(t_new)
    y_new = spline_y(t_new)

    return [QPointF(x, y) for x, y in zip(x_new, y_new)]
```

### 배치 전송
- 마우스 이벤트마다 전송하지 않고 일정 주기로 배치 전송 (50ms마다)
- 네트워크 부하 감소
- QTimer 사용

### 드로잉 렌더링
- QPainter로 곡선 그리기
- QPainterPath로 부드러운 곡선 표현
- 선 두께: 3px
- 안티앨리어싱 활성화

```python
def paintEvent(self, event: QPaintEvent):
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    for line in self.lines.values():
        pen = QPen(line.color, 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        path = QPainterPath()
        if line.points:
            path.moveTo(line.points[0])
            for point in line.points[1:]:
                path.lineTo(point)

        painter.drawPath(path)
```

## 기술 결정

### 배치 전송 주기
- 50ms (초당 20회)
- 너무 빠르면 네트워크 부하, 너무 느리면 끊김 현상
- 실험적으로 조정 가능

### Spline 샘플링 수
- 100개 포인트로 충분히 부드러움
- 성능과 품질의 균형

## TODO

- [ ] DrawingCanvas 클래스 구현 (drawing/canvas.py)
- [ ] Spline 보간 함수 구현 (drawing/spline.py)
- [ ] 배치 전송 로직 (타이머)
- [ ] 드로잉 렌더링 (QPainter)
- [ ] 선 데이터 관리 (dict로 line_id → Line)
- [ ] 유닛 테스트 작성 (test_drawing.py, test_spline.py)

## 클로드 코드 일기

_이 섹션은 작업 진행 시 업데이트됩니다._
