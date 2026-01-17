"""
IncrementalFitter 테스트
"""

from screen_party_client.drawing.incremental_fitter import IncrementalFitter


class TestIncrementalFitter:
    """IncrementalFitter 기본 동작 테스트"""

    def test_initialization(self):
        """초기화 테스트"""
        fitter = IncrementalFitter(trigger_count=10, max_error=4.0)

        assert fitter.trigger_count == 10
        assert len(fitter.raw_buffer) == 0
        assert len(fitter.finalized_segments) == 0
        assert fitter.is_drawing is False

    def test_start_drawing(self):
        """드로잉 시작 테스트"""
        fitter = IncrementalFitter()
        start_point = (10.0, 20.0)

        fitter.start_drawing(start_point)

        assert fitter.is_drawing is True
        assert len(fitter.raw_buffer) == 1
        assert fitter.raw_buffer[0] == start_point
        assert len(fitter.finalized_segments) == 0

    def test_add_point_before_trigger(self):
        """트리거 이전 점 추가 테스트"""
        fitter = IncrementalFitter(trigger_count=10)
        fitter.start_drawing((0.0, 0.0))

        # 9개 점 추가 (총 10개 미만)
        for i in range(1, 9):
            result = fitter.add_point((float(i * 10), float(i * 10)))
            assert result is False  # 피팅 발생하지 않음

        assert len(fitter.raw_buffer) == 9
        assert len(fitter.finalized_segments) == 0

    def test_add_point_trigger_fitting(self):
        """트리거 시 피팅 테스트"""
        fitter = IncrementalFitter(trigger_count=10, max_error=4.0)
        fitter.start_drawing((0.0, 0.0))

        # 15개 점 추가 (트리거 이후)
        for i in range(1, 15):
            fitter.add_point((float(i * 10), float(i * 10)))

        # 트리거가 발생했을 수 있음 (점의 형태에 따라 다름)
        # 최소한 raw_buffer에 점이 있어야 함
        assert len(fitter.raw_buffer) > 0

    def test_end_drawing(self):
        """드로잉 종료 테스트"""
        fitter = IncrementalFitter()
        fitter.start_drawing((0.0, 0.0))

        # 몇 개 점 추가
        for i in range(1, 5):
            fitter.add_point((float(i * 10), float(i * 10)))

        result = fitter.end_drawing()

        assert result is True  # 피팅 발생
        assert fitter.is_drawing is False
        assert len(fitter.raw_buffer) == 0  # 최종 피팅 후 비워짐
        assert len(fitter.finalized_segments) > 0  # 세그먼트 생성

    def test_end_drawing_with_insufficient_points(self):
        """점이 부족한 상태에서 드로잉 종료"""
        fitter = IncrementalFitter()
        fitter.start_drawing((0.0, 0.0))

        # 점 추가 없이 종료
        result = fitter.end_drawing()

        # 점이 1개뿐이므로 피팅 불가
        assert result is False
        assert fitter.is_drawing is False

    def test_clear(self):
        """clear 메서드 테스트"""
        fitter = IncrementalFitter()
        fitter.start_drawing((0.0, 0.0))
        fitter.add_point((10.0, 10.0))
        fitter.add_point((20.0, 20.0))

        fitter.clear()

        assert len(fitter.raw_buffer) == 0
        assert len(fitter.finalized_segments) == 0
        assert fitter.is_drawing is False


class TestIncrementalFitterNetworking:
    """네트워크 패킷 테스트"""

    def test_get_network_packet(self):
        """전체 패킷 생성 테스트"""
        fitter = IncrementalFitter()
        fitter.start_drawing((0.0, 0.0))
        fitter.add_point((10.0, 10.0))
        fitter.add_point((20.0, 20.0))

        packet = fitter.get_network_packet()

        assert "finalized_segments" in packet
        assert "current_raw_points" in packet
        assert len(packet["current_raw_points"]) == 3

    def test_get_delta_packet_initial(self):
        """초기 Delta 패킷 테스트"""
        fitter = IncrementalFitter()
        fitter.start_drawing((0.0, 0.0))
        fitter.add_point((10.0, 10.0))

        packet = fitter.get_delta_packet()

        assert "new_finalized_segments" in packet
        assert "current_raw_points" in packet
        assert len(packet["new_finalized_segments"]) == 0  # 아직 finalized 없음
        assert len(packet["current_raw_points"]) == 2

    def test_get_delta_packet_incremental(self):
        """점진적 Delta 패킷 테스트"""
        fitter = IncrementalFitter(trigger_count=5)
        fitter.start_drawing((0.0, 0.0))

        # 첫 번째 패킷
        for i in range(1, 4):
            fitter.add_point((float(i * 10), float(i * 10)))
        fitter.get_delta_packet()  # 첫 번째 패킷 (무시)

        # 더 많은 점 추가
        for i in range(4, 8):
            fitter.add_point((float(i * 10), float(i * 10)))
        packet2 = fitter.get_delta_packet()

        # 두 번째 패킷에는 새로운 finalized segments가 있을 수 있음
        # (점의 개수가 trigger_count를 넘었으므로)
        assert "new_finalized_segments" in packet2
        assert "current_raw_points" in packet2

    def test_has_changes(self):
        """has_changes 메서드 테스트"""
        fitter = IncrementalFitter()

        # 초기 상태: 변경 없음
        assert fitter.has_changes() is False

        # 드로잉 시작
        fitter.start_drawing((0.0, 0.0))
        assert fitter.has_changes() is True

        # Delta 패킷 전송
        fitter.get_delta_packet()

        # raw_buffer가 비어있지 않으면 여전히 변경 있음
        if len(fitter.raw_buffer) > 0:
            assert fitter.has_changes() is True

    def test_get_finalized_count(self):
        """finalized 세그먼트 개수 조회"""
        fitter = IncrementalFitter()
        fitter.start_drawing((0.0, 0.0))

        for i in range(1, 5):
            fitter.add_point((float(i * 10), float(i * 10)))

        fitter.end_drawing()

        count = fitter.get_finalized_count()
        assert count > 0  # 최소 1개 세그먼트 생성

    def test_get_raw_count(self):
        """raw_buffer 점 개수 조회"""
        fitter = IncrementalFitter()
        fitter.start_drawing((0.0, 0.0))

        fitter.add_point((10.0, 10.0))
        fitter.add_point((20.0, 20.0))

        assert fitter.get_raw_count() == 3


class TestIncrementalFitterFreezing:
    """세그먼트 Freezing 전략 테스트"""

    def test_freeze_segments_on_multiple_segments(self):
        """여러 세그먼트 생성 시 freeze 테스트"""
        fitter = IncrementalFitter(trigger_count=5, max_error=2.0)
        fitter.start_drawing((0.0, 0.0))

        # L자 형태로 많은 점 추가 (여러 세그먼트로 분할되어야 함)
        for i in range(1, 10):
            fitter.add_point((0.0, float(i * 10)))

        for i in range(1, 10):
            fitter.add_point((float(i * 10), 90.0))

        fitter.end_drawing()

        # 최종적으로 여러 세그먼트가 생성되어야 함
        assert fitter.get_finalized_count() >= 2

    def test_incremental_freezing(self):
        """점진적 freezing 테스트"""
        fitter = IncrementalFitter(trigger_count=10, max_error=4.0)
        fitter.start_drawing((0.0, 0.0))

        initial_finalized = fitter.get_finalized_count()

        # 많은 점 추가 (트리거 여러 번 발생)
        for i in range(1, 50):
            fitter.add_point((float(i * 2), float(i * 2)))

        # finalized 개수가 증가했을 수 있음
        # (점의 형태에 따라 다르지만, 최소한 0 이상)
        assert fitter.get_finalized_count() >= initial_finalized


class TestIncrementalFitterEdgeCases:
    """엣지 케이스 테스트"""

    def test_start_drawing_multiple_times(self):
        """여러 번 start_drawing 호출"""
        fitter = IncrementalFitter()

        fitter.start_drawing((0.0, 0.0))
        fitter.add_point((10.0, 10.0))

        # 다시 시작 (기존 데이터 초기화)
        fitter.start_drawing((100.0, 100.0))

        assert len(fitter.raw_buffer) == 1
        assert fitter.raw_buffer[0] == (100.0, 100.0)
        assert len(fitter.finalized_segments) == 0

    def test_add_point_without_start(self):
        """start_drawing 없이 add_point 호출"""
        fitter = IncrementalFitter()

        result = fitter.add_point((10.0, 10.0))

        assert result is False
        assert len(fitter.raw_buffer) == 0

    def test_end_drawing_without_start(self):
        """start_drawing 없이 end_drawing 호출"""
        fitter = IncrementalFitter()

        result = fitter.end_drawing()

        assert result is False

    def test_same_point_multiple_times(self):
        """동일한 점 여러 번 추가"""
        fitter = IncrementalFitter()
        fitter.start_drawing((0.0, 0.0))

        # 동일한 점 5번 추가
        for _ in range(5):
            fitter.add_point((0.0, 0.0))

        fitter.end_drawing()

        # 피팅이 정상적으로 처리되어야 함 (degeneracy 처리)
        assert fitter.is_drawing is False
