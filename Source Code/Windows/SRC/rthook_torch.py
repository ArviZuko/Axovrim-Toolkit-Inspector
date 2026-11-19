# PyInstaller runtime hook for AXOVRIM
# Ensures DLL directories (PyTorch, PyQt5, OpenCV, pyrealsense2) are registered early on Windows
# and handles Visual C++ runtime ordering to prevent WinError 1114 initialization failures.

import sys
import os
import ctypes

# Prevent OpenMP crash with PyTorch and OpenCV MKL libraries
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

# Retain handles globally so Windows DLL directory registrations remain active for the process lifetime
_AXOVRIM_DLL_HANDLES = []

if getattr(sys, 'frozen', False):
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    
    # 1. Register base directory (_internal) and torch/lib FIRST
    priority_dirs = [
        base_dir,
        os.path.join(base_dir, 'torch', 'lib'),
    ]
    for d in priority_dirs:
        if os.path.isdir(d):
            if hasattr(os, 'add_dll_directory'):
                try:
                    _AXOVRIM_DLL_HANDLES.append(os.add_dll_directory(d))
                except Exception:
                    pass

    # 2. Pre-load modern MSVC runtimes from base_dir into process memory before anything else can load outdated versions
    vc_runtime_libs = [
        'vcruntime140.dll',
        'vcruntime140_1.dll',
        'vcruntime140_threads.dll',
        'msvcp140.dll',
        'MSVCP140_ATOMIC_WAIT.dll',
    ]
    for lib in vc_runtime_libs:
        lib_path = os.path.join(base_dir, lib)
        if os.path.isfile(lib_path):
            try:
                ctypes.CDLL(lib_path)
            except Exception:
                pass

    # 3. Register OpenCV, RealSense, and PyQt5
    secondary_dirs = [
        os.path.join(base_dir, 'cv2'),
        os.path.join(base_dir, 'pyrealsense2'),
        os.path.join(base_dir, 'PyQt5', 'Qt5', 'bin'),
    ]
    for d in secondary_dirs:
        if os.path.isdir(d):
            if hasattr(os, 'add_dll_directory'):
                try:
                    _AXOVRIM_DLL_HANDLES.append(os.add_dll_directory(d))
                except Exception:
                    pass

    # 4. Set PATH with base_dir and torch/lib prioritized at the front
    all_registered = [d for d in priority_dirs + secondary_dirs if os.path.isdir(d)]
    existing_path = os.environ.get('PATH', '')
    os.environ['PATH'] = os.pathsep.join(all_registered) + os.pathsep + existing_path

