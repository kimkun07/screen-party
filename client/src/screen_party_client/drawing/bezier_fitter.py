"""
Schneider 알고리즘 기반 큐빅 베지어 커브 피팅

참고: GraphicsGems/FitCurves.c
https://github.com/erich666/GraphicsGems/blob/master/gems/FitCurves.c
"""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
from numpy.typing import NDArray


@dataclass
class BezierSegment:
    """큐빅 베지어 커브 세그먼트 (P0, P1, P2, P3)"""

    p0: Tuple[float, float]
    p1: Tuple[float, float]
    p2: Tuple[float, float]
    p3: Tuple[float, float]

    def to_dict(self):
        """네트워크 전송용 dict 변환"""
        return {
            "p0": self.p0,
            "p1": self.p1,
            "p2": self.p2,
            "p3": self.p3,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BezierSegment":
        """dict에서 BezierSegment 생성"""
        return cls(
            p0=tuple(data["p0"]),
            p1=tuple(data["p1"]),
            p2=tuple(data["p2"]),
            p3=tuple(data["p3"]),
        )

    def to_relative(self, width: float, height: float) -> "BezierSegment":
        """절대 좌표를 상대 좌표로 변환

        Args:
            width: 캔버스 너비
            height: 캔버스 높이

        Returns:
            상대 좌표 BezierSegment
        """
        return BezierSegment(
            p0=(self.p0[0] / width, self.p0[1] / height),
            p1=(self.p1[0] / width, self.p1[1] / height),
            p2=(self.p2[0] / width, self.p2[1] / height),
            p3=(self.p3[0] / width, self.p3[1] / height),
        )

    def to_absolute(self, width: float, height: float) -> "BezierSegment":
        """상대 좌표를 절대 좌표로 변환

        Args:
            width: 캔버스 너비
            height: 캔버스 높이

        Returns:
            절대 좌표 BezierSegment
        """
        return BezierSegment(
            p0=(self.p0[0] * width, self.p0[1] * height),
            p1=(self.p1[0] * width, self.p1[1] * height),
            p2=(self.p2[0] * width, self.p2[1] * height),
            p3=(self.p3[0] * width, self.p3[1] * height),
        )


class BezierFitter:
    """
    Schneider 알고리즘을 사용한 큐빅 베지어 커브 피팅

    주요 파라미터:
    - max_error: 허용 가능한 최대 오차 (픽셀 단위)
    - max_iterations: Newton-Raphson 최대 반복 횟수
    """

    def __init__(self, max_error: float = 4.0, max_iterations: int = 4):
        self.max_error = max_error
        self.max_iterations = max_iterations

    def fit(self, points: List[Tuple[float, float]]) -> List[BezierSegment]:
        """
        점들을 큐빅 베지어 커브로 피팅

        Args:
            points: 입력 점들 [(x, y), ...]

        Returns:
            베지어 세그먼트 리스트
        """
        if len(points) < 2:
            return []

        if len(points) == 2:
            # 2개 점은 직선으로 처리
            p0, p3 = points
            # 직선을 베지어 커브로 표현 (제어점을 1/3, 2/3 위치에)
            p1 = self._lerp(p0, p3, 1 / 3)
            p2 = self._lerp(p0, p3, 2 / 3)
            return [BezierSegment(p0, p1, p2, p3)]

        # numpy 배열로 변환
        pts = np.array(points, dtype=float)

        # 탄젠트 벡터 계산 (시작점과 끝점)
        left_tangent = self._compute_left_tangent(pts, 0)
        right_tangent = self._compute_right_tangent(pts, len(pts) - 1)

        # 재귀적으로 피팅
        return self._fit_cubic(pts, left_tangent, right_tangent)

    def _fit_cubic(
        self,
        points: NDArray,
        left_tangent: NDArray,
        right_tangent: NDArray,
    ) -> List[BezierSegment]:
        """
        재귀적으로 큐빅 베지어 커브 피팅 (Schneider 알고리즘 핵심)

        Args:
            points: 점들 배열
            left_tangent: 시작 탄젠트
            right_tangent: 끝 탄젠트

        Returns:
            베지어 세그먼트 리스트
        """
        n = len(points)

        # 기저 조건: 2개 점
        if n == 2:
            dist = np.linalg.norm(points[1] - points[0]) / 3.0
            p0 = tuple(points[0])
            p3 = tuple(points[-1])
            p1 = tuple(points[0] + left_tangent * dist)
            p2 = tuple(points[-1] + right_tangent * dist)
            return [BezierSegment(p0, p1, p2, p3)]

        # Chord length parameterization
        u = self._chord_length_parameterize(points)

        # Newton-Raphson으로 베지어 커브 생성 및 최적화
        bezier, max_error, split_point = self._generate_and_fit(
            points, u, left_tangent, right_tangent
        )

        # 오차가 허용 범위 내면 성공
        if max_error < self.max_error:
            return [bezier]

        # 오차가 크면 분할하여 재귀적으로 처리
        # 분할점이 너무 가까우면 강제로 중간에서 분할
        if split_point < 1:
            split_point = 1
        elif split_point >= n - 1:
            split_point = n - 2

        # 분할점에서 탄젠트 계산
        center_tangent = self._compute_center_tangent(points, split_point)

        # 왼쪽 부분 피팅
        left_segments = self._fit_cubic(
            points[: split_point + 1], left_tangent, center_tangent
        )

        # 오른쪽 부분 피팅
        right_segments = self._fit_cubic(
            points[split_point:], -center_tangent, right_tangent
        )

        return left_segments + right_segments

    def _generate_and_fit(
        self,
        points: NDArray,
        u: NDArray,
        left_tangent: NDArray,
        right_tangent: NDArray,
    ) -> Tuple[BezierSegment, float, int]:
        """
        베지어 커브 생성 및 Newton-Raphson으로 파라미터 최적화

        Returns:
            (베지어 세그먼트, 최대 오차, 최대 오차 발생 인덱스)
        """
        # 초기 베지어 커브 생성
        bezier = self._generate_bezier(points, u, left_tangent, right_tangent)

        # Newton-Raphson 반복
        for _ in range(self.max_iterations):
            max_error, split_point = self._compute_max_error(points, bezier, u)

            if max_error < self.max_error:
                break

            # 파라미터 재조정 (reparameterize)
            u_prime = self._reparameterize(points, bezier, u)

            # 새로운 베지어 커브 생성
            bezier = self._generate_bezier(points, u_prime, left_tangent, right_tangent)
            u = u_prime

        max_error, split_point = self._compute_max_error(points, bezier, u)
        return bezier, max_error, split_point

    def _generate_bezier(
        self,
        points: NDArray,
        u: NDArray,
        left_tangent: NDArray,
        right_tangent: NDArray,
    ) -> BezierSegment:
        """
        최소 제곱법으로 베지어 커브의 제어점 계산

        Args:
            points: 입력 점들
            u: 파라미터 값들 [0, 1]
            left_tangent: 시작 탄젠트
            right_tangent: 끝 탄젠트

        Returns:
            베지어 세그먼트
        """
        n = len(points)
        p0 = points[0]
        p3 = points[-1]

        # C 행렬 계산 (Bernstein basis functions)
        A = np.zeros((n, 2, 2))
        for i, ui in enumerate(u):
            b1 = 3 * (1 - ui) ** 2 * ui
            b2 = 3 * (1 - ui) * ui**2

            A[i, 0] = b1 * left_tangent
            A[i, 1] = b2 * right_tangent

        # 우변 계산
        tmp = points - (p0[:, np.newaxis] * self._b0(u) + p3[:, np.newaxis] * self._b3(u)).T

        # X, Y 좌표별로 최소 제곱법
        C = np.zeros((2, 2))
        X = np.zeros(2)

        for i in range(n):
            C[0, 0] += np.dot(A[i, 0], A[i, 0])
            C[0, 1] += np.dot(A[i, 0], A[i, 1])
            C[1, 0] = C[0, 1]
            C[1, 1] += np.dot(A[i, 1], A[i, 1])

            X[0] += np.dot(A[i, 0], tmp[i])
            X[1] += np.dot(A[i, 1], tmp[i])

        # 행렬식 계산
        det_C0_C1 = C[0, 0] * C[1, 1] - C[1, 0] * C[0, 1]

        # 특이 행렬 체크
        if abs(det_C0_C1) < 1e-10:
            # 특이 행렬이면 휴리스틱 사용
            dist = np.linalg.norm(p3 - p0) / 3.0
            p1 = p0 + left_tangent * dist
            p2 = p3 + right_tangent * dist
        else:
            # 제어점 계산
            alpha_l = (X[0] * C[1, 1] - X[1] * C[0, 1]) / det_C0_C1
            alpha_r = (C[0, 0] * X[1] - C[1, 0] * X[0]) / det_C0_C1

            # 음수 alpha 체크 (잘못된 방향)
            if alpha_l < 0 or alpha_r < 0:
                dist = np.linalg.norm(p3 - p0) / 3.0
                p1 = p0 + left_tangent * dist
                p2 = p3 + right_tangent * dist
            else:
                p1 = p0 + left_tangent * alpha_l
                p2 = p3 + right_tangent * alpha_r

        return BezierSegment(
            p0=tuple(p0),
            p1=tuple(p1),
            p2=tuple(p2),
            p3=tuple(p3),
        )

    def _reparameterize(
        self, points: NDArray, bezier: BezierSegment, u: NDArray
    ) -> NDArray:
        """
        Newton-Raphson으로 파라미터 재조정

        Args:
            points: 입력 점들
            bezier: 현재 베지어 커브
            u: 현재 파라미터 값들

        Returns:
            새로운 파라미터 값들
        """
        u_prime = np.zeros_like(u)

        for i, (pt, ui) in enumerate(zip(points, u)):
            # Q(u) - P
            qu = self._bezier_point(bezier, ui)
            diff = qu - pt

            # Q'(u)
            q1 = self._bezier_derivative1(bezier, ui)

            # Q''(u)
            q2 = self._bezier_derivative2(bezier, ui)

            # Newton-Raphson: u' = u - (Q(u)-P)·Q'(u) / (Q'(u)·Q'(u) + (Q(u)-P)·Q''(u))
            numerator = np.dot(diff, q1)
            denominator = np.dot(q1, q1) + np.dot(diff, q2)

            if abs(denominator) > 1e-10:
                u_prime[i] = ui - numerator / denominator
            else:
                u_prime[i] = ui

            # [0, 1] 범위로 클램핑
            u_prime[i] = np.clip(u_prime[i], 0.0, 1.0)

        return u_prime

    def _compute_max_error(
        self, points: NDArray, bezier: BezierSegment, u: NDArray
    ) -> Tuple[float, int]:
        """
        베지어 커브와 점들 사이의 최대 오차 계산

        Returns:
            (최대 오차, 최대 오차 발생 인덱스)
        """
        max_dist = 0.0
        split_point = len(points) // 2

        for i, (pt, ui) in enumerate(zip(points, u)):
            qu = self._bezier_point(bezier, ui)
            dist = np.linalg.norm(qu - pt)

            if dist > max_dist:
                max_dist = dist
                split_point = i

        return max_dist, split_point

    def _chord_length_parameterize(self, points: NDArray) -> NDArray:
        """
        Chord length parameterization으로 초기 u 값 계산

        Args:
            points: 입력 점들

        Returns:
            파라미터 값들 [0, 1]
        """
        n = len(points)
        u = np.zeros(n)

        # 누적 거리 계산
        for i in range(1, n):
            u[i] = u[i - 1] + np.linalg.norm(points[i] - points[i - 1])

        # [0, 1]로 정규화
        if u[-1] > 0:
            u /= u[-1]

        return u

    def _bezier_point(self, bezier: BezierSegment, t: float) -> NDArray:
        """베지어 커브 위의 점 계산 Q(t)"""
        p0 = np.array(bezier.p0)
        p1 = np.array(bezier.p1)
        p2 = np.array(bezier.p2)
        p3 = np.array(bezier.p3)

        return (
            self._b0(t) * p0
            + self._b1(t) * p1
            + self._b2(t) * p2
            + self._b3(t) * p3
        )

    def _bezier_derivative1(self, bezier: BezierSegment, t: float) -> NDArray:
        """베지어 커브의 1차 미분 Q'(t)"""
        p0 = np.array(bezier.p0)
        p1 = np.array(bezier.p1)
        p2 = np.array(bezier.p2)
        p3 = np.array(bezier.p3)

        return (
            self._b0_prime(t) * p0
            + self._b1_prime(t) * p1
            + self._b2_prime(t) * p2
            + self._b3_prime(t) * p3
        )

    def _bezier_derivative2(self, bezier: BezierSegment, t: float) -> NDArray:
        """베지어 커브의 2차 미분 Q''(t)"""
        p0 = np.array(bezier.p0)
        p1 = np.array(bezier.p1)
        p2 = np.array(bezier.p2)
        p3 = np.array(bezier.p3)

        return (
            self._b0_double_prime(t) * p0
            + self._b1_double_prime(t) * p1
            + self._b2_double_prime(t) * p2
            + self._b3_double_prime(t) * p3
        )

    # Bernstein basis functions (3차)
    def _b0(self, t):
        """B0(t) = (1-t)^3"""
        return (1 - t) ** 3

    def _b1(self, t):
        """B1(t) = 3(1-t)^2 * t"""
        return 3 * (1 - t) ** 2 * t

    def _b2(self, t):
        """B2(t) = 3(1-t) * t^2"""
        return 3 * (1 - t) * t**2

    def _b3(self, t):
        """B3(t) = t^3"""
        return t**3

    # Bernstein basis 1차 미분
    def _b0_prime(self, t):
        """B0'(t) = -3(1-t)^2"""
        return -3 * (1 - t) ** 2

    def _b1_prime(self, t):
        """B1'(t) = 3(1-t)^2 - 6(1-t)t"""
        return 3 * (1 - t) ** 2 - 6 * (1 - t) * t

    def _b2_prime(self, t):
        """B2'(t) = 6(1-t)t - 3t^2"""
        return 6 * (1 - t) * t - 3 * t**2

    def _b3_prime(self, t):
        """B3'(t) = 3t^2"""
        return 3 * t**2

    # Bernstein basis 2차 미분
    def _b0_double_prime(self, t):
        """B0''(t) = 6(1-t)"""
        return 6 * (1 - t)

    def _b1_double_prime(self, t):
        """B1''(t) = -12(1-t) + 6t"""
        return -12 * (1 - t) + 6 * t

    def _b2_double_prime(self, t):
        """B2''(t) = 6(1-t) - 12t"""
        return 6 * (1 - t) - 12 * t

    def _b3_double_prime(self, t):
        """B3''(t) = 6t"""
        return 6 * t

    def _compute_left_tangent(self, points: NDArray, index: int) -> NDArray:
        """왼쪽 탄젠트 계산 (정규화)"""
        tangent = points[index + 1] - points[index]
        norm = np.linalg.norm(tangent)
        if norm > 0:
            return tangent / norm
        return tangent

    def _compute_right_tangent(self, points: NDArray, index: int) -> NDArray:
        """오른쪽 탄젠트 계산 (정규화)"""
        tangent = points[index - 1] - points[index]
        norm = np.linalg.norm(tangent)
        if norm > 0:
            return tangent / norm
        return tangent

    def _compute_center_tangent(self, points: NDArray, index: int) -> NDArray:
        """중심 탄젠트 계산 (정규화)"""
        tangent = points[index - 1] - points[index + 1]
        norm = np.linalg.norm(tangent)
        if norm > 0:
            return tangent / norm
        return tangent

    @staticmethod
    def _lerp(p0: Tuple[float, float], p1: Tuple[float, float], t: float) -> Tuple[float, float]:
        """선형 보간"""
        return (
            p0[0] + (p1[0] - p0[0]) * t,
            p0[1] + (p1[1] - p0[1]) * t,
        )
