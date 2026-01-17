"""MainWindow GUI 테스트 (pytest-qt 사용)"""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from screen_party_client.gui.main_window import MainWindow

# GUI 테스트 마커 추가
pytestmark = pytest.mark.gui


@pytest.fixture
def app(qapp):
    """QApplication fixture (pytest-qt 제공)"""
    return qapp


class TestStartScreen:
    """시작 화면 테스트"""

    def test_initial_state(self, qtbot):
        """초기 상태 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()  # 윈도우 표시

        # 시작 화면이 표시되고 메인 화면은 숨겨져 있어야 함
        assert window.start_widget.isVisible()
        assert not window.main_widget.isVisible()

        # 연결 상태 확인 (AppState 사용)
        assert not window.state.is_connected
        assert window.state.session_id is None
        assert window.state.user_id is None

    def test_server_input_default_value(self, qtbot):
        """서버 주소 입력 필드 기본값 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)

        # 기본값 확인 (로컬 저장소에서 불러온 값 또는 빈 칸)
        # 저장된 값이 없으면 빈 칸이어야 함
        assert isinstance(window.server_input.text(), str)
        assert window.server_input.placeholderText() == "ws://localhost:8765"

    def test_server_input_custom_value(self, qtbot):
        """서버 주소 입력 필드 커스텀 값 테스트"""
        custom_url = "ws://192.168.1.100:9000"
        window = MainWindow()
        qtbot.addWidget(window)

        # 커스텀 값 설정
        window.server_input.setText(custom_url)

        # 커스텀 값 확인
        assert window.server_input.text() == custom_url

    def test_session_input_enables_join_button(self, qtbot):
        """세션 번호 입력 시 접속 버튼 활성화 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)

        # 초기 상태: 접속 버튼 비활성화
        assert not window.join_button.isEnabled()

        # 세션 번호 입력
        qtbot.keyClicks(window.session_input, "ABC123")

        # 접속 버튼 활성화됨
        assert window.join_button.isEnabled()
        assert window.session_input.text() == "ABC123"

    def test_session_input_empty_disables_join_button(self, qtbot):
        """세션 번호 입력을 지우면 접속 버튼 비활성화 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)

        # 세션 번호 입력
        qtbot.keyClicks(window.session_input, "ABC123")
        assert window.join_button.isEnabled()

        # 입력 지우기
        window.session_input.clear()

        # 접속 버튼 비활성화됨
        assert not window.join_button.isEnabled()

    def test_create_button_enabled_by_default(self, qtbot):
        """세션 생성 버튼은 기본적으로 활성화 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)

        assert window.create_button.isEnabled()


class TestMainScreen:
    """메인 화면 테스트"""

    def test_show_main_screen(self, qtbot):
        """메인 화면 표시 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()  # 윈도우 표시

        # Mock 세션 데이터 설정 (AppState 사용)
        server_url = "ws://example.com:8765"
        window.state.set_connected("ABC123", "user-001", server_url)

        # 메인 화면 표시
        window.show_main_screen()

        # 메인 화면이 표시되고 시작 화면은 숨겨져 있어야 함
        assert window.main_scroll.isVisible()
        assert not window.start_scroll.isVisible()

        # 서버 주소와 세션 번호가 표시되어야 함
        assert window.server_info_label.text() == f"서버 주소: {server_url}"
        assert window.session_info_label.text() == "세션 번호: ABC123"

    def test_copy_server_address(self, qtbot):
        """서버 주소 클립보드 복사 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)

        # 서버 주소 설정 (AppState 사용)
        server_url = "ws://test.example.com:8888"
        window.server_input.setText(server_url)
        window.state.is_connected = True
        window.show_main_screen()

        # 복사 버튼 클릭
        qtbot.mouseClick(window.copy_server_button, Qt.MouseButton.LeftButton)

        # 클립보드 확인
        clipboard = QApplication.clipboard()
        assert clipboard.text() == server_url

        # 상태 메시지 확인
        assert "클립보드에 복사" in window.state.status_message

    def test_copy_session_id(self, qtbot):
        """세션 번호 클립보드 복사 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)

        # Mock 세션 데이터 설정
        window.state.session_id = "XYZ789"
        window.state.is_connected = True
        window.show_main_screen()

        # 복사 버튼 클릭
        qtbot.mouseClick(window.copy_session_button, Qt.MouseButton.LeftButton)

        # 클립보드 확인
        clipboard = QApplication.clipboard()
        assert clipboard.text() == "XYZ789"

        # 상태 메시지 확인
        assert "클립보드에 복사" in window.state.status_message


class TestUIState:
    """UI 상태 관리 테스트"""

    def test_disable_start_buttons(self, qtbot):
        """시작 화면 버튼 비활성화 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)

        # 세션 번호 입력 (접속 버튼 활성화)
        qtbot.keyClicks(window.session_input, "ABC123")
        assert window.join_button.isEnabled()

        # 버튼 비활성화
        window.disable_start_buttons()

        # 모든 버튼과 입력 필드가 비활성화되어야 함
        assert not window.create_button.isEnabled()
        assert not window.join_button.isEnabled()
        assert not window.server_input.isEnabled()
        assert not window.session_input.isEnabled()

    def test_enable_start_buttons(self, qtbot):
        """시작 화면 버튼 활성화 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)

        # 버튼 비활성화
        window.disable_start_buttons()

        # 세션 번호 입력 (비활성화 상태에서는 입력 불가능하지만 프로그래밍 방식으로 설정)
        window.session_input.setText("ABC123")

        # 버튼 활성화
        window.enable_start_buttons()

        # 버튼과 입력 필드가 활성화되어야 함
        assert window.create_button.isEnabled()
        assert window.join_button.isEnabled()  # 세션 번호가 있으므로 활성화
        assert window.server_input.isEnabled()
        assert window.session_input.isEnabled()

    def test_enable_start_buttons_without_session(self, qtbot):
        """세션 번호 없이 버튼 활성화 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)

        # 버튼 비활성화
        window.disable_start_buttons()

        # 버튼 활성화 (세션 번호 없음)
        window.enable_start_buttons()

        # 세션 생성 버튼은 활성화, 접속 버튼은 비활성화
        assert window.create_button.isEnabled()
        assert not window.join_button.isEnabled()  # 세션 번호가 없으므로 비활성화


class TestStatusMessages:
    """상태 메시지 테스트"""

    def test_set_start_status(self, qtbot):
        """시작 화면 상태 메시지 설정 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)

        status_message = "서버에 연결 중..."
        window.set_start_status(status_message)

        assert window.start_status_label.text() == status_message

    def test_set_status_when_connected(self, qtbot):
        """연결 상태일 때 메인 화면 상태 메시지 설정 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)

        # 연결 상태 설정
        window.state.set_connected("ABC123", "user-001", "ws://example.com:8765")
        window.show_main_screen()

        status_message = "게스트가 참여했습니다"
        window.state.set_status(status_message)

        # 상태가 연결된 상태이므로 status_label에 메시지가 표시됨
        assert window.status_label.text() == status_message

    def test_set_status_when_not_connected(self, qtbot):
        """미연결 상태일 때 메인 화면 상태 메시지 설정 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)

        # 미연결 상태 확인
        assert not window.state.is_connected

        status_message = "이 메시지는 표시되지 않아야 함"
        window.state.set_status(status_message)

        # is_connected=False이므로 상태 메시지는 업데이트되지만 status_label에는 표시되지 않음
        # (observer가 is_connected일 때만 표시함)
        assert window.status_label.text() == ""


class TestScreenTransition:
    """화면 전환 테스트"""

    def test_show_start_screen(self, qtbot):
        """시작 화면 표시 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()  # 윈도우 표시

        # Mock 데이터 설정
        window.state.session_id = "TEST01"

        # 메인 화면을 먼저 표시
        window.show_main_screen()
        assert window.main_widget.isVisible()

        # 다시 시작 화면으로 전환
        window.show_start_screen()

        assert window.start_widget.isVisible()
        assert not window.main_widget.isVisible()

    def test_show_main_screen_updates_labels(self, qtbot):
        """메인 화면 표시 시 레이블 업데이트 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)

        # Mock 데이터 설정
        server_url = "ws://custom.server.com:9999"
        session_id = "TEST01"
        window.state.set_connected(session_id, "user-001", server_url)

        # 메인 화면 표시
        window.show_main_screen()

        # 레이블 업데이트 확인
        assert server_url in window.server_info_label.text()
        assert session_id in window.session_info_label.text()


class TestColorSystem:
    """색상 설정 시스템 테스트"""

    def test_color_buttons_exist(self, qtbot):
        """색상 버튼이 생성되었는지 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)
        window.show_main_screen()

        # 6개의 색상 버튼이 있어야 함
        assert len(window.color_buttons) == 6

    def test_alpha_slider_initial_value(self, qtbot):
        """투명도 슬라이더 초기값 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)
        window.show_main_screen()

        # 초기값은 100 (100% 불투명)
        assert window.alpha_slider.value() == 100

    def test_set_pen_color_red(self, qtbot):
        """핑크 색상 버튼 클릭 테스트 (파스텔 핑크)"""

        window = MainWindow()
        qtbot.addWidget(window)
        window.state.set_connected("TEST01", "user-001", "ws://localhost:8765")
        window.show_main_screen()

        # DrawingCanvas user_id 설정
        window.canvas_manager.main_canvas.set_user_id("user-001")

        # 핑크 버튼 클릭 (첫 번째 버튼)
        qtbot.mouseClick(window.color_buttons[0], Qt.MouseButton.LeftButton)

        # DrawingCanvas의 pen_color가 파스텔 핑크로 변경되었는지 확인
        canvas_color = window.canvas_manager.main_canvas.pen_color
        assert canvas_color.red() == 255
        assert canvas_color.green() == 182
        assert canvas_color.blue() == 193

    def test_set_pen_color_blue(self, qtbot):
        """블루 색상 버튼 클릭 테스트 (파스텔 블루)"""

        window = MainWindow()
        qtbot.addWidget(window)
        window.state.set_connected("TEST01", "user-001", "ws://localhost:8765")
        window.show_main_screen()

        window.canvas_manager.main_canvas.set_user_id("user-001")

        # 블루 버튼 클릭 (두 번째 버튼)
        qtbot.mouseClick(window.color_buttons[1], Qt.MouseButton.LeftButton)

        canvas_color = window.canvas_manager.main_canvas.pen_color
        assert canvas_color.red() == 173
        assert canvas_color.green() == 216
        assert canvas_color.blue() == 230

    def test_alpha_slider_change(self, qtbot):
        """투명도 슬라이더 변경 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)
        window.state.set_connected("TEST01", "user-001", "ws://localhost:8765")
        window.show_main_screen()

        window.canvas_manager.main_canvas.set_user_id("user-001")

        # 슬라이더를 50%로 변경
        window.alpha_slider.setValue(50)

        # DrawingCanvas의 pen_alpha가 0.5로 변경되었는지 확인
        assert window.canvas_manager.main_canvas.pen_alpha == pytest.approx(0.5, rel=0.01)

    def test_alpha_slider_zero(self, qtbot):
        """투명도 슬라이더를 0으로 변경 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)
        window.state.set_connected("TEST01", "user-001", "ws://localhost:8765")
        window.show_main_screen()

        window.canvas_manager.main_canvas.set_user_id("user-001")

        # 슬라이더를 0%로 변경
        window.alpha_slider.setValue(0)

        # DrawingCanvas의 pen_alpha가 0.0으로 변경되었는지 확인
        assert window.canvas_manager.main_canvas.pen_alpha == pytest.approx(0.0, rel=0.01)

    def test_alpha_slider_full(self, qtbot):
        """투명도 슬라이더를 100으로 변경 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)
        window.state.set_connected("TEST01", "user-001", "ws://localhost:8765")
        window.show_main_screen()

        window.canvas_manager.main_canvas.set_user_id("user-001")

        # 슬라이더를 100%로 변경
        window.alpha_slider.setValue(100)

        # DrawingCanvas의 pen_alpha가 1.0으로 변경되었는지 확인
        assert window.canvas_manager.main_canvas.pen_alpha == pytest.approx(1.0, rel=0.01)

    def test_multiple_color_changes(self, qtbot):
        """여러 번 색상 변경 테스트 (파스텔 톤)"""

        window = MainWindow()
        qtbot.addWidget(window)
        window.state.set_connected("TEST01", "user-001", "ws://localhost:8765")
        window.show_main_screen()

        window.canvas_manager.main_canvas.set_user_id("user-001")

        # 초기 색상: 파스텔 핑크 (첫 번째 프리셋)
        initial_color = window.canvas_manager.main_canvas.pen_color
        assert initial_color.red() == 255
        assert initial_color.green() == 182
        assert initial_color.blue() == 193

        # 파스텔 블루로 변경
        qtbot.mouseClick(window.color_buttons[1], Qt.MouseButton.LeftButton)
        assert window.canvas_manager.main_canvas.pen_color.red() == 173
        assert window.canvas_manager.main_canvas.pen_color.green() == 216
        assert window.canvas_manager.main_canvas.pen_color.blue() == 230

        # 파스텔 그린으로 변경
        qtbot.mouseClick(window.color_buttons[2], Qt.MouseButton.LeftButton)
        assert window.canvas_manager.main_canvas.pen_color.red() == 152
        assert window.canvas_manager.main_canvas.pen_color.green() == 251
        assert window.canvas_manager.main_canvas.pen_color.blue() == 152

        # 파스텔 오렌지로 변경
        qtbot.mouseClick(window.color_buttons[4], Qt.MouseButton.LeftButton)
        assert window.canvas_manager.main_canvas.pen_color.red() == 255
        assert window.canvas_manager.main_canvas.pen_color.green() == 210
        assert window.canvas_manager.main_canvas.pen_color.blue() == 182

    def test_user_color_change_no_duplication(self, qtbot):
        """사용자 색상 변경 시 참여자 중복 버그 테스트

        시나리오:
        1. User A가 접속 (초기 색상: 파스텔 핑크)
        2. User A가 색상 변경 (파스텔 블루로)
        3. User B 입장에서 A는 1명이어야 함 (중복되지 않음)
        """
        from PyQt6.QtGui import QColor

        window = MainWindow()
        qtbot.addWidget(window)
        window.state.set_connected("TEST01", "user-bob", "ws://localhost:8765")
        window.show_main_screen()

        window.canvas_manager.main_canvas.set_user_id("user-bob")

        # User A가 접속 (초기 색상: 파스텔 핑크)
        user_a_id = "user-alice"
        initial_color = QColor(255, 182, 193)  # 파스텔 핑크

        # 현재 사용자(user-bob)의 색상 추가 (자신은 핑크로 시작)
        window.state.user_colors[window.state.user_id] = initial_color
        window.canvas_manager.main_canvas.user_colors[window.state.user_id] = initial_color
        window.canvas_manager.main_canvas.user_alphas[window.state.user_id] = 1.0

        # User A가 접속 (초기 색상: 파스텔 핑크)
        # State와 Canvas 모두에 색상 정보 추가
        window.state.user_colors[user_a_id] = initial_color
        window.canvas_manager.main_canvas.user_colors[user_a_id] = initial_color
        window.canvas_manager.main_canvas.user_alphas[user_a_id] = 1.0
        window.update_users_colors_display()

        # 초기 상태: state.user_colors에 2명 (나 + User A)
        assert len(window.state.user_colors) == 2
        assert user_a_id in window.state.user_colors
        assert window.state.user_id in window.state.user_colors

        # User A가 색상 변경 (파스텔 블루로)
        new_color = QColor(173, 216, 230)  # 파스텔 블루
        # State와 Canvas 모두에 새 색상 설정
        window.state.user_colors[user_a_id] = new_color
        window.canvas_manager.main_canvas.user_colors[user_a_id] = new_color
        window.canvas_manager.main_canvas.user_alphas[user_a_id] = 0.8
        window.update_users_colors_display()

        # 색상 변경 후: state.user_colors에 여전히 2명 (중복 없음)
        assert len(window.state.user_colors) == 2
        assert user_a_id in window.state.user_colors
        assert window.state.user_colors[user_a_id] == new_color
        assert window.canvas_manager.main_canvas.user_alphas[user_a_id] == 0.8

        # 참여자 라벨 텍스트 확인
        label_text = window.users_colors_label.text()
        # User A의 user_id는 한 번만 나타나야 함
        assert label_text.count(user_a_id[:8]) == 1
