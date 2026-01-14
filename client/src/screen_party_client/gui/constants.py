"""GUI 상수 정의"""

from PyQt6.QtGui import QColor


# 프리셋 색상 팔레트 (파스텔 톤)
PRESET_COLORS = [
    QColor(255, 182, 193),  # 파스텔 핑크
    QColor(173, 216, 230),  # 파스텔 블루
    QColor(152, 251, 152),  # 파스텔 그린
    QColor(193, 182, 255),  # 파스텔 퍼플
    QColor(255, 210, 182),  # 파스텔 오렌지
    QColor(255, 243, 182),  # 파스텔 옐로우
]


def get_default_pen_color() -> QColor:
    """기본 펜 색상 반환 (첫 번째 프리셋)"""
    return PRESET_COLORS[0]
