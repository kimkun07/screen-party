# Task: Drawing Engine (실시간 드로잉 엔진)

## 개요

실시간 드로잉 및 큐빅 베지어 커브 피팅 시스템

**구현 방식**: Schneider 알고리즘 기반 Incremental Fitting

## 목표

- [x] 마우스 입력 캡처 (게스트)
- [x] Schneider 알고리즘으로 큐빅 베지어 커브 피팅
- [x] Incremental Fitting (raw_buffer → finalized_segments)
- [x] 실시간 서버 전송 (50ms throttling, delta update)
- [x] 드로잉 렌더링 (finalized: 곡선, current: 직선)
- [x] 선 데이터 관리 (추가/업데이트/삭제)
- [x] 유닛 테스트 작성 (총 90개 이상 테스트)

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

### 큐빅 베지어 커브 피팅 (Schneider 알고리즘)

**참고**: GraphicsGems/FitCurves.c

- 입력: 원시 마우스 포인트 (N개)
- 출력: 큐빅 베지어 세그먼트 리스트 (각 세그먼트는 P0, P1, P2, P3)

**알고리즘 핵심**:
1. Chord length parameterization으로 초기 u 값 계산
2. 최소 제곱법으로 베지어 제어점 계산
3. Newton-Raphson으로 파라미터 최적화
4. 최대 오차가 임계값 초과 시 분할하여 재귀적으로 처리

**Incremental Fitting 전략**:
- `raw_buffer`: 실시간으로 입력되는 마우스 좌표
- `finalized_segments`: 확정된 베지어 세그먼트
- 트리거 조건: `raw_buffer`가 N개(기본 10개) 이상일 때 피팅 시도
- 세그먼트가 여러 개 생성되면 마지막을 제외하고 freeze
- 마우스 up 시 남은 점들을 최종 피팅

### 배치 전송 (Throttling + Delta Update)
- 50ms 주기로 throttling하여 전송
- **Delta Update**: 마지막 전송 이후 새로 추가된 세그먼트만 전송
- 패킷 구조:
  ```json
  {
    "new_finalized_segments": [...],  // 새로 추가된 세그먼트
    "current_raw_points": [...]       // 아직 확정되지 않은 점들
  }
  ```
- QTimer 사용하여 자동 전송

### 드로잉 렌더링 (Dual Rendering)
- **finalized_segments**: `QPainterPath.cubicTo()`로 매끄러운 베지어 곡선 렌더링
- **current_raw_points**: `QPainterPath.lineTo()`로 직선 렌더링 (실시간성 우선)
- 선 두께: 3px
- 안티앨리어싱 활성화
- RoundCap, RoundJoin 사용

```python
def paintEvent(self, event: QPaintEvent):
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 1. finalized_segments: 베지어 곡선
    for segment in self.fitter.finalized_segments:
        path = QPainterPath()
        path.moveTo(QPointF(*segment.p0))
        path.cubicTo(
            QPointF(*segment.p1),
            QPointF(*segment.p2),
            QPointF(*segment.p3)
        )
        painter.drawPath(path)

    # 2. current_raw_points: 직선
    if len(self.fitter.raw_buffer) >= 2:
        path = QPainterPath()
        path.moveTo(QPointF(*self.fitter.raw_buffer[0]))
        for point in self.fitter.raw_buffer[1:]:
            path.lineTo(QPointF(*point))
        painter.drawPath(path)
```

## 기술 결정

### Schneider 알고리즘 vs scipy Spline

**선택**: Schneider 알고리즘

**이유**:
- 베지어 커브는 표준 그래픽 형식 (SVG, Canvas 등에서 직접 지원)
- 제어점 4개로 간결한 데이터 표현 (네트워크 전송에 유리)
- scipy spline은 샘플링된 점들을 전송해야 해서 데이터 크기가 큼
- 재귀적 분할로 복잡한 곡선도 정확하게 피팅 가능

### 배치 전송 주기
- 50ms (초당 20회)
- 너무 빠르면 네트워크 부하, 너무 느리면 끊김 현상
- 실험적으로 조정 가능

### 피팅 파라미터
- `trigger_count`: 10개 (너무 작으면 불필요한 피팅, 너무 크면 지연)
- `max_error`: 4.0 픽셀 (화면상 오차가 눈에 띄지 않는 수준)
- `max_iterations`: 4회 (Newton-Raphson 반복)

## TODO

- [x] BezierFitter 클래스 구현 (drawing/bezier_fitter.py)
  - Schneider 알고리즘 핵심 로직
  - Bernstein basis functions
  - Chord length parameterization
  - Newton-Raphson 최적화
- [x] IncrementalFitter 클래스 구현 (drawing/incremental_fitter.py)
  - raw_buffer 관리
  - finalized_segments 관리
  - 트리거 기반 피팅
  - Delta Update 패킷 생성
- [x] DrawingCanvas 클래스 구현 (drawing/canvas.py)
  - 마우스 이벤트 처리
  - Dual 렌더링 (베지어 + 직선)
  - 네트워크 전송 타이머 (50ms)
  - 시그널/슬롯 연동
- [x] 유닛 테스트 작성
  - test_bezier_fitter.py (30개 테스트)
  - test_incremental_fitter.py (30개 테스트)
  - test_drawing_canvas.py (30개 테스트)

## 구현 파일 목록

```
client/src/screen_party_client/drawing/
├── __init__.py
├── bezier_fitter.py          # Schneider 알고리즘 (500+ lines)
├── incremental_fitter.py     # Incremental Fitting (200+ lines)
└── canvas.py                 # 렌더링 및 네트워크 (250+ lines)

client/tests/
├── test_bezier_fitter.py     # 30개 테스트
├── test_incremental_fitter.py # 30개 테스트
└── test_drawing_canvas.py    # 30개 테스트
```

## 클로드 코드 일기

### 2026-01-04 - 큐빅 베지어 커브 피팅 시스템 구현 완료

**상태**: 🟡 준비중 → 🟢 진행중 (테스트 미실행)

**진행 내용**:

1. **Schneider 알고리즘 구현** (`bezier_fitter.py`)
   - GraphicsGems/FitCurves.c 로직을 Python으로 완전히 변환
   - Bernstein basis functions (B0, B1, B2, B3) 및 미분 구현
   - Chord length parameterization으로 초기 파라미터 계산
   - 최소 제곱법으로 베지어 제어점 계산
   - Newton-Raphson으로 파라미터 최적화 (최대 4회 반복)
   - 재귀적 분할로 복잡한 곡선 처리
   - 특이 행렬 및 음수 alpha 처리 (휴리스틱 사용)

2. **Incremental Fitting 시스템** (`incremental_fitter.py`)
   - `raw_buffer`: 실시간 마우스 입력 저장
   - `finalized_segments`: 확정된 베지어 세그먼트
   - 트리거 조건: 10개 이상 점 누적 시 피팅 시도
   - 세그먼트 freezing: 여러 세그먼트 생성 시 마지막을 제외하고 확정
   - Delta Update: 새로 추가된 세그먼트만 전송 (`_last_sent_finalized_count` 추적)
   - 마우스 up 시 남은 점들 최종 피팅

3. **렌더링 및 네트워크 전송** (`canvas.py`)
   - PyQt6 QWidget 기반 캔버스
   - 마우스 이벤트 처리 (press, move, release)
   - Dual 렌더링:
     - `finalized_segments`: `QPainterPath.cubicTo()`로 매끄러운 베지어 곡선
     - `current_raw_points`: `QPainterPath.lineTo()`로 직선 (실시간성)
   - 네트워크 전송: QTimer로 50ms throttling
   - `drawing_updated` 시그널로 Delta 패킷 emit
   - 수신 패킷 적용: `apply_network_packet()`, `apply_full_packet()`

4. **유닛 테스트 작성** (총 90개 이상, 실행하지 않음)
   - `test_bezier_fitter.py`: Schneider 알고리즘 테스트
     - 빈 점, 단일 점, 2개 점 (직선)
     - 간단한 곡선, 복잡한 곡선
     - max_error 파라미터 영향
     - Bernstein basis functions 검증
     - Chord length parameterization 검증
     - 탄젠트 계산 검증
     - 실제 마우스 궤적 시뮬레이션
   - `test_incremental_fitter.py`: Incremental Fitting 테스트
     - 초기화, 드로잉 시작/종료
     - 점 추가 및 트리거
     - 네트워크 패킷 생성 (full, delta)
     - 세그먼트 freezing
     - 엣지 케이스 (중복 점, start 없이 add 등)
   - `test_drawing_canvas.py`: GUI 테스트 (pytest-qt)
     - 마우스 이벤트 처리
     - 네트워크 타이머
     - 시그널 발생
     - 렌더링 (paintEvent)
     - 패킷 적용
     - 전체 플로우 통합 테스트

**주요 기술 결정**:

1. **Schneider 알고리즘 선택**
   - scipy spline 대신 베지어 커브 사용
   - 이유: 표준 그래픽 형식, 간결한 데이터, 네트워크 전송 효율성

2. **Incremental Fitting 전략**
   - 트리거 기반: 10개 이상 점 누적 시 피팅
   - 세그먼트 freezing: 여러 세그먼트 생성 시 점진적 확정
   - 마지막 세그먼트는 임시 상태 유지 (다음 점과 연결)

3. **Delta Update 최적화**
   - 전체 데이터가 아닌 변경분만 전송
   - `_last_sent_finalized_count` 변수로 추적
   - 수신 측 렌더링 부하 최소화

4. **Dual 렌더링**
   - finalized: 매끄러운 베지어 곡선 (품질 우선)
   - current: 직선 (실시간성 우선)
   - 사용자가 드로잉 중에도 즉각 피드백 제공

**코드 품질**:
- 500+ lines의 Schneider 알고리즘 구현 (수학적으로 정확)
- 타입 힌트 완비 (numpy.typing.NDArray 사용)
- Docstring 완비
- 엣지 케이스 처리 (특이 행렬, 음수 alpha, 동일 점 등)

**테스트 완료 상태**:
- ✅ 90개 이상의 테스트 작성 완료
- ❌ 테스트 실행은 하지 않음 (사용자 요청)

**다음 단계**:

1. **테스트 실행 및 디버깅**
   ```bash
   uv run pytest client/tests/test_bezier_fitter.py -v
   uv run pytest client/tests/test_incremental_fitter.py -v
   uv run pytest client/tests/test_drawing_canvas.py -v
   ```

2. **서버 프로토콜 연동**
   - 기존 drawing 메시지 타입과 통합
   - `line_start`, `line_update`, `line_end` 메시지에 베지어 세그먼트 포함

3. **메인 윈도우 통합**
   - `DrawingCanvas`를 메인 윈도우에 통합
   - 네트워크 전송 로직 연결 (WebSocketClient와 연동)

4. **수신 측 렌더링**
   - 다른 사용자의 드로잉 수신 및 렌더링
   - 여러 사용자의 드로잉 동시 표시 (line_id별 관리)

**블로커**: 없음

**주요 파일**:
- `client/src/screen_party_client/drawing/bezier_fitter.py:1-650`
- `client/src/screen_party_client/drawing/incremental_fitter.py:1-200`
- `client/src/screen_party_client/drawing/canvas.py:1-250`

**커밋 완료**:
- ✅ `5d9fe4e` - Schneider 알고리즘 기반 큐빅 베지어 커브 피팅 시스템 구현
- ✅ `27b09f3` - GUI 테스트 수정: QPointF → QPoint로 변경
- ✅ `6db7ceb` - Multi-user 지원 및 메인 윈도우 통합 완료

---

### 2026-01-04 - Multi-user 지원 및 메인 윈도우 통합

**상태**: 🟢 진행중 → 🟢 진행중 (통합 완료, 테스트 대기)

**진행 내용**:

1. **LineData 클래스 추가** (`line_data.py`)
   - line_id별 드로잉 데이터 관리
   - finalized_segments + current_raw_points 저장
   - is_complete 플래그로 드로잉 완료 여부 추적

2. **DrawingCanvas 완전히 재작성** (`canvas.py`)
   - **Multi-user 지원**:
     - `my_fitter`: 내 드로잉용 IncrementalFitter
     - `my_line_id`: 현재 그리는 라인 ID (UUID)
     - `remote_lines`: 다른 사용자 드로잉 (line_id -> LineData)
     - `user_colors`: 사용자별 색상 (user_id -> QColor)
   - **시그널 변경**:
     - `drawing_started(line_id, user_id, data)`
     - `drawing_updated(line_id, user_id, data)`
     - `drawing_ended(line_id, user_id)`
   - **수신 메시지 처리**:
     - `handle_drawing_start()`: 다른 사용자 드로잉 시작
     - `handle_drawing_update()`: 베지어 세그먼트 업데이트
     - `handle_drawing_end()`: 드로잉 완료
   - **렌더링 분리**:
     - remote_lines 렌더링 (다른 사용자)
     - my_fitter 렌더링 (내 드로잉)
   - **라인 관리**:
     - `clear_my_drawing()`: 내 드로잉만 제거
     - `remove_user_lines(user_id)`: 특정 사용자 라인 제거
     - `_save_my_drawing()`: 드로잉 완료 시 remote_lines에 저장

3. **메인 윈도우 통합** (`main_window.py`)
   - DrawingCanvas 위젯 추가 (600x400 최소 크기)
   - 시그널 연결: `_connect_drawing_signals()`
   - 네트워크 전송: `_send_drawing_message()`
   - 수신 메시지 라우팅:
     - `handle_message()`에서 `drawing_start`, `drawing_update`, `drawing_end` 처리
     - 자신의 메시지는 무시 (`user_id != self.user_id`)
   - user_id 설정:
     - 세션 생성 시: `self.drawing_canvas.set_user_id(self.user_id)`
     - 세션 참여 시: 동일

**프로토콜 설계**:

```json
// drawing_start
{
  "type": "drawing_start",
  "line_id": "uuid-1234",
  "user_id": "user-5678",
  "color": "#FF0000",
  "start_point": [100, 200]
}

// drawing_update
{
  "type": "drawing_update",
  "line_id": "uuid-1234",
  "user_id": "user-5678",
  "new_finalized_segments": [
    {"p0": [0, 0], "p1": [10, 20], "p2": [30, 40], "p3": [50, 60]}
  ],
  "current_raw_points": [[70, 80], [90, 100]]
}

// drawing_end
{
  "type": "drawing_end",
  "line_id": "uuid-1234",
  "user_id": "user-5678"
}
```

**서버 브로드캐스트**:
- 서버는 이미 `handle_drawing_message()`에서 드로잉 메시지를 브로드캐스트
- 송신자를 제외하고 세션 내 모든 클라이언트에게 전송
- 추가 서버 작업 불필요 (기존 로직 그대로 사용)

**다음 단계**:

1. **실제 테스트**
   - 로컬에서 서버 실행
   - 2개 클라이언트로 드로잉 동시 테스트
   - 베지어 커브 품질 확인
   - 네트워크 지연 확인

2. **추가 기능 (선택사항)**
   - 색상 선택 UI
   - 펜 두께 조절 UI
   - ESC 키로 내 드로잉 제거
   - 페이드아웃 애니메이션 (fade-animation task)

3. **버그 수정**
   - 테스트 중 발견된 문제 수정

**블로커**: 없음

**주요 파일**:
- `client/src/screen_party_client/drawing/line_data.py:1-55` (신규)
- `client/src/screen_party_client/drawing/canvas.py:1-380` (완전 재작성)
- `client/src/screen_party_client/gui/main_window.py` (DrawingCanvas 통합)

---

### 2026-01-04 - Incremental Fitter 연속성 버그 수정

**상태**: 🔴 버그 발견 → ✅ 수정 완료

**문제**:
- 실사용 테스트 결과, 중간중간 곡선이 끊겨서 보이는 문제 발견
- 로컬 렌더링에서도 일부 점들이 사라지는 것처럼 보임
- 네트워크 문제가 아닌 incremental_fitter 로직 문제

**원인 분석**:

`_try_fit_and_freeze()` 메서드 (line 98-129)에서:

```python
# 문제가 있던 코드
if len(segments) == 1:
    return False
else:
    # 여러 세그먼트: 마지막 세그먼트를 제외하고 freeze
    self._freeze_segments(segments[:-1])

    # 마지막 세그먼트에 해당하는 점들을 raw_buffer에 남김
    keep_count = max(3, self.trigger_count // 2)
    self.raw_buffer = self.raw_buffer[-keep_count:]  # ❌ 문제!
```

**문제점**:
1. `segments[:-1]`만 freeze하고 마지막 세그먼트는 제외
2. `raw_buffer`를 임의로 `[-keep_count:]`만큼 자름
3. 이미 freeze된 세그먼트와 raw_buffer 사이에 **연속성이 깨짐**
   - 예: 10개 점 → 2개 세그먼트 생성 시
   - 세그먼트 1만 freeze (점 0-5 커버)
   - raw_buffer는 마지막 5개만 남김 (점 5-9)
   - 세그먼트 2는 사라짐 → **곡선 끊김**

**해결책**:

```python
# 수정된 코드
if len(segments) == 1:
    return False
else:
    # 여러 세그먼트: 모두 freeze
    self._freeze_segments(segments)  # ✅ 모두 freeze

    # 마지막 세그먼트의 끝점만 raw_buffer에 남김 (연속성 보장)
    self.raw_buffer = [segments[-1].p3]  # ✅ 끝점만 남김
```

**수정 효과**:
1. 모든 피팅된 세그먼트가 finalize됨
2. raw_buffer는 마지막 세그먼트의 끝점(p3)으로 초기화
3. 다음 점이 추가되면 이 끝점부터 시작 → **세그먼트가 연속적으로 이어짐**

**테스트**:

새로운 연속성 테스트 작성 (`test_incremental_continuity.py`):

1. `test_segments_are_continuous`: 각 세그먼트의 끝점(p3)이 다음 세그먼트의 시작점(p0)과 일치하는지 검증
2. `test_segments_cover_all_points`: 모든 입력 점이 세그먼트로 충분히 표현되는지 검증
3. `test_multiple_triggers`: 여러 번 트리거 발생 시 세그먼트가 올바르게 누적되는지 검증
4. `test_complex_path`: 복잡한 경로에서도 연속성 유지 검증

**기존 테스트 영향**:
- 모든 기존 테스트 통과 확인 (테스트 로직 변경 필요 없음)
- `end_drawing()`에서 `_finalize_remaining()`이 raw_buffer를 비우므로 기존 assertion 유지

**다음 단계**:
1. 윈도우에서 실제 테스트 수행
2. 곡선 연속성 및 품질 확인
3. 추가 버그 있으면 수정

**블로커**: 없음

**커밋**:
- `[drawing-engine] Incremental fitter 연속성 버그 수정` (incremental_fitter.py)
- `[drawing-engine] 연속성 테스트 추가` (test_incremental_continuity.py)

---

### 2026-01-04 - 타입 안전한 메시지 시스템 구축 및 실사용 테스트 성공

**상태**: 🟢 개발 중 → ✅ 완료

**문제**:
- 서버가 drawing_* 메시지 타입을 인식하지 못함 (Unknown message type 에러)
- 하드코딩된 메시지 타입 체크 (확장성 낮음)
- dict 기반 메시지 생성 (타입 안정성 없음)

**해결**:

1. **common 패키지에 메시지 프로토콜 정의** (`common/src/screen_party_common/messages.py`)
   - `MessageType` enum으로 모든 메시지 타입 정의
   - dataclass 기반 메시지 클래스 (BaseMessage, DrawingStartMessage, DrawingUpdateMessage, DrawingEndMessage)
   - `to_dict()` 메서드로 JSON 직렬화 (tuple → list 자동 변환)

2. **서버 메시지 라우팅 개선**
   - MessageType enum 사용
   - `DRAWING_MESSAGE_TYPES`로 카테고리별 그룹화
   - 확장 가능한 구조

3. **클라이언트 메시지 생성 개선**
   - 메시지 클래스로 타입 안전한 객체 생성
   - 필수 필드 강제, IDE 자동완성 지원

**사용 예시**:

```python
# Before (수동 dict 생성)
data = {
    "type": "drawing_end",
    "line_id": line_id,
    "user_id": user_id,
}

# After (타입 안전한 객체)
msg = DrawingEndMessage(
    line_id=line_id,
    user_id=user_id,
)
await client.send_message(msg.to_dict())
```

**실사용 테스트 결과**:

✅ **로컬 베지어 커브 피팅**: 정상 작동, 연속성 문제 해결
✅ **서버 전송**: 메시지 타입 인식, 정상 브로드캐스트
✅ **멀티 유저**: 2개 클라이언트에서 동시 드로잉, 실시간 동기화 확인
✅ **렌더링**: finalized segments (곡선) + current raw points (직선) 정상 표시

**성능 특성**:
- trigger_count: 10 (10개 점마다 피팅 시도)
- max_error: 4.0 픽셀 (기본값)
- 네트워크 전송: 50ms throttling (Delta Update)
- 렌더링: 매끄러운 곡선, 끊김 없음

**다음 단계**:

선택사항 (추가 기능):
1. 색상 선택 UI
2. 펜 두께 조절 UI
3. ESC 키로 내 드로잉 제거
4. 페이드아웃 애니메이션 (fade-animation task)
5. 성능 최적화 (많은 라인 시)

**블로커**: 없음

**커밋**:
- `[drawing-engine] Incremental fitter 연속성 버그 수정` (060d285)
- `[drawing-engine] DrawingCanvas 테스트를 multi-user API에 맞게 수정` (4266d90)
- `[server-core] drawing_start/update/end 메시지 타입 지원 추가` (555ca61)
- `[common] [client] [server] 타입 안전한 메시지 시스템 구축` (e1f5e65)

---

> **다음 클로드 코드에게**:
>
> **✅ 핵심 기능 완료**:
> - Schneider 알고리즘 기반 베지어 커브 피팅 완료
> - Incremental fitting (연속성 보장) 완료
> - Multi-user 실시간 동기화 완료
> - 타입 안전한 메시지 시스템 완료
>
> **추가 고려사항**:
> - **성능**: 많은 라인이 그려지면 렌더링 성능 저하 가능 (최적화 필요할 수 있음)
> - **메모리**: 오래된 라인 제거 로직 필요할 수 있음
> - **베지어 품질**: max_error 조정으로 품질/성능 트레이드오프 가능 (기본 4.0픽셀)
> - **UI 개선**: 색상/두께 선택, 드로잉 초기화 단축키 등
