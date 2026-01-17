"""UI 생성 관련 메서드"""

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QLabel, QHBoxLayout, QLineEdit,
    QGroupBox, QSlider, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from .constants import PRESET_COLORS, get_default_pen_color
from ..drawing import DrawingCanvas

if TYPE_CHECKING:
    from .main_window import MainWindow


class UIBuilder:
    """UI 생성 로직을 담당하는 헬퍼 클래스"""

    def __init__(self, window: "MainWindow"):
        self.window = window

    def create_start_screen(self):
        """시작 화면 생성"""
        # 스크롤 영역 생성
        self.window.start_scroll = QScrollArea()
        self.window.start_scroll.setWidgetResizable(True)
        self.window.start_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.window.start_widget = QWidget()
        start_layout = QVBoxLayout()
        start_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.window.start_widget.setLayout(start_layout)

        # Title
        title = QLabel("Screen Party")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        start_layout.addWidget(title)

        start_layout.addSpacing(40)

        # 서버 주소 입력
        server_label = QLabel("서버 주소:")
        start_layout.addWidget(server_label)
        self.window.server_input = QLineEdit()
        # QSettings에서 저장된 서버 주소 불러오기
        saved_server = self.window.settings.value("server_url", "")
        self.window.server_input.setText(saved_server)
        self.window.server_input.setPlaceholderText("ws://localhost:8765")
        start_layout.addWidget(self.window.server_input)

        start_layout.addSpacing(20)

        # 세션 생성 / 세션 참여 (두 column 배치, 1:1 비율)
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)

        # 세션 생성 column (왼쪽)
        self._create_session_column(columns_layout)

        # 세션 참여 column (오른쪽)
        self._create_join_column(columns_layout)

        start_layout.addLayout(columns_layout)

        start_layout.addSpacing(20)

        # Status label
        self.window.start_status_label = QLabel("")
        self.window.start_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        start_layout.addWidget(self.window.start_status_label)

        start_layout.addStretch()

        # 스크롤 영역에 위젯 설정
        self.window.start_scroll.setWidget(self.window.start_widget)
        self.window.main_layout.addWidget(self.window.start_scroll)

    def _create_session_column(self, columns_layout: QHBoxLayout):
        """세션 생성 column 생성"""
        import asyncio

        create_column = QVBoxLayout()
        create_label = QLabel("새 세션")
        create_label_font = QFont()
        create_label_font.setPointSize(14)
        create_label_font.setBold(True)
        create_label.setFont(create_label_font)
        create_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        create_column.addWidget(create_label)
        create_column.addSpacing(10)

        self.window.create_button = QPushButton("세션 생성")
        self.window.create_button.setMinimumHeight(50)
        self.window.create_button.clicked.connect(
            lambda: asyncio.create_task(self.window.session_manager.on_create_session()))
        create_column.addWidget(self.window.create_button)
        create_column.addStretch()  # 아래쪽 공간 채우기

        columns_layout.addLayout(create_column, 1)  # stretch factor = 1

    def _create_join_column(self, columns_layout: QHBoxLayout):
        """세션 참여 column 생성"""
        import asyncio

        join_column = QVBoxLayout()
        join_label = QLabel("기존 세션 참여")
        join_label_font = QFont()
        join_label_font.setPointSize(14)
        join_label_font.setBold(True)
        join_label.setFont(join_label_font)
        join_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        join_column.addWidget(join_label)
        join_column.addSpacing(10)

        session_label = QLabel("세션 번호:")
        join_column.addWidget(session_label)

        self.window.session_input = QLineEdit()
        self.window.session_input.setPlaceholderText("세션 번호 입력")
        self.window.session_input.textChanged.connect(self.window.on_session_input_changed)
        join_column.addWidget(self.window.session_input)

        join_column.addSpacing(5)  # 입력과 버튼 사이 간격

        self.window.join_button = QPushButton("접속")
        self.window.join_button.setMinimumHeight(50)
        self.window.join_button.setEnabled(False)
        self.window.join_button.clicked.connect(
            lambda: asyncio.create_task(self.window.session_manager.on_join_session()))
        join_column.addWidget(self.window.join_button)

        columns_layout.addLayout(join_column, 1)  # stretch factor = 1

    def create_main_screen(self):
        """메인 화면 생성"""
        # 스크롤 영역 생성
        self.window.main_scroll = QScrollArea()
        self.window.main_scroll.setWidgetResizable(True)
        self.window.main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.window.main_widget = QWidget()
        main_screen_layout = QVBoxLayout()
        main_screen_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.window.main_widget.setLayout(main_screen_layout)

        # Title
        self._create_main_title(main_screen_layout)

        main_screen_layout.addSpacing(20)

        # Status label (상단에 배치)
        self.window.status_label = QLabel("")
        self.window.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_screen_layout.addWidget(self.window.status_label)

        main_screen_layout.addSpacing(20)

        # ===== 그림 영역 설정 섹션 (통합) =====
        self._create_overlay_group(main_screen_layout)

        main_screen_layout.addSpacing(15)

        # ===== 참여자 섹션 =====
        self._create_participants_group(main_screen_layout)

        main_screen_layout.addSpacing(15)

        # ===== 정보 섹션 =====
        self._create_info_group(main_screen_layout)

        main_screen_layout.addStretch()

        # 스크롤 영역에 위젯 설정
        self.window.main_scroll.setWidget(self.window.main_widget)
        self.window.main_layout.addWidget(self.window.main_scroll)
        self.window.main_scroll.hide()  # 초기에는 시작 화면만 표시

        # Drawing Canvas 생성 (오버레이용으로만 사용)
        self._create_main_canvas()

    def _create_main_title(self, layout: QVBoxLayout):
        """메인 화면 타이틀 생성"""
        title = QLabel("Screen Party")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

    def _create_overlay_group(self, layout: QVBoxLayout):
        """오버레이 그룹 생성"""
        overlay_group = QGroupBox("그림 영역 설정")
        self.window.overlay_group_layout = QVBoxLayout()
        overlay_group.setLayout(self.window.overlay_group_layout)

        # 초기 상태: 그림 영역 생성 버튼
        self.window.setup_overlay_button = QPushButton("그림 영역 생성")
        self.window.setup_overlay_button.setMinimumHeight(45)
        self.window.setup_overlay_button.clicked.connect(self.window.overlay_manager.toggle_overlay)
        self.window.overlay_group_layout.addWidget(self.window.setup_overlay_button)

        # 생성 후 상태: 크기 조정 + 삭제 버튼 (8:2 비율)
        self._create_overlay_controls()

        # 그리기 활성화/비활성화 버튼
        self._create_drawing_toggle_button()

        # 색상 팔레트
        self._create_color_palette()

        # Alpha 슬라이더
        self._create_alpha_slider()

        # 그림 모두 지우기 버튼
        self.window.clear_drawings_button = QPushButton("그림 모두 지우기")
        self.window.clear_drawings_button.setMinimumHeight(40)
        self.window.clear_drawings_button.setEnabled(False)
        self.window.clear_drawings_button.clicked.connect(self.window.overlay_manager.clear_overlay_drawings)
        self.window.overlay_group_layout.addWidget(self.window.clear_drawings_button)

        layout.addWidget(overlay_group)

    def _create_overlay_controls(self):
        """오버레이 컨트롤 버튼 생성"""
        self.window.overlay_control_widget = QWidget()
        overlay_control_layout = QHBoxLayout()
        overlay_control_layout.setContentsMargins(0, 0, 0, 0)
        overlay_control_layout.setSpacing(10)
        self.window.overlay_control_widget.setLayout(overlay_control_layout)

        self.window.resize_overlay_button = QPushButton("그림 영역 크기 조정")
        self.window.resize_overlay_button.setMinimumHeight(40)
        self.window.resize_overlay_button.clicked.connect(self.window.overlay_manager.toggle_resize_mode)
        overlay_control_layout.addWidget(self.window.resize_overlay_button, 8)  # 80%

        self.window.delete_overlay_button = QPushButton("삭제")
        self.window.delete_overlay_button.setMinimumHeight(40)
        self.window.delete_overlay_button.clicked.connect(self.window.overlay_manager.stop_overlay)
        overlay_control_layout.addWidget(self.window.delete_overlay_button, 2)  # 20%

        self.window.overlay_group_layout.addWidget(self.window.overlay_control_widget)
        self.window.overlay_control_widget.hide()  # 초기에는 숨김

    def _create_drawing_toggle_button(self):
        """그리기 토글 버튼 생성"""
        self.window.toggle_drawing_button = QPushButton("그리기 활성화")
        self.window.toggle_drawing_button.setMinimumHeight(40)
        self.window.toggle_drawing_button.setEnabled(False)
        self.window.toggle_drawing_button.clicked.connect(self.window.overlay_manager.toggle_drawing_mode)
        self.window.overlay_group_layout.addWidget(self.window.toggle_drawing_button)

    def _create_color_palette(self):
        """색상 팔레트 생성"""
        palette_label = QLabel("색상:")
        self.window.overlay_group_layout.addWidget(palette_label)

        palette_layout = QHBoxLayout()
        self.window.color_buttons = []

        for color in PRESET_COLORS:
            btn = QPushButton()
            btn.setFixedSize(40, 40)  # 정사각형 버튼
            # 기본 색상과 hover/pressed 효과를 모두 정의하여 Qt 기본 피드백 제공
            base_r, base_g, base_b = color.red(), color.green(), color.blue()
            hover_r = min(255, int(base_r * 1.1))  # 10% 밝게
            hover_g = min(255, int(base_g * 1.1))
            hover_b = min(255, int(base_b * 1.1))
            pressed_r = max(0, int(base_r * 0.9))  # 10% 어둡게
            pressed_g = max(0, int(base_g * 0.9))
            pressed_b = max(0, int(base_b * 0.9))
            btn.setStyleSheet(
                f"QPushButton {{"
                f"  background-color: rgb({base_r}, {base_g}, {base_b}); "
                f"  border: 2px solid #888; "
                f"  border-radius: 4px;"
                f"}}"
                f"QPushButton:hover {{"
                f"  background-color: rgb({hover_r}, {hover_g}, {hover_b}); "
                f"  border: 2px solid #AAA;"
                f"}}"
                f"QPushButton:pressed {{"
                f"  background-color: rgb({pressed_r}, {pressed_g}, {pressed_b}); "
                f"  border: 2px solid #666;"
                f"}}"
            )
            btn.clicked.connect(lambda checked, c=color: self.window.drawing_handler.set_pen_color(c))
            palette_layout.addWidget(btn)
            self.window.color_buttons.append(btn)

        self.window.overlay_group_layout.addLayout(palette_layout)

    def _create_alpha_slider(self):
        """투명도 슬라이더 생성"""
        alpha_label = QLabel("투명도: 100%")
        self.window.overlay_group_layout.addWidget(alpha_label)

        self.window.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.window.alpha_slider.setMinimum(0)
        self.window.alpha_slider.setMaximum(100)
        self.window.alpha_slider.setValue(100)
        self.window.alpha_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.window.alpha_slider.setTickInterval(10)
        self.window.alpha_slider.valueChanged.connect(
            lambda value: self.window.drawing_handler.on_alpha_changed(value, alpha_label)
        )
        self.window.overlay_group_layout.addWidget(self.window.alpha_slider)

    def _create_participants_group(self, layout: QVBoxLayout):
        """참여자 그룹 생성"""
        participants_group = QGroupBox("참여자")
        participants_layout = QVBoxLayout()
        participants_group.setLayout(participants_layout)

        self.window.users_colors_label = QLabel("연결 대기 중...")
        self.window.users_colors_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        participants_layout.addWidget(self.window.users_colors_label)

        layout.addWidget(participants_group)

    def _create_info_group(self, layout: QVBoxLayout):
        """정보 그룹 생성"""
        import asyncio

        info_group = QGroupBox("정보")
        info_layout = QVBoxLayout()
        info_group.setLayout(info_layout)

        # 서버 주소 표시 + 복사 버튼
        server_info_layout = QHBoxLayout()
        self.window.server_info_label = QLabel("")
        server_info_layout.addWidget(self.window.server_info_label)
        self.window.copy_server_button = QPushButton("복사")
        self.window.copy_server_button.setMaximumWidth(60)
        self.window.copy_server_button.clicked.connect(self.window.copy_server_address)
        server_info_layout.addWidget(self.window.copy_server_button)
        info_layout.addLayout(server_info_layout)

        # 세션 번호 표시 + 복사 버튼
        session_info_layout = QHBoxLayout()
        self.window.session_info_label = QLabel("")
        session_info_layout.addWidget(self.window.session_info_label)
        self.window.copy_session_button = QPushButton("복사")
        self.window.copy_session_button.setMaximumWidth(60)
        self.window.copy_session_button.clicked.connect(self.window.copy_session_id)
        session_info_layout.addWidget(self.window.copy_session_button)
        info_layout.addLayout(session_info_layout)

        # 세션 나가기 버튼
        self.window.leave_session_button = QPushButton("세션 나가기")
        self.window.leave_session_button.setMinimumHeight(40)
        self.window.leave_session_button.clicked.connect(lambda: asyncio.create_task(self.window.disconnect()))
        info_layout.addWidget(self.window.leave_session_button)

        # 사용법 링크 + 버전 정보
        self._create_footer(info_layout)

        layout.addWidget(info_group)

    def _create_footer(self, layout: QVBoxLayout):
        """푸터 (사용법 링크 + 버전) 생성"""
        from .main_window import get_version

        footer_layout = QHBoxLayout()
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        github_label = QLabel('<a href="https://github.com/kimkun07/screen-party">사용법 (GitHub)</a>')
        github_label.setOpenExternalLinks(True)
        footer_layout.addWidget(github_label)

        version_label = QLabel(f"v{get_version()}")
        version_label.setStyleSheet("color: gray;")
        footer_layout.addWidget(version_label)

        layout.addLayout(footer_layout)

    def _create_main_canvas(self):
        """메인 캔버스 생성"""
        from ..drawing.canvas_manager import CanvasManager
        from ..network.message_handler import MessageHandler

        main_canvas = DrawingCanvas(
            parent=self.window.main_widget,
            user_id=None,  # 세션 연결 시 설정
            pen_color=get_default_pen_color(),  # 첫 번째 프리셋 색상 (파스텔 핑크)
            pen_width=3,
        )
        main_canvas.hide()  # 화면에 표시하지 않음

        # Canvas Manager 생성
        self.window.canvas_manager = CanvasManager(main_canvas)

        # Drawing Canvas 시그널 연결
        self.window.drawing_handler._connect_drawing_signals(main_canvas)

        # Message Handler 생성
        self.window.message_handler = MessageHandler(
            state=self.window.state,
            canvas_manager=self.window.canvas_manager,
            disconnect_callback=self.window.disconnect,
        )
