#!/usr/bin/env bash
# ==============================================================================
# AXOVRIM — Main Raspberry Pi 5 Application Launcher
# Auto-detects directory, sets up display environment, and launches main.py
# ==============================================================================

set -e

# Automatically locate directory regardless of where script is invoked from
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

LOG_FILE="${SCRIPT_DIR}/app_launch.log"

echo "================================================================================"
echo " Starting AXOVRIM — AI-Powered Toolkit Quality Inspection"
echo " Host: $(uname -n) ($(uname -m))"
echo " Directory: ${SCRIPT_DIR}"
echo " Timestamp: $(date)"
echo "================================================================================"

# Check if running as root
if [ "$(id -u)" -eq 0 ]; then
    echo "WARNING: Running graphical desktop applications as root/sudo is not recommended."
    echo "It may cause display permissions conflicts with X11/Wayland."
fi

# Locate Python Virtual Environment
VENV_PYTHON="${SCRIPT_DIR}/.venv/bin/python3"
if [ ! -x "${VENV_PYTHON}" ]; then
    # Fallback to system python3 if venv not yet created
    if command -v python3 &> /dev/null; then
        VENV_PYTHON="python3"
        echo "Note: .venv not found; using system python3. Run ./install_dependencies.sh first for full setup."
    else
        echo "ERROR: Python 3 not found! Please run ./install_dependencies.sh first."
        exit 1
    fi
fi

# Verify critical asset files
if [ ! -f "${SCRIPT_DIR}/Models/best (2).pt" ]; then
    echo "ERROR: Model file not found at ${SCRIPT_DIR}/Models/best (2).pt"
    exit 1
fi
if [ ! -f "${SCRIPT_DIR}/Excel Sheet/Book1.xlsx" ]; then
    echo "ERROR: Excel Sheet/Book1.xlsx not found!"
    exit 1
fi
if [ ! -f "${SCRIPT_DIR}/Excel Sheet/Book2.xlsx" ]; then
    echo "ERROR: Excel Sheet/Book2.xlsx not found!"
    exit 1
fi

# Display & Qt Platform Configuration
# Raspberry Pi OS Bookworm uses Wayland by default.
# Fallback to xcb if Wayland plugin is not installed to ensure reliable launch.
if [ -z "${DISPLAY}" ] && [ -z "${WAYLAND_DISPLAY}" ]; then
    if [ -e /tmp/.X11-unix/X0 ]; then
        export DISPLAY=":0"
    fi
fi

if [ -n "${WAYLAND_DISPLAY}" ]; then
    # If running on Wayland, check if qtwayland is available
    if [ ! -f /usr/lib/aarch64-linux-gnu/qt5/plugins/platforms/libqwayland-generic.so ] && \
       [ ! -f /usr/lib/qt5/plugins/platforms/libqwayland-generic.so ]; then
        export QT_QPA_PLATFORM="xcb"
    fi
fi

# Set writable environment variables
export KMP_DUPLICATE_LIB_OK="TRUE"
export PYTHONUNBUFFERED=1

echo "Launching application engine..."
exec "${VENV_PYTHON}" "${SCRIPT_DIR}/main.py" "$@" 2>&1 | tee -a "${LOG_FILE}"
