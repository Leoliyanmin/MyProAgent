# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['passlib.handlers.bcrypt', 'passlib.handlers.sha2_crypt', 'passlib.handlers.pbkdf2', 'email_validator', 'apscheduler.triggers.interval', 'apscheduler.triggers.cron', 'apscheduler.executors.asyncio', 'apscheduler.executors.pool', 'jose', 'sqlite3', 'redis', 'aiosmtplib', 'python_multipart', 'dotenv', 'httpx']
hiddenimports += collect_submodules('passlib')
hiddenimports += collect_submodules('email')
hiddenimports += collect_submodules('jose')
hiddenimports += collect_submodules('cryptography')


a = Analysis(
    ['/Users/yanmin/Documents/SE Project/scripts/python_backend.py'],
    pathex=['/Users/yanmin/Documents/SE Project', '/Users/yanmin/Documents/SE Project/local_backend', '/Users/yanmin/Documents/SE Project/localagent', '/Users/yanmin/Documents/SE Project/personality'],
    binaries=[],
    datas=[('/Users/yanmin/Documents/SE Project/local_backend', 'local_backend'), ('/Users/yanmin/Documents/SE Project/localagent', 'localagent'), ('/Users/yanmin/Documents/SE Project/personality', 'personality'), ('/Users/yanmin/Documents/SE Project/logging_config.py', '.')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='python-backend-aarch64-apple-darwin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
