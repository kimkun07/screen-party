# Task: Client Deployment (클라이언트 실행 파일 빌드)

## 개요

PyInstaller로 클라이언트를 단일 실행 파일로 빌드 (Windows .exe, Linux binary)

## 목표

- [ ] PyInstaller 설정
- [ ] Windows .exe 빌드
- [ ] Linux binary 빌드
- [ ] 앱 아이콘 추가
- [ ] 빌드 자동화 (GitHub Actions)
- [ ] 릴리스 가이드 작성

## 상세 요구사항

### PyInstaller 명령어
```bash
# Windows
pyinstaller --onefile --windowed \
    --name ScreenParty \
    --icon=assets/icon.ico \
    client/src/screen_party_client/main.py

# Linux
pyinstaller --onefile --windowed \
    --name ScreenParty \
    --icon=assets/icon.png \
    client/src/screen_party_client/main.py
```

### .spec 파일 (고급 설정)
```python
# ScreenParty.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['client/src/screen_party_client/main.py'],
    pathex=[],
    binaries=[],
    datas=[],  # 필요 시 리소스 파일 추가
    hiddenimports=['PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ScreenParty',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # UPX 압축 (선택 사항)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 모드
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',  # Windows
)
```

### GitHub Actions 자동 빌드
- Windows 및 Linux 환경에서 동시 빌드
- 릴리스 태그 push 시 자동 빌드
- 빌드된 바이너리를 GitHub Releases에 업로드

```yaml
name: Build Client

on:
  push:
    tags: ["v*"]

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install Poetry
        run: pip install poetry
      - name: Install dependencies
        run: cd client && poetry install
      - name: Build with PyInstaller
        run: cd client && poetry run pyinstaller ScreenParty.spec
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: ScreenParty-Windows
          path: client/dist/ScreenParty.exe

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install Poetry
        run: pip install poetry
      - name: Install dependencies
        run: cd client && poetry install
      - name: Build with PyInstaller
        run: cd client && poetry run pyinstaller ScreenParty.spec
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: ScreenParty-Linux
          path: client/dist/ScreenParty

  release:
    needs: [build-windows, build-linux]
    runs-on: ubuntu-latest
    steps:
      - name: Download Windows artifact
        uses: actions/download-artifact@v3
        with:
          name: ScreenParty-Windows
      - name: Download Linux artifact
        uses: actions/download-artifact@v3
        with:
          name: ScreenParty-Linux
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            ScreenParty.exe
            ScreenParty
```

## 기술 결정

### PyInstaller vs Nuitka
- PyInstaller: 간단하고 안정적, PyQt6 지원 좋음
- Nuitka: 더 빠르지만 설정 복잡
- 초기 버전은 PyInstaller 사용

### --onefile vs --onedir
- `--onefile`: 단일 실행 파일 (사용자 편의)
- `--onedir`: 디렉토리 형태 (더 빠른 실행)
- 초기 버전은 `--onefile` (배포 편의)

### UPX 압축
- 실행 파일 크기 감소
- 일부 백신에서 오탐 가능성
- 선택 사항으로 유지

## TODO

- [ ] PyInstaller 설정 파일 작성 (ScreenParty.spec)
- [ ] 앱 아이콘 준비 (assets/icon.ico, assets/icon.png)
- [ ] Windows에서 빌드 테스트
- [ ] Linux에서 빌드 테스트
- [ ] GitHub Actions 워크플로우 작성
- [ ] 릴리스 가이드 작성 (배포 방법, 다운로드 링크 등)

## 클로드 코드 일기

_이 섹션은 작업 진행 시 업데이트됩니다._
