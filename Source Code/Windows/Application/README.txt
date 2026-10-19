================================================================================
AXOVRIM — AI-Powered Toolkit Quality Inspection System
Standalone Industrial Metrology & Automated Optical Inspection Application
================================================================================

QUICK START GUIDE & OPERATING INSTRUCTIONS

1. DOWNLOAD AND FOLDER PLACEMENT
   - Download the entire '05. Application' folder from Google Drive to your local PC.
   - Place it in a directory where your Windows user has standard read/write permissions 
     (e.g., C:\AXOVRIM\ or your Desktop).
   - CRITICAL: Keep AXOVRIM.exe and all accompanying folders (_internal, Models, 
     Excel Sheet, config, data, Reports, output) together in the same directory.
     Do NOT move AXOVRIM.exe out of this folder.

2. HARDWARE & SYSTEM REQUIREMENTS
   - Operating System: Windows 10 (64-bit) or Windows 11 (64-bit).
   - Sensor: Intel RealSense D455 / D455F RGB-D Camera (or D435 / D435i).
   - Port: USB 3.0 / USB 3.2 Gen 1 (5 Gbps) high-speed USB port using an official 
     RealSense USB-C 3.x cable. USB 2.0 is not recommended for depth streaming.
   - System Runtimes: Microsoft Visual C++ 2015-2022 Redistributable (x64).
     (Included with most modern Windows installations; if needed, download from Microsoft:
     https://aka.ms/vs/17/release/vc_redist.x64.exe)

3. LAUNCHING THE APPLICATION
   - Double-click 'AXOVRIM.exe'.
   - The application starts directly as a standalone native Windows desktop application.
   - Python, PyTorch, CUDA, Ultralytics, or VS Code do NOT need to be installed.

4. STEP-BY-STEP WORKFLOW
   Step 1 — Register Worker ID:
     Enter your Operator / Worker ID in the top-left session control panel and click 'Register'.
     All subsequent inspections, logs, and batch reports are tied to this Worker ID.

   Step 2 — Select Company / Reference Profile:
     Select the target company from the dropdown menu (e.g., Kinchrome, REDAI, Yash, Tektron, Ama).
     The application dynamically loads expected toolkit component quantities from 'Excel Sheet/Book1.xlsx'
     and socket reference diameters from 'Excel Sheet/Book2.xlsx'.

   Step 3 — Camera Initialization & Live Streaming:
     Connect the Intel RealSense camera to a USB 3.0 port and click 'Start Camera' (or 'Reconnect Camera').
     The live RGB video stream and active telemetry will appear in the primary inspection viewport.

   Step 4 — Perform Inspection:
     Click 'Capture & Inspect' (or 'Run Inspection').
     The YOLOv11 instance segmentation AI engine segments all tools and sockets,
     the 3D ray-to-plane metrology calculates outer diameters, and the rigid registration
     algorithm matches detected sockets to the taught layout (S01 to SN).

   Step 5 — Review & Verify Results:
     - Review the tool counts table (Expected vs Detected vs Delta).
     - Review the socket outer diameter measurements and caliper error grid.
     - Review the overall status: PASS (Green), REVIEW (Amber), or FAIL (Red).
     - If necessary, an authorized supervisor can toggle manual overrides with audit tracking.

   Step 6 — Save Results & Generate Reports:
     - Click 'Save Results' to record the inspection into the persistent database ('data/inspections/').
     - Click 'Generate Report' to create an audit-compliant PDF batch report and structured JSON file.
     - Reports are automatically saved inside the 'Reports/' directory organized by Batch ID and Worker ID.

================================================================================
CUSTOMIZATION & REFERENCE EXCEL WORKBOOKS
================================================================================

The application reads its engineering references from external, editable Excel files:

1. 'Excel Sheet/Book1.xlsx':
   - Defines company profiles and expected tool counts across all 14 tool categories
     (Adaptor, Allen Key, Bit Holder, Bit Socket, Bits, Deep Socket, Extension Bar,
     Flex Handle, Long bit socket, Rachet Handle, S Handle, Sockets, Spanners, universal joint).
   - To add a company or change expected tool counts, edit Book1.xlsx in Microsoft Excel,
     save the file, and restart or select the company in AXOVRIM.

2. 'Excel Sheet/Book2.xlsx':
   - Contains high-precision Vernier caliper ground-truth diameters and nominal tolerances
     for sockets (S01 through SN) grouped by company.
   - Columns follow the format: [Socket ID], [Nominal Size (mm)], [Ref Outer Diameter (mm)].
   - Modifications made to Book2.xlsx take effect immediately on next inspection or reload.

================================================================================
CALIBRATION INSTRUCTIONS
================================================================================

The application includes an automated RANSAC 3D plane calibration system to establish
the exact height and tilt angle between the RealSense camera and the inspection fixture:

1. Open 'Engineering Settings' from the application menu or toolbar.
2. Ensure the inspection table surface is clear of foreign debris.
3. Click 'Run Auto-Calibration'.
4. The system back-projects the 3D depth point cloud, fits a spatial plane using RANSAC/SVD,
   and computes the camera mounting height (in mm) and fixture tilt angle (in degrees).
5. Click 'Save Calibration' to store parameters in 'data/calibration/calibration.json'.
   *Note: If the camera is moved or remounted, re-running auto-calibration is recommended.*

================================================================================
TROUBLESHOOTING & COMMON ISSUES
================================================================================

1. "Camera Disconnected" or "No RealSense devices found":
   - Ensure the RealSense camera is plugged into a USB 3.0 (blue/SS) port.
   - Try unplugging and re-inserting the USB cable.
   - Verify that the camera appears in Windows Device Manager under "Cameras"
     (Intel(R) RealSense(TM) Depth Camera).
   - If using a USB hub, ensure it is externally powered.
   - Click 'Reconnect Camera' in AXOVRIM.

2. "Model File Not Found":
   - Ensure 'Models/best (2).pt' exists inside the 'Models' folder next to AXOVRIM.exe.
   - Verify that 'config/model_manifest.json' specifies '"relative_path": "Models/best (2).pt"'.

3. "Company Reference Workbook Not Found":
   - Ensure 'Book1.xlsx' and 'Book2.xlsx' are present inside the 'Excel Sheet' subfolder.
   - Ensure the files are not locked exclusively by another program during application launch.

4. Permission / Save Errors:
   - Make sure the application folder is located on a writable local drive (e.g., C:\ or D:\)
     and not inside a write-restricted directory like C:\Program Files\ without administrative permissions.

================================================================================
SmartLab — AXOVRIM Toolkit Metrology Team
================================================================================
