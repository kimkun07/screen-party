"""
드로잉 라인 데이터 관리

각 사용자의 드로잉을 line_id별로 관리합니다.
"""

from typing import List, Tuple
from dataclasses import dataclass, field
from PyQt6.QtGui import QColor

from .bezier_fitter import BezierSegment


@dataclass
class LineData:
    """
    단일 드로잉 라인 데이터

    Attributes:
        line_id: 라인 고유 ID
        user_id: 그린 사용자 ID
        color: 라인 색상
        finalized_segments: 확정된 베지어 세그먼트
        current_raw_points: 아직 확정되지 않은 raw 점들
        is_complete: 드로잉 완료 여부 (마우스 up)
    """

    line_id: str
    user_id: str
    color: QColor
    finalized_segments: List[BezierSegment] = field(default_factory=list)
    current_raw_points: List[Tuple[float, float]] = field(default_factory=list)
    is_complete: bool = False

    def add_finalized_segments(self, segments: List[BezierSegment]):
        """확정된 세그먼트 추가"""
        self.finalized_segments.extend(segments)

    def update_raw_points(self, points: List[Tuple[float, float]]):
        """raw 점들 업데이트"""
        self.current_raw_points = points.copy()

    def finalize(self):
        """드로잉 완료 (raw points 제거)"""
        self.is_complete = True
        self.current_raw_points = []

    def clear(self):
        """모든 데이터 초기화"""
        self.finalized_segments = []
        self.current_raw_points = []
        self.is_complete = False
