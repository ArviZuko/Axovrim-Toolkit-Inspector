#!/usr/bin/env bash
# ==============================================================================
# AXOVRIM — Diagnostic System & Hardware Verifier
# Checks ARM64 architecture, OS, Python packages, RealSense, Model, and Workbooks
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

REPORT_FILE="${SCRIPT_DIR}/check_system_report.txt"

echo "================================================================================" | tee "${REPORT_FILE}"
echo " AXOVRIM — System & Hardware Diagnostic Report" | tee -a "${REPORT_FILE}"
echo " Generated on: $(date)" | tee -a "${REPORT_FILE}"
echo " Host: $(uname -n) | Kernel: $(uname -r)" | tee -a "${REPORT_FILE}"
echo "================================================================================" | tee -a "${REPORT_FILE}"

PASS_COUNT=0
FAIL_COUNT=0
NOT_TESTED_COUNT=0

check_result() {
    local name="$1"
    local status="$2"
    local detail="$3"
    printf "%-35s [%s] %s\n" "${name}" "${status}" "${detail}" | tee -a "${REPORT_FILE}"
    if [ "${status}" = "PASS" ]; then
        PASS_COUNT=$((PASS_COUNT + 1))
    elif [ "${status}" = "FAIL" ]; then
        FAIL_COUNT=$((FAIL_COUNT + 1))
    else
        NOT_TESTED_COUNT=$((NOT_TESTED_COUNT + 1))
    fi
}

# 1. Architecture Check
ARCH=$(uname -m)
if [ "${ARCH}" = "aarch64" ] || [ "${ARCH}" = "arm64" ]; then
    check_result "CPU Architecture" "PASS" "${ARCH} (64-bit ARM)"
else
    check_result "CPU Architecture" "FAIL" "Expected aarch64, got ${ARCH}"
fi

# 2. OS Check
if [ -f /etc/os-release ]; then
    . /etc/os-release
    check_result "Operating System" "PASS" "${PRETTY_NAME:-Linux}"
else
    check_result "Operating System" "NOT TESTED" "No /etc/os-release found"
fi

# 3. Python Version
if command -v python3 &> /dev/null; then
    PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    check_result "Python 3 Interpreter" "PASS" "Version ${PY_VER}"
else
    check_result "Python 3 Interpreter" "FAIL" "python3 not found in PATH"
fi

# 4. Virtual Environment
VENV_PY="${SCRIPT_DIR}/.venv/bin/python3"
if [ -x "${VENV_PY}" ]; then
    check_result "Python Virtual Environment" "PASS" ".venv/bin/python3 exists and is executable"
    USE_PY="${VENV_PY}"
else
    check_result "Python Virtual Environment" "FAIL" ".venv not created. Run ./install_dependencies.sh"
    USE_PY="python3"
fi

# 5. Display / HDMI Environment
if [ -n "${WAYLAND_DISPLAY}" ]; then
    check_result "Display Environment" "PASS" "Wayland active (${WAYLAND_DISPLAY})"
elif [ -n "${DISPLAY}" ]; then
    check_result "Display Environment" "PASS" "X11 active (${DISPLAY})"
else
    check_result "Display Environment" "FAIL" "Neither DISPLAY nor WAYLAND_DISPLAY is set"
fi

# 6. Library Imports Check via Python
check_python_lib() {
    local lib_name="$1"
    local import_cmd="$2"
    if "${USE_PY}" -c "${import_cmd}" &> /dev/null; then
        local version
        version=$("${USE_PY}" -c "${import_cmd}; print(getattr(${lib_name}, '__version__', 'OK'))" 2>/dev/null || echo "OK")
        check_result "Python: ${lib_name}" "PASS" "Loaded (v${version})"
    else
        check_result "Python: ${lib_name}" "FAIL" "Import failed"
    fi
}

check_python_lib "torch" "import torch"
check_python_lib "torchvision" "import torchvision"
check_python_lib "ultralytics" "import ultralytics"
check_python_lib "cv2" "import cv2"
check_python_lib "numpy" "import numpy"
check_python_lib "scipy" "import scipy"
check_python_lib "openpyxl" "import openpyxl"
check_python_lib "reportlab" "import reportlab"
check_python_lib "PyQt5" "from PyQt5.QtWidgets import QApplication"

# 7. Intel RealSense Library & Hardware Check
if "${USE_PY}" -c "import pyrealsense2 as rs" &> /dev/null; then
    check_result "Intel RealSense Library" "PASS" "pyrealsense2 imported successfully"
    # Check physical hardware discovery
    CAM_TEST=$("${USE_PY}" -c "
import pyrealsense2 as rs
ctx = rs.context()
devs = ctx.query_devices()
if len(devs) > 0:
    print(f'FOUND:{devs[0].get_info(rs.camera_info.name)}:{devs[0].get_info(rs.camera_info.serial_number)}')
else:
    print('NONE')
" 2>/dev/null || echo "ERROR")

    if [[ "${CAM_TEST}" == FOUND:* ]]; then
        CAM_DETAIL=$(echo "${CAM_TEST}" | cut -d':' -f2-)
        check_result "RealSense Hardware Discovery" "PASS" "${CAM_DETAIL}"
    elif [ "${CAM_TEST}" = "NONE" ]; then
        check_result "RealSense Hardware Discovery" "FAIL" "No RealSense camera detected on USB port"
    else
        check_result "RealSense Hardware Discovery" "NOT TESTED" "Device query returned error"
    fi
else
    check_result "Intel RealSense Library" "FAIL" "pyrealsense2 not installed"
    check_result "RealSense Hardware Discovery" "NOT TESTED" "Requires pyrealsense2 binding"
fi

# 8. Model Weights File Check
MODEL_PATH="${SCRIPT_DIR}/Models/best (2).pt"
if [ -f "${MODEL_PATH}" ] && [ -s "${MODEL_PATH}" ]; then
    SIZE_MB=$(du -m "${MODEL_PATH}" | cut -f1)
    check_result "YOLOv11 Model Weights" "PASS" "best (2).pt exists (${SIZE_MB} MB)"
else
    check_result "YOLOv11 Model Weights" "FAIL" "Missing or empty: ${MODEL_PATH}"
fi

# 9. Excel Sheets Check
if [ -f "${SCRIPT_DIR}/Excel Sheet/Book1.xlsx" ] && [ -s "${SCRIPT_DIR}/Excel Sheet/Book1.xlsx" ]; then
    check_result "Excel Sheet/Book1.xlsx" "PASS" "Present and non-empty"
else
    check_result "Excel Sheet/Book1.xlsx" "FAIL" "File missing or empty"
fi

if [ -f "${SCRIPT_DIR}/Excel Sheet/Book2.xlsx" ] && [ -s "${SCRIPT_DIR}/Excel Sheet/Book2.xlsx" ]; then
    check_result "Excel Sheet/Book2.xlsx" "PASS" "Present and non-empty"
else
    check_result "Excel Sheet/Book2.xlsx" "FAIL" "File missing or empty"
fi

# 10. Writable Directories Check
for dir_name in "data/calibration" "data/inspections" "Reports" "output"; do
    if [ -w "${SCRIPT_DIR}/${dir_name}" ]; then
        check_result "Writable: ${dir_name}" "PASS" "Directory is writable"
    else
        check_result "Writable: ${dir_name}" "FAIL" "Directory is not writable or missing"
    fi
done

echo "================================================================================" | tee -a "${REPORT_FILE}"
echo " Summary: ${PASS_COUNT} PASSED | ${FAIL_COUNT} FAILED | ${NOT_TESTED_COUNT} NOT TESTED" | tee -a "${REPORT_FILE}"
echo " Diagnostic report saved to: ${REPORT_FILE}" | tee -a "${REPORT_FILE}"
echo "================================================================================" | tee -a "${REPORT_FILE}"
