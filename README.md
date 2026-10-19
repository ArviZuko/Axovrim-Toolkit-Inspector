# AXOVRIM — AI-Powered Toolkit Inspector

AXOVRIM is a desktop and Raspberry Pi 5 inspection system for checking whether an industrial toolkit contains the expected tools and whether sockets meet dimensional references. It combines instance segmentation, RGB-D camera measurements, configurable toolkit layouts, and recorded inspection decisions in one operator workflow.

## What makes it distinctive

- **Visual inventory and metrology together:** a YOLO segmentation model identifies individual tools and sockets, while depth-assisted geometry estimates socket outer diameters.
- **Reference-aware verification:** editable Excel workbooks hold company-specific tool counts and nominal socket measurements; JSON layout and calibration files support spatial matching.
- **Traceable decisions:** inspections associate results with a worker and batch, compare expected and observed values, allow audited review/overrides, and export PDF/JSON reports.
- **Two deployment targets:** a Windows PyQt5 application and a Raspberry Pi 5 build for edge inspection. The `Models` directories also preserve detection and segmentation experiments for comparison.

This is an inspection aid. Its measurements depend on camera calibration, depth quality, lighting, model performance, and the chosen reference data; verify tolerances against calibrated instruments before production use.

## Project layout

```text
Dataset/                       Annotated train/valid/test images and labels
Documentation/                 Final report and presentation
Screenshots/                   Main dashboard and inspection/report views
Source Code/
  Windows/
    SRC/                       PyQt5 application, launcher and build scripts
    Models/                    Detection and segmentation experiments/weights
    Application/               Windows executable and its configuration/assets
    Installer/                 Inno Setup source and installer output
  Raspberry Pi/                Pi app, setup scripts, model and configuration
requirements.txt              Windows source dependencies
```

The repository excludes the generated Windows `_internal` runtime, the oversized installer executable, and the oversized Mask R-CNN weight file because they exceed practical Git/GitHub limits. Their source files, build specification, experimental notebooks, and other model weights remain in the tree. To build a complete Windows distribution, use `Source Code/Windows/SRC/build_exe.bat` and the installer specification in `Source Code/Windows/Installer/AXOVRIM_Setup.iss`.

## Run from source on Windows

Use a 64-bit Python environment and an Intel RealSense D455/D455F (or compatible D435-series camera) connected over USB 3. Install dependencies in a virtual environment:

```powershell
cd "Source Code\Windows\SRC"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r ..\..\..\requirements.txt
python main.py
```

`run_app.bat` is an alternative launcher once `.venv` exists in `SRC`. The app looks for its model, Excel reference sheets, configuration, and writable data directories; keep the supplied directory structure intact. If a relative asset path does not resolve in your local setup, launch from the packaged `Application` directory or adjust the configured model paths in `config/model_manifest.json`.

For Raspberry Pi 5, follow [`Source Code/Raspberry Pi/README.md`](Source%20Code/Raspberry%20Pi/README.md), which includes ARM64 setup, system packages, RealSense installation, and `requirements-pi.txt`. Its installer script and `launch_axovrim.sh` are the intended entry points.

## Inspection workflow

1. Register a worker and choose a company/reference profile.
2. Connect and initialize the RealSense camera; capture a toolkit image.
3. Review segmented tool counts against `Book1.xlsx` and socket measurements against `Book2.xlsx`.
4. Review the PASS, REVIEW, or FAIL decision and any manual override.
5. Save the inspection and generate a PDF/JSON batch report.

See the [final report](Documentation/AXOVRIM_Final_Report.docx), [presentation](Documentation/AXOVRIM_Presentation.pptx), and [screenshots](Screenshots/) for the project background and interface.

## Model and data notes

The live application uses a YOLO instance-segmentation weight in its `Models` directory. Other `Source Code/Windows/Models` subfolders contain training notebooks, metrics, result plots, and alternative detection/segmentation weights. The `Dataset` folder contains image/label splits and a `data.yaml`; review its paths and class metadata before starting new training, as the checked-in YAML may need adjustment for your environment.

No accuracy, dimensional tolerance, or certification claim is implied by this repository; consult the included experimental results and validate with your own test set and calibrated hardware.
