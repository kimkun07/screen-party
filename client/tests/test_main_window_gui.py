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

        # 연결 상태 확인
        assert not window.is_connected
        assert window.session_id is None
        assert window.user_id is None
        assert not window.is_host

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

        # Mock 세션 데이터 설정
        window.session_id = "ABC123"
        window.is_connected = True
        server_url = "ws://example.com:8765"
        window.server_input.setText(server_url)

        # 메인 화면 표시
        window.show_main_screen()

        # 메인 화면이 표시되고 시작 화면은 숨겨져 있어야 함
        assert window.main_widget.isVisible()
        assert not window.start_widget.isVisible()

        # 서버 주소와 세션 번호가 표시되어야 함
        assert window.server_info_label.text() == f"서버 주소: {server_url}"
        assert window.session_info_label.text() == f"세션 번호: ABC123"

    def test_copy_server_address(self, qtbot):
        """서버 주소 클립보드 복사 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)

        # 서버 주소 설정
        server_url = "ws://test.example.com:8888"
        window.server_input.setText(server_url)
        window.is_connected = True
        window.show_main_screen()

        # 복사 버튼 클릭
        qtbot.mouseClick(window.copy_server_button, Qt.MouseButton.LeftButton)

        # 클립보드 확인
        clipboard = QApplication.clipboard()
        assert clipboard.text() == server_url

        # 상태 메시지 확인
        assert "클립보드에 복사" in window.status_label.text()

    def test_copy_session_id(self, qtbot):
        """세션 번호 클립보드 복사 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)

        # Mock 세션 데이터 설정
        window.session_id = "XYZ789"
        window.is_connected = True
        window.show_main_screen()

        # 복사 버튼 클릭
        qtbot.mouseClick(window.copy_session_button, Qt.MouseButton.LeftButton)

        # 클립보드 확인
        clipboard = QApplication.clipboard()
        assert clipboard.text() == "XYZ789"

        # 상태 메시지 확인
        assert "클립보드에 복사" in window.status_label.text()


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
        window.is_connected = True
        window.session_id = "ABC123"
        window.show_main_screen()

        status_message = "게스트가 참여했습니다"
        window.set_status(status_message)

        assert window.status_label.text() == status_message

    def test_set_status_when_not_connected(self, qtbot):
        """미연결 상태일 때 메인 화면 상태 메시지 설정 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)

        # 미연결 상태
        assert not window.is_connected

        status_message = "이 메시지는 표시되지 않아야 함"
        window.set_status(status_message)

        # is_connected=False이므로 status_label에 텍스트가 설정되지 않음
        assert window.status_label.text() == ""


class TestScreenTransition:
    """화면 전환 테스트"""

    def test_show_start_screen(self, qtbot):
        """시작 화면 표시 테스트"""
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()  # 윈도우 표시

        # Mock 데이터 설정
        window.session_id = "TEST01"

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
        window.server_input.setText(server_url)
        window.session_id = session_id

        # 메인 화면 표시
        window.show_main_screen()

        # 레이블 업데이트 확인
        assert server_url in window.server_info_label.text()
        assert session_id in window.session_info_label.text()
