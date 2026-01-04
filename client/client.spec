# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Screen Party Client

단일 파일 모드로 Windows 실행 파일 생성
"""

import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# screen_party_client 패키지의 모든 의존성 수집
datas = []
binaries = []
hiddenimports = []

# common 패키지 수집
tmp_ret = collect_all('screen_party_common')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# client 패키지 수집
tmp_ret = collect_all('screen_party_client')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# 추가 hidden imports (명시적 지정)
hiddenimports += [
    'PyQt6.QtCore',
    'PyQt6.QtWidgets',
    'PyQt6.QtGui',
    'PyQt6.sip',
    'qasync',
    'websockets',
    'websockets.legacy',
    'websockets.legacy.client',
    'scipy',
    'scipy.interpolate',
    'numpy',
    'asyncio',
]

a = Analysis(
    ['../scripts/run_client.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',  # 사용하지 않는 큰 라이브러리 제외
        'pandas',
        'IPython',
        'tkinter',
    ],
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
    upx=True,  # UPX 압축으로 파일 크기 감소
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 앱이므로 콘솔 창 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',  # 아이콘 파일 (필요 시 주석 해제)
)
