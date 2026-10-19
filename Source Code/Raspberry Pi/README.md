# AXOVRIM — AI-Powered Toolkit Quality Inspection (Raspberry Pi 5 Deployment)

Standalone edge metrology and optical quality inspection deployment for **Raspberry Pi 5 (ARM64 / aarch64)**.

---

## 1. Supported Hardware & Operating System

- **Single-Board Computer**: Raspberry Pi 5 (4GB or 8GB RAM recommended).
- **Operating System**: **Raspberry Pi OS (64-bit)** based on Debian 12 (Bookworm).
- **Camera Sensor**: Intel RealSense D455 / D455F RGB-D Depth Camera (or D435 / D435i).
- **USB Interface**: Official RealSense USB-C 3.x cable connected to a blue **USB 3.0** port.
  *(Note: A powered USB 3.0 hub is recommended if using multiple USB peripherals to avoid power budget drops).*
- **Power Supply**: Official Raspberry Pi 27W USB-C Power Supply (5.1V / 5.0A).
- **Display**: HDMI monitor connected to the **HDMI0** micro-HDMI port on the Raspberry Pi 5.

---

## 2. Package Directory Structure

```text
07. Raspberry Pi 5 Application/
├── main.py                     # Consolidated single-entry application engine
├── launch_axovrim.sh           # Main bash launcher script
├── install_dependencies.sh     # Automated first-time environment installer
├── check_system.sh             # Diagnostic hardware and environment verifier
├── requirements-pi.txt         # Verified ARM64 Python package requirements
├── axovrim.desktop             # Linux XDG desktop shortcut
├── README.md                   # This instruction and operational manual
├── Smartlab Logo.png           # Header brand asset
├── Models/
│   └── best (2).pt             # Trained YOLOv11 instance segmentation weights
├── Excel Sheet/
│   ├── Book1.xlsx              # Company profiles and nominal tool counts
│   └── Book2.xlsx              # Ground-truth Vernier caliper socket diameters
├── config/
│   ├── model_manifest.json     # Model path configuration
│   └── class_mapping.json      # 14-tool category mappings
├── data/
│   ├── calibration/            # RANSAC plane camera height and tilt parameters
│   ├── inspections/            # Persistent SQLite/JSON inspection records
│   └── layouts/                # Socket coordinate spatial layouts
├── Reports/                    # Generated audit-compliant PDF and JSON batch reports
└── output/                     # Inspection visual overlays and diagnostic renders
```

---

## 3. First-Time Setup & Installation

### Step 1: Transfer Application Folder to the Raspberry Pi
Copy the entire `07. Raspberry Pi 5 Application` folder to the Raspberry Pi user home directory, for example:
```bash
cp -r "07. Raspberry Pi 5 Application" ~/AXOVRIM
cd ~/AXOVRIM
```

### Step 2: Run the Automated Installer
Execute the installation script. This script automatically checks your ARM64 environment, installs system dependencies via `apt`, configures RealSense `udev` rules, creates an isolated virtual environment (`.venv`), and installs all Python dependencies:
```bash
chmod +x install_dependencies.sh
./install_dependencies.sh
```

### Step 3: Connect Camera & Display
1. Plug the micro-HDMI cable into **HDMI0** on the Raspberry Pi 5 and connect to your monitor.
2. Plug the Intel RealSense camera into one of the blue **USB 3.0** ports.
3. If this is the first time the camera has been connected, re-login or run:
   ```bash
   sudo udevadm control --reload-rules && sudo udevadm trigger
   ```

---

## 4. Running AXOVRIM

### Method A: From Terminal
```bash
./launch_axovrim.sh
```

### Method B: From Raspberry Pi Desktop (Shortcut)
1. Copy the desktop launcher to your desktop:
   ```bash
   cp axovrim.desktop ~/Desktop/
   chmod +x ~/Desktop/axovrim.desktop
   ```
2. Right-click the desktop icon and select **"Allow Launching"** (if prompted by the desktop manager).
3. Double-click the icon to open AXOVRIM.

---

## 5. System Verification & Diagnostics

Before beginning high-precision tool inspections, run the automated diagnostic verifier:
```bash
./check_system.sh
```
This tests CPU architecture, desktop session, PyTorch tensor execution, Ultralytics YOLOv11 loading, PyQt5 GUI bindings, RealSense USB hardware connection, and Excel workbook presence, outputting `check_system_report.txt`.

---

## 6. Daily Inspection Workflow

1. **Register Worker ID**:
   Enter your Operator ID (e.g. `WRK-001`) in the top-left panel and click **Register**.
2. **Select Company Profile**:
   Choose the target manufacturer from the dropdown (e.g. `Kinchrome`, `REDAI`, `Yash`, `Tektron`, `Ama`).
   The application loads tool counts from `Excel Sheet/Book1.xlsx` and socket specs from `Excel Sheet/Book2.xlsx`.
3. **Initialize Camera**:
   Click **Start Camera**. Live RGB and aligned depth streams will display in the primary viewport.
4. **Auto-Calibration (Fixture Setup)**:
   Ensure the inspection table is clear, open **Engineering Settings**, and click **Run Auto-Calibration**. The RANSAC spatial algorithm back-projects depth points, fits the fixture plane, and saves height/tilt parameters in `data/calibration/calibration.json`.
5. **Inspect Toolkit**:
   Position the toolkit in the camera field of view and click **Capture & Inspect**.
   - YOLOv11 segments all 14 tool categories.
   - 3D ray-to-plane metrology computes outer socket diameters.
   - PCA sequential sorting registers socket order (S01 to SN).
   - Expected counts are compared against ground truth.
6. **Save & Report**:
   Click **Save Results** to log inspection records into `data/inspections/`. Click **Generate Report** to produce an audit-compliant PDF report in `Reports/`.

---

## 7. Customization & Calibration

- **Editing Tool Quantities**: Open `Excel Sheet/Book1.xlsx` with LibreOffice Calc or Microsoft Excel to adjust expected counts for each category.
- **Editing Caliper References**: Open `Excel Sheet/Book2.xlsx` to update nominal socket diameters and tolerance thresholds.
- **RANSAC Calibration**: If the camera is remounted or adjusted, re-run auto-calibration in the GUI.

---

## 8. Troubleshooting & Common Issues

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `Camera Disconnected` | USB 2.0 port or insufficient USB power | Connect camera to blue USB 3.0 port. Use a powered USB 3.0 hub if camera disconnects during depth streaming. |
| `Permission denied` on `/dev/bus/usb` | Missing RealSense udev rules | Run `sudo cp /etc/udev/rules.d/99-realsense-libusb.rules` and verify current user is in `plugdev` group (`sudo usermod -a -G plugdev $USER`). |
| `Could not connect to display` | Launching over SSH without X11/Wayland | Run directly on the physical HDMI desktop session or use `ssh -X` with X11 forwarding. |
| `Wayland display error` | Missing qtwayland package | `launch_axovrim.sh` automatically falls back to `QT_QPA_PLATFORM=xcb`. Ensure `python3-pyqt5` is installed. |
| `Model file not found` | Relative path configuration | Verify `Models/best (2).pt` exists and matches `config/model_manifest.json`. |

---
**SmartLab — AXOVRIM Toolkit Metrology Team**
