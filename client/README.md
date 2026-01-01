# Screen Party Client

PyQt6 기반 실시간 드로잉 클라이언트

## 개요

Screen Party 클라이언트는 호스트 모드와 게스트 모드를 지원하는 GUI 애플리케이션입니다.

## 주요 기능

- **Host 모드**: 게임 창에 투명 오버레이 표시, 세션 생성
- **Guest 모드**: 세션 참여, 디스코드 화면에서 드로잉
- **실시간 동기화**: WebSocket을 통한 실시간 드로잉 공유

## 아키텍처

```
client/src/screen_party_client/
├── gui/
│   ├── main_window.py      # 메인 GUI (Host/Guest 선택)
│   ├── overlay.py          # 투명 오버레이 (예정)
│   └── calibration.py      # 영역 설정 (예정)
├── network/
│   └── client.py           # WebSocket 클라이언트
└── drawing/
    ├── engine.py           # 드로잉 엔진 (예정)
    └── spline.py           # Spline 변환 (예정)
```

## 알려진 이슈

- PyInstaller Python 3.13 미지원 → Python 3.12 사용 권장
- 투명 오버레이 기능 미구현 (P2)
- 드로잉 엔진 미구현 (P2)

## 라이선스

TBD
