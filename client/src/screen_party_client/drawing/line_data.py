"""
드로잉 라인 데이터 관리

각 사용자의 드로잉을 line_id별로 관리합니다.
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass, field
import time
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
        alpha: 투명도 (0.0 ~ 1.0, 페이드아웃용)
        initial_alpha: 초기 투명도 (페이드아웃 시 기준값)
        end_time: 드로잉 종료 시각 (time.time(), None이면 아직 그리는 중)
        last_update_time: 마지막 업데이트 시각 (타임아웃 감지용)
    """

    line_id: str
    user_id: str
    color: QColor
    finalized_segments: List[BezierSegment] = field(default_factory=list)
    current_raw_points: List[Tuple[float, float]] = field(default_factory=list)
    is_complete: bool = False
    alpha: float = 1.0
    initial_alpha: float = 1.0  # 초기 alpha 값 저장
    end_time: Optional[float] = None
    last_update_time: float = field(default_factory=time.time)

    def add_finalized_segments(self, segments: List[BezierSegment]):
        """확정된 세그먼트 추가"""
        self.finalized_segments.extend(segments)
        self.last_update_time = time.time()

    def update_raw_points(self, points: List[Tuple[float, float]]):
        """raw 점들 업데이트"""
        self.current_raw_points = points.copy()
        self.last_update_time = time.time()

    def finalize(self):
        """드로잉 완료 (raw points 제거)"""
        self.is_complete = True
        self.current_raw_points = []
        self.end_time = time.time()

    def clear(self):
        """모든 데이터 초기화"""
        self.finalized_segments = []
        self.current_raw_points = []
        self.is_complete = False
        self.alpha = 1.0
        self.initial_alpha = 1.0
        self.end_time = None
        self.last_update_time = time.time()
