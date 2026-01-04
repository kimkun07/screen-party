"""
DrawingCanvas GUI 테스트 (pytest-qt 사용)
"""

import pytest
from PyQt6.QtCore import Qt, QPointF, QTimer
from PyQt6.QtGui import QColor
from pytestqt.qtbot import QtBot

from screen_party_client.drawing.canvas import DrawingCanvas


class TestDrawingCanvas:
    """DrawingCanvas 기본 동작 테스트"""

    def test_initialization(self, qtbot: QtBot):
        """초기화 테스트"""
        canvas = DrawingCanvas(
            pen_color=QColor(255, 0, 0),
            pen_width=3,
            trigger_count=10,
            max_error=4.0,
        )
        qtbot.addWidget(canvas)

        assert canvas.pen_color == QColor(255, 0, 0)
        assert canvas.pen_width == 3
        assert canvas.fitter.trigger_count == 10
        assert canvas.fitter.fitter.max_error == 4.0

    def test_mouse_press_starts_drawing(self, qtbot: QtBot):
        """마우스 눌림 시 드로잉 시작"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        # 마우스 클릭 시뮬레이션
        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPointF(10, 20))

        assert canvas.fitter.is_drawing is True
        assert len(canvas.fitter.raw_buffer) == 1

    def test_mouse_move_adds_points(self, qtbot: QtBot):
        """마우스 이동 시 점 추가"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        # 드로잉 시작
        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPointF(10, 10))

        # 마우스 이동
        qtbot.mouseMove(canvas, QPointF(20, 20))
        qtbot.mouseMove(canvas, QPointF(30, 30))

        # 점이 추가되어야 함
        assert len(canvas.fitter.raw_buffer) >= 1

    def test_mouse_release_ends_drawing(self, qtbot: QtBot):
        """마우스 떼기 시 드로잉 종료"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        # 드로잉 시작
        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPointF(10, 10))

        # 몇 개 점 추가
        qtbot.mouseMove(canvas, QPointF(20, 20))
        qtbot.mouseMove(canvas, QPointF(30, 30))

        # 마우스 떼기
        qtbot.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=QPointF(40, 40))

        assert canvas.fitter.is_drawing is False

    def test_clear_drawing(self, qtbot: QtBot):
        """clear_drawing 메서드 테스트"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        # 드로잉
        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPointF(10, 10))
        qtbot.mouseMove(canvas, QPointF(20, 20))
        qtbot.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=QPointF(30, 30))

        # 초기화
        canvas.clear_drawing()

        assert len(canvas.fitter.raw_buffer) == 0
        assert len(canvas.fitter.finalized_segments) == 0

    def test_set_pen_color(self, qtbot: QtBot):
        """펜 색상 변경 테스트"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        new_color = QColor(0, 255, 0)
        canvas.set_pen_color(new_color)

        assert canvas.pen_color == new_color

    def test_set_pen_width(self, qtbot: QtBot):
        """펜 두께 변경 테스트"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        canvas.set_pen_width(5)

        assert canvas.pen_width == 5


class TestDrawingCanvasNetworking:
    """네트워크 전송 테스트"""

    def test_drawing_updated_signal(self, qtbot: QtBot):
        """drawing_updated 시그널 발생 테스트"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        # 시그널 감지
        with qtbot.waitSignal(canvas.drawing_updated, timeout=1000):
            # 드로잉
            qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPointF(10, 10))
            qtbot.mouseMove(canvas, QPointF(20, 20))
            qtbot.mouseMove(canvas, QPointF(30, 30))

            # 타이머 대기 (50ms 이상)
            qtbot.wait(100)

    def test_network_timer_starts_on_mouse_press(self, qtbot: QtBot):
        """마우스 눌림 시 네트워크 타이머 시작"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        assert not canvas.network_timer.isActive()

        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPointF(10, 10))

        assert canvas.network_timer.isActive()

    def test_network_timer_stops_on_mouse_release(self, qtbot: QtBot):
        """마우스 떼기 시 네트워크 타이머 중지"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPointF(10, 10))
        qtbot.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=QPointF(20, 20))

        assert not canvas.network_timer.isActive()

    def test_apply_network_packet(self, qtbot: QtBot):
        """네트워크 패킷 적용 테스트"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        # 패킷 데이터
        packet = {
            "new_finalized_segments": [
                {
                    "p0": (0.0, 0.0),
                    "p1": (10.0, 20.0),
                    "p2": (30.0, 40.0),
                    "p3": (50.0, 60.0),
                }
            ],
            "current_raw_points": [],
        }

        canvas.apply_network_packet(packet)

        # 세그먼트가 추가되어야 함
        assert len(canvas.fitter.finalized_segments) == 1

    def test_apply_full_packet(self, qtbot: QtBot):
        """전체 패킷 적용 테스트"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        # 기존 데이터 추가
        canvas.fitter.finalized_segments.append(
            canvas.fitter.fitter.fit([(0, 0), (10, 10)])[0]
        )

        # 전체 패킷으로 덮어쓰기
        packet = {
            "finalized_segments": [
                {
                    "p0": (100.0, 100.0),
                    "p1": (110.0, 120.0),
                    "p2": (130.0, 140.0),
                    "p3": (150.0, 160.0),
                }
            ],
            "current_raw_points": [],
        }

        canvas.apply_full_packet(packet)

        # 기존 데이터가 초기화되고 새 데이터만 있어야 함
        assert len(canvas.fitter.finalized_segments) == 1
        assert canvas.fitter.finalized_segments[0].p0 == (100.0, 100.0)


class TestDrawingCanvasRendering:
    """렌더링 테스트"""

    def test_paint_event_called(self, qtbot: QtBot):
        """paintEvent가 호출되는지 테스트"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)
        canvas.show()

        # 드로잉
        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPointF(10, 10))
        qtbot.mouseMove(canvas, QPointF(20, 20))

        # update() 호출 후 paintEvent가 호출되어야 함
        canvas.update()
        qtbot.wait(50)

        # 정상적으로 렌더링되면 오류 없음
        # (실제 렌더링 결과는 이미지 비교로 검증 가능하지만 여기서는 생략)

    def test_render_finalized_segments(self, qtbot: QtBot):
        """finalized segments 렌더링 테스트"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)
        canvas.show()

        # 세그먼트 추가
        from screen_party_client.drawing.bezier_fitter import BezierSegment

        segment = BezierSegment(
            p0=(10.0, 10.0),
            p1=(20.0, 30.0),
            p2=(40.0, 50.0),
            p3=(60.0, 70.0),
        )
        canvas.fitter.finalized_segments.append(segment)

        # 렌더링
        canvas.update()
        qtbot.wait(50)

        # 오류 없이 렌더링되어야 함

    def test_render_raw_points(self, qtbot: QtBot):
        """raw points 렌더링 테스트"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)
        canvas.show()

        # raw_buffer에 점 추가
        canvas.fitter.raw_buffer = [
            (10.0, 10.0),
            (20.0, 20.0),
            (30.0, 30.0),
        ]

        # 렌더링
        canvas.update()
        qtbot.wait(50)

        # 오류 없이 렌더링되어야 함


class TestDrawingCanvasIntegration:
    """통합 테스트"""

    def test_full_drawing_flow(self, qtbot: QtBot):
        """전체 드로잉 플로우 테스트"""
        canvas = DrawingCanvas(trigger_count=5)
        qtbot.addWidget(canvas)
        canvas.show()

        # 1. 드로잉 시작
        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPointF(10, 10))

        # 2. 여러 점 추가
        for i in range(1, 10):
            qtbot.mouseMove(canvas, QPointF(10 + i * 10, 10 + i * 10))

        # 3. 드로잉 종료
        qtbot.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=QPointF(100, 100))

        # 4. finalized segments가 생성되어야 함
        assert len(canvas.fitter.finalized_segments) > 0

    def test_network_transmission_flow(self, qtbot: QtBot):
        """네트워크 전송 플로우 테스트"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        received_packets = []

        def on_drawing_updated(packet):
            received_packets.append(packet)

        canvas.drawing_updated.connect(on_drawing_updated)

        # 드로잉
        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPointF(10, 10))

        for i in range(1, 5):
            qtbot.mouseMove(canvas, QPointF(10 + i * 10, 10 + i * 10))

        # 타이머 대기 (50ms 이상)
        qtbot.wait(100)

        qtbot.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=QPointF(50, 50))

        # 패킷이 전송되었어야 함
        assert len(received_packets) > 0

        # 패킷 구조 검증
        packet = received_packets[0]
        assert "new_finalized_segments" in packet
        assert "current_raw_points" in packet
