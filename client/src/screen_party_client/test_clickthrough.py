"""투명 창 + Click Passthrough 테스트 프로그램

컨트롤 창과 테스트 오버레이 창을 분리하여 Passthrough 상태에서도 제어 가능
사용법: uv run client-test [방법번호]
"""

import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QPen, QColor, QFont


class TestOverlayBase(QWidget):
    """테스트 오버레이 창 베이스 클래스 (투명, 버튼 없음)"""

    def __init__(self, method_name: str):
        super().__init__()
        self.method_name = method_name
        self.passthrough_enabled = False
        self.click_count = 0
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        # 윈도우 설정
        self.setWindowTitle(f"Test Overlay - {self.method_name}")
        self.setGeometry(100, 100, 800, 600)

        # 기본 윈도우 플래그: 프레임 없음, 항상 위
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        # 투명 배경 설정
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        """테두리와 상태 표시"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 반투명 배경
        painter.fillRect(self.rect(), QColor(50, 50, 50, 80))

        # 테두리 (노란색)
        pen = QPen(QColor(255, 255, 0, 255), 4)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(2, 2, -2, -2))

        # 클릭 카운터 표시
        font = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(font)

        # 배경 박스
        counter_rect = QRect(20, 20, 300, 100)
        if self.passthrough_enabled:
            painter.fillRect(counter_rect, QColor(255, 100, 100, 200))
        else:
            painter.fillRect(counter_rect, QColor(100, 255, 100, 200))

        # 텍스트
        painter.setPen(QColor(255, 255, 255, 255))
        status_text = "PASSTHROUGH ON" if self.passthrough_enabled else "PASSTHROUGH OFF"
        painter.drawText(counter_rect.adjusted(10, 10, -10, -10), Qt.AlignmentFlag.AlignTop, status_text)

        # 클릭 횟수
        font.setPointSize(18)
        painter.setFont(font)
        painter.drawText(counter_rect.adjusted(10, 50, -10, -10), Qt.AlignmentFlag.AlignTop, f"클릭: {self.click_count}회")

    def mousePressEvent(self, event):
        """마우스 클릭 이벤트"""
        self.click_count += 1
        self.update()
        print(f"[{self.method_name}] 오버레이 창 클릭됨! (총 {self.click_count}회)")

    def set_passthrough(self, enabled: bool):
        """Passthrough 설정 - 서브클래스에서 구현"""
        raise NotImplementedError("서브클래스에서 구현해야 합니다")


class Overlay1_WindowTransparentForInput(TestOverlayBase):
    """방법 1: WindowTransparentForInput 플래그 (Qt 포럼 권장)"""

    def __init__(self):
        super().__init__("Method 1: WindowTransparentForInput")

    def set_passthrough(self, enabled: bool):
        """WindowTransparentForInput 플래그 설정"""
        self.passthrough_enabled = enabled
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, enabled)
        self.show()
        self.update()
        print(f"[Method 1] Passthrough: {enabled}")


class Overlay2_WA_TransparentForMouseEvents(TestOverlayBase):
    """방법 2: WA_TransparentForMouseEvents 속성"""

    def __init__(self):
        super().__init__("Method 2: WA_TransparentForMouseEvents")

    def set_passthrough(self, enabled: bool):
        """WA_TransparentForMouseEvents 속성 설정"""
        self.passthrough_enabled = enabled
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, enabled)
        self.update()
        print(f"[Method 2] Passthrough: {enabled}")


class Overlay3_CombinedFlags(TestOverlayBase):
    """방법 3: 여러 플래그 조합"""

    def __init__(self):
        super().__init__("Method 3: Combined Flags")

    def set_passthrough(self, enabled: bool):
        """여러 플래그 조합"""
        self.passthrough_enabled = enabled

        if enabled:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
                | Qt.WindowType.WindowTransparentForInput
            )
        else:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
            )

        self.show()
        self.update()
        print(f"[Method 3] Passthrough: {enabled}")


class Overlay4_AttributeAndFlag(TestOverlayBase):
    """방법 4: Attribute + Flag 동시 사용"""

    def __init__(self):
        super().__init__("Method 4: Attribute + Flag")

    def set_passthrough(self, enabled: bool):
        """Attribute와 Flag 동시 설정"""
        self.passthrough_enabled = enabled
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, enabled)
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, enabled)
        self.show()
        self.update()
        print(f"[Method 4] Passthrough: {enabled}")


class Overlay5_NoPassthrough(TestOverlayBase):
    """방법 5: Passthrough 없음 (대조군)"""

    def __init__(self):
        super().__init__("Method 5: No Passthrough (Control)")

    def set_passthrough(self, enabled: bool):
        """아무것도 하지 않음 (대조군)"""
        self.passthrough_enabled = enabled
        self.update()
        print(f"[Method 5] Passthrough: {enabled} (실제로는 항상 OFF)")


class ControlWindow(QWidget):
    """컨트롤 창 (항상 클릭 가능)"""

    def __init__(self, overlay: TestOverlayBase):
        super().__init__()
        self.overlay = overlay
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle(f"Control Panel - {self.overlay.method_name}")
        self.setGeometry(920, 100, 350, 300)

        # 일반 창 (투명하지 않음, 항상 위)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        # 레이아웃
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 제목
        title_label = QLabel("🎮 Click Passthrough 테스트")
        title_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; "
            "color: #333; padding: 10px; "
            "background-color: #e0e0e0; border-radius: 5px;"
        )
        layout.addWidget(title_label)

        # 방법 표시
        method_label = QLabel(f"방법: {self.overlay.method_name}")
        method_label.setStyleSheet(
            "font-size: 12px; color: #666; "
            "padding: 5px; background-color: #f5f5f5; border-radius: 3px;"
        )
        method_label.setWordWrap(True)
        layout.addWidget(method_label)

        # 상태 표시
        self.status_label = QLabel("상태: Passthrough OFF")
        self.status_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; "
            "color: white; padding: 15px; "
            "background-color: #4CAF50; border-radius: 5px;"
        )
        layout.addWidget(self.status_label)

        # 설명
        info_label = QLabel(
            "• OFF: 오버레이 창 클릭 시 카운터 증가\n"
            "• ON: 오버레이 창 클릭이 뒤로 통과"
        )
        info_label.setStyleSheet(
            "font-size: 11px; color: #555; "
            "padding: 10px; background-color: #f9f9f9; "
            "border-radius: 3px; border: 1px solid #ddd;"
        )
        layout.addWidget(info_label)

        layout.addStretch()

        # Passthrough ON 버튼
        self.on_btn = QPushButton("✓ Passthrough ON")
        self.on_btn.setStyleSheet(
            "QPushButton { "
            "  background-color: #f44336; color: white; "
            "  padding: 15px; border-radius: 5px; "
            "  font-size: 14px; font-weight: bold; "
            "}"
            "QPushButton:hover { background-color: #da190b; }"
        )
        self.on_btn.clicked.connect(self.enable_passthrough)
        layout.addWidget(self.on_btn)

        # Passthrough OFF 버튼
        self.off_btn = QPushButton("✗ Passthrough OFF")
        self.off_btn.setStyleSheet(
            "QPushButton { "
            "  background-color: #4CAF50; color: white; "
            "  padding: 15px; border-radius: 5px; "
            "  font-size: 14px; font-weight: bold; "
            "}"
            "QPushButton:hover { background-color: #45a049; }"
        )
        self.off_btn.clicked.connect(self.disable_passthrough)
        layout.addWidget(self.off_btn)

        # 닫기 버튼
        close_btn = QPushButton("🚪 닫기")
        close_btn.setStyleSheet(
            "QPushButton { "
            "  background-color: #9E9E9E; color: white; "
            "  padding: 12px; border-radius: 5px; "
            "  font-size: 13px; font-weight: bold; "
            "}"
            "QPushButton:hover { background-color: #757575; }"
        )
        close_btn.clicked.connect(self.close_all)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def enable_passthrough(self):
        """Passthrough 켜기"""
        self.overlay.set_passthrough(True)
        self.update_status()

    def disable_passthrough(self):
        """Passthrough 끄기"""
        self.overlay.set_passthrough(False)
        self.update_status()

    def update_status(self):
        """상태 업데이트"""
        if self.overlay.passthrough_enabled:
            self.status_label.setText("상태: Passthrough ON")
            self.status_label.setStyleSheet(
                "font-size: 16px; font-weight: bold; "
                "color: white; padding: 15px; "
                "background-color: #f44336; border-radius: 5px;"
            )
        else:
            self.status_label.setText("상태: Passthrough OFF")
            self.status_label.setStyleSheet(
                "font-size: 16px; font-weight: bold; "
                "color: white; padding: 15px; "
                "background-color: #4CAF50; border-radius: 5px;"
            )

    def close_all(self):
        """모든 창 닫기"""
        self.overlay.close()
        self.close()

    def closeEvent(self, event):
        """창 닫을 때 오버레이도 함께 닫기"""
        self.overlay.close()
        event.accept()


def main():
    """메인 함수"""
    # 방법 선택
    method = 1
    if len(sys.argv) > 1:
        try:
            method = int(sys.argv[1])
        except ValueError:
            print(f"잘못된 방법 번호: {sys.argv[1]}")
            method = 1

    # QApplication 생성
    app = QApplication(sys.argv)

    # 방법별 오버레이 클래스
    overlay_classes = {
        1: Overlay1_WindowTransparentForInput,
        2: Overlay2_WA_TransparentForMouseEvents,
        3: Overlay3_CombinedFlags,
        4: Overlay4_AttributeAndFlag,
        5: Overlay5_NoPassthrough,
    }

    if method not in overlay_classes:
        print(f"지원하지 않는 방법 번호: {method}")
        print("사용 가능한 방법:")
        print("  1: WindowTransparentForInput (Qt 포럼 권장)")
        print("  2: WA_TransparentForMouseEvents")
        print("  3: Combined Flags")
        print("  4: Attribute + Flag")
        print("  5: No Passthrough (Control)")
        sys.exit(1)

    # 오버레이 창 생성
    overlay = overlay_classes[method]()
    overlay.show()

    # 컨트롤 창 생성
    control = ControlWindow(overlay)
    control.show()

    print(f"\n=== Click Passthrough Test - Method {method} ===")
    print(f"방법: {overlay.method_name}")
    print("\n사용법:")
    print("1. 컨트롤 창(오른쪽)에서 'Passthrough ON/OFF' 버튼 클릭")
    print("2. OFF: 오버레이 창(왼쪽, 노란 테두리)을 클릭하면 카운터 증가")
    print("3. ON: 오버레이 창을 클릭하면 뒤의 창이 클릭됨 (클릭 통과)")
    print("4. 컨트롤 창은 항상 클릭 가능\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
