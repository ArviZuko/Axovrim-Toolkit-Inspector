#!/usr/bin/env bash
# ==============================================================================
# AXOVRIM — Raspberry Pi 5 First-Time Dependency Installer
# Installs system libraries, RealSense udev rules, and Python environment
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/install_dependencies.log"

# Redirect output to both console and log file
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "================================================================================"
echo " AXOVRIM — Raspberry Pi 5 Automated Dependency Installation"
echo " Date: $(date)"
echo " Directory: ${SCRIPT_DIR}"
echo "================================================================================"

# 1. Architecture Check
ARCH=$(uname -m)
echo "[1/10] Checking CPU Architecture: ${ARCH}"
if [ "${ARCH}" != "aarch64" ] && [ "${ARCH}" != "arm64" ]; then
    echo "ERROR: AXOVRIM Raspberry Pi deployment requires 64-bit ARM (aarch64)."
    echo "Current architecture '${ARCH}' is unsupported."
    exit 1
fi
echo "  Architecture PASS: ${ARCH} (64-bit ARM)"

# 2. OS & Python Check
echo "[2/10] Checking Operating System & Python..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "  OS Detected: ${PRETTY_NAME:-Linux}"
fi

if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Please install Python 3."
    exit 1
fi
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
echo "  Python Version: ${PY_VER}"

# 3. System Resources Check (RAM & Disk)
echo "[3/10] Checking System Resources..."
TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
AVAIL_DISK=$(df -m "${SCRIPT_DIR}" | awk 'NR==2 {print $4}')
echo "  RAM Available: ${TOTAL_RAM} MB (Recommended: >= 4096 MB)"
echo "  Free Disk Space: ${AVAIL_DISK} MB (Recommended: >= 3000 MB)"

if [ "${TOTAL_RAM}" -lt 2000 ]; then
    echo "WARNING: Raspberry Pi has less than 2GB RAM. Performance may be degraded."
fi
if [ "${AVAIL_DISK}" -lt 1500 ]; then
    echo "ERROR: Insufficient disk space (< 1.5 GB). Please free disk space."
    exit 1
fi

# 4. Display Environment Check
echo "[4/10] Checking Display & Desktop Environment..."
if [ -n "${WAYLAND_DISPLAY}" ]; then
    echo "  Display: Wayland active (${WAYLAND_DISPLAY})"
elif [ -n "${DISPLAY}" ]; then
    echo "  Display: X11 active (${DISPLAY})"
else
    echo "  Display: Headless/Console (Note: GUI requires an active desktop or X/Wayland session to launch)"
fi

# 5. System Package Installation (apt)
echo "[5/10] Installing system packages via apt..."
echo "  Note: Sudo password may be requested."
sudo apt-get update -y
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    python3-pyqt5 \
    python3-opencv \
    python3-numpy \
    python3-scipy \
    python3-openpyxl \
    python3-yaml \
    python3-pil \
    python3-pandas \
    python3-reportlab \
    build-essential \
    cmake \
    pkg-config \
    libusb-1.0-0-dev \
    libssl-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgtk-3-dev \
    libatlas-base-dev \
    udev

# 6. Intel RealSense udev Rules Setup
echo "[6/10] Configuring Intel RealSense udev rules..."
UDEV_RULE_FILE="/etc/udev/rules.d/99-realsense-libusb.rules"
if [ ! -f "${UDEV_RULE_FILE}" ]; then
    echo "  Installing RealSense udev permissions to ${UDEV_RULE_FILE}..."
    sudo bash -c 'cat > /etc/udev/rules.d/99-realsense-libusb.rules << "EOF"
# Intel RealSense Depth Camera udev rules
SUBSYSTEM=="usb", ATTR{idVendor}=="8086", ATTR{idProduct}=="0b07", MODE:="0666", GROUP:="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="8086", ATTR{idProduct}=="0b3a", MODE:="0666", GROUP:="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="8086", ATTR{idProduct}=="0b4b", MODE:="0666", GROUP:="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="8086", ATTR{idProduct}=="0b5c", MODE:="0666", GROUP:="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="8086", ATTR{idProduct}=="0ad3", MODE:="0666", GROUP:="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="8086", ATTR{idProduct}=="0ad4", MODE:="0666", GROUP:="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="8086", ATTR{idProduct}=="0ad5", MODE:="0666", GROUP:="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="8086", ATTR{idProduct}=="0b03", MODE:="0666", GROUP:="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="8086", ATTR{idProduct}=="0b3d", MODE:="0666", GROUP:="plugdev"
EOF'
    sudo udevadm control --reload-rules && sudo udevadm trigger
    echo "  udev rules installed and reloaded."
else
    echo "  udev rules already exist: ${UDEV_RULE_FILE}"
fi

# Ensure current user is in plugdev group
if ! groups | grep -q "plugdev"; then
    echo "  Adding user $(whoami) to plugdev group..."
    sudo usermod -a -G plugdev "$(whoami)"
fi

# 7. Create Python Virtual Environment with --system-site-packages
echo "[7/10] Setting up Python virtual environment (.venv)..."
VENV_DIR="${SCRIPT_DIR}/.venv"
if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv --system-site-packages "${VENV_DIR}"
    echo "  Created virtual environment with system site-packages."
else
    echo "  Existing virtual environment detected at ${VENV_DIR}"
fi

# 8. Install Python Requirements
echo "[8/10] Installing Python packages in virtual environment..."
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${SCRIPT_DIR}/requirements-pi.txt"

# 9. Verify Critical Packages and pyrealsense2
echo "[9/10] Verifying Python library imports..."
"${VENV_DIR}/bin/python3" -c "import torch; print(f'  PyTorch: {torch.__version__} (CPU)')"
"${VENV_DIR}/bin/python3" -c "import ultralytics; print(f'  Ultralytics: {ultralytics.__version__}')"
"${VENV_DIR}/bin/python3" -c "import cv2; print(f'  OpenCV: {cv2.__version__}')"
"${VENV_DIR}/bin/python3" -c "import openpyxl; print('  openpyxl: OK')"
"${VENV_DIR}/bin/python3" -c "from PyQt5.QtWidgets import QApplication; print('  PyQt5: OK')"

# Check pyrealsense2
if "${VENV_DIR}/bin/python3" -c "import pyrealsense2 as rs; print(f'  pyrealsense2: {rs.__version__}')" 2>/dev/null; then
    echo "  pyrealsense2: Native library available."
else
    echo "  WARNING: pyrealsense2 not yet compiled/linked for this Python interpreter."
    echo "  Intel RealSense Python binding (pyrealsense2) on ARM64 requires building librealsense with Python bindings."
    echo "  If needed, run the following commands to compile librealsense2 from source:"
    echo "    sudo apt-get install -y git cmake build-essential libusb-1.0-0-dev pkg-config"
    echo "    git clone --depth 1 https://github.com/IntelRealSense/librealsense.git /tmp/librealsense"
    echo "    mkdir -p /tmp/librealsense/build && cd /tmp/librealsense/build"
    echo "    cmake .. -DCMAKE_BUILD_TYPE=Release -DFORCE_RSUSB_BACKEND=ON -DBUILD_PYTHON_BINDINGS:bool=true -DPYTHON_EXECUTABLE=$(which python3)"
    echo "    make -j4 && sudo make install"
fi

# 10. Check Project Assets and Set Permissions
echo "[10/10] Checking Project Assets and Setting Executable Permissions..."
chmod +x "${SCRIPT_DIR}/launch_axovrim.sh" 2>/dev/null || true
chmod +x "${SCRIPT_DIR}/check_system.sh" 2>/dev/null || true
chmod +x "${SCRIPT_DIR}/install_dependencies.sh" 2>/dev/null || true

MODEL_FILE="${SCRIPT_DIR}/Models/best (2).pt"
if [ -f "${MODEL_FILE}" ]; then
    echo "  YOLOv11 Model Weights: PASS ($(du -h "${MODEL_FILE}" | cut -f1))"
else
    echo "  WARNING: Model file missing at ${MODEL_FILE}"
fi

if [ -f "${SCRIPT_DIR}/Excel Sheet/Book1.xlsx" ] && [ -f "${SCRIPT_DIR}/Excel Sheet/Book2.xlsx" ]; then
    echo "  Excel Workbooks (Book1.xlsx, Book2.xlsx): PASS"
else
    echo "  WARNING: Excel workbooks missing in Excel Sheet/"
fi

echo "================================================================================"
echo " INSTALLATION COMPLETE!"
echo " You can now launch AXOVRIM by executing: ./launch_axovrim.sh"
echo " Or run system diagnostics by executing: ./check_system.sh"
echo " Full installation log saved to: ${LOG_FILE}"
echo "================================================================================"
