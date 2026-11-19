# -*- mode: python ; coding: utf-8 -*-
# AXOVRIM — Standalone Onedir Executable PyInstaller Specification

import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files, copy_metadata

block_cipher = None

# Base directory dynamically resolved from spec file location (no hardcoded developer paths)
app_dir = os.path.abspath(SPECPATH)

# Bundled internal application resources (logo fallback)
datas = [
    (os.path.join(app_dir, 'Smartlab Logo.png'), '.'),
]

binaries = []

hiddenimports = [
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtPrintSupport',
    'openpyxl',
    'pandas',
    'numpy',
    'cv2',
    'torch',
    'torchvision',
    'scipy',
    'scipy.spatial',
    'scipy.ndimage',
    'scipy.optimize',
    'yaml',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
]

# Ultralytics full package collection
u_datas, u_binaries, u_hidden = collect_all('ultralytics')
datas += u_datas
binaries += u_binaries
hiddenimports += u_hidden

# Pyrealsense2 collection
rs_datas, rs_binaries, rs_hidden = collect_all('pyrealsense2')
datas += rs_datas
binaries += rs_binaries
hiddenimports += rs_hidden

# Openpyxl collection
op_datas, op_binaries, op_hidden = collect_all('openpyxl')
datas += op_datas
binaries += op_binaries
hiddenimports += op_hidden

# Package metadata for runtime inspection
datas += copy_metadata('ultralytics')
datas += copy_metadata('torch')
datas += copy_metadata('torchvision')

# Explicitly collect pyrealsense2 native pyd extensions and DLLs
try:
    import pyrealsense2
    rs_dir = os.path.dirname(pyrealsense2.__file__)
    for fname in os.listdir(rs_dir):
        if fname.endswith('.pyd') or fname.endswith('.dll'):
            binaries.append((os.path.join(rs_dir, fname), 'pyrealsense2'))
except Exception:
    pass

# Explicitly collect torchvision native extensions (_C_stable.pyd, image_stable.pyd, libpng, libwebp, etc.)
try:
    import torchvision
    tv_dir = os.path.dirname(torchvision.__file__)
    for fname in os.listdir(tv_dir):
        if fname.endswith('.pyd') or fname.endswith('.dll') or fname.endswith('.so'):
            binaries.append((os.path.join(tv_dir, fname), 'torchvision'))
except Exception:
    pass

# Collect system vcruntime140_threads.dll for portable PyTorch CPU threading support
vc_threads = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'System32', 'vcruntime140_threads.dll')
if os.path.isfile(vc_threads):
    binaries.append((vc_threads, '.'))


a = Analysis(
    [os.path.join(app_dir, 'main.py')],
    pathex=[app_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[os.path.join(app_dir, 'rthook_torch.py')],
    excludes=['tkinter', 'matplotlib.tests', 'scipy.spatial.tests', 'pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out conflicting outdated MSVC runtime DLLs bundled by PyQt5-Qt5
conflicting_msvc = {'msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll', 'vcruntime140.dll', 'vcruntime140_1.dll'}
filtered_binaries = []
for entry in a.binaries:
    dest = entry[0]
    dest_norm = dest.replace('\\', '/').lower()
    fname = os.path.basename(dest_norm)
    if 'pyqt5/qt5/bin' in dest_norm and fname in conflicting_msvc:
        print(f"Spec: excluding conflicting PyQt5 MSVC runtime: {dest}")
        continue
    filtered_binaries.append(entry)
a.binaries = filtered_binaries


pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AXOVRIM',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
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
    upx=False,
    upx_exclude=[],
    name='AXOVRIM',
)
