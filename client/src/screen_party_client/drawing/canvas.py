"""
드로잉 캔버스 및 렌더링 컴포넌트 (Multi-user 지원)

베지어 커브와 raw 점들을 렌더링하며, 네트워크 전송을 관리합니다.
여러 사용자의 드로잉을 line_id별로 관리합니다.
"""

from typing import Optional, Dict, Any
import uuid
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QPainterPath, QMouseEvent, QPaintEvent, QColor

from screen_party_common import MessageType, DrawingStartMessage, DrawingUpdateMessage, DrawingEndMessage
from .incremental_fitter import IncrementalFitter
from .bezier_fitter import BezierSegment
from .line_data import LineData


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
        pen_color: QColor = QColor(255, 0, 0),
        pen_width: int = 3,
        trigger_count: int = 10,
        max_error: float = 4.0,
    ):
        """
        Args:
            parent: 부모 위젯
            user_id: 현재 사용자 ID
            pen_color: 펜 색상
            pen_width: 펜 두께
            trigger_count: 피팅 트리거 점 개수
            max_error: 베지어 피팅 최대 오차
        """
        super().__init__(parent)

        # 사용자 정보
        self.user_id = user_id or str(uuid.uuid4())
        self.pen_color = pen_color
        self.pen_width = pen_width

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

        # 네트워크 전송 타이머 (50ms)
        self.network_timer = QTimer(self)
        self.network_timer.timeout.connect(self._send_network_update)
        self.network_interval = 50  # ms

        # 마우스 추적 활성화
        self.setMouseTracking(True)

        # 배경 투명
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_user_id(self, user_id: str):
        """사용자 ID 설정"""
        self.user_id = user_id
        if user_id not in self.user_colors:
            self.user_colors[user_id] = self.pen_color

    def set_user_color(self, user_id: str, color: QColor):
        """사용자별 색상 설정"""
        self.user_colors[user_id] = color

    def mousePressEvent(self, event: QMouseEvent):
        """마우스 눌림: 드로잉 시작"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            start_point = (pos.x(), pos.y())

            # 새로운 line_id 생성
            self.my_line_id = str(uuid.uuid4())

            # 드로잉 시작
            self.my_fitter.start_drawing(start_point)

            # 시작 이벤트 전송
            msg = DrawingStartMessage(
                line_id=self.my_line_id,
                user_id=self.user_id,
                color=self.pen_color.name(),
                start_point=start_point,
            )
            self.drawing_started.emit(self.my_line_id, self.user_id, msg.to_dict())

            # 네트워크 전송 타이머 시작
            self.network_timer.start(self.network_interval)

            self.update()  # 화면 갱신

    def mouseMoveEvent(self, event: QMouseEvent):
        """마우스 이동: 점 추가"""
        if self.my_fitter.is_drawing and self.my_line_id:
            pos = event.position()
            point = (pos.x(), pos.y())

            self.my_fitter.add_point(point)
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
            pen = QPen(line_data.color, self.pen_width)
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
        """네트워크 업데이트 전송 (Delta Update)"""
        if not self.my_fitter.has_changes() or not self.my_line_id:
            return

        # Delta 패킷 생성
        packet = self.my_fitter.get_delta_packet()

        # 메시지 생성
        msg = DrawingUpdateMessage(
            line_id=self.my_line_id,
            user_id=self.user_id,
            new_finalized_segments=packet["new_finalized_segments"],
            current_raw_points=packet["current_raw_points"],
        )

        # 시그널 emit
        self.drawing_updated.emit(self.my_line_id, self.user_id, msg.to_dict())

    def _save_my_drawing(self):
        """내 드로잉을 remote_lines에 저장 (렌더링 유지용)"""
        if not self.my_line_id:
            return

        # LineData 생성
        line_data = LineData(
            line_id=self.my_line_id,
            user_id=self.user_id,
            color=self.pen_color,
            finalized_segments=self.my_fitter.finalized_segments.copy(),
            current_raw_points=[],
            is_complete=True,
        )

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
        """펜 색상 변경"""
        self.pen_color = color
        self.user_colors[self.user_id] = color
        self.update()

    def set_pen_width(self, width: int):
        """펜 두께 변경"""
        self.pen_width = width
        self.update()

    # === 수신 메시지 처리 ===

    def handle_drawing_start(self, line_id: str, user_id: str, data: Dict[str, Any]):
        """
        다른 사용자의 드로잉 시작 처리

        Args:
            line_id: 라인 ID
            user_id: 사용자 ID
            data: 시작 데이터 (color, start_point 등)
        """
        # 색상 파싱
        color_str = data.get("color", "#FF0000")
        color = QColor(color_str)

        # LineData 생성
        line_data = LineData(
            line_id=line_id,
            user_id=user_id,
            color=color,
        )

        self.remote_lines[line_id] = line_data
        self.user_colors[user_id] = color

        self.update()

    def handle_drawing_update(self, line_id: str, user_id: str, data: Dict[str, Any]):
        """
        다른 사용자의 드로잉 업데이트 처리

        Args:
            line_id: 라인 ID
            user_id: 사용자 ID
            data: 업데이트 데이터 (new_finalized_segments, current_raw_points)
        """
        # LineData 가져오기 (없으면 생성)
        if line_id not in self.remote_lines:
            color = self.user_colors.get(user_id, QColor(255, 0, 0))
            self.remote_lines[line_id] = LineData(
                line_id=line_id,
                user_id=user_id,
                color=color,
            )

        line_data = self.remote_lines[line_id]

        # 새로운 finalized segments 추가
        if "new_finalized_segments" in data:
            new_segments = []
            for seg_dict in data["new_finalized_segments"]:
                segment = BezierSegment.from_dict(seg_dict)
                new_segments.append(segment)
            line_data.add_finalized_segments(new_segments)

        # current raw points 업데이트
        if "current_raw_points" in data:
            line_data.update_raw_points(data["current_raw_points"])

        self.update()

    def handle_drawing_end(self, line_id: str, user_id: str):
        """
        다른 사용자의 드로잉 종료 처리

        Args:
            line_id: 라인 ID
            user_id: 사용자 ID
        """
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
