# Almoxarifado.spec - VERSÃO FINAL RECOMENDADA

# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['almoxarifado_gui.py'],  # Seu script principal aqui
    pathex=[],
    binaries=[],
    datas=[
        ('style.qss', '.')  # Adiciona o arquivo de estilo na raiz do executável
    ],
    hiddenimports=[
        'PyQt6.sip',       # Importações que o PyInstaller pode não encontrar sozinho
        'PyQt6.QtCharts'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Almoxarifado',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # Garante que a janela de terminal não apareça
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Almoxarifado', # Nome da pasta de saída
)