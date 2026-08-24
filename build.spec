# -*- mode: python ; coding: utf-8 -*-
# Build with: pyinstaller build.spec
# Produces a standalone executable. The GGUF model is NOT bundled --
# it downloads on first run into ~/.smart_resume_screener/models/,
# keeping the installer itself small.

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('prompts/extraction_prompt.txt', 'prompts'),
        ('prompts/justification_prompt.txt', 'prompts'),
    ],
    hiddenimports=['llama_cpp'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SmartResumeScreener',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
