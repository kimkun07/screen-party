"""
드로잉 캔버스 및 렌더링 컴포넌트

베지어 커브와 raw 점들을 렌더링하며, 네트워크 전송을 관리합니다.
"""

from typing import Optional, Callable, Dict, Any
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QPainterPath, QMouseEvent, QPaintEvent, QColor

from .incremental_fitter import IncrementalFitter
from .bezier_fitter import BezierSegment


class DrawingCanvas(QWidget):
    """
    드로잉 캔버스

    기능:
    - 마우스 입력 캡처
    - 실시간 베지어 커브 피팅
    - 렌더링 (finalized: 곡선, current: 직선)
    - 네트워크 전송 (50ms throttling)
    """

    # 네트워크 전송 시그널
    drawing_updated = pyqtSignal(dict)  # 드로잉 데이터 업데이트

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        pen_color: QColor = QColor(255, 0, 0),
        pen_width: int = 3,
        trigger_count: int = 10,
        max_error: float = 4.0,
    ):
        """
        Args:
            parent: 부모 위젯
            pen_color: 펜 색상
            pen_width: 펜 두께
            trigger_count: 피팅 트리거 점 개수
            max_error: 베지어 피팅 최대 오차
        """
        super().__init__(parent)

        # 드로잉 설정
        self.pen_color = pen_color
        self.pen_width = pen_width

        # Incremental Fitter
        self.fitter = IncrementalFitter(
            trigger_count=trigger_count,
            max_error=max_error,
        )

        # 네트워크 전송 타이머 (50ms)
        self.network_timer = QTimer(self)
        self.network_timer.timeout.connect(self._send_network_update)
        self.network_interval = 50  # ms

        # 마우스 추적 활성화
        self.setMouseTracking(True)

        # 배경 투명
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def mousePressEvent(self, event: QMouseEvent):
        """마우스 눌림: 드로잉 시작"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            start_point = (pos.x(), pos.y())

            self.fitter.start_drawing(start_point)

            # 네트워크 전송 타이머 시작
            self.network_timer.start(self.network_interval)

            self.update()  # 화면 갱신

    def mouseMoveEvent(self, event: QMouseEvent):
        """마우스 이동: 점 추가"""
        if self.fitter.is_drawing:
            pos = event.position()
            point = (pos.x(), pos.y())

            self.fitter.add_point(point)
            self.update()  # 화면 갱신

    def mouseReleaseEvent(self, event: QMouseEvent):
        """마우스 떼기: 드로잉 종료"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.fitter.is_drawing:
                self.fitter.end_drawing()

                # 네트워크 전송 타이머 중지
                self.network_timer.stop()

                # 최종 업데이트 전송
                self._send_network_update()

                self.update()  # 화면 갱신

    def paintEvent(self, event: QPaintEvent):
        """렌더링"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(self.pen_color, self.pen_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        # 1. finalized_segments: 매끄러운 베지어 곡선 렌더링
        for segment in self.fitter.finalized_segments:
            self._draw_bezier_segment(painter, segment)

        # 2. current_raw_points: 직선으로 렌더링
        if len(self.fitter.raw_buffer) >= 2:
            self._draw_raw_points(painter, self.fitter.raw_buffer)

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
        if not self.fitter.has_changes():
            return

        # Delta 패킷 생성
        packet = self.fitter.get_delta_packet()

        # 시그널 emit
        self.drawing_updated.emit(packet)

    def clear_drawing(self):
        """드로잉 초기화"""
        self.fitter.clear()
        self.update()

    def set_pen_color(self, color: QColor):
        """펜 색상 변경"""
        self.pen_color = color
        self.update()

    def set_pen_width(self, width: int):
        """펜 두께 변경"""
        self.pen_width = width
        self.update()

    # 수신한 데이터 렌더링 (다른 사용자의 드로잉)
    def apply_network_packet(self, packet: Dict[str, Any]):
        """
        네트워크로부터 수신한 드로잉 데이터 적용

        Args:
            packet: {
                "new_finalized_segments": [...],
                "current_raw_points": [...]
            }
        """
        # 새로운 finalized segments 추가
        if "new_finalized_segments" in packet:
            for seg_dict in packet["new_finalized_segments"]:
                segment = BezierSegment.from_dict(seg_dict)
                self.fitter.finalized_segments.append(segment)

        # current raw points 업데이트
        if "current_raw_points" in packet:
            # 원격 사용자의 raw_buffer를 별도로 관리할 수도 있지만,
            # 여기서는 간단히 무시 (finalized만 표시)
            pass

        self.update()

    def apply_full_packet(self, packet: Dict[str, Any]):
        """
        전체 드로잉 데이터 적용 (초기 동기화용)

        Args:
            packet: {
                "finalized_segments": [...],
                "current_raw_points": [...]
            }
        """
        # 기존 데이터 초기화
        self.fitter.finalized_segments = []

        # finalized segments 로드
        if "finalized_segments" in packet:
            for seg_dict in packet["finalized_segments"]:
                segment = BezierSegment.from_dict(seg_dict)
                self.fitter.finalized_segments.append(segment)

        self.update()
