# Task: Client Deployment (클라이언트 실행 파일 빌드)

## 개요

PyInstaller로 클라이언트를 단일 실행 파일로 빌드 (Windows .exe, Linux binary)

## 목표

- [x] PyInstaller 설정
- [x] Windows .exe 빌드 스크립트
- [ ] Linux binary 빌드 (미정)
- [ ] 앱 아이콘 추가 (선택 사항)
- [ ] 빌드 자동화 (GitHub Actions) (향후)
- [x] 릴리스 가이드 작성 (README.md)

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

- [x] PyInstaller 설정 파일 작성 (client.spec)
- [ ] 앱 아이콘 준비 (assets/icon.ico) - 향후
- [ ] Windows에서 빌드 테스트 - 사용자가 직접 테스트
- [ ] Linux에서 빌드 테스트 (향후)
- [ ] GitHub Actions 워크플로우 작성 (향후)
- [x] 릴리스 가이드 작성 (README.md)

## 클로드 코드 일기

### 2026-01-03 - PyInstaller 패키징 시스템 구축

**상태**: 🟡 준비중 → ✅ 완료 (스크립트 작성)

**작업 내용**:

1. **client.spec 파일 작성** ✅
   - 단일 파일 모드 (--onefile)
   - PyQt6, qasync, websockets 등 hidden imports 설정
   - screen_party_common, screen_party_client 패키지 자동 수집
   - UPX 압축 활성화 (파일 크기 감소)
   - GUI 모드 (console=False)
   - 불필요한 라이브러리 제외 (matplotlib, pandas, tkinter 등)

2. **scripts/package_client.py 스크립트 작성** ✅
   - publish-server와 유사한 구조
   - 버전 태그 지정 (예: v0.1.0)
   - 기존 빌드 정리 (build/, dist/)
   - PyInstaller 자동 실행
   - README.txt 자동 생성 (사용 방법 안내)
   - ZIP 압축 (ScreenParty-v0.1.0-windows.zip)
   - GitHub Release 배포 안내
   - --dry-run, --skip-clean 옵션 지원

3. **의존성 추가** ✅
   - client/pyproject.toml에 pyinstaller>=6.0.0 추가
   - 루트 pyproject.toml에 package-client 스크립트 등록

4. **.gitignore 업데이트** ✅
   - *.spec 제외하되 client.spec 포함 (!client.spec)
   - *.zip 파일 제외 추가

5. **README.md 업데이트** ✅
   - "클라이언트 앱 패키징 (Windows)" 섹션 추가
   - package-client 사용법 설명
   - GitHub Release 배포 방법 안내
   - 주의사항 명시 (바이러스 백신 오탐, 파일 크기 등)

**주요 설계 결정**:

1. **단일 파일 모드 선택**
   - 배포 편의성 (ZIP 파일 하나만 배포)
   - 사용자 경험 개선 (폴더 구조 신경 쓸 필요 없음)
   - 단점: 실행 시 임시 압축 해제 (약간 느림)

2. **Windows만 지원 (현재)**
   - PyQt6 클라이언트는 Windows 테스트 환경에서만 실행
   - Linux 빌드는 향후 필요 시 추가

3. **코드 서명 없음**
   - 비용 문제로 현재는 제외
   - 바이러스 백신 오탐 가능성은 사용자 안내로 대응

4. **GitHub Release 배포**
   - ZIP 파일로 배포
   - 수동 또는 GitHub CLI 사용

**실행 방법** (Windows):

```powershell
# Windows PowerShell
cd D:\Data\Develop\screen-party-mirrored
.\.venv-windows\Scripts\activate.ps1

# 패키징
uv run package-client v0.1.0
```

**결과물**:
- `dist/ScreenParty.exe` - 단일 실행 파일 (~100-200MB)
- `ScreenParty-v0.1.0-windows.zip` - 배포용 ZIP

**다음 단계**:
- 사용자가 Windows에서 실제 빌드 테스트
- GitHub Release 생성
- 필요 시 앱 아이콘 추가

---

### 2026-01-11 - uv workspace 환경에서 패키징 스크립트 개선

**상태**: 🟢 진행중 → ✅ 완료

**문제**:
- `uv run package-client`를 root에서 실행 시 PyInstaller를 찾지 못함
- root pyproject.toml에는 pyinstaller가 없고, client/pyproject.toml의 dev 의존성에만 존재
- 사용자가 root pyproject.toml에 pyinstaller를 추가하지 않기를 원함

**해결 방법**:
- `package_client.py` 스크립트를 수정하여 PyInstaller를 client 환경에서 실행하도록 변경
- `python -m PyInstaller` → `uv run --directory client pyinstaller`로 변경
- `--with pyinstaller` 불필요 (client의 dev 의존성에 이미 포함)

**변경 내용**:

```python
# 이전
pyinstaller_cmd = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--clean",
    "--noconfirm",
    str(spec_file)
]

# 이후
pyinstaller_cmd = [
    "uv",
    "run",
    "--directory",
    str(project_root / "client"),
    "pyinstaller",
    "--clean",
    "--noconfirm",
    str(spec_file)
]
```

**테스트 결과**:
- ✅ Dry-run 테스트 성공 (WSL)
- ✅ Windows 환경에서 실제 패키징 테스트 성공

**실행 방법** (변경 없음):
```bash
# root에서 실행 가능
uv run package-client v0.1.0
```

**장점**:
- ✅ root pyproject.toml에 pyinstaller 추가 불필요
- ✅ 간결한 명령어 유지
- ✅ uv workspace 구조에 적합한 방식

**결과물**:
- `dist/ScreenParty.exe` - Windows 실행 파일
- `ScreenParty-v0.1.0-windows.zip` - 배포용 ZIP

---

> **다음 Claude Code에게**:
>
> **클라이언트 패키징 시스템 완성됨**:
> - `uv run package-client v0.1.0` 명령어로 Windows 실행 파일 생성
> - client.spec: PyInstaller 설정 (단일 파일, hidden imports)
> - scripts/package_client.py: 자동화 스크립트 (uv workspace 지원)
> - Windows 환경에서 테스트 완료 ✅
>
> **패키징 스크립트 개선사항**:
> - `uv run --directory client pyinstaller` 방식 사용
> - root에 pyinstaller 의존성 추가하지 않고도 실행 가능
> - uv workspace monorepo 구조에 적합
>
> **사용자가 할 일**:
> 1. GitHub Release 생성 및 ZIP 업로드
>
> **향후 개선 사항** (선택):
> - 앱 아이콘 추가 (client.spec의 icon 파라미터)
> - GitHub Actions 자동 빌드 (향후)
> - Linux 빌드 지원 (필요 시)
