"""
드로잉 캔버스 및 렌더링 컴포넌트 (Multi-user 지원)

베지어 커브와 raw 점들을 렌더링하며, 네트워크 전송을 관리합니다.
여러 사용자의 드로잉을 line_id별로 관리합니다.
"""

from typing import Optional, Dict, Any, Tuple, Set, TYPE_CHECKING
import uuid
import time
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QPainterPath, QMouseEvent, QPaintEvent, QColor

from screen_party_common import MessageType, DrawingStartMessage, DrawingUpdateMessage, DrawingEndMessage
from .incremental_fitter import IncrementalFitter
from .bezier_fitter import BezierSegment
from .line_data import LineData

if TYPE_CHECKING:
    pass


def _get_default_pen_color() -> QColor:
    """기본 펜 색상 반환 (파스텔 핑크)"""
    return QColor(255, 182, 193)  # 첫 번째 프리셋 색상과 동일


class DrawingCanvas(QWidget):
    """
    Multi-user 드로잉 캔버스

    기능:
    - 마우스 입력 캡처 (자신의 드로잉)
    - 실시간 베지어 커브 피팅
    - 렌더링 (finalized: 곡선, current: 직선)
    - 네트워크 전송 (50ms throttling)
    - 다른 사용자의 드로잉 수신 및 렌더링
    """

    # 네트워크 전송 시그널 (line_id, user_id, packet)
    drawing_started = pyqtSignal(str, str, dict)  # line_id, user_id, start_data
    drawing_updated = pyqtSignal(str, str, dict)  # line_id, user_id, update_data
    drawing_ended = pyqtSignal(str, str)  # line_id, user_id

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        user_id: Optional[str] = None,
        pen_color: Optional[QColor] = None,
        pen_width: int = 3,
        pen_alpha: float = 1.0,
        trigger_count: int = 10,
        max_error: float = 4.0,
        fade_hold_duration: float = 2.0,
        fade_duration: float = 1.0,
        timeout_duration: float = 10.0,
    ):
        """
        Args:
            parent: 부모 위젯
            user_id: 현재 사용자 ID
            pen_color: 펜 색상
            pen_width: 펜 두께
            pen_alpha: 펜 초기 투명도 (0.0 ~ 1.0)
            trigger_count: 피팅 트리거 점 개수
            max_error: 베지어 피팅 최대 오차
            fade_hold_duration: 페이드아웃 전 유지 시간 (초)
            fade_duration: 페이드아웃 시간 (초)
            timeout_duration: 강제 삭제 타임아웃 (초)
        """
        super().__init__(parent)

        # 사용자 정보
        self.user_id = user_id or str(uuid.uuid4())
        self.pen_color = pen_color if pen_color is not None else _get_default_pen_color()
        self.pen_width = pen_width
        self.pen_alpha = pen_alpha

        # 자신의 드로잉
        self.my_fitter = IncrementalFitter(
            trigger_count=trigger_count,
            max_error=max_error,
        )
        self.my_line_id: Optional[str] = None

        # 다른 사용자의 드로잉 (line_id -> LineData)
        self.remote_lines: Dict[str, LineData] = {}

        # 사용자별 색상 (user_id -> QColor)
        self.user_colors: Dict[str, QColor] = {}
        self.user_colors[self.user_id] = pen_color

        # 사용자별 알파값 (user_id -> float, 0.0 ~ 1.0)
        self.user_alphas: Dict[str, float] = {}
        self.user_alphas[self.user_id] = pen_alpha

        # 페이드아웃 설정
        self.fade_hold_duration = fade_hold_duration
        self.fade_duration = fade_duration
        self.timeout_duration = timeout_duration

        # 삭제된 라인 추적 (타임아웃으로 삭제된 라인은 이후 이벤트 무시)
        self.deleted_line_ids: Set[str] = set()

        # 네트워크 전송 타이머 (50ms)
        self.network_timer = QTimer(self)
        self.network_timer.timeout.connect(self._send_network_update)
        self.network_interval = 50  # ms

        # 페이드아웃 애니메이션 타이머 (60fps, 16ms)
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._update_animations)
        self.animation_timer.start(16)  # ~60 FPS

        # 마우스 추적 활성화
        self.setMouseTracking(True)

        # 배경 투명
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_user_id(self, user_id: str):
        """사용자 ID 설정"""
        # 이전 user_id 제거 (중복 방지)
        old_user_id = self.user_id
        if old_user_id and old_user_id in self.user_colors:
            del self.user_colors[old_user_id]
        if old_user_id and old_user_id in self.user_alphas:
            del self.user_alphas[old_user_id]

        # 새로운 user_id 설정
        self.user_id = user_id
        if user_id not in self.user_colors:
            self.user_colors[user_id] = self.pen_color
        if user_id not in self.user_alphas:
            self.user_alphas[user_id] = self.pen_alpha

    def set_user_color(self, user_id: str, color: QColor):
        """사용자별 색상 설정"""
        self.user_colors[user_id] = color

    def set_user_alpha(self, user_id: str, alpha: float):
        """사용자별 알파값 설정"""
        self.user_alphas[user_id] = max(0.0, min(1.0, alpha))

    # === 좌표 변환 메서드 ===

    def _to_relative_point(self, x: float, y: float) -> Tuple[float, float]:
        """절대 좌표를 상대 좌표로 변환 (0.0 ~ 1.0)

        Args:
            x: 절대 X 좌표 (픽셀)
            y: 절대 Y 좌표 (픽셀)

        Returns:
            (rel_x, rel_y): 상대 좌표 (0.0 ~ 1.0)
        """
        width = self.width() or 1  # 0으로 나누기 방지
        height = self.height() or 1

        rel_x = x / width
        rel_y = y / height

        return (rel_x, rel_y)

    def _to_absolute_point(self, rel_x: float, rel_y: float) -> Tuple[float, float]:
        """상대 좌표를 절대 좌표로 변환

        Args:
            rel_x: 상대 X 좌표 (0.0 ~ 1.0)
            rel_y: 상대 Y 좌표 (0.0 ~ 1.0)

        Returns:
            (x, y): 절대 좌표 (픽셀)
        """
        width = self.width()
        height = self.height()

        x = rel_x * width
        y = rel_y * height

        return (x, y)

    def mousePressEvent(self, event: QMouseEvent):
        """마우스 눌림: 드로잉 시작"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            abs_point = (pos.x(), pos.y())

            # 새로운 line_id 생성
            self.my_line_id = str(uuid.uuid4())

            # 드로잉 시작 (내부적으로는 절대 좌표 사용)
            self.my_fitter.start_drawing(abs_point)

            # 네트워크 전송용 상대 좌표로 변환
            rel_start_point = self._to_relative_point(abs_point[0], abs_point[1])

            # 시작 이벤트 전송 (상대 좌표)
            msg = DrawingStartMessage(
                line_id=self.my_line_id,
                user_id=self.user_id,
                color=self.pen_color.name(),
                start_point=rel_start_point,
            )
            self.drawing_started.emit(self.my_line_id, self.user_id, msg.to_dict())

            # 네트워크 전송 타이머 시작
            self.network_timer.start(self.network_interval)

            self.update()  # 화면 갱신

    def mouseMoveEvent(self, event: QMouseEvent):
        """마우스 이동: 점 추가"""
        if self.my_fitter.is_drawing and self.my_line_id:
            pos = event.position()
            abs_point = (pos.x(), pos.y())

            # 내부적으로는 절대 좌표로 드로잉 (렌더링용)
            self.my_fitter.add_point(abs_point)
            self.update()  # 화면 갱신

    def mouseReleaseEvent(self, event: QMouseEvent):
        """마우스 떼기: 드로잉 종료"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.my_fitter.is_drawing and self.my_line_id:
                self.my_fitter.end_drawing()

                # 네트워크 전송 타이머 중지
                self.network_timer.stop()

                # 최종 업데이트 전송
                self._send_network_update()

                # 종료 이벤트 전송
                self.drawing_ended.emit(self.my_line_id, self.user_id)

                # 내 드로잉을 remote_lines에 추가 (렌더링 유지)
                self._save_my_drawing()

                # 초기화
                self.my_line_id = None

                self.update()  # 화면 갱신

    def paintEvent(self, event: QPaintEvent):
        """렌더링"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. 다른 사용자의 드로잉 렌더링
        for line_id, line_data in self.remote_lines.items():
            # 알파값 적용
            color = QColor(line_data.color)
            color.setAlphaF(line_data.alpha)

            pen = QPen(color, self.pen_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)

            # finalized_segments: 베지어 곡선
            for segment in line_data.finalized_segments:
                self._draw_bezier_segment(painter, segment)

            # current_raw_points: 직선 (완료되지 않은 경우)
            if not line_data.is_complete and len(line_data.current_raw_points) >= 2:
                self._draw_raw_points(painter, line_data.current_raw_points)

        # 2. 내 드로잉 렌더링
        if self.my_fitter.is_drawing or len(self.my_fitter.finalized_segments) > 0:
            pen = QPen(self.pen_color, self.pen_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)

            # finalized_segments: 베지어 곡선
            for segment in self.my_fitter.finalized_segments:
                self._draw_bezier_segment(painter, segment)

            # current_raw_points: 직선
            if len(self.my_fitter.raw_buffer) >= 2:
                self._draw_raw_points(painter, self.my_fitter.raw_buffer)

    def _draw_bezier_segment(self, painter: QPainter, segment: BezierSegment):
        """베지어 세그먼트를 매끄러운 곡선으로 렌더링"""
        path = QPainterPath()

        p0 = QPointF(*segment.p0)
        p1 = QPointF(*segment.p1)
        p2 = QPointF(*segment.p2)
        p3 = QPointF(*segment.p3)

        path.moveTo(p0)
        path.cubicTo(p1, p2, p3)

        painter.drawPath(path)

    def _draw_raw_points(self, painter: QPainter, points):
        """raw 점들을 직선으로 렌더링"""
        if len(points) < 2:
            return

        path = QPainterPath()
        path.moveTo(QPointF(*points[0]))

        for point in points[1:]:
            path.lineTo(QPointF(*point))

        painter.drawPath(path)

    def _send_network_update(self):
        """네트워크 업데이트 전송 (Delta Update) - 상대 좌표로 변환"""
        if not self.my_fitter.has_changes() or not self.my_line_id:
            return

        # Delta 패킷 생성 (절대 좌표)
        packet = self.my_fitter.get_delta_packet()

        # 상대 좌표로 변환
        width = self.width() or 1
        height = self.height() or 1

        # new_finalized_segments를 상대 좌표로 변환
        rel_segments = []
        for seg_dict in packet["new_finalized_segments"]:
            seg = BezierSegment.from_dict(seg_dict)
            rel_seg = seg.to_relative(width, height)
            rel_segments.append(rel_seg.to_dict())

        # current_raw_points를 상대 좌표로 변환
        rel_raw_points = [
            self._to_relative_point(x, y) for x, y in packet["current_raw_points"]
        ]

        # 메시지 생성 (상대 좌표)
        msg = DrawingUpdateMessage(
            line_id=self.my_line_id,
            user_id=self.user_id,
            new_finalized_segments=rel_segments,
            current_raw_points=rel_raw_points,
        )

        # 시그널 emit
        self.drawing_updated.emit(self.my_line_id, self.user_id, msg.to_dict())

    def _update_animations(self):
        """페이드아웃 애니메이션 업데이트 (60fps)"""
        current_time = time.time()
        lines_to_delete = []

        for line_id, line_data in self.remote_lines.items():
            # 1. 타임아웃 체크 (마지막 업데이트로부터 10초)
            time_since_last_update = current_time - line_data.last_update_time
            if time_since_last_update >= self.timeout_duration:
                # 타임아웃 - 강제 삭제
                lines_to_delete.append(line_id)
                self.deleted_line_ids.add(line_id)
                continue

            # 2. 페이드아웃 계산 (drawing_end 이후)
            if line_data.end_time is not None:
                elapsed_since_end = current_time - line_data.end_time

                if elapsed_since_end < self.fade_hold_duration:
                    # 유지 단계 (초기 alpha 유지)
                    line_data.alpha = line_data.initial_alpha
                elif elapsed_since_end < self.fade_hold_duration + self.fade_duration:
                    # 페이드아웃 단계 (초기 alpha → 0.0)
                    fade_progress = (elapsed_since_end - self.fade_hold_duration) / self.fade_duration
                    line_data.alpha = max(0.0, line_data.initial_alpha * (1.0 - fade_progress))
                else:
                    # 완전히 사라짐 - 삭제
                    line_data.alpha = 0.0
                    lines_to_delete.append(line_id)
                    self.deleted_line_ids.add(line_id)

        # 삭제할 라인 제거
        for line_id in lines_to_delete:
            del self.remote_lines[line_id]

        # 변경사항이 있으면 화면 갱신
        if lines_to_delete or any(
            line_data.alpha < 1.0 for line_data in self.remote_lines.values()
        ):
            self.update()

    def _save_my_drawing(self):
        """내 드로잉을 remote_lines에 저장 (렌더링 유지용)"""
        if not self.my_line_id:
            return

        # LineData 생성 (초기 alpha 값 적용)
        line_data = LineData(
            line_id=self.my_line_id,
            user_id=self.user_id,
            color=self.pen_color,
            finalized_segments=self.my_fitter.finalized_segments.copy(),
            current_raw_points=[],
            is_complete=True,
            alpha=self.pen_alpha,  # 초기 alpha 값 적용
            initial_alpha=self.pen_alpha,  # 초기 alpha 값 저장
        )

        # 페이드아웃 시작을 위해 end_time 설정
        line_data.finalize()

        self.remote_lines[self.my_line_id] = line_data

        # my_fitter 초기화
        self.my_fitter.clear()

    def clear_my_drawing(self):
        """내 드로잉만 초기화"""
        self.my_fitter.clear()
        self.my_line_id = None

        # remote_lines에서 내 라인만 제거
        my_lines = [lid for lid, ldata in self.remote_lines.items() if ldata.user_id == self.user_id]
        for line_id in my_lines:
            del self.remote_lines[line_id]

        self.update()

    def clear_all_drawings(self):
        """모든 드로잉 초기화"""
        self.my_fitter.clear()
        self.my_line_id = None
        self.remote_lines.clear()
        self.update()

    def set_pen_color(self, color: QColor):
        """펜 색상 변경 (신규 곡선에만 적용)"""
        self.pen_color = color
        self.user_colors[self.user_id] = color
        self.update()

    def set_pen_width(self, width: int):
        """펜 두께 변경"""
        self.pen_width = width
        self.update()

    def set_pen_alpha(self, alpha: float):
        """펜 초기 투명도 변경 (0.0 ~ 1.0, 신규 곡선에만 적용)"""
        self.pen_alpha = max(0.0, min(1.0, alpha))
        self.update()

    # === 수신 메시지 처리 ===

    def handle_drawing_start(self, line_id: str, user_id: str, data: Dict[str, Any]):
        """
        다른 사용자의 드로잉 시작 처리 (상대 좌표 수신)

        Args:
            line_id: 라인 ID
            user_id: 사용자 ID
            data: 시작 데이터 (color, start_point 등) - start_point는 상대 좌표
        """
        # 삭제된 라인 무시
        if line_id in self.deleted_line_ids:
            return

        # 색상 파싱
        color_str = data.get("color", "#FF0000")
        color = QColor(color_str)

        # 사용자별 알파값 가져오기 (없으면 1.0)
        user_alpha = self.user_alphas.get(user_id, 1.0)

        # 상대 좌표 start_point (참고용, LineData 생성에는 사용하지 않음)
        # start_point = data.get("start_point")  # 필요 시 사용

        # LineData 생성 (사용자의 알파값 적용)
        line_data = LineData(
            line_id=line_id,
            user_id=user_id,
            color=color,
            alpha=user_alpha,
            initial_alpha=user_alpha,
        )

        self.remote_lines[line_id] = line_data
        self.user_colors[user_id] = color

        self.update()

    def handle_drawing_update(self, line_id: str, user_id: str, data: Dict[str, Any]):
        """
        다른 사용자의 드로잉 업데이트 처리 (상대 좌표 수신)

        Args:
            line_id: 라인 ID
            user_id: 사용자 ID
            data: 업데이트 데이터 (new_finalized_segments, current_raw_points) - 상대 좌표
        """
        # 삭제된 라인 무시
        if line_id in self.deleted_line_ids:
            return

        # LineData 가져오기 (없으면 생성)
        if line_id not in self.remote_lines:
            color = self.user_colors.get(user_id, QColor(255, 0, 0))
            user_alpha = self.user_alphas.get(user_id, 1.0)
            self.remote_lines[line_id] = LineData(
                line_id=line_id,
                user_id=user_id,
                color=color,
                alpha=user_alpha,
                initial_alpha=user_alpha,
            )

        line_data = self.remote_lines[line_id]

        # 상대 좌표를 절대 좌표로 변환
        width = self.width()
        height = self.height()

        # 새로운 finalized segments 추가 (상대 좌표 → 절대 좌표)
        if "new_finalized_segments" in data:
            new_segments = []
            for seg_dict in data["new_finalized_segments"]:
                rel_segment = BezierSegment.from_dict(seg_dict)
                abs_segment = rel_segment.to_absolute(width, height)
                new_segments.append(abs_segment)
            line_data.add_finalized_segments(new_segments)

        # current raw points 업데이트 (상대 좌표 → 절대 좌표)
        if "current_raw_points" in data:
            abs_raw_points = [
                self._to_absolute_point(rel_x, rel_y)
                for rel_x, rel_y in data["current_raw_points"]
            ]
            line_data.update_raw_points(abs_raw_points)

        self.update()

    def handle_drawing_end(self, line_id: str, user_id: str):
        """
        다른 사용자의 드로잉 종료 처리

        Args:
            line_id: 라인 ID
            user_id: 사용자 ID
        """
        # 삭제된 라인 무시
        if line_id in self.deleted_line_ids:
            return

        if line_id in self.remote_lines:
            self.remote_lines[line_id].finalize()
            self.update()

    def handle_line_remove(self, line_id: str):
        """
        라인 제거 (서버 명령)

        Args:
            line_id: 제거할 라인 ID
        """
        if line_id in self.remote_lines:
            del self.remote_lines[line_id]
            self.update()

    def remove_user_lines(self, user_id: str):
        """
        특정 사용자의 모든 라인 제거

        Args:
            user_id: 사용자 ID
        """
        lines_to_remove = [lid for lid, ldata in self.remote_lines.items() if ldata.user_id == user_id]
        for line_id in lines_to_remove:
            del self.remote_lines[line_id]

        if user_id in self.user_colors:
            del self.user_colors[user_id]

        self.update()
