"""
DrawingCanvas GUI 테스트 (pytest-qt 사용)
"""

from PyQt6.QtCore import Qt, QPoint
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
        assert canvas.my_fitter.trigger_count == 10
        assert canvas.my_fitter.fitter.max_error == 4.0

    def test_mouse_press_starts_drawing(self, qtbot: QtBot):
        """마우스 눌림 시 드로잉 시작"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        # 마우스 클릭 시뮬레이션
        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPoint(10, 20))

        assert canvas.my_fitter.is_drawing is True
        assert len(canvas.my_fitter.raw_buffer) == 1

    def test_mouse_move_adds_points(self, qtbot: QtBot):
        """마우스 이동 시 점 추가"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        # 드로잉 시작
        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))

        # 마우스 이동
        qtbot.mouseMove(canvas, pos=QPoint(20, 20))
        qtbot.mouseMove(canvas, pos=QPoint(30, 30))

        # 점이 추가되어야 함
        assert len(canvas.my_fitter.raw_buffer) >= 1

    def test_mouse_release_ends_drawing(self, qtbot: QtBot):
        """마우스 떼기 시 드로잉 종료"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        # 드로잉 시작
        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))

        # 몇 개 점 추가
        qtbot.mouseMove(canvas, pos=QPoint(20, 20))
        qtbot.mouseMove(canvas, pos=QPoint(30, 30))

        # 마우스 떼기
        qtbot.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=QPoint(40, 40))

        assert canvas.my_fitter.is_drawing is False

    def test_clear_drawing(self, qtbot: QtBot):
        """clear_my_drawing 메서드 테스트"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        # 드로잉
        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))
        qtbot.mouseMove(canvas, pos=QPoint(20, 20))
        qtbot.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=QPoint(30, 30))

        # 초기화
        canvas.clear_my_drawing()

        assert len(canvas.my_fitter.raw_buffer) == 0
        assert len(canvas.my_fitter.finalized_segments) == 0
        # 내 라인만 제거됨
        my_lines = [
            lid for lid, ldata in canvas.remote_lines.items() if ldata.user_id == canvas.user_id
        ]
        assert len(my_lines) == 0

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
            qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))
            qtbot.mouseMove(canvas, pos=QPoint(20, 20))
            qtbot.mouseMove(canvas, pos=QPoint(30, 30))

            # 타이머 대기 (50ms 이상)
            qtbot.wait(100)

    def test_network_timer_starts_on_mouse_press(self, qtbot: QtBot):
        """마우스 눌림 시 네트워크 타이머 시작"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        assert not canvas.network_timer.isActive()

        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))

        assert canvas.network_timer.isActive()

    def test_network_timer_stops_on_mouse_release(self, qtbot: QtBot):
        """마우스 떼기 시 네트워크 타이머 중지"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))
        qtbot.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=QPoint(20, 20))

        assert not canvas.network_timer.isActive()

    def test_handle_drawing_update(self, qtbot: QtBot):
        """다른 사용자의 드로잉 업데이트 처리 테스트"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        # 패킷 데이터
        line_id = "test-line-123"
        user_id = "other-user"
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

        # 시작 처리
        canvas.handle_drawing_start(line_id, user_id, {"color": "#FF0000"})

        # 업데이트 처리
        canvas.handle_drawing_update(line_id, user_id, packet)

        # remote_lines에 라인이 추가되어야 함
        assert line_id in canvas.remote_lines
        assert len(canvas.remote_lines[line_id].finalized_segments) == 1

    def test_handle_drawing_end(self, qtbot: QtBot):
        """다른 사용자의 드로잉 종료 처리 테스트"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        line_id = "test-line-456"
        user_id = "other-user-2"

        # 시작 처리
        canvas.handle_drawing_start(line_id, user_id, {"color": "#00FF00"})

        # 업데이트 처리
        canvas.handle_drawing_update(
            line_id,
            user_id,
            {
                "new_finalized_segments": [
                    {
                        "p0": (100.0, 100.0),
                        "p1": (110.0, 120.0),
                        "p2": (130.0, 140.0),
                        "p3": (150.0, 160.0),
                    }
                ],
                "current_raw_points": [(200.0, 200.0), (210.0, 210.0)],
            },
        )

        # 종료 처리
        canvas.handle_drawing_end(line_id, user_id)

        # 라인이 완료 상태가 되어야 함
        assert line_id in canvas.remote_lines
        assert canvas.remote_lines[line_id].is_complete is True


class TestDrawingCanvasRendering:
    """렌더링 테스트"""

    def test_paint_event_called(self, qtbot: QtBot):
        """paintEvent가 호출되는지 테스트"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)
        canvas.show()

        # 드로잉
        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))
        qtbot.mouseMove(canvas, pos=QPoint(20, 20))

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
        canvas.my_fitter.finalized_segments.append(segment)

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
        canvas.my_fitter.raw_buffer = [
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
        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))

        # 2. 여러 점 추가
        for i in range(1, 10):
            qtbot.mouseMove(canvas, pos=QPoint(10 + i * 10, 10 + i * 10))

        # 3. 드로잉 종료
        qtbot.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))

        # 4. finalized segments가 생성되어야 함 (remote_lines에 저장됨)
        # 내 드로잉이 remote_lines에 저장되었는지 확인
        my_lines = [
            lid for lid, ldata in canvas.remote_lines.items() if ldata.user_id == canvas.user_id
        ]
        assert len(my_lines) > 0
        # 해당 라인에 finalized segments가 있어야 함
        assert len(canvas.remote_lines[my_lines[0]].finalized_segments) > 0

    def test_network_transmission_flow(self, qtbot: QtBot):
        """네트워크 전송 플로우 테스트"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        received_packets = []

        def on_drawing_updated(line_id, user_id, packet):
            # 시그널이 (line_id, user_id, packet) 형식으로 전달됨
            received_packets.append(packet)

        canvas.drawing_updated.connect(on_drawing_updated)

        # 드로잉
        qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))

        for i in range(1, 5):
            qtbot.mouseMove(canvas, pos=QPoint(10 + i * 10, 10 + i * 10))

        # 타이머 대기 (50ms 이상)
        qtbot.wait(100)

        qtbot.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=QPoint(50, 50))

        # 패킷이 전송되었어야 함
        assert len(received_packets) > 0

        # 패킷 구조 검증
        packet = received_packets[0]
        assert "new_finalized_segments" in packet
        assert "current_raw_points" in packet


class TestDrawingCanvasFadeAnimation:
    """페이드아웃 애니메이션 테스트"""

    def test_fade_animation_initialization(self, qtbot: QtBot):
        """페이드아웃 파라미터 초기화 테스트"""
        canvas = DrawingCanvas(
            fade_hold_duration=3.0,
            fade_duration=2.0,
            timeout_duration=15.0,
        )
        qtbot.addWidget(canvas)

        assert canvas.fade_hold_duration == 3.0
        assert canvas.fade_duration == 2.0
        assert canvas.timeout_duration == 15.0
        assert canvas.animation_timer.isActive()

    def test_fade_animation_default_parameters(self, qtbot: QtBot):
        """페이드아웃 기본 파라미터 테스트"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        assert canvas.fade_hold_duration == 2.0
        assert canvas.fade_duration == 1.0
        assert canvas.timeout_duration == 10.0

    def test_line_data_has_fade_fields(self, qtbot: QtBot):
        """LineData에 페이드아웃 필드가 있는지 확인"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        line_id = "test-fade-line"
        user_id = "test-user"

        canvas.handle_drawing_start(line_id, user_id, {"color": "#FF0000"})

        line_data = canvas.remote_lines[line_id]
        assert hasattr(line_data, "alpha")
        assert hasattr(line_data, "end_time")
        assert hasattr(line_data, "last_update_time")
        assert line_data.alpha == 1.0
        assert line_data.end_time is None

    def test_drawing_end_sets_end_time(self, qtbot: QtBot):
        """drawing_end 호출 시 end_time 설정 확인"""
        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        line_id = "test-end-time"
        user_id = "test-user"

        canvas.handle_drawing_start(line_id, user_id, {"color": "#00FF00"})
        canvas.handle_drawing_end(line_id, user_id)

        line_data = canvas.remote_lines[line_id]
        assert line_data.end_time is not None
        assert line_data.is_complete is True

    def test_fade_hold_phase(self, qtbot: QtBot):
        """페이드 유지 단계 (2초) 테스트"""

        canvas = DrawingCanvas(
            fade_hold_duration=0.5,  # 테스트용 짧은 시간
            fade_duration=0.3,
        )
        qtbot.addWidget(canvas)

        line_id = "test-hold-phase"
        user_id = "test-user"

        canvas.handle_drawing_start(line_id, user_id, {"color": "#0000FF"})
        canvas.handle_drawing_end(line_id, user_id)

        # 0.2초 대기 (hold 단계)
        qtbot.wait(200)

        # 알파값이 1.0이어야 함
        line_data = canvas.remote_lines.get(line_id)
        assert line_data is not None
        assert line_data.alpha == 1.0

    def test_fade_animation_phase(self, qtbot: QtBot):
        """페이드아웃 단계 (1초) 테스트"""

        canvas = DrawingCanvas(
            fade_hold_duration=0.1,  # 매우 짧은 hold
            fade_duration=0.5,
        )
        qtbot.addWidget(canvas)

        line_id = "test-fade-phase"
        user_id = "test-user"

        canvas.handle_drawing_start(line_id, user_id, {"color": "#FF00FF"})
        canvas.handle_drawing_end(line_id, user_id)

        # hold 단계 대기
        qtbot.wait(150)

        # 페이드 중간 대기
        qtbot.wait(250)

        # 알파값이 감소했어야 함
        line_data = canvas.remote_lines.get(line_id)
        assert line_data is not None
        assert 0.0 < line_data.alpha < 1.0

    def test_fade_complete_removes_line(self, qtbot: QtBot):
        """페이드 완료 후 라인 삭제 테스트"""
        canvas = DrawingCanvas(
            fade_hold_duration=0.1,
            fade_duration=0.2,
        )
        qtbot.addWidget(canvas)

        line_id = "test-fade-complete"
        user_id = "test-user"

        canvas.handle_drawing_start(line_id, user_id, {"color": "#00FFFF"})
        canvas.handle_drawing_end(line_id, user_id)

        # hold + fade 완료 대기
        qtbot.wait(400)

        # 라인이 삭제되었어야 함
        assert line_id not in canvas.remote_lines
        assert line_id in canvas.deleted_line_ids

    def test_timeout_removes_line_without_fade(self, qtbot: QtBot):
        """타임아웃 시 페이드 없이 즉시 삭제 테스트"""
        canvas = DrawingCanvas(
            timeout_duration=0.3,  # 짧은 타임아웃
        )
        qtbot.addWidget(canvas)

        line_id = "test-timeout"
        user_id = "test-user"

        canvas.handle_drawing_start(line_id, user_id, {"color": "#FFFF00"})

        # drawing_end 호출하지 않음 (타임아웃 시나리오)
        # 타임아웃 대기
        qtbot.wait(400)

        # 라인이 강제 삭제되었어야 함
        assert line_id not in canvas.remote_lines
        assert line_id in canvas.deleted_line_ids

    def test_deleted_line_ignores_subsequent_events(self, qtbot: QtBot):
        """삭제된 라인은 이후 이벤트 무시"""
        canvas = DrawingCanvas(
            fade_hold_duration=0.1,
            fade_duration=0.1,
        )
        qtbot.addWidget(canvas)

        line_id = "test-deleted-ignore"
        user_id = "test-user"

        canvas.handle_drawing_start(line_id, user_id, {"color": "#FF8800"})
        canvas.handle_drawing_end(line_id, user_id)

        # 페이드 완료 대기
        qtbot.wait(300)

        # 라인 삭제 확인
        assert line_id in canvas.deleted_line_ids

        # 이후 이벤트 전송
        canvas.handle_drawing_update(
            line_id,
            user_id,
            {
                "new_finalized_segments": [],
                "current_raw_points": [(100.0, 100.0)],
            },
        )

        # 여전히 삭제 상태여야 함
        assert line_id not in canvas.remote_lines

    def test_last_update_time_updated_on_events(self, qtbot: QtBot):
        """이벤트 발생 시 last_update_time 갱신 확인"""
        import time

        canvas = DrawingCanvas()
        qtbot.addWidget(canvas)

        line_id = "test-last-update"
        user_id = "test-user"

        canvas.handle_drawing_start(line_id, user_id, {"color": "#8800FF"})

        initial_time = canvas.remote_lines[line_id].last_update_time

        # 약간 대기
        time.sleep(0.1)

        # 업데이트 이벤트
        canvas.handle_drawing_update(
            line_id,
            user_id,
            {
                "new_finalized_segments": [],
                "current_raw_points": [(50.0, 50.0)],
            },
        )

        # last_update_time이 갱신되었어야 함
        updated_time = canvas.remote_lines[line_id].last_update_time
        assert updated_time > initial_time

    def test_alpha_applied_to_rendering(self, qtbot: QtBot):
        """렌더링 시 알파값 적용 확인 (간접 테스트)"""
        canvas = DrawingCanvas(
            fade_hold_duration=0.1,
            fade_duration=0.5,
        )
        qtbot.addWidget(canvas)
        canvas.show()

        line_id = "test-alpha-render"
        user_id = "test-user"

        canvas.handle_drawing_start(line_id, user_id, {"color": "#FF0080"})
        canvas.handle_drawing_update(
            line_id,
            user_id,
            {
                "new_finalized_segments": [
                    {
                        "p0": (10.0, 10.0),
                        "p1": (20.0, 30.0),
                        "p2": (40.0, 50.0),
                        "p3": (60.0, 70.0),
                    }
                ],
                "current_raw_points": [],
            },
        )
        canvas.handle_drawing_end(line_id, user_id)

        # hold 대기
        qtbot.wait(150)

        # 페이드 중간
        qtbot.wait(250)

        # 알파값 감소 확인
        line_data = canvas.remote_lines.get(line_id)
        assert line_data is not None
        assert 0.0 < line_data.alpha < 1.0

        # 렌더링 (오류 없이 완료되어야 함)
        canvas.update()
        qtbot.wait(50)
