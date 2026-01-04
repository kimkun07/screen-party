"""
Incremental Fitter 연속성 테스트

실제 사용 시나리오에서 세그먼트가 끊기지 않고 연속적으로 이어지는지 검증
"""

import pytest
from screen_party_client.drawing.incremental_fitter import IncrementalFitter


class TestIncrementalContinuity:
    """세그먼트 연속성 테스트"""

    def test_segments_are_continuous(self):
        """
        여러 점을 추가했을 때 생성된 세그먼트들이 연속적으로 이어져야 함

        검증:
        1. 각 세그먼트의 끝점(p3)이 다음 세그먼트의 시작점(p0)과 일치
        2. 첫 세그먼트의 시작점이 첫 입력 점과 일치
        3. 마지막 세그먼트의 끝점이 마지막 입력 점과 일치
        """
        fitter = IncrementalFitter(trigger_count=10, max_error=4.0)

        # 직선 경로 생성 (0,0) -> (100, 100)
        points = [(i * 5.0, i * 5.0) for i in range(21)]  # 21개 점

        fitter.start_drawing(points[0])

        # 점들을 순차적으로 추가
        for point in points[1:]:
            fitter.add_point(point)

        # 드로잉 종료
        fitter.end_drawing()

        segments = fitter.finalized_segments

        # 최소 1개 이상의 세그먼트가 생성되어야 함
        assert len(segments) >= 1, f"세그먼트가 생성되지 않음"

        # 1. 첫 세그먼트의 시작점이 첫 입력 점과 일치 (허용 오차 1.0)
        first_seg = segments[0]
        assert abs(first_seg.p0[0] - points[0][0]) < 1.0, \
            f"첫 세그먼트 시작점 불일치: {first_seg.p0} vs {points[0]}"
        assert abs(first_seg.p0[1] - points[0][1]) < 1.0, \
            f"첫 세그먼트 시작점 불일치: {first_seg.p0} vs {points[0]}"

        # 2. 각 세그먼트가 연속적으로 이어져야 함
        for i in range(len(segments) - 1):
            current_seg = segments[i]
            next_seg = segments[i + 1]

            # 현재 세그먼트의 끝점 == 다음 세그먼트의 시작점
            assert abs(current_seg.p3[0] - next_seg.p0[0]) < 0.01, \
                f"세그먼트 {i}와 {i+1} 사이 연속성 깨짐: {current_seg.p3} != {next_seg.p0}"
            assert abs(current_seg.p3[1] - next_seg.p0[1]) < 0.01, \
                f"세그먼트 {i}와 {i+1} 사이 연속성 깨짐: {current_seg.p3} != {next_seg.p0}"

        # 3. 마지막 세그먼트의 끝점이 마지막 입력 점과 일치 (허용 오차 1.0)
        last_seg = segments[-1]
        assert abs(last_seg.p3[0] - points[-1][0]) < 1.0, \
            f"마지막 세그먼트 끝점 불일치: {last_seg.p3} vs {points[-1]}"
        assert abs(last_seg.p3[1] - points[-1][1]) < 1.0, \
            f"마지막 세그먼트 끝점 불일치: {last_seg.p3} vs {points[-1]}"

    def test_segments_cover_all_points(self):
        """
        모든 입력 점들이 생성된 세그먼트들로 충분히 표현되는지 검증

        검증:
        - 각 입력 점에서 가장 가까운 세그먼트까지의 거리가 max_error 이내
        """
        fitter = IncrementalFitter(trigger_count=8, max_error=4.0)

        # 곡선 경로 생성 (사인 곡선)
        import math
        points = [(i * 2.0, 50.0 + 30.0 * math.sin(i * 0.3)) for i in range(25)]

        fitter.start_drawing(points[0])

        for point in points[1:]:
            fitter.add_point(point)

        fitter.end_drawing()

        segments = fitter.finalized_segments

        # 최소 1개 이상의 세그먼트
        assert len(segments) >= 1

        # 각 입력 점에 대해 가장 가까운 세그먼트까지의 거리 검증
        max_error = 4.0

        for i, point in enumerate(points):
            min_distance = float('inf')

            for seg in segments:
                # 베지어 곡선 위의 샘플 점들과 비교
                for t in [i / 20.0 for i in range(21)]:
                    # 베지어 곡선 계산 B(t)
                    bx = (
                        (1-t)**3 * seg.p0[0] +
                        3*(1-t)**2*t * seg.p1[0] +
                        3*(1-t)*t**2 * seg.p2[0] +
                        t**3 * seg.p3[0]
                    )
                    by = (
                        (1-t)**3 * seg.p0[1] +
                        3*(1-t)**2*t * seg.p1[1] +
                        3*(1-t)*t**2 * seg.p2[1] +
                        t**3 * seg.p3[1]
                    )

                    distance = ((point[0] - bx)**2 + (point[1] - by)**2) ** 0.5
                    min_distance = min(min_distance, distance)

            # 점이 세그먼트로부터 너무 멀면 실패
            assert min_distance < max_error * 2, \
                f"점 {i} ({point})이 세그먼트로부터 너무 멀리 떨어짐: {min_distance:.2f}"

    def test_multiple_triggers(self):
        """
        여러 번 트리거가 발생할 때 세그먼트가 올바르게 누적되는지 검증
        """
        fitter = IncrementalFitter(trigger_count=5, max_error=4.0)

        # 긴 직선 경로
        points = [(i * 3.0, i * 3.0) for i in range(30)]

        fitter.start_drawing(points[0])

        segment_counts = []

        for i, point in enumerate(points[1:], start=1):
            fitter.add_point(point)
            segment_counts.append(len(fitter.finalized_segments))

        fitter.end_drawing()

        # 세그먼트 수가 점진적으로 증가해야 함 (감소하면 안 됨)
        for i in range(len(segment_counts) - 1):
            assert segment_counts[i] <= segment_counts[i+1], \
                f"세그먼트 수가 감소함: {segment_counts[i]} -> {segment_counts[i+1]}"

        # 최종적으로 세그먼트가 연속적이어야 함
        segments = fitter.finalized_segments

        for i in range(len(segments) - 1):
            current_seg = segments[i]
            next_seg = segments[i + 1]

            assert abs(current_seg.p3[0] - next_seg.p0[0]) < 0.01, \
                f"세그먼트 {i}와 {i+1} 사이 끊김"
            assert abs(current_seg.p3[1] - next_seg.p0[1]) < 0.01, \
                f"세그먼트 {i}와 {i+1} 사이 끊김"

    def test_complex_path(self):
        """
        복잡한 경로에서도 연속성이 유지되는지 검증
        """
        fitter = IncrementalFitter(trigger_count=10, max_error=5.0)

        # 복잡한 경로: 지그재그 + 곡선
        import math
        points = []
        for i in range(40):
            x = i * 5.0
            y = 50.0 + 20.0 * math.sin(i * 0.5) + 10.0 * (i % 2)
            points.append((x, y))

        fitter.start_drawing(points[0])

        for point in points[1:]:
            fitter.add_point(point)

        fitter.end_drawing()

        segments = fitter.finalized_segments

        # 최소 1개 이상
        assert len(segments) >= 1

        # 연속성 검증
        for i in range(len(segments) - 1):
            current_seg = segments[i]
            next_seg = segments[i + 1]

            distance = (
                (current_seg.p3[0] - next_seg.p0[0])**2 +
                (current_seg.p3[1] - next_seg.p0[1])**2
            ) ** 0.5

            assert distance < 0.01, \
                f"세그먼트 {i}와 {i+1} 사이 간격: {distance:.4f}, p3={current_seg.p3}, p0={next_seg.p0}"
