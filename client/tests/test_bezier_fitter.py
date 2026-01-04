"""
BezierFitter (Schneider 알고리즘) 테스트
"""

import pytest
from screen_party_client.drawing.bezier_fitter import BezierFitter, BezierSegment


class TestBezierSegment:
    """BezierSegment 데이터 클래스 테스트"""

    def test_to_dict(self):
        """to_dict 메서드 테스트"""
        segment = BezierSegment(
            p0=(0.0, 0.0),
            p1=(10.0, 20.0),
            p2=(30.0, 40.0),
            p3=(50.0, 60.0),
        )

        result = segment.to_dict()

        assert result["p0"] == (0.0, 0.0)
        assert result["p1"] == (10.0, 20.0)
        assert result["p2"] == (30.0, 40.0)
        assert result["p3"] == (50.0, 60.0)

    def test_from_dict(self):
        """from_dict 클래스 메서드 테스트"""
        data = {
            "p0": (0.0, 0.0),
            "p1": (10.0, 20.0),
            "p2": (30.0, 40.0),
            "p3": (50.0, 60.0),
        }

        segment = BezierSegment.from_dict(data)

        assert segment.p0 == (0.0, 0.0)
        assert segment.p1 == (10.0, 20.0)
        assert segment.p2 == (30.0, 40.0)
        assert segment.p3 == (50.0, 60.0)


class TestBezierFitter:
    """BezierFitter (Schneider 알고리즘) 테스트"""

    def test_fit_empty_points(self):
        """빈 점 리스트 피팅"""
        fitter = BezierFitter()
        segments = fitter.fit([])

        assert len(segments) == 0

    def test_fit_single_point(self):
        """단일 점 피팅"""
        fitter = BezierFitter()
        segments = fitter.fit([(0.0, 0.0)])

        assert len(segments) == 0

    def test_fit_two_points(self):
        """2개 점 피팅 (직선)"""
        fitter = BezierFitter()
        points = [(0.0, 0.0), (100.0, 100.0)]

        segments = fitter.fit(points)

        assert len(segments) == 1
        segment = segments[0]

        # 시작점과 끝점 확인
        assert segment.p0 == (0.0, 0.0)
        assert segment.p3 == (100.0, 100.0)

        # 제어점은 직선 위에 있어야 함 (1/3, 2/3 위치)
        # 대략적인 검증
        assert 30.0 <= segment.p1[0] <= 35.0
        assert 30.0 <= segment.p1[1] <= 35.0
        assert 65.0 <= segment.p2[0] <= 70.0
        assert 65.0 <= segment.p2[1] <= 70.0

    def test_fit_simple_curve(self):
        """간단한 곡선 피팅 (3개 점)"""
        fitter = BezierFitter(max_error=4.0)
        points = [
            (0.0, 0.0),
            (50.0, 100.0),
            (100.0, 0.0),
        ]

        segments = fitter.fit(points)

        # 최소 1개 세그먼트 생성
        assert len(segments) >= 1

        # 시작점과 끝점 확인
        assert segments[0].p0 == (0.0, 0.0)
        assert segments[-1].p3 == (100.0, 0.0)

    def test_fit_complex_curve(self):
        """복잡한 곡선 피팅 (10개 점)"""
        fitter = BezierFitter(max_error=4.0)
        points = [
            (0.0, 0.0),
            (10.0, 20.0),
            (20.0, 35.0),
            (30.0, 45.0),
            (40.0, 50.0),
            (50.0, 48.0),
            (60.0, 42.0),
            (70.0, 30.0),
            (80.0, 15.0),
            (90.0, 5.0),
        ]

        segments = fitter.fit(points)

        # 세그먼트가 생성되어야 함
        assert len(segments) >= 1

        # 시작점과 끝점 확인
        assert segments[0].p0 == (0.0, 0.0)
        assert segments[-1].p3 == (90.0, 5.0)

    def test_fit_max_error_parameter(self):
        """max_error 파라미터 영향 테스트"""
        points = [
            (0.0, 0.0),
            (10.0, 20.0),
            (20.0, 35.0),
            (30.0, 45.0),
            (40.0, 50.0),
        ]

        # 낮은 오차 허용치 (더 많은 세그먼트 생성)
        fitter_strict = BezierFitter(max_error=1.0)
        segments_strict = fitter_strict.fit(points)

        # 높은 오차 허용치 (더 적은 세그먼트 생성)
        fitter_loose = BezierFitter(max_error=10.0)
        segments_loose = fitter_loose.fit(points)

        # strict가 더 많은 세그먼트를 생성해야 함
        assert len(segments_strict) >= len(segments_loose)

    def test_chord_length_parameterize(self):
        """chord length parameterization 테스트"""
        import numpy as np

        fitter = BezierFitter()
        points = np.array(
            [
                [0.0, 0.0],
                [10.0, 0.0],
                [20.0, 0.0],
                [30.0, 0.0],
            ]
        )

        u = fitter._chord_length_parameterize(points)

        # u는 [0, 1] 범위
        assert u[0] == 0.0
        assert u[-1] == 1.0

        # u는 증가해야 함
        for i in range(len(u) - 1):
            assert u[i] <= u[i + 1]

    def test_bernstein_basis_functions(self):
        """Bernstein basis functions 테스트"""
        fitter = BezierFitter()

        # t=0에서
        assert fitter._b0(0.0) == 1.0
        assert fitter._b1(0.0) == 0.0
        assert fitter._b2(0.0) == 0.0
        assert fitter._b3(0.0) == 0.0

        # t=1에서
        assert fitter._b0(1.0) == 0.0
        assert fitter._b1(1.0) == 0.0
        assert fitter._b2(1.0) == 0.0
        assert fitter._b3(1.0) == 1.0

        # t=0.5에서 합이 1
        t = 0.5
        total = fitter._b0(t) + fitter._b1(t) + fitter._b2(t) + fitter._b3(t)
        assert abs(total - 1.0) < 1e-10

    def test_bezier_point(self):
        """베지어 커브 위의 점 계산 테스트"""
        fitter = BezierFitter()
        segment = BezierSegment(
            p0=(0.0, 0.0),
            p1=(0.0, 100.0),
            p2=(100.0, 100.0),
            p3=(100.0, 0.0),
        )

        # t=0에서 p0
        p = fitter._bezier_point(segment, 0.0)
        assert abs(p[0] - 0.0) < 1e-10
        assert abs(p[1] - 0.0) < 1e-10

        # t=1에서 p3
        p = fitter._bezier_point(segment, 1.0)
        assert abs(p[0] - 100.0) < 1e-10
        assert abs(p[1] - 0.0) < 1e-10

    def test_compute_tangents(self):
        """탄젠트 계산 테스트"""
        import numpy as np

        fitter = BezierFitter()
        points = np.array(
            [
                [0.0, 0.0],
                [10.0, 10.0],
                [20.0, 0.0],
            ]
        )

        # 왼쪽 탄젠트
        left = fitter._compute_left_tangent(points, 0)
        norm_left = np.linalg.norm(left)
        assert abs(norm_left - 1.0) < 1e-10  # 정규화 확인

        # 오른쪽 탄젠트
        right = fitter._compute_right_tangent(points, 2)
        norm_right = np.linalg.norm(right)
        assert abs(norm_right - 1.0) < 1e-10

        # 중심 탄젠트
        center = fitter._compute_center_tangent(points, 1)
        norm_center = np.linalg.norm(center)
        assert abs(norm_center - 1.0) < 1e-10


class TestBezierFitterIntegration:
    """통합 테스트"""

    def test_fit_real_mouse_trajectory(self):
        """실제 마우스 궤적 시뮬레이션 피팅"""
        fitter = BezierFitter(max_error=4.0)

        # S자 곡선 시뮬레이션
        import numpy as np

        t = np.linspace(0, 1, 20)
        x = t * 100
        y = 50 * np.sin(t * 2 * np.pi)
        points = list(zip(x, y))

        segments = fitter.fit(points)

        # 세그먼트가 생성되어야 함
        assert len(segments) >= 1

        # 시작점과 끝점 확인
        assert abs(segments[0].p0[0] - 0.0) < 1e-5
        assert abs(segments[-1].p3[0] - 100.0) < 1e-5

    def test_fit_sharp_corner(self):
        """예각 코너 피팅 (여러 세그먼트로 분할되어야 함)"""
        fitter = BezierFitter(max_error=2.0)

        # L자 형태
        points = [
            (0.0, 0.0),
            (0.0, 10.0),
            (0.0, 20.0),
            (0.0, 30.0),
            (10.0, 30.0),
            (20.0, 30.0),
            (30.0, 30.0),
        ]

        segments = fitter.fit(points)

        # 예각이므로 여러 세그먼트로 분할되어야 함
        assert len(segments) >= 2
