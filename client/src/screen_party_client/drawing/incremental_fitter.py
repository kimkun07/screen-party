"""
Incremental Fitting 시스템

실시간으로 입력되는 raw_points를 베지어 커브로 변환하며,
finalized_segments와 current_raw_points를 관리합니다.
"""

from typing import List, Tuple, Dict, Any
from .bezier_fitter import BezierFitter, BezierSegment


class IncrementalFitter:
    """
    실시간 베지어 커브 피팅 관리자

    전략:
    1. raw_buffer에 마우스 입력 점들을 실시간으로 추가
    2. N개 이상이 되면 Schneider 알고리즘 실행
    3. 성공하면 finalized_segments로 이동, 실패하면 분할
    4. 마우스 up 시 남은 점들을 최종 피팅
    """

    def __init__(
        self,
        trigger_count: int = 10,
        max_error: float = 4.0,
        max_iterations: int = 4,
    ):
        """
        Args:
            trigger_count: 피팅을 트리거할 최소 점 개수 (기본: 10)
            max_error: 베지어 피팅 최대 허용 오차 (기본: 4.0 픽셀)
            max_iterations: Newton-Raphson 최대 반복 횟수 (기본: 4)
        """
        self.trigger_count = trigger_count
        self.fitter = BezierFitter(max_error=max_error, max_iterations=max_iterations)

        # 상태
        self.raw_buffer: List[Tuple[float, float]] = []
        self.finalized_segments: List[BezierSegment] = []
        self.is_drawing = False

        # 네트워크 전송용 상태 추적
        self._last_sent_finalized_count = 0

    def start_drawing(self, start_point: Tuple[float, float]):
        """
        드로잉 시작

        Args:
            start_point: 시작 점 (x, y)
        """
        self.is_drawing = True
        self.raw_buffer = [start_point]
        self.finalized_segments = []
        self._last_sent_finalized_count = 0

    def add_point(self, point: Tuple[float, float]) -> bool:
        """
        점 추가 및 자동 피팅

        Args:
            point: 추가할 점 (x, y)

        Returns:
            피팅이 발생했으면 True, 아니면 False
        """
        if not self.is_drawing:
            return False

        self.raw_buffer.append(point)

        # 트리거 조건: N개 이상
        if len(self.raw_buffer) >= self.trigger_count:
            return self._try_fit_and_freeze()

        return False

    def end_drawing(self) -> bool:
        """
        드로잉 종료 및 최종 피팅

        Returns:
            피팅이 발생했으면 True
        """
        if not self.is_drawing:
            return False

        self.is_drawing = False

        # 남은 점들을 최종 피팅
        if len(self.raw_buffer) >= 2:
            self._finalize_remaining()
            return True

        return False

    def _try_fit_and_freeze(self) -> bool:
        """
        현재 raw_buffer를 피팅 시도하고, 성공하면 freeze

        Returns:
            피팅 성공 여부
        """
        if len(self.raw_buffer) < 2:
            return False

        # Schneider 알고리즘으로 피팅
        segments = self.fitter.fit(self.raw_buffer)

        # 피팅 성공 (항상 성공하지만, 오차 검증은 내부에서 이루어짐)
        # 여기서는 단순히 세그먼트가 생성되면 성공으로 간주

        # 세그먼트가 1개이고 오차가 작으면 "임시" 상태 유지
        # 세그먼트가 여러 개이면 일부를 freeze
        if len(segments) == 1:
            # 단일 세그먼트: 아직 확정하지 않고 임시 상태 유지
            # (다음 점이 추가되면 다시 피팅)
            return False
        else:
            # 여러 세그먼트: 마지막 세그먼트를 제외하고 freeze
            self._freeze_segments(segments[:-1])

            # 마지막 세그먼트에 해당하는 점들을 raw_buffer에 남김
            # (간단히 마지막 N개 점만 남김)
            keep_count = max(3, self.trigger_count // 2)
            self.raw_buffer = self.raw_buffer[-keep_count:]

            return True

    def _freeze_segments(self, segments: List[BezierSegment]):
        """
        세그먼트를 finalized_segments로 확정

        Args:
            segments: 확정할 세그먼트 리스트
        """
        self.finalized_segments.extend(segments)

    def _finalize_remaining(self):
        """
        남은 raw_buffer를 최종 피팅하여 finalized_segments로 이동
        """
        if len(self.raw_buffer) >= 2:
            segments = self.fitter.fit(self.raw_buffer)
            self.finalized_segments.extend(segments)
            self.raw_buffer = []

    def get_network_packet(self) -> Dict[str, Any]:
        """
        네트워크 전송용 패킷 생성

        Returns:
            {
                "finalized_segments": [...],  # BezierSegment 리스트
                "current_raw_points": [...],  # raw_buffer의 점들
            }
        """
        return {
            "finalized_segments": [seg.to_dict() for seg in self.finalized_segments],
            "current_raw_points": self.raw_buffer.copy(),
        }

    def get_delta_packet(self) -> Dict[str, Any]:
        """
        Delta Update용 패킷 생성 (변경된 부분만)

        Returns:
            {
                "new_finalized_segments": [...],  # 새로 추가된 세그먼트만
                "current_raw_points": [...],      # 전체 raw_buffer
            }
        """
        new_segments = self.finalized_segments[self._last_sent_finalized_count :]

        packet = {
            "new_finalized_segments": [seg.to_dict() for seg in new_segments],
            "current_raw_points": self.raw_buffer.copy(),
        }

        # 전송 상태 업데이트
        self._last_sent_finalized_count = len(self.finalized_segments)

        return packet

    def clear(self):
        """모든 상태 초기화"""
        self.raw_buffer = []
        self.finalized_segments = []
        self.is_drawing = False
        self._last_sent_finalized_count = 0

    # 상태 조회 메서드
    def get_finalized_count(self) -> int:
        """확정된 세그먼트 개수"""
        return len(self.finalized_segments)

    def get_raw_count(self) -> int:
        """raw_buffer의 점 개수"""
        return len(self.raw_buffer)

    def has_changes(self) -> bool:
        """전송해야 할 변경사항이 있는지 확인"""
        return (
            len(self.finalized_segments) > self._last_sent_finalized_count
            or len(self.raw_buffer) > 0
        )
