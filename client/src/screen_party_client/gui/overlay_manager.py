"""오버레이 관리 (생성/삭제/크기조정/그리기모드) 관련 메서드"""

import logging
from typing import TYPE_CHECKING

from .constants import get_default_pen_color

if TYPE_CHECKING:
    from .main_window import MainWindow

logger = logging.getLogger(__name__)


class OverlayManager:
    """오버레이 관리 로직을 담당하는 헬퍼 클래스"""

    def __init__(self, window: "MainWindow"):
        self.window = window

    def toggle_overlay(self):
        """그림 영역 생성 (버튼에서 호출)"""
        self.create_overlay()

    def create_overlay(self):
        """그림 영역 생성 (비즈니스 로직만, UI 업데이트는 state를 통해)"""
        from .overlay_window import OverlayWindow

        try:
            # 오버레이 윈도우 생성
            overlay_window = OverlayWindow(
                user_id=self.window.state.user_id,
                pen_color=get_default_pen_color(),  # 첫 번째 프리셋 색상 (파스텔 핑크)
            )

            # Canvas Manager에 오버레이 캔버스 등록
            canvas = overlay_window.get_canvas()
            self.window.canvas_manager.set_overlay_canvas(canvas)

            # DrawingCanvas 시그널 연결
            self.window.drawing_handler._connect_drawing_signals(canvas)

            # 오버레이 시그널 연결
            overlay_window.drawing_mode_changed.connect(
                self.on_drawing_mode_changed)
            overlay_window.resize_mode_changed.connect(
                self.on_resize_mode_changed)

            # State에 오버레이 설정 (이것만이 UI를 업데이트함)
            self.window.state.set_overlay(overlay_window)
            self.window.state.set_status("그림 영역이 생성되었습니다. 크기를 조정하세요.")

            # 창 표시
            overlay_window.show()

            # 리사이즈 모드 활성화 (overlay_window에 직접 설정)
            overlay_window.set_resize_mode(True)

            logger.info("Overlay created and resize mode enabled")

        except Exception as e:
            logger.error(f"Failed to create overlay: {e}", exc_info=True)
            self.window.state.set_status(f"오류: 그림 영역 생성 실패: {e}")
            self.stop_overlay()

    def stop_overlay(self):
        """그림 영역 삭제 (비즈니스 로직만, UI 업데이트는 state를 통해)"""
        if self.window.state.overlay_window:
            try:
                self.window.state.overlay_window.close()
            except Exception as e:
                logger.error(f"Error closing overlay: {e}")

        # Canvas Manager에서 오버레이 제거
        self.window.canvas_manager.set_overlay_canvas(None)

        # State에서 오버레이 제거 (이것만이 UI를 업데이트함)
        self.window.state.clear_overlay()
        self.window.state.set_status("그림 영역이 삭제되었습니다")

        logger.info("Overlay stopped")

    def toggle_resize_mode(self):
        """그림 영역 크기 조정 토글 (비즈니스 로직만, UI 업데이트는 state를 통해)"""
        if self.window.state.overlay_window:
            current = self.window.state.overlay_window.is_resize_mode()
            new_mode = not current

            # overlay_window에 직접 설정
            # This will emit resize_mode_changed signal, which will call on_resize_mode_changed
            self.window.state.overlay_window.set_resize_mode(new_mode)

    def toggle_drawing_mode(self):
        """그리기 모드 토글 (비즈니스 로직만, UI 업데이트는 state를 통해)"""
        if self.window.state.overlay_window:
            current = self.window.state.overlay_window.is_drawing_enabled()
            new_mode = not current

            # overlay_window에 직접 설정
            self.window.state.overlay_window.set_drawing_enabled(new_mode)

    def on_resize_mode_changed(self, enabled: bool):
        """리사이즈 모드 변경 핸들러 (overlay_window에서 시그널로 호출됨)

        비즈니스 로직만 처리하고, UI 업데이트는 state를 통해 수행합니다.
        """
        # State 업데이트 (이것만이 UI를 업데이트함)
        self.window.state.set_resize_mode(enabled)

        # 상태 메시지 업데이트
        if enabled:
            self.window.state.set_status("크기 조정 모드: 창 테두리를 드래그하여 조정하세요 (Enter로 완료)")
            logger.info("Resize mode enabled")
        else:
            self.window.state.set_status("그림 영역 준비 완료. 그리기 활성화 버튼을 누르세요")
            logger.info("Resize mode disabled")

    def on_drawing_mode_changed(self, enabled: bool):
        """그리기 모드 변경 핸들러 (overlay_window에서 시그널로 호출됨)

        비즈니스 로직만 처리하고, UI 업데이트는 state를 통해 수행합니다.
        """
        # State 업데이트 (이것만이 UI를 업데이트함)
        self.window.state.set_drawing_mode(enabled)

        # 상태 메시지 업데이트
        if enabled:
            self.window.state.set_status("그리기 활성화됨 (ESC 키로 비활성화 가능)")
            logger.info("Drawing mode enabled")
        else:
            self.window.state.set_status("그리기 비활성화됨 (클릭이 아래로 전달됨)")
            logger.info("Drawing mode disabled")

    def clear_overlay_drawings(self):
        """그림 모두 지우기"""
        if self.window.state.overlay_window:
            self.window.canvas_manager.clear_all_drawings()
            self.window.state.set_status("모든 그림이 지워졌습니다")
            logger.info("All drawings cleared")
