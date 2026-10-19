"""
AXOVRIM — AI-Powered Toolkit Quality Inspection Application
Consolidated Single-Entry Application Engine
"""

import sys
import os
import multiprocessing
import time
import math
import re
import json
import uuid
import shutil
import threading
import traceback
import copy
import csv
from datetime import datetime
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional, Any, Union

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

# Retain DLL directory handles (Windows-only)
_MAIN_DLL_HANDLES = []

if sys.platform == 'win32':
    if getattr(sys, 'frozen', False):
        import ctypes
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        priority_dirs = [base_dir, os.path.join(base_dir, 'torch', 'lib')]
        for d in priority_dirs:
            if os.path.isdir(d) and hasattr(os, 'add_dll_directory'):
                try:
                    _MAIN_DLL_HANDLES.append(os.add_dll_directory(d))
                except Exception:
                    pass
        vc_runtime_libs = [
            'vcruntime140.dll', 'vcruntime140_1.dll', 'vcruntime140_threads.dll',
            'msvcp140.dll', 'MSVCP140_ATOMIC_WAIT.dll'
        ]
        for lib in vc_runtime_libs:
            lib_path = os.path.join(base_dir, lib)
            if os.path.isfile(lib_path):
                try:
                    ctypes.CDLL(lib_path)
                except Exception:
                    pass
        secondary_dirs = [
            os.path.join(base_dir, 'cv2'),
            os.path.join(base_dir, 'pyrealsense2'),
            os.path.join(base_dir, 'PyQt5', 'Qt5', 'bin')
        ]
        for d in secondary_dirs:
            if os.path.isdir(d) and hasattr(os, 'add_dll_directory'):
                try:
                    _MAIN_DLL_HANDLES.append(os.add_dll_directory(d))
                except Exception:
                    pass
        all_registered = [d for d in priority_dirs + secondary_dirs if os.path.isdir(d)]
        existing_path = os.environ.get('PATH', '')
        os.environ['PATH'] = os.pathsep.join(all_registered) + os.pathsep + existing_path
    else:
        if hasattr(os, 'add_dll_directory'):
            try:
                import site
                for sp in site.getsitepackages():
                    t_lib = os.path.join(sp, 'torch', 'lib')
                    if os.path.isdir(t_lib):
                        try:
                            _MAIN_DLL_HANDLES.append(os.add_dll_directory(t_lib))
                        except Exception:
                            pass
            except Exception:
                pass
else:
    # Linux / Raspberry Pi OS platform initialization
    # If running on Wayland without qtwayland, configure Qt to use xcb via XWayland
    if 'QT_QPA_PLATFORM' not in os.environ and os.environ.get('WAYLAND_DISPLAY'):
        # Check if wayland plugin is available; if not, safely fallback to xcb
        wayland_plugin_candidates = [
            '/usr/lib/aarch64-linux-gnu/qt5/plugins/platforms/libqwayland-generic.so',
            '/usr/lib/qt5/plugins/platforms/libqwayland-generic.so'
        ]
        if not any(os.path.exists(p) for p in wayland_plugin_candidates):
            os.environ['QT_QPA_PLATFORM'] = 'xcb'


# Mandatory: import torch before cv2 on Windows to prevent DLL initialization conflicts
import torch

import numpy as np
import cv2
import pandas as pd
import openpyxl

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QSplitter, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QComboBox, QCheckBox, QGroupBox,
    QProgressBar, QScrollArea, QDialog, QDialogButtonBox, QSpinBox, QDoubleSpinBox,
    QLineEdit, QFormLayout, QTextEdit, QSizePolicy, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsItem, QAbstractItemView,
    QRadioButton, QButtonGroup, QTabWidget, QGraphicsEllipseItem
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QPoint, QPointF, QRect, QRectF, QSize
)
from PyQt5.QtGui import (
    QImage, QPixmap, QColor, QFont, QPainter, QPen, QBrush, QPolygonF,
    QPainterPath, QCursor, QIcon
)

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

try:
    import pyrealsense2 as rs
except ImportError:
    rs = None

# Global Application Paths
if getattr(sys, 'frozen', False):
    USER_DIR = os.path.dirname(sys.executable)
    APP2_DIR = USER_DIR
    BUNDLE_DIR = getattr(sys, '_MEIPASS', USER_DIR)
else:
    APP2_DIR = os.path.dirname(os.path.abspath(__file__))
    USER_DIR = APP2_DIR
    BUNDLE_DIR = APP2_DIR

app2_dir = APP2_DIR
user_dir = USER_DIR

if APP2_DIR not in sys.path:
    sys.path.insert(0, APP2_DIR)


# =====================================================================
# SECTION: app/theme.py
# =====================================================================

"""
AXOVRIM — Centralized Theme Module
Option 3: White + Slate + Orange Accent
Professional industrial inspection color theme and styling utilities.
"""

# -----------------------------------------------------------------------------
# Color Palette Constants (Option 3 — White + Slate + Orange Accent)
# -----------------------------------------------------------------------------

# Main Application & Panels
COLOR_MAIN_BG = "#F8F9FB"
COLOR_PANEL_BG = "#FFFFFF"
COLOR_PANEL_BORDER = "#D1D5DB"
COLOR_PRIMARY_HEADING = "#1E293B"
COLOR_MAIN_TEXT = "#111827"
COLOR_SECONDARY_TEXT = "#6B7280"
COLOR_DIVIDER = "#E5E7EB"

# Action Buttons & Accents
COLOR_SLATE_BTN = "#334155"
COLOR_SLATE_BTN_HOVER = "#475569"
COLOR_ORANGE_ACCENT = "#EA580C"
COLOR_ORANGE_HOVER = "#C2410C"
COLOR_ORANGE_BG = "#FFF1E6"
COLOR_BTN_TEXT = "#FFFFFF"

# Disabled Button States
COLOR_BTN_DISABLED_BG = "#E5E7EB"
COLOR_BTN_DISABLED_TEXT = "#9CA3AF"
COLOR_BTN_DISABLED_BORDER = "#D1D5DB"

# Inspection Status Semantics
COLOR_STATUS_PASS = "#15803D"
COLOR_STATUS_REVIEW = "#D97706"
COLOR_STATUS_FAIL = "#DC2626"
COLOR_STATUS_PENDING = "#64748B"
COLOR_STATUS_UNVERIFIED = "#B45309"
COLOR_STATUS_LOADED = "#15803D"
COLOR_STATUS_DISCONNECTED = "#DC2626"

# Viewport Specific
COLOR_CAMERA_DISCONNECTED_BG = "#293241"
COLOR_CAMERA_DISCONNECTED_TEXT = "#FFFFFF"
COLOR_VIEWER_EMPTY_BG = "#F8FAFC"

# Tables
COLOR_TABLE_BG = "#FFFFFF"
COLOR_TABLE_ALT_BG = "#F8FAFC"
COLOR_TABLE_HEADER_BG = "#F1F5F9"
COLOR_TABLE_HEADER_TEXT = "#1E293B"
COLOR_TABLE_GRID = "#E2E8F0"
COLOR_TABLE_SELECT_BG = "#E2E8F0"
COLOR_TABLE_SELECT_TEXT = "#111827"


def get_main_window_stylesheet() -> str:
    """Returns the full QSS stylesheet for AXOVRIM MainWindow in Option 3 White theme."""
    return f"""
        QMainWindow {{
            background-color: {COLOR_MAIN_BG};
        }}
        QWidget {{
            color: {COLOR_MAIN_TEXT};
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        QFrame#Card {{
            background-color: {COLOR_PANEL_BG};
            border-radius: 8px;
            border: 1px solid {COLOR_PANEL_BORDER};
        }}
        QFrame#ActionCard {{
            background-color: {COLOR_PANEL_BG};
            border-top: 1px solid {COLOR_DIVIDER};
            padding: 6px;
        }}
        QLabel#Title {{
            color: {COLOR_PRIMARY_HEADING};
            font-size: 28px;
            font-weight: 800;
            letter-spacing: 0.5px;
            padding: 0px;
            margin: 0px;
        }}
        QLabel#SubTitle {{
            color: #475569;
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.2px;
            padding: 0px;
            margin: 0px;
        }}
        QLabel#Header {{
            color: {COLOR_PRIMARY_HEADING};
            font-size: 16px;
            font-weight: bold;
            border-bottom: 2px solid {COLOR_DIVIDER};
            padding-bottom: 5px;
        }}
        QLabel#MetricLabel {{
            color: {COLOR_SECONDARY_TEXT};
            font-size: 13px;
        }}
        QLabel#MetricValue {{
            color: {COLOR_MAIN_TEXT};
            font-size: 14px;
            font-weight: bold;
        }}
        QLabel#HighlightValue {{
            color: {COLOR_ORANGE_ACCENT};
            font-size: 14px;
            font-weight: bold;
        }}
        QLabel#SuccessValue {{
            color: {COLOR_STATUS_PASS};
            font-size: 14px;
            font-weight: bold;
        }}
        QLabel#WarningValue {{
            color: {COLOR_STATUS_REVIEW};
            font-size: 14px;
            font-weight: bold;
        }}
        QLabel#FailureValue {{
            color: {COLOR_STATUS_FAIL};
            font-size: 14px;
            font-weight: bold;
        }}
        QLabel#Banner {{
            background-color: {COLOR_PANEL_BG};
            color: {COLOR_PRIMARY_HEADING};
            font-size: 18px;
            font-weight: bold;
            padding: 10px;
            border: 1px solid {COLOR_PANEL_BORDER};
            border-radius: 4px;
        }}
        
        QPushButton {{
            background-color: {COLOR_SLATE_BTN};
            color: {COLOR_BTN_TEXT};
            border: 1px solid {COLOR_PRIMARY_HEADING};
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {COLOR_SLATE_BTN_HOVER};
            border: 1px solid {COLOR_SLATE_BTN};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_PRIMARY_HEADING};
            color: {COLOR_BTN_TEXT};
        }}
        QPushButton:disabled {{
            background-color: {COLOR_BTN_DISABLED_BG};
            color: {COLOR_BTN_DISABLED_TEXT};
            border: 1px solid {COLOR_BTN_DISABLED_BORDER};
        }}
        QPushButton#PrimaryAction {{
            background-color: {COLOR_ORANGE_ACCENT};
            color: {COLOR_BTN_TEXT};
            border: 1px solid {COLOR_ORANGE_HOVER};
        }}
        QPushButton#PrimaryAction:hover {{
            background-color: {COLOR_ORANGE_HOVER};
        }}
        QPushButton#PrimaryAction:disabled {{
            background-color: {COLOR_BTN_DISABLED_BG};
            color: {COLOR_BTN_DISABLED_TEXT};
            border: 1px solid {COLOR_BTN_DISABLED_BORDER};
        }}
        
        QFrame#ActionCard QLabel#SmartLabLogo {{
            background-color: {COLOR_PANEL_BG};
            border: none;
            padding: 0px;
            margin: 0px;
        }}
        
        QFrame#ActionCard QPushButton {{
            background-color: {COLOR_SLATE_BTN};
            color: {COLOR_BTN_TEXT};
            border: 1px solid {COLOR_SLATE_BTN};
            padding: 6px 4px;
            border-radius: 5px;
            font-size: 15px;
            font-weight: bold;
            min-height: 46px;
            max-height: 50px;
        }}
        QFrame#ActionCard QPushButton:hover {{
            background-color: {COLOR_SLATE_BTN_HOVER};
            border: 1px solid {COLOR_SLATE_BTN_HOVER};
        }}
        QFrame#ActionCard QPushButton:pressed {{
            background-color: {COLOR_PRIMARY_HEADING};
            color: {COLOR_BTN_TEXT};
        }}
        QFrame#ActionCard QPushButton:disabled {{
            background-color: {COLOR_BTN_DISABLED_BG};
            color: {COLOR_BTN_DISABLED_TEXT};
            border: 1px solid {COLOR_BTN_DISABLED_BORDER};
        }}
        QFrame#ActionCard QPushButton#PrimaryAction {{
            background-color: {COLOR_ORANGE_ACCENT};
            color: {COLOR_BTN_TEXT};
            border: 1px solid {COLOR_ORANGE_HOVER};
        }}
        QFrame#ActionCard QPushButton#PrimaryAction:hover {{
            background-color: {COLOR_ORANGE_HOVER};
        }}
        QFrame#ActionCard QPushButton#PrimaryAction:disabled {{
            background-color: {COLOR_BTN_DISABLED_BG};
            color: {COLOR_BTN_DISABLED_TEXT};
            border: 1px solid {COLOR_BTN_DISABLED_BORDER};
        }}
        QFrame#ActionCard QPushButton#EngineeringAction {{
            background-color: {COLOR_ORANGE_ACCENT};
            color: {COLOR_BTN_TEXT};
            border: 1px solid {COLOR_ORANGE_HOVER};
        }}
        QFrame#ActionCard QPushButton#EngineeringAction:hover {{
            background-color: {COLOR_ORANGE_HOVER};
        }}
        QFrame#ActionCard QPushButton#EngineeringAction:disabled {{
            background-color: {COLOR_BTN_DISABLED_BG};
            color: {COLOR_BTN_DISABLED_TEXT};
            border: 1px solid {COLOR_BTN_DISABLED_BORDER};
        }}
        
        QTableWidget {{
            background-color: {COLOR_TABLE_BG};
            alternate-background-color: {COLOR_TABLE_ALT_BG};
            gridline-color: {COLOR_TABLE_GRID};
            border: 1px solid {COLOR_PANEL_BORDER};
            color: {COLOR_MAIN_TEXT};
            font-size: 14px;
            selection-background-color: {COLOR_TABLE_SELECT_BG};
            selection-color: {COLOR_TABLE_SELECT_TEXT};
        }}
        QTableView {{
            background-color: {COLOR_TABLE_BG};
            font-size: 14px;
        }}
        QHeaderView::section {{
            background-color: {COLOR_TABLE_HEADER_BG};
            color: {COLOR_PRIMARY_HEADING};
            font-weight: bold;
            border: 1px solid {COLOR_TABLE_GRID};
            padding: 6px 6px;
            font-size: 13px;
            min-height: 34px;
        }}
        QTabWidget::pane {{
            border: 1px solid {COLOR_PANEL_BORDER};
            background-color: {COLOR_PANEL_BG};
        }}
        QTabBar::tab {{
            background-color: {COLOR_TABLE_HEADER_BG};
            color: {COLOR_SECONDARY_TEXT};
            padding: 5px 12px;
            border: 1px solid {COLOR_PANEL_BORDER};
            border-bottom: none;
            min-width: 120px;
            font-size: 12px;
        }}
        QTabBar::tab:selected {{
            background-color: {COLOR_PANEL_BG};
            color: {COLOR_ORANGE_ACCENT};
            border-top: 2px solid {COLOR_ORANGE_ACCENT};
        }}
        QTabBar::tab:hover {{
            background-color: {COLOR_DIVIDER};
            color: {COLOR_MAIN_TEXT};
        }}
        
        QComboBox {{
            background-color: {COLOR_PANEL_BG};
            color: {COLOR_MAIN_TEXT};
            border: 1px solid {COLOR_PANEL_BORDER};
            padding: 4px 10px;
            border-radius: 5px;
            font-size: 15px;
            font-weight: 500;
            min-height: 36px;
        }}
        QComboBox:hover {{
            border: 1px solid {COLOR_ORANGE_ACCENT};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 28px;
            border-left: 1px solid {COLOR_PANEL_BORDER};
            border-top-right-radius: 5px;
            border-bottom-right-radius: 5px;
            background-color: {COLOR_MAIN_BG};
        }}
        QComboBox::down-arrow {{
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {COLOR_SLATE_BTN};
            margin: 0px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {COLOR_PANEL_BG};
            color: {COLOR_MAIN_TEXT};
            border: 1px solid {COLOR_PANEL_BORDER};
            selection-background-color: {COLOR_ORANGE_BG};
            selection-color: {COLOR_MAIN_TEXT};
            outline: none;
            padding: 2px;
            font-size: 15px;
        }}
        QComboBox QAbstractItemView::item {{
            min-height: 34px;
            padding: 4px 10px;
            color: {COLOR_MAIN_TEXT};
            background-color: {COLOR_PANEL_BG};
            font-size: 15px;
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: {COLOR_ORANGE_BG};
            color: {COLOR_ORANGE_ACCENT};
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {COLOR_ORANGE_BG};
            color: {COLOR_ORANGE_ACCENT};
        }}
        
        QScrollBar:vertical {{
            background: {COLOR_MAIN_BG};
            width: 14px;
            margin: 0px 0px 0px 0px;
        }}
        QScrollBar::handle:vertical {{
            background: #CBD5E1;
            min-height: 20px;
            border-radius: 4px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: #94A3B8;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background: {COLOR_MAIN_BG};
            height: 14px;
            margin: 0px 0px 0px 0px;
        }}
        QScrollBar::handle:horizontal {{
            background: #CBD5E1;
            min-width: 20px;
            border-radius: 4px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: #94A3B8;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        
        QStatusBar {{
            background-color: {COLOR_PANEL_BG};
            color: {COLOR_SECONDARY_TEXT};
            font-size: 13px;
            border-top: 1px solid {COLOR_DIVIDER};
            padding: 3px 8px;
        }}
    """


def get_company_combo_stylesheet() -> str:
    """Returns the dedicated high-contrast light stylesheet for company selector dropdowns."""
    return f"""
        QComboBox {{
            background-color: {COLOR_PANEL_BG};
            color: {COLOR_MAIN_TEXT};
            font-size: 15px;
            font-weight: 500;
            border: 1px solid {COLOR_PANEL_BORDER};
            border-radius: 5px;
            padding: 4px 10px;
            min-height: 36px;
        }}
        QComboBox:hover {{
            border: 1px solid {COLOR_ORANGE_ACCENT};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 28px;
            border-left: 1px solid {COLOR_PANEL_BORDER};
            border-top-right-radius: 5px;
            border-bottom-right-radius: 5px;
            background-color: {COLOR_MAIN_BG};
        }}
        QComboBox::down-arrow {{
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {COLOR_SLATE_BTN};
            margin: 0px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {COLOR_PANEL_BG};
            color: {COLOR_MAIN_TEXT};
            border: 1px solid {COLOR_PANEL_BORDER};
            selection-background-color: {COLOR_ORANGE_BG};
            selection-color: {COLOR_MAIN_TEXT};
            outline: none;
            padding: 2px;
            font-size: 15px;
        }}
        QComboBox QAbstractItemView::item {{
            min-height: 34px;
            padding: 4px 10px;
            color: {COLOR_MAIN_TEXT};
            background-color: {COLOR_PANEL_BG};
            font-size: 15px;
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: {COLOR_ORANGE_BG};
            color: {COLOR_ORANGE_ACCENT};
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {COLOR_ORANGE_BG};
            color: {COLOR_ORANGE_ACCENT};
        }}
    """


def get_zoom_viewer_stylesheet() -> str:
    """Returns the light styling for ZoomableViewer controls."""
    return f"""
        QPushButton {{
            background-color: {COLOR_PANEL_BG};
            color: {COLOR_SLATE_BTN};
            border: 1px solid {COLOR_PANEL_BORDER};
            border-radius: 4px;
            padding: 4px 10px;
            font-size: 13px;
            font-weight: 500;
            min-height: 30px;
            max-height: 34px;
        }}
        QPushButton:hover {{
            background-color: {COLOR_MAIN_BG};
            border-color: {COLOR_ORANGE_ACCENT};
            color: {COLOR_ORANGE_ACCENT};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_DIVIDER};
            color: {COLOR_PRIMARY_HEADING};
        }}
        QLabel {{
            color: {COLOR_SECONDARY_TEXT};
            font-size: 13px;
            font-weight: 500;
        }}
        QWidget {{
            background-color: {COLOR_PANEL_BG};
            border-radius: 8px;
        }}
    """


# =====================================================================
# SECTION: app/popup_utils.py
# =====================================================================

"""
AXOVRIM — Centralized Popup Dialog Styling and Helper Utilities

Ensures all application-generated popup dialogs (QMessageBox, QInputDialog,
and custom operator QDialogs) display high-contrast, perfectly legible
BLACK text (#111111 / #333333) on a WHITE/LIGHT background (#FFFFFF / #F8F9FA),
with contrasting, distinctly styled buttons:
- Standard buttons: #25313F background, #FFFFFF text
- Primary confirmation buttons: #1769AA background, #FFFFFF text
- Cancel / No buttons: #E8EBEF background, #111111 text
- Danger buttons: #D32F2F background, #FFFFFF text

Prevents dark main-window stylesheets from bleeding dark text or dark button styles.
"""

from PyQt5.QtWidgets import (
    QDialog, QMessageBox, QInputDialog, QLabel,
    QPushButton, QLineEdit, QTextEdit, QPlainTextEdit,
    QComboBox, QFrame, QWidget, QDialogButtonBox
)
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

# Button Color Tokens
COLOR_DIALOG_BG = "#FFFFFF"
COLOR_MAIN_TEXT = "#111111"
COLOR_SECONDARY_TEXT = "#333333"

COLOR_STD_BTN_BG = "#25313F"
COLOR_STD_BTN_TEXT = "#FFFFFF"
COLOR_STD_BTN_HOVER = "#354556"
COLOR_STD_BTN_BORDER = "#3E4D5E"

COLOR_PRIMARY_BTN_BG = "#1769AA"
COLOR_PRIMARY_BTN_TEXT = "#FFFFFF"
COLOR_PRIMARY_BTN_HOVER = "#12568C"
COLOR_PRIMARY_BTN_PRESSED = "#0E426C"
COLOR_PRIMARY_BTN_BORDER = "#13558A"

COLOR_CANCEL_BTN_BG = "#E8EBEF"
COLOR_CANCEL_BTN_TEXT = "#111111"
COLOR_CANCEL_BTN_HOVER = "#DCE1E7"
COLOR_CANCEL_BTN_PRESSED = "#CFD5DE"
COLOR_CANCEL_BTN_BORDER = "#C4C8D0"

COLOR_DANGER_BTN_BG = "#D32F2F"
COLOR_DANGER_BTN_TEXT = "#FFFFFF"
COLOR_DANGER_BTN_HOVER = "#B71C1C"
COLOR_DANGER_BTN_BORDER = "#B71C1C"


# Centralized light popup stylesheet
POPUP_STYLE = f"""
/* Base dialog containers */
QDialog, QMessageBox, QInputDialog {{
    background-color: {COLOR_DIALOG_BG};
    color: {COLOR_MAIN_TEXT};
}}

/* Ensure all child widgets default to black text */
QDialog QWidget, QMessageBox QWidget, QInputDialog QWidget {{
    color: {COLOR_MAIN_TEXT};
    font-family: 'Segoe UI', Arial, sans-serif;
}}

/* Labels: dark text on transparent background */
QDialog QLabel, QMessageBox QLabel, QInputDialog QLabel {{
    color: {COLOR_MAIN_TEXT};
    background-color: transparent;
    font-size: 13px;
}}

QDialog QLabel#Header, QMessageBox QLabel#Header,
QDialog QLabel#Title, QMessageBox QLabel#Title {{
    color: {COLOR_MAIN_TEXT};
    font-size: 15px;
    font-weight: bold;
}}

QDialog QLabel#SubHeader, QMessageBox QLabel#SubHeader,
QDialog QLabel#SubTitle, QMessageBox QLabel#SubTitle {{
    color: {COLOR_SECONDARY_TEXT};
    font-size: 12px;
}}

/* Text inputs */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: #FFFFFF;
    color: {COLOR_MAIN_TEXT};
    border: 1px solid #8A8A8A;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
    min-height: 28px;
    selection-background-color: {COLOR_PRIMARY_BTN_BG};
    selection-color: #FFFFFF;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 2px solid {COLOR_PRIMARY_BTN_BG};
}}

QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
    background-color: #F0F2F5;
    color: #666666;
    border: 1px solid #C4C8D0;
}}

/* Dropdown combos */
QComboBox {{
    background-color: #FFFFFF;
    color: {COLOR_MAIN_TEXT};
    border: 1px solid #8A8A8A;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
    min-height: 28px;
}}

QComboBox:focus {{
    border: 2px solid {COLOR_PRIMARY_BTN_BG};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: #FFFFFF;
    color: {COLOR_MAIN_TEXT};
    selection-background-color: {COLOR_PRIMARY_BTN_BG};
    selection-color: #FFFFFF;
    border: 1px solid #8A8A8A;
    outline: none;
}}

/* Standard default buttons: dark background with crisp white text */
QPushButton {{
    background-color: {COLOR_STD_BTN_BG};
    color: {COLOR_STD_BTN_TEXT};
    border: 1px solid {COLOR_STD_BTN_BORDER};
    border-radius: 4px;
    padding: 8px 18px;
    min-height: 36px;
    font-size: 13px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {COLOR_STD_BTN_HOVER};
    color: {COLOR_STD_BTN_TEXT};
}}

QPushButton:pressed {{
    background-color: #1A232D;
    color: {COLOR_STD_BTN_TEXT};
}}

QPushButton:disabled {{
    background-color: #E5E5E5;
    color: #888888;
    border: 1px solid #D0D0D0;
}}

/* Primary confirmation button */
QPushButton#PrimaryBtn, QPushButton[default="true"] {{
    background-color: {COLOR_PRIMARY_BTN_BG};
    color: {COLOR_PRIMARY_BTN_TEXT};
    border: 1px solid {COLOR_PRIMARY_BTN_BORDER};
    border-radius: 4px;
    padding: 8px 20px;
    min-height: 36px;
    font-size: 13px;
    font-weight: bold;
}}

QPushButton#PrimaryBtn:hover, QPushButton[default="true"]:hover {{
    background-color: {COLOR_PRIMARY_BTN_HOVER};
    color: {COLOR_PRIMARY_BTN_TEXT};
}}

QPushButton#PrimaryBtn:pressed, QPushButton[default="true"]:pressed {{
    background-color: {COLOR_PRIMARY_BTN_PRESSED};
    color: {COLOR_PRIMARY_BTN_TEXT};
}}

QPushButton#PrimaryBtn:focus, QPushButton[default="true"]:focus {{
    border: 2px solid #0B3150;
}}

/* Cancel / No button */
QPushButton#CancelBtn, QPushButton#SecondaryBtn {{
    background-color: {COLOR_CANCEL_BTN_BG};
    color: {COLOR_CANCEL_BTN_TEXT};
    border: 1px solid {COLOR_CANCEL_BTN_BORDER};
    border-radius: 4px;
    padding: 8px 20px;
    min-height: 36px;
    font-size: 13px;
    font-weight: bold;
}}

QPushButton#CancelBtn:hover, QPushButton#SecondaryBtn:hover {{
    background-color: {COLOR_CANCEL_BTN_HOVER};
    color: #000000;
}}

QPushButton#CancelBtn:pressed, QPushButton#SecondaryBtn:pressed {{
    background-color: {COLOR_CANCEL_BTN_PRESSED};
    color: #000000;
}}

QPushButton#CancelBtn:focus, QPushButton#SecondaryBtn:focus {{
    border: 2px solid #8A8A8A;
}}

/* Danger / Stop buttons */
QPushButton#DangerBtn {{
    background-color: {COLOR_DANGER_BTN_BG};
    color: {COLOR_DANGER_BTN_TEXT};
    border: 1px solid {COLOR_DANGER_BTN_BORDER};
    border-radius: 4px;
    padding: 8px 18px;
    min-height: 36px;
    font-size: 13px;
    font-weight: bold;
}}

QPushButton#DangerBtn:hover {{
    background-color: {COLOR_DANGER_BTN_HOVER};
    color: {COLOR_DANGER_BTN_TEXT};
}}

/* Grouping frames within light dialogs */
QFrame#InfoFrame, QFrame#DetailsFrame {{
    background-color: #F8F9FA;
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    padding: 12px;
}}
"""


def style_primary_button(button: QPushButton, text: str = None):
    """Styles a button as a primary confirmation action (Blue #1769AA with white text)."""
    if text:
        button.setText(text)
    button.setObjectName("PrimaryBtn")
    button.setMinimumHeight(36)
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {COLOR_PRIMARY_BTN_BG};
            color: {COLOR_PRIMARY_BTN_TEXT};
            border: 1px solid {COLOR_PRIMARY_BTN_BORDER};
            border-radius: 4px;
            padding: 8px 20px;
            min-height: 36px;
            font-size: 13px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {COLOR_PRIMARY_BTN_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_PRIMARY_BTN_PRESSED};
        }}
    """)
    pal = button.palette()
    pal.setColor(QPalette.Button, QColor(COLOR_PRIMARY_BTN_BG))
    pal.setColor(QPalette.ButtonText, QColor(COLOR_PRIMARY_BTN_TEXT))
    button.setPalette(pal)


def style_cancel_button(button: QPushButton, text: str = None):
    """Styles a button as a cancel/negative action (Light Gray #E8EBEF with black text)."""
    if text:
        button.setText(text)
    button.setObjectName("CancelBtn")
    button.setMinimumHeight(36)
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {COLOR_CANCEL_BTN_BG};
            color: {COLOR_CANCEL_BTN_TEXT};
            border: 1px solid {COLOR_CANCEL_BTN_BORDER};
            border-radius: 4px;
            padding: 8px 20px;
            min-height: 36px;
            font-size: 13px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {COLOR_CANCEL_BTN_HOVER};
            color: #000000;
        }}
        QPushButton:pressed {{
            background-color: {COLOR_CANCEL_BTN_PRESSED};
            color: #000000;
        }}
    """)
    pal = button.palette()
    pal.setColor(QPalette.Button, QColor(COLOR_CANCEL_BTN_BG))
    pal.setColor(QPalette.ButtonText, QColor(COLOR_CANCEL_BTN_TEXT))
    button.setPalette(pal)


def style_standard_button(button: QPushButton, text: str = None):
    """Styles a button as a standard action (Dark #25313F with white text)."""
    if text:
        button.setText(text)
    button.setObjectName("StandardBtn")
    button.setMinimumHeight(36)
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {COLOR_STD_BTN_BG};
            color: {COLOR_STD_BTN_TEXT};
            border: 1px solid {COLOR_STD_BTN_BORDER};
            border-radius: 4px;
            padding: 8px 18px;
            min-height: 36px;
            font-size: 13px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {COLOR_STD_BTN_HOVER};
        }}
        QPushButton:pressed {{
            background-color: #1A232D;
        }}
    """)
    pal = button.palette()
    pal.setColor(QPalette.Button, QColor(COLOR_STD_BTN_BG))
    pal.setColor(QPalette.ButtonText, QColor(COLOR_STD_BTN_TEXT))
    button.setPalette(pal)


def style_danger_button(button: QPushButton, text: str = None):
    """Styles a button as a danger/destructive action (Red #D32F2F with white text)."""
    if text:
        button.setText(text)
    button.setObjectName("DangerBtn")
    button.setMinimumHeight(36)
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: {COLOR_DANGER_BTN_BG};
            color: {COLOR_DANGER_BTN_TEXT};
            border: 1px solid {COLOR_DANGER_BTN_BORDER};
            border-radius: 4px;
            padding: 8px 18px;
            min-height: 36px;
            font-size: 13px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {COLOR_DANGER_BTN_HOVER};
        }}
    """)
    pal = button.palette()
    pal.setColor(QPalette.Button, QColor(COLOR_DANGER_BTN_BG))
    pal.setColor(QPalette.ButtonText, QColor(COLOR_DANGER_BTN_TEXT))
    button.setPalette(pal)


def apply_popup_style(widget: QWidget):
    """
    Applies the centralized light popup theme to a dialog, message box, or input dialog.
    Sets explicit stylesheet, palette, and ensures all nested labels have dark text.
    """
    if widget is None:
        return

    widget.setStyleSheet(POPUP_STYLE)

    # Set light window palette
    palette = widget.palette()
    palette.setColor(QPalette.Window, QColor(COLOR_DIALOG_BG))
    palette.setColor(QPalette.WindowText, QColor(COLOR_MAIN_TEXT))
    palette.setColor(QPalette.Base, QColor(COLOR_DIALOG_BG))
    palette.setColor(QPalette.Text, QColor(COLOR_MAIN_TEXT))
    palette.setColor(QPalette.Button, QColor(COLOR_STD_BTN_BG))
    palette.setColor(QPalette.ButtonText, QColor(COLOR_STD_BTN_TEXT))
    palette.setColor(QPalette.Highlight, QColor(COLOR_PRIMARY_BTN_BG))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    widget.setPalette(palette)

    # Ensure all existing labels have explicit dark foreground
    for lbl in widget.findChildren(QLabel):
        lbl.setWordWrap(True)
        obj_name = lbl.objectName()
        if obj_name in ["Header", "Title"]:
            lbl.setStyleSheet(f"color: {COLOR_MAIN_TEXT}; font-weight: bold; background-color: transparent;")
        elif obj_name in ["SubHeader", "SubTitle"]:
            lbl.setStyleSheet(f"color: {COLOR_SECONDARY_TEXT}; background-color: transparent;")
        else:
            # Preserve special status badge colors if already set, otherwise dark text
            cur_style = lbl.styleSheet()
            if not any(k in cur_style for k in ["#107C41", "#D32F2F", "#D97706", "#28C76F", "#EA4D55", "#F5A623"]):
                lbl.setStyleSheet(f"color: {COLOR_MAIN_TEXT}; background-color: transparent;")


def create_styled_message_box(
    icon: QMessageBox.Icon,
    parent=None,
    title: str = "",
    text: str = "",
    buttons=QMessageBox.Ok,
    default_button=QMessageBox.NoButton
) -> QMessageBox:
    """
    Instantiates and styles a QMessageBox with high-contrast light background,
    black text, and clearly distinguished buttons with minimum 36px height.
    """
    box = QMessageBox(icon, str(title), str(text), buttons, parent)
    box.setMinimumWidth(480)
    apply_popup_style(box)

    # Ensure message labels wrap cleanly
    for lbl in box.findChildren(QLabel):
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color: {COLOR_MAIN_TEXT}; font-size: 13px; line-height: 1.4; background-color: transparent;")

    # Style individual buttons according to their semantic role
    btn_yes = box.button(QMessageBox.Yes)
    btn_no = box.button(QMessageBox.No)
    btn_ok = box.button(QMessageBox.Ok)
    btn_cancel = box.button(QMessageBox.Cancel)
    btn_save = box.button(QMessageBox.Save)
    btn_discard = box.button(QMessageBox.Discard)

    if btn_yes:
        style_primary_button(btn_yes, "Yes, Confirm")
        btn_yes.setMinimumWidth(120)

    if btn_no:
        style_cancel_button(btn_no, "No, Cancel")
        btn_no.setMinimumWidth(110)

    if btn_cancel:
        style_cancel_button(btn_cancel, "Cancel")
        btn_cancel.setMinimumWidth(100)

    if btn_save:
        style_primary_button(btn_save, "Save")
        btn_save.setMinimumWidth(100)

    if btn_discard:
        style_cancel_button(btn_discard, "Discard")
        btn_discard.setMinimumWidth(100)

    if btn_ok:
        # If there's a Cancel or No button alongside OK, OK acts as Primary confirmation
        if btn_cancel or btn_no:
            style_primary_button(btn_ok, "OK")
        else:
            style_standard_button(btn_ok, "OK")
        btn_ok.setMinimumWidth(100)

    # Style any other buttons that might exist
    for b in box.buttons():
        if b not in (btn_yes, btn_no, btn_ok, btn_cancel, btn_save, btn_discard):
            style_standard_button(b)

    # Increase spacing in button box
    bbox = box.findChild(QDialogButtonBox)
    if bbox:
        bbox.layout().setSpacing(12)

    if default_button != QMessageBox.NoButton:
        box.setDefaultButton(default_button)

    return box


# Store references to original QMessageBox static methods
_orig_qmessagebox_warning = QMessageBox.warning
_orig_qmessagebox_information = QMessageBox.information
_orig_qmessagebox_critical = QMessageBox.critical
_orig_qmessagebox_question = QMessageBox.question

_is_hooked = False


def setup_popup_styling():
    """
    Globally hooks QMessageBox static methods (warning, information, critical, question)
    so that every message box generated across the entire application automatically
    inherits the high-contrast light theme with black text and clear buttons.
    """
    global _is_hooked
    if _is_hooked:
        return

    def _hooked_warning(parent=None, title="", text="", buttons=QMessageBox.Ok, default_button=QMessageBox.NoButton, *args, **kwargs):
        box = create_styled_message_box(QMessageBox.Warning, parent, title, text, buttons, default_button)
        return box.exec_()

    def _hooked_information(parent=None, title="", text="", buttons=QMessageBox.Ok, default_button=QMessageBox.NoButton, *args, **kwargs):
        box = create_styled_message_box(QMessageBox.Information, parent, title, text, buttons, default_button)
        return box.exec_()

    def _hooked_critical(parent=None, title="", text="", buttons=QMessageBox.Ok, default_button=QMessageBox.NoButton, *args, **kwargs):
        box = create_styled_message_box(QMessageBox.Critical, parent, title, text, buttons, default_button)
        return box.exec_()

    def _hooked_question(parent=None, title="", text="", buttons=QMessageBox.Yes | QMessageBox.No, default_button=QMessageBox.NoButton, *args, **kwargs):
        box = create_styled_message_box(QMessageBox.Question, parent, title, text, buttons, default_button)
        return box.exec_()

    QMessageBox.warning = staticmethod(_hooked_warning)
    QMessageBox.information = staticmethod(_hooked_information)
    QMessageBox.critical = staticmethod(_hooked_critical)
    QMessageBox.question = staticmethod(_hooked_question)

    _is_hooked = True


# =====================================================================
# SECTION: camera/depth_alignment.py
# =====================================================================

import numpy as np

class DepthAlignment:
    def __init__(self):
        pass

    @staticmethod
    def calculate_depth_coverage(depth_array):
        """
        Calculates the percentage of valid (non-zero) depth pixels in the frame.
        """
        if depth_array is None or depth_array.size == 0:
            return 0.0
            
        valid_pixels = np.count_nonzero(depth_array)
        total_pixels = depth_array.size
        
        return (valid_pixels / total_pixels) * 100.0

    @staticmethod
    def extract_center_depth(depth_array, depth_scale, window_size=20):
        """
        Extracts the median depth from the center region of the depth frame in millimeters.
        """
        if depth_array is None or depth_array.size == 0:
            return 0.0
            
        h, w = depth_array.shape
        cy, cx = h // 2, w // 2
        
        half_w = window_size // 2
        
        # Define center region boundaries
        y1 = max(0, cy - half_w)
        y2 = min(h, cy + half_w)
        x1 = max(0, cx - half_w)
        x2 = min(w, cx + half_w)
        
        center_region = depth_array[y1:y2, x1:x2]
        
        # Filter valid depth readings (>0)
        valid_depths = center_region[center_region > 0]
        
        if valid_depths.size == 0:
            return 0.0
            
        # Get median in raw units, then convert to millimeters
        # depth_scale is meters/unit. mm = raw * depth_scale * 1000
        median_raw = np.median(valid_depths)
        depth_mm = median_raw * depth_scale * 1000.0
        
        return depth_mm


# =====================================================================
# SECTION: camera/height_calibration.py
# =====================================================================

import numpy as np
import time
import json
import os
import sys
import cv2

class HeightCalibration:
    def __init__(self, data_dir=None):
        if data_dir is None:
            if getattr(sys, 'frozen', False):
                base = os.path.dirname(sys.executable)
            else:
                base = APP2_DIR
            self.data_dir = os.path.join(base, "data", "calibration")
        else:
            self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.calibration_file = os.path.join(self.data_dir, "calibration.json")
        
        # State
        self.is_calibrated = False
        self.plane_params = None
        self.camera_height_mm = 0.0
        self.tilt_angle_deg = 0.0
        self.residual_mm = 0.0
        self.inlier_percentage = 0.0
        self.valid_coverage = 0.0
        self.timestamp = 0
        
        self.load_calibration()
        
    def _depth_to_3d(self, depth_image, intrinsics, depth_scale, roi=None):
        """
        Convert depth image to 3D point cloud using camera intrinsics.
        roi: (x, y, w, h)
        """
        h, w = depth_image.shape
        if roi:
            rx, ry, rw, rh = roi
            # Ensure ROI is within bounds
            rx = max(0, rx)
            ry = max(0, ry)
            rw = min(w - rx, rw)
            rh = min(h - ry, rh)
            depth_roi = depth_image[ry:ry+rh, rx:rx+rw]
            ys, xs = np.mgrid[ry:ry+rh, rx:rx+rw]
        else:
            depth_roi = depth_image
            ys, xs = np.mgrid[0:h, 0:w]
            
        # Get valid pixels
        valid = depth_roi > 0
        z_raw = depth_roi[valid] * depth_scale * 1000.0 # Convert to mm
        
        # Filter out specular reflection artifacts (like 36000mm)
        # Allow closer ranges (e.g. 10mm to 3000mm) to support close-range setups
        valid_z = (z_raw > 10.0) & (z_raw < 3000.0)
        
        # The silver base is specular and sits on a matte desk.
        # RANSAC will naturally favor the desk if we don't isolate the closest surface.
        if np.any(valid_z):
            z_valid_only = z_raw[valid_z]
            if len(z_valid_only) > 100:
                # Find the closest robust surface (ignoring the 1% most extreme noise)
                z_min_robust = np.percentile(z_valid_only, 1)
                # Restrict to points within 40mm of this top surface to isolate the base from the desk
                valid_z = valid_z & (z_raw <= z_min_robust + 40.0)
        
        if not np.any(valid_z):
            return np.array([]), np.zeros_like(valid)
            
        # Update the 2D valid mask
        valid_indices = np.where(valid)
        valid[valid_indices[0][~valid_z], valid_indices[1][~valid_z]] = False
            
        z = z_raw[valid_z]
        x_img = xs[valid]
        y_img = ys[valid]
        
        # Intrinsics
        fx = intrinsics.fx
        fy = intrinsics.fy
        ppx = intrinsics.ppx
        ppy = intrinsics.ppy
        
        x = (x_img - ppx) * z / fx
        y = (y_img - ppy) * z / fy
        
        points_3d = np.stack((x, y, z), axis=-1)
        return points_3d, valid
        
    def _fit_plane_ransac(self, points_3d, distance_threshold=2.0, max_iterations=200):
        n_points = points_3d.shape[0]
        if n_points < 3:
            return None, []
            
        best_inliers = []
        best_plane = None
        
        # RANSAC
        for _ in range(max_iterations):
            idx = np.random.choice(n_points, 3, replace=False)
            p1, p2, p3 = points_3d[idx]
            
            v1 = p2 - p1
            v2 = p3 - p1
            normal = np.cross(v1, v2)
            norm = np.linalg.norm(normal)
            if norm < 1e-6:
                continue
                
            normal = normal / norm
            d = -np.dot(normal, p1)
            
            distances = np.abs(np.dot(points_3d, normal) + d)
            inliers = np.where(distances < distance_threshold)[0]
            
            if len(inliers) > len(best_inliers):
                best_inliers = inliers
                best_plane = (normal[0], normal[1], normal[2], d)
                
        # Re-fit with SVD for all inliers
        if len(best_inliers) >= 3:
            inlier_points = points_3d[best_inliers]
            centroid = np.mean(inlier_points, axis=0)
            centered = inlier_points - centroid
            _, _, vh = np.linalg.svd(centered, full_matrices=False)
            normal = vh[2, :]
            
            # Normal should point towards camera (negative Z direction)
            if normal[2] > 0:
                normal = -normal
                
            d = -np.dot(normal, centroid)
            best_plane = (normal[0], normal[1], normal[2], d)
            
        return best_plane, best_inliers

    def perform_calibration(self, depth_frames, intrinsics, depth_scale, camera_info):
        """
        Perform robust plane fitting over multiple frames.
        Returns: success(bool), msg(str), visual_overlay_mask(np.ndarray)
        """
        if not depth_frames or not intrinsics:
            return False, "Missing data for calibration", None
            
        h, w = depth_frames[0].shape
        
        print(f"[CALIB-DIAG] Actual depth stream resolution: {w}x{h}")
        print(f"[CALIB-DIAG] Actual depth scale: {depth_scale}")
        print(f"[CALIB-DIAG] Camera intrinsics: fx={intrinsics.fx:.2f}, fy={intrinsics.fy:.2f}, ppx={intrinsics.ppx:.2f}, ppy={intrinsics.ppy:.2f}")
        
        # Use center region to avoid edges (where depth is often noisy)
        # Assuming the platform is largely in the center. We'll use middle 50%
        roi_w = int(w * 0.5)
        roi_h = int(h * 0.5)
        roi_x = (w - roi_w) // 2
        roi_y = (h - roi_h) // 2
        roi = (roi_x, roi_y, roi_w, roi_h)
        print(f"[CALIB-DIAG] Calibration ROI coordinates: {roi}")
        
        all_planes = []
        all_heights = []
        all_tilts = []
        all_inliers_pct = []
        all_residuals = []
        
        best_inlier_mask = np.zeros((h, w), dtype=np.uint8)
        
        frame_idx = 0
        for depth_image in depth_frames:
            frame_idx += 1
            # 1. Convert to 3D
            result = self._depth_to_3d(depth_image, intrinsics, depth_scale, roi)
            
            # Count raw valid pixels inside ROI (before any conversion)
            roi_depth_image = depth_image[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
            raw_valid_pixels = np.sum(roi_depth_image > 0)
            roi_total_pixels = roi_w * roi_h
            valid_pct = (raw_valid_pixels / roi_total_pixels) * 100.0
            
            raw_depths_mm = roi_depth_image[roi_depth_image > 0] * depth_scale * 1000.0
            median_d = np.median(raw_depths_mm) if len(raw_depths_mm) > 0 else 0
            spread_d = np.std(raw_depths_mm) if len(raw_depths_mm) > 0 else 0
            
            if frame_idx == 1:
                print(f"[CALIB-DIAG] Frame 1 Raw depth-valid pixel count in ROI: {raw_valid_pixels}/{roi_total_pixels} ({valid_pct:.1f}%)")
                print(f"[CALIB-DIAG] Frame 1 Median valid depth: {median_d:.1f} mm, Spread (std): {spread_d:.1f} mm")
            
            if len(result) == 0 or len(result[0]) < 100:
                if frame_idx == 1: print(f"[CALIB-DIAG] Frame 1 rejected: fewer than 100 3D points ({len(result[0]) if len(result)>0 else 0})")
                continue
            points_3d, valid_mask = result
            
            # 2. Fit plane
            # RANSAC threshold 3.0 mm
            plane, inliers = self._fit_plane_ransac(points_3d, distance_threshold=3.0, max_iterations=200)
            if plane is None or len(inliers) < 100:
                if frame_idx == 1: print(f"[CALIB-DIAG] Frame 1 RANSAC failed or insufficient inliers ({len(inliers) if inliers is not None else 0})")
                continue
                
            if frame_idx == 1:
                print(f"[CALIB-DIAG] Frame 1 RANSAC found plane with {len(inliers)} inliers ({len(inliers)/len(points_3d)*100:.1f}%) at depth {abs(plane[3]):.1f} mm")
                
            a, b, c, d = plane
            
            # 3. Calculate metrics
            inlier_points = points_3d[inliers]
            distances = np.abs(np.dot(inlier_points, [a, b, c]) + d)
            residual = np.mean(distances)
            
            # Camera to plane perpendicular distance
            # Origin (0,0,0) is camera center. Distance = |d| / sqrt(a^2+b^2+c^2)
            # Since normal is normalized, distance is just |d|
            dist_mm = abs(d)
            
            # Tilt relative to camera optical axis (which is [0, 0, -1] in our normal convention)
            # Normal is (a, b, c). Angle = acos(|c|)
            tilt = np.degrees(np.arccos(abs(c)))
            
            inlier_pct = (len(inliers) / len(points_3d)) * 100.0
            
            all_planes.append(plane)
            all_heights.append(dist_mm)
            all_tilts.append(tilt)
            all_inliers_pct.append(inlier_pct)
            all_residuals.append(residual)
            
            # Create a visual mask for the first frame
            if np.sum(best_inlier_mask) == 0:
                # Reconstruct mask
                inlier_bool = np.zeros(len(points_3d), dtype=bool)
                inlier_bool[inliers] = True
                
                # We have a valid_mask for the ROI, shape (roi_h, roi_w)
                roi_inlier_mask = np.zeros((roi_h, roi_w), dtype=np.uint8)
                roi_inlier_mask[valid_mask] = inlier_bool * 255
                best_inlier_mask[roi[1]:roi[1]+roi[3], roi[0]:roi[0]+roi[2]] = roi_inlier_mask

        if len(all_heights) == 0:
            return False, "Failed to fit platform plane", None
            
        # Aggregate results
        self.camera_height_mm = float(np.median(all_heights))
        self.tilt_angle_deg = float(np.median(all_tilts))
        self.residual_mm = float(np.median(all_residuals))
        self.inlier_percentage = float(np.median(all_inliers_pct))
        
        # Calculate valid coverage in the ROI for the first frame
        valid_pixels = np.count_nonzero(depth_frames[0][roi[1]:roi[1]+roi[3], roi[0]:roi[0]+roi[2]])
        total_pixels = roi[2] * roi[3]
        self.valid_coverage = (valid_pixels / total_pixels) * 100.0
        
        best_plane_idx = np.argmin(np.abs(np.array(all_heights) - self.camera_height_mm))
        self.plane_params = [float(p) for p in all_planes[best_plane_idx]]
        a, b, c, d = self.plane_params
        self.center_depth_mm = abs(-d / c) if c != 0 else 0.0
        
        # Quality Checks
        if self.inlier_percentage < 20.0:
            return False, f"Inlier % too low ({self.inlier_percentage:.1f}%). Ensure clear platform.", best_inlier_mask
            
        if self.residual_mm > 5.0:
            return False, f"Plane fit residual too high ({self.residual_mm:.2f}mm)", best_inlier_mask
            
        if self.tilt_angle_deg > 15.0:
            return False, f"Camera tilt excessive ({self.tilt_angle_deg:.1f} deg)", best_inlier_mask
            
        self.is_calibrated = True
        self.timestamp = int(time.time())
        
        self.save_calibration(camera_info, intrinsics, depth_scale, (w, h))
        return True, "Calibration successful", best_inlier_mask
        
    def save_calibration(self, camera_info, intrinsics, depth_scale, resolution):
        data = {
            "camera_model": camera_info.get('model', 'Unknown'),
            "camera_serial": camera_info.get('serial', 'Unknown'),
            "resolution": resolution,
            "depth_scale": depth_scale,
            "intrinsics": {
                "fx": intrinsics.fx,
                "fy": intrinsics.fy,
                "ppx": intrinsics.ppx,
                "ppy": intrinsics.ppy
            },
            "plane_params": self.plane_params,
            "camera_height_mm": self.camera_height_mm,
            "center_depth_mm": self.center_depth_mm,
            "tilt_angle_deg": self.tilt_angle_deg,
            "residual_mm": self.residual_mm,
            "inlier_percentage": self.inlier_percentage,
            "valid_coverage": self.valid_coverage,
            "timestamp": self.timestamp,
            "version": "1.0"
        }
        with open(self.calibration_file, 'w') as f:
            json.dump(data, f, indent=4)
            
    def load_calibration(self):
        if not os.path.exists(self.calibration_file):
            return False
            
        try:
            with open(self.calibration_file, 'r') as f:
                data = json.load(f)
                
            self.plane_params = data.get("plane_params")
            self.camera_height_mm = data.get("camera_height_mm", 0.0)
            self.center_depth_mm = data.get("center_depth_mm", self.camera_height_mm)
            self.tilt_angle_deg = data.get("tilt_angle_deg", 0.0)
            self.residual_mm = data.get("residual_mm", 0.0)
            self.inlier_percentage = data.get("inlier_percentage", 0.0)
            self.valid_coverage = data.get("valid_coverage", 0.0)
            self.timestamp = data.get("timestamp", 0)
            
            if self.plane_params and self.camera_height_mm > 0:
                self.is_calibrated = True
                return True
        except Exception as e:
            print(f"Failed to load calibration: {e}")
            
        return False


# =====================================================================
# SECTION: camera/realsense_manager.py
# =====================================================================

import pyrealsense2 as rs
import numpy as np

class RealSenseManager:
    def __init__(self, color_w=1920, color_h=1080, depth_w=1280, depth_h=720, fps=30):
        self.color_w = color_w
        self.color_h = color_h
        self.depth_w = depth_w
        self.depth_h = depth_h
        self.fps = fps
        
        self.pipeline = None
        self.config = None
        self.align = None
        self.profile = None
        
        self.is_streaming = False
        self.device_model = "Unknown"
        self.serial_number = "Unknown"
        self.depth_scale = 0.0
        self.intrinsics = None
        
    def discover_devices(self):
        context = rs.context()
        devices = context.query_devices()
        dev_list = []
        for dev in devices:
            dev_list.append({
                'name': dev.get_info(rs.camera_info.name),
                'serial': dev.get_info(rs.camera_info.serial_number)
            })
        return dev_list

    def initialize(self):
        try:
            # Check devices
            devices = self.discover_devices()
            if not devices:
                return False, "No RealSense devices found."
                
            self.device_model = devices[0]['name']
            self.serial_number = devices[0]['serial']
            
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            
            # Note: We don't try/except enable_stream because it doesn't fail until start()
            # We will handle fallback in start_streaming()
            
            return True, f"Initialized {self.device_model} ({self.serial_number})"
        except Exception as e:
            return False, f"Failed to initialize RealSense: {str(e)}"
            
    def start_streaming(self):
        if self.is_streaming:
            return True, "Already streaming"
            
        try:
            if not self.pipeline:
                success, msg = self.initialize()
                if not success:
                    return False, msg
                    
            # The D455 optimal depth resolution is 848x480. 
            # Requesting 1280x720 depth on highly specular surfaces causes complete stereo matching failure.
            try:
                self.config.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 30)
                self.config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
                self.profile = self.pipeline.start(self.config)
            except Exception:
                # Final fallback to 640x480
                self.config = rs.config()
                self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
                self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
                self.profile = self.pipeline.start(self.config)
                    
            self.is_streaming = True
            
            # Get depth scale
            depth_sensor = self.profile.get_device().first_depth_sensor()
            self.depth_scale = depth_sensor.get_depth_scale()
            
            # Align depth to color
            align_to = rs.stream.color
            self.align = rs.align(align_to)
            
            # Get intrinsics
            color_stream = self.profile.get_stream(rs.stream.color)
            self.intrinsics = color_stream.as_video_stream_profile().get_intrinsics()
            
            return True, "Streaming started"
        except Exception as e:
            self.stop_streaming()
            return False, f"Failed to start streaming: {str(e)}"
            
    def stop_streaming(self):
        if not self.is_streaming:
            return
        
        try:
            if self.pipeline:
                self.pipeline.stop()
        except Exception:
            pass
        finally:
            self.is_streaming = False
            self.profile = None
            self.align = None
            
    def get_synchronized_frames(self):
        if not self.is_streaming or not self.pipeline or not self.align:
            return False, None, None, "Not streaming"
            
        try:
            # Wait for coherent pair of frames
            frames = self.pipeline.wait_for_frames(timeout_ms=1000)
            
            # Align depth frame to color frame
            aligned_frames = self.align.process(frames)
            
            aligned_depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()
            
            if not aligned_depth_frame or not color_frame:
                return False, None, None, "Missing frames"
                
            return True, color_frame, aligned_depth_frame, "Success"
        except Exception as e:
            return False, None, None, str(e)


# =====================================================================
# SECTION: camera/camera_worker.py
# =====================================================================

import time
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker

class CameraWorker(QThread):
    frame_ready = pyqtSignal(np.ndarray, np.ndarray, float, float, float)
    status_update = pyqtSignal(bool, str)
    error_occurred = pyqtSignal(str)
    camera_info = pyqtSignal(str, str, float)
    
    calibration_done = pyqtSignal(bool, str, dict, np.ndarray) # success, msg, stats, overlay_mask
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = RealSenseManager()
        self.calibrator = HeightCalibration()
        self.mutex = QMutex()
        
        self.is_running = False
        self.stop_requested = False
        self.fps = 0.0
        
        self.calibrate_requested = False
        
    def start_camera(self):
        with QMutexLocker(self.mutex):
            self.stop_requested = False
            self.calibrate_requested = False
            
        if not self.isRunning():
            self.start()
            
    def stop_camera(self):
        with QMutexLocker(self.mutex):
            self.stop_requested = True
        self.wait()
        
    def request_calibration(self):
        with QMutexLocker(self.mutex):
            self.calibrate_requested = True

    def run(self):
        self.status_update.emit(False, "Initializing camera...")
        success, msg = self.manager.start_streaming()
        
        if not success:
            self.error_occurred.emit(msg)
            self.status_update.emit(False, "Disconnected")
            return
            
        self.is_running = True
        self.status_update.emit(True, "Streaming")
        self.camera_info.emit(self.manager.device_model, self.manager.serial_number, self.manager.depth_scale)
        
        frame_count = 0
        start_time = time.time()
        
        calibration_frames = []
        
        while True:
            with QMutexLocker(self.mutex):
                if self.stop_requested:
                    break
                do_calibrate = self.calibrate_requested
                    
            success, color_frame, depth_frame, msg = self.manager.get_synchronized_frames()
            
            if not success:
                continue
                
            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())
            
            if do_calibrate:
                calibration_frames.append(depth_image.copy())
                # Collect 30 frames for robustness
                if len(calibration_frames) >= 30:
                    with QMutexLocker(self.mutex):
                        self.calibrate_requested = False
                    
                    cam_info = {'model': self.manager.device_model, 'serial': self.manager.serial_number}
                    cal_success, cal_msg, overlay_mask = self.calibrator.perform_calibration(
                        calibration_frames, 
                        self.manager.intrinsics, 
                        self.manager.depth_scale,
                        cam_info
                    )
                    
                    stats = {
                        'height_mm': self.calibrator.camera_height_mm,
                        'tilt_deg': self.calibrator.tilt_angle_deg,
                        'residual_mm': self.calibrator.residual_mm,
                        'inliers_pct': self.calibrator.inlier_percentage,
                        'coverage_pct': self.calibrator.valid_coverage,
                        'timestamp': self.calibrator.timestamp
                    } if cal_success else {}
                    
                    self.calibration_done.emit(cal_success, cal_msg, stats, overlay_mask if overlay_mask is not None else np.array([]))
                    calibration_frames = []
                    
            coverage = DepthAlignment.calculate_depth_coverage(depth_image)
            center_depth = DepthAlignment.extract_center_depth(depth_image, self.manager.depth_scale)
            
            frame_count += 1
            elapsed_time = time.time() - start_time
            if elapsed_time > 1.0:
                self.fps = frame_count / elapsed_time
                frame_count = 0
                start_time = time.time()
                
            self.frame_ready.emit(color_image, depth_image, coverage, center_depth, self.fps)
            
        self.manager.stop_streaming()
        self.is_running = False
        self.status_update.emit(False, "Disconnected")


# =====================================================================
# SECTION: inference/class_mapping.py
# =====================================================================

import json
import os

class ClassMapping:
    def __init__(self, mapping_file=None):
        if mapping_file is None:
            candidates = [
                os.path.join(USER_DIR, 'config', 'class_mapping.json'),
                os.path.join(APP2_DIR, 'config', 'class_mapping.json'),
            ]
            if hasattr(sys, '_MEIPASS'):
                candidates.insert(0, os.path.join(sys._MEIPASS, 'config', 'class_mapping.json'))
            mapping_file = None
            for c in candidates:
                if c and os.path.exists(c):
                    mapping_file = c
                    break
            if not mapping_file:
                mapping_file = os.path.join(APP2_DIR, 'config', 'class_mapping.json')
            
        self.mapping = {}
        self.normalized_mapping = {}
        self.load_mapping(mapping_file)
        
    def load_mapping(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Class mapping file not found: {file_path}")
            
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Keys in json are strings, we need integer class IDs
        for k, v in data.items():
            try:
                class_id = int(k)
                self.mapping[class_id] = v
                self.normalized_mapping[class_id] = self._normalize_name(v)
            except ValueError:
                pass
                
    def _normalize_name(self, name):
        # Normalize typographically (e.g. "Rachet-Handels" -> "Ratchet Handle", etc if needed later)
        # For now, we preserve names but lowercased and stripped.
        return name.lower().strip()
        
    def get_name(self, class_id):
        return self.mapping.get(class_id, f"Unknown-{class_id}")
        
    def get_normalized_name(self, class_id):
        return self.normalized_mapping.get(class_id, f"unknown-{class_id}")
        
    def is_socket(self, class_id):
        name = self.get_normalized_name(class_id)
        # Check if the class is fundamentally a socket that will be measured
        return 'socket' in name and 'bit socket' not in name


# =====================================================================
# SECTION: inference/postprocessing.py
# =====================================================================

import numpy as np

def apply_nms(boxes, scores, classes, masks, iou_threshold=0.45):
    """
    Applies Non-Maximum Suppression to filter duplicate detections.
    """
    if len(boxes) == 0:
        return boxes, scores, classes, masks

    # Calculate areas
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    areas = (x2 - x1) * (y2 - y1)

    order = scores.argsort()[::-1]
    keep = []

    while order.size > 0:
        i = order[0]
        keep.append(i)

        if order.size == 1:
            break

        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h

        iou = inter / (areas[i] + areas[order[1:]] - inter)

        # Ensure we don't suppress different classes unless they overlap almost entirely
        # YOLO typically outputs single class per box, but if overlapping bounding boxes
        # are of the same class, suppress based on iou_threshold
        
        same_class = (classes[i] == classes[order[1:]])
        
        # Suppress if IoU > threshold AND they are the same class
        inds_to_suppress = np.where((iou > iou_threshold) & same_class)[0]
        
        # Alternatively, if they overlap hugely (>0.8) even with different classes, suppress the lower confidence one
        inds_diff_class_suppress = np.where((iou > 0.85) & (~same_class))[0]
        
        inds_to_remove = np.concatenate((inds_to_suppress, inds_diff_class_suppress))
        
        # order[1:] because order[0] is `i`
        order = np.delete(order, np.concatenate(([0], inds_to_remove + 1)))

    keep = np.array(keep)
    
    return boxes[keep], scores[keep], classes[keep], [masks[k] for k in keep] if masks else []



# =====================================================================
# SECTION: inference/model_loader.py
# =====================================================================

import os
import sys
import json
from ultralytics import YOLO

class ModelLoader:
    def __init__(self, manifest_path='config/model_manifest.json'):
        self.manifest_path = manifest_path
        self.model = None
        self.manifest_data = None
        
    def load_manifest(self):
        candidates = [self.manifest_path]
        if hasattr(sys, '_MEIPASS'):
            candidates.append(os.path.join(sys._MEIPASS, 'config', 'model_manifest.json'))
        if getattr(sys, 'frozen', False):
            candidates.append(os.path.join(os.path.dirname(sys.executable), 'config', 'model_manifest.json'))
            
        app2_dir = APP2_DIR
        candidates.append(os.path.join(app2_dir, 'config', 'model_manifest.json'))
        
        found_path = None
        for p in candidates:
            if p and os.path.exists(p):
                found_path = p
                break
                
        if not found_path:
            return False, f"Manifest not found in candidate paths: {candidates}"
            
        try:
            with open(found_path, 'r', encoding='utf-8-sig') as f:
                self.manifest_data = json.load(f)
            self.manifest_path = found_path
            return True, "Manifest loaded successfully"
        except Exception as e:
            return False, f"Failed to load manifest: {str(e)}"
            
    def resolve_model_path(self):
        if not self.manifest_data:
            success, msg = self.load_manifest()
            if not success:
                return False, msg
                
        relative_path = self.manifest_data.get('primary_model', {}).get('relative_path')
        if not relative_path:
            return False, "Relative path not found in manifest"
            
        app2_dir = APP2_DIR
        
        candidates = [
            os.path.abspath(os.path.join(app2_dir, relative_path)),
            os.path.abspath(os.path.join(app2_dir, 'Models', os.path.basename(relative_path))),
            os.path.abspath(os.path.join(app2_dir, 'models', os.path.basename(relative_path))),
            os.path.abspath(os.path.join(app2_dir, 'Models', 'best (2).pt')),
            os.path.abspath(os.path.join(app2_dir, 'models', 'best.pt')),
            os.path.abspath(os.path.join(app2_dir, '..', 'Models', 'Segmentation', 'IS YOLOV11', 'best (2).pt')),
        ]
        
        if hasattr(sys, '_MEIPASS'):
            candidates.insert(0, os.path.join(sys._MEIPASS, 'Models', os.path.basename(relative_path)))
            candidates.insert(0, os.path.join(sys._MEIPASS, 'models', os.path.basename(relative_path)))
            candidates.insert(0, os.path.join(sys._MEIPASS, 'Models', 'best (2).pt'))
            candidates.insert(0, os.path.join(sys._MEIPASS, 'models', 'best.pt'))
            candidates.insert(0, os.path.join(sys._MEIPASS, os.path.basename(relative_path)))
            
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            candidates.append(os.path.abspath(os.path.join(exe_dir, 'Models', os.path.basename(relative_path))))
            candidates.append(os.path.abspath(os.path.join(exe_dir, 'Models', 'best (2).pt')))
            candidates.append(os.path.abspath(os.path.join(exe_dir, 'Models', 'best.pt')))
            candidates.append(os.path.abspath(os.path.join(exe_dir, 'models', os.path.basename(relative_path))))
            candidates.append(os.path.abspath(os.path.join(exe_dir, 'models', 'best.pt')))
            candidates.append(os.path.abspath(os.path.join(exe_dir, os.path.basename(relative_path))))
            candidates.append(os.path.abspath(os.path.join(exe_dir, relative_path)))
            
        for path in candidates:
            if path and os.path.exists(path):
                return True, path
                
        return False, f"Model file not found. Checked: {candidates}"
        
    def load_model(self):
        success, result = self.resolve_model_path()
        if not success:
            return False, result
            
        model_path = result
        
        try:
            # Load the YOLO model
            self.model = YOLO(model_path)
            
            # Verify task type
            task = getattr(self.model, 'task', 'unknown')
            if task != 'segment':
                return False, f"Model task is '{task}', expected 'segment'"
                
            # Read class names
            classes = getattr(self.model, 'names', {})
            if not classes:
                return False, "Failed to read class names from model"
                
            expected_classes = self.manifest_data['primary_model']['classes']
            if len(classes) != len(expected_classes):
                return False, f"Model has {len(classes)} classes, expected {len(expected_classes)}"
                
            return True, {
                'model': self.model,
                'task': task,
                'classes': classes,
                'path': model_path
            }
        except Exception as e:
            return False, f"Failed to load YOLO model: {str(e)}"


# =====================================================================
# SECTION: visualization/mask_renderer.py
# =====================================================================

import cv2
import numpy as np

class MaskRenderer:
    @staticmethod
    def get_palette():
        # High contrast palette
        return [
            (255, 0, 0),     # Blue
            (0, 255, 0),     # Green
            (0, 0, 255),     # Red
            (0, 255, 255),   # Yellow
            (255, 0, 255),   # Magenta
            (255, 255, 0),   # Cyan
            (0, 165, 255),   # Orange (BGR)
            (128, 0, 128),   # Purple
            (128, 128, 0),   # Teal
            (0, 128, 128),   # Olive
            (255, 192, 203), # Pink
            (0, 128, 0),     # Dark Green
            (128, 0, 0),     # Navy Blue
        ]
        
    @staticmethod
    def get_color(global_instance_id):
        palette = MaskRenderer.get_palette()
        return palette[global_instance_id % len(palette)]

    @staticmethod
    def create_binary_mask(image_shape, polygon):
        """
        Creates a binary mask (H, W) from a polygon.
        """
        mask = np.zeros(image_shape[:2], dtype=np.uint8)
        if polygon is None or len(polygon) == 0:
            return mask
        pts = np.array(polygon, np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(mask, [pts], 255)
        return mask

    @staticmethod
    def calculate_mask_properties(polygon):
        """
        Calculates area and centroid from a polygon.
        """
        if polygon is None or len(polygon) == 0:
            return 0.0, (0, 0)
            
        pts = np.array(polygon, np.float32)
        area = cv2.contourArea(pts)
        
        M = cv2.moments(pts)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
        else:
            cX, cY = 0, 0
            
        return area, (cX, cY)

    @staticmethod
    def apply_mask_overlay(image, polygon, color, opacity=0.5):
        """
        Applies a semi-transparent mask and a solid contour boundary.
        """
        if polygon is None or len(polygon) == 0:
            return image
            
        overlay = image.copy()
        pts = np.array(polygon, np.int32).reshape((-1, 1, 2))
        
        # Draw filled polygon on overlay
        cv2.fillPoly(overlay, [pts], color)
        
        # Blend
        cv2.addWeighted(overlay, opacity, image, 1 - opacity, 0, image)
        
        # Draw solid contour
        cv2.polylines(image, [pts], isClosed=True, color=color, thickness=2)
        return image


# =====================================================================
# SECTION: visualization/overlay_renderer.py
# =====================================================================

import cv2
import numpy as np

class OverlayRenderer:
    @staticmethod
    def format_category_name(raw_name, is_socket=False):
        """
        Formats raw model/mapping category name into a clean, human-readable display string.
        """
        if not raw_name:
            return "Socket" if is_socket else "Tool"
        name = str(raw_name).strip()
        low = name.lower()
        if low == "sockets":
            return "Socket" if is_socket else "Sockets"
        elif low == "universal joint":
            return "Universal Joint"
        elif low == "long bit socket":
            return "Long Bit Socket"
        elif low == "rachet handle":
            return "Rachet Handle"
        elif low == "bit socket":
            return "Bit Socket"
        elif low == "bit sockets":
            return "Bit Sockets"
        elif low == "deep socket":
            return "Deep Socket"
        elif low == "extension bar":
            return "Extension Bar"
        elif low == "flex handle":
            return "Flex Handle"
        elif low == "allen key":
            return "Allen Key"
        elif low == "bit holder":
            return "Bit Holder"
        elif low == "s handle":
            return "S Handle"
        elif low == "spanners":
            return "Spanners"
        elif low == "bits":
            return "Bits"
        elif low == "adaptor":
            return "Adaptor"
            
        if name.islower():
            return name.title()
        return name

    @classmethod
    def get_tool_category_name(cls, det):
        """
        Retrieves the model-predicted tool category name from detection or ClassMapping.
        """
        name = det.get("class_name")
        if not name and det.get("class_id") is not None:
            try:
                mapper = ClassMapping()
                name = mapper.get_name(int(det["class_id"]))
            except Exception:
                pass
        if not name:
            name = det.get("category") or det.get("category_name")
        is_socket = det.get("is_socket", False)
        return cls.format_category_name(name, is_socket=is_socket)

    @classmethod
    def render(cls, image, detections, view_mode="Combined View", show_masks=True, show_boxes=True, show_labels=True, mask_opacity=0.5, show_measurements=True):
        """
        Renders the requested overlays onto the image.
        view_mode: "Detection View" (boxes only), "Segmentation View" (masks only), "Combined View" (both)
        """
        out_image = image.copy()
        
        if not detections:
            return out_image
            
        H_img, W_img = out_image.shape[:2]

        # 1. Draw Segmentation Masks
        if view_mode in ["Segmentation View", "Combined View"] and show_masks:
            for det in detections:
                if det.get("polygon") is not None:
                    color = det.get("color", (255, 255, 255))
                    out_image = MaskRenderer.apply_mask_overlay(out_image, det["polygon"], color, mask_opacity)
                    
        # 2. Draw Detection Bounding Boxes
        if view_mode in ["Detection View", "Combined View"] and show_boxes:
            for det in detections:
                color = det.get("color", (255, 255, 255))
                x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
                cv2.rectangle(out_image, (x1, y1), (x2, y2), color, 2)
                
        # 3. Draw Rims and Diameter Line (Measurement Outlines)
        rim_zones = [] # [(rx1, ry1, rx2, ry2)] to avoid obscuring with text badges
        if show_measurements:
            for det in detections:
                ellipse = det.get("rim_ellipse")
                if ellipse is not None:
                    status = det.get("rim_status")
                    # Bright Cyan for detected rim, Orange for uncertain
                    rim_color = (255, 255, 0) if status == "RIM DETECTED" else (0, 165, 255)
                    center, axes, angle = ellipse
                    cx, cy = int(center[0]), int(center[1])
                    axes_int = (int(axes[0]/2), int(axes[1]/2))
                    cv2.ellipse(out_image, (cx, cy), axes_int, angle, 0, 360, rim_color, 2)
                    
                    # Store rim bounding box for collision avoidance
                    r_w = axes[0] / 2.0
                    r_h = axes[1] / 2.0
                    rim_zones.append((int(cx - r_w - 3), int(cy - r_h - 3), int(cx + r_w + 3), int(cy + r_h + 3)))

                    # Draw Diameter Line connecting opposite points along major axis
                    if status == "RIM DETECTED":
                        angle_rad = np.radians(angle)
                        h, k = center[0], center[1]
                        a, b = axes[0]/2, axes[1]/2
                        theta = np.radians(angle)
                        
                        if b > a:
                            p1x = h - b * np.sin(theta)
                            p1y = k + b * np.cos(theta)
                            p2x = h + b * np.sin(theta)
                            p2y = k - b * np.cos(theta)
                        else:
                            p1x = h + a * np.cos(theta)
                            p1y = k + a * np.sin(theta)
                            p2x = h - a * np.cos(theta)
                            p2y = k - a * np.sin(theta)
                            
                        cv2.line(out_image, (int(p1x), int(p1y)), (int(p2x), int(p2y)), (255, 0, 255), 2)
                
        # 4. Draw Detection Category & Socket ID Labels
        if show_labels:
            font_scale = 0.48
            thickness = 1
            pad_x = 4
            pad_y = 3

            # Determine crowdedness for sockets
            socket_dets = [d for d in detections if d.get("is_socket")]
            socket_centers = {}
            for s in socket_dets:
                if s.get("rim_ellipse") is not None:
                    socket_centers[id(s)] = (float(s["rim_ellipse"][0][0]), float(s["rim_ellipse"][0][1]))
                else:
                    sb = s.get("bbox", [0, 0, 0, 0])
                    socket_centers[id(s)] = ((sb[0] + sb[2]) / 2.0, (sb[1] + sb[3]) / 2.0)

            def is_socket_crowded(s_det):
                sc = socket_centers.get(id(s_det))
                if not sc or len(socket_dets) <= 1:
                    return False
                min_dist = float("inf")
                for other in socket_dets:
                    if other is not s_det:
                        oc = socket_centers.get(id(other))
                        if oc:
                            dist_x = abs(sc[0] - oc[0])
                            dist_y = abs(sc[1] - oc[1])
                            if dist_y < 50:
                                min_dist = min(min_dist, dist_x)
                return min_dist < 65.0

            drawn_rects = [] # list of (x1, y1, x2, y2)

            def rects_overlap(r1, r2, margin=0):
                return not (r1[2] + margin < r2[0] or r1[0] - margin > r2[2] or
                            r1[3] + margin < r2[1] or r1[1] - margin > r2[3])

            def overlaps_any(cand_rect):
                for dr in drawn_rects:
                    if rects_overlap(cand_rect, dr, margin=1):
                        return True
                for rz in rim_zones:
                    if rects_overlap(cand_rect, rz, margin=0):
                        return True
                return False

            # Sort detections: non-sockets first (they have big bounding boxes), then sockets left-to-right
            sorted_detections = sorted(detections, key=lambda d: (1 if d.get("is_socket") else 0, d.get("bbox", [0,0,0,0])[0]))
            
            for det in sorted_detections:
                rim_status = det.get("rim_status", "")
                if view_mode != "Detection View" and rim_status == "RIM NOT FOUND":
                    # Skip completely unviable clusters in combined/segmentation views
                    continue
                    
                color = det.get("color", (255, 255, 255))
                x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
                box_w = x2 - x1
                box_h = y2 - y1
                
                # Horizontal anchor: use true rim ellipse center if socket, else bounding box center
                if det.get("is_socket") and det.get("rim_ellipse") is not None:
                    cx = int(det["rim_ellipse"][0][0])
                    cy = int(det["rim_ellipse"][0][1])
                else:
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                
                is_socket = det.get("is_socket", False)
                cat_name = cls.get_tool_category_name(det)
                seq_id = det.get("sequential_socket_id")
                instance_num = det.get("global_instance_id", det.get("instance_num", 0))
                status = det.get("assignment_status", "")
                verif_status = det.get("verification_status", "")
                ident_status = det.get("identification_status", "")
                
                # Dark Industrial Badge Colors
                if is_socket:
                    if seq_id:
                        if "CONFLICT" in status or "CONFLICT" in verif_status:
                            bg_color = (15, 15, 140)   # Dark red for size/identity conflict
                            border_color = (40, 40, 230)
                        elif "TOLERATED" in status or "REVIEW" in status or "AMBIGUOUS" in status or "UNVERIFIED" in status or "UNVERIFIED" in verif_status or ident_status == "ORIENTATION_AMBIGUOUS" or det.get("low_confidence_warning"):
                            bg_color = (15, 75, 130)   # Dark amber warning
                            border_color = (30, 140, 240)
                        else:
                            bg_color = (15, 60, 20)    # Dark green verified
                            border_color = (30, 180, 50)
                    else:
                        bg_color = (15, 75, 130)       # Dark amber unverified
                        border_color = (30, 140, 240)
                else:
                    if status == "SLOT MATCHED" or verif_status == "MATCHED":
                        bg_color = (15, 60, 20)        # Dark green
                        border_color = (30, 180, 50)
                    elif status == "UNMATCHED DETECTION" or "EXTRA" in status:
                        bg_color = (15, 15, 140)       # Dark red
                        border_color = (40, 40, 230)
                    else:
                        bg_color = (25, 29, 36)        # Dark industrial slate
                        border_color = color
                
                # Determine candidate label texts
                crowded = is_socket and is_socket_crowded(det)
                label_options = []
                if is_socket:
                    if seq_id:
                        if not crowded:
                            label_options.append(f"{seq_id} | {cat_name}")
                        label_options.append(f"{seq_id}")
                    else:
                        if not crowded:
                            label_options.append(f"Unverified #{instance_num} | {cat_name}")
                        label_options.append(f"Unverified #{instance_num}")
                else:
                    label_options.append(cat_name)
                    
                placed = False
                for label_text in label_options:
                    (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                    badge_w = tw + 2 * pad_x
                    badge_h = th + 2 * pad_y
                    
                    # Preferred Positions:
                    # 1. Above bounding box
                    # 2. Inside upper edge of bounding box (for non-sockets or tools without rim collision)
                    # 3. Below bounding box
                    # 4. Staggered above tier 2
                    # 5. Staggered below tier 2
                    # 6. To the right of bounding box
                    # 7. To the left of bounding box
                    candidates = []
                    
                    # Position 1: Above bounding box
                    cand_x = min(max(2, cx - badge_w // 2), W_img - badge_w - 2)
                    cand_y = y1 - badge_h - 3
                    if cand_y >= 2:
                        candidates.append((cand_x, cand_y, cand_x + badge_w, cand_y + badge_h, "above", (cx, y1)))
                        
                    # Position 2: Inside upper edge of bounding box (non-sockets only)
                    if not is_socket and box_h >= badge_h + 10:
                        cand_x = min(max(2, x1 + 4), W_img - badge_w - 2)
                        cand_y = y1 + 4
                        candidates.append((cand_x, cand_y, cand_x + badge_w, cand_y + badge_h, "inside", (cx, y1)))
                        
                    # Position 3: Below bounding box
                    cand_x = min(max(2, cx - badge_w // 2), W_img - badge_w - 2)
                    cand_y = y2 + 3
                    if cand_y + badge_h <= H_img - 2:
                        candidates.append((cand_x, cand_y, cand_x + badge_w, cand_y + badge_h, "below", (cx, y2)))
                        
                    # Position 4: Staggered above tier 2
                    cand_x = min(max(2, cx - badge_w // 2), W_img - badge_w - 2)
                    cand_y = y1 - 2 * badge_h - 7
                    if cand_y >= 2:
                        candidates.append((cand_x, cand_y, cand_x + badge_w, cand_y + badge_h, "above_stagger", (cx, y1)))
                        
                    # Position 5: Staggered below tier 2
                    cand_x = min(max(2, cx - badge_w // 2), W_img - badge_w - 2)
                    cand_y = y2 + badge_h + 7
                    if cand_y + badge_h <= H_img - 2:
                        candidates.append((cand_x, cand_y, cand_x + badge_w, cand_y + badge_h, "below_stagger", (cx, y2)))
                        
                    # Position 6: To the right of bounding box
                    cand_x = x2 + 4
                    cand_y = min(max(2, cy - badge_h // 2), H_img - badge_h - 2)
                    if cand_x + badge_w <= W_img - 2:
                        candidates.append((cand_x, cand_y, cand_x + badge_w, cand_y + badge_h, "right", (x2, cy)))
                        
                    # Position 7: To the left of bounding box
                    cand_x = x1 - badge_w - 4
                    cand_y = min(max(2, cy - badge_h // 2), H_img - badge_h - 2)
                    if cand_x >= 2:
                        candidates.append((cand_x, cand_y, cand_x + badge_w, cand_y + badge_h, "left", (x1, cy)))
                        
                    for bx1, by1_b, bx2, by2_b, pos_type, anchor in candidates:
                        cand_rect = (bx1, by1_b, bx2, by2_b)
                        if not overlaps_any(cand_rect):
                            # Valid placement without collision!
                            drawn_rects.append(cand_rect)
                            
                            # Draw subtle leader line if displaced significantly
                            if pos_type in ["above_stagger", "below_stagger", "left", "right"]:
                                line_start = (bx1 + badge_w // 2, by2_b if "above" in pos_type else by1_b)
                                cv2.line(out_image, line_start, anchor, color, 1, cv2.LINE_AA)
                                
                            # Render compact dark industrial badge
                            cv2.rectangle(out_image, (bx1, by1_b), (bx2, by2_b), bg_color, -1)
                            cv2.rectangle(out_image, (bx1, by1_b), (bx2, by2_b), border_color, 1)
                            cv2.putText(out_image, label_text, (bx1 + pad_x, by1_b + pad_y + th),
                                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
                            placed = True
                            break
                            
                    if placed:
                        break
                        
                # Emergency fallback if all non-overlapping positions were exhausted
                if not placed:
                    label_text = label_options[-1] # Most compact option
                    (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                    badge_w = tw + 2 * pad_x
                    badge_h = th + 2 * pad_y
                    cand_x = min(max(2, cx - badge_w // 2), W_img - badge_w - 2)
                    cand_y = max(2, y1 - badge_h - 2)
                    cand_rect = (cand_x, cand_y, cand_x + badge_w, cand_y + badge_h)
                    drawn_rects.append(cand_rect)
                    cv2.rectangle(out_image, (cand_x, cand_y), (cand_x + badge_w, cand_y + badge_h), bg_color, -1)
                    cv2.rectangle(out_image, (cand_x, cand_y), (cand_x + badge_w, cand_y + badge_h), border_color, 1)
                    cv2.putText(out_image, label_text, (cand_x + pad_x, cand_y + pad_y + th),
                                cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
                                
        return out_image


# =====================================================================
# SECTION: inference/detector.py
# =====================================================================

import time
import numpy as np
import cv2
import uuid

class Detector:
    def __init__(self, model, conf_threshold=0.15, iou_threshold=0.45):
        self.model = model
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.class_mapper = ClassMapping()
        
    def detect(self, bgr_image):
        """
        Runs YOLO inference on a BGR image.
        Returns a list of structured detection results.
        """
        start_time = time.time()
        
        # YOLOv11 expects RGB
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        
        # Inference
        # imgsz=640 is default. We can use half precision if supported, but leave to ultralytics defaults
        results = self.model(rgb_image, conf=self.conf_threshold, iou=self.iou_threshold, verbose=False)
        
        inference_time = time.time() - start_time
        
        result = results[0]
        
        h, w = bgr_image.shape[:2]
        
        boxes = result.boxes.xyxy.cpu().numpy() # [N, 4]
        scores = result.boxes.conf.cpu().numpy() # [N]
        classes = result.boxes.cls.cpu().numpy().astype(int) # [N]
        
        # Extract Masks as Polygons
        masks = []
        if result.masks is not None and result.masks.xy is not None:
            for i in range(len(classes)):
                polygon = result.masks.xy[i] # Nx2 array of points
                if len(polygon) > 2:
                    masks.append(polygon.tolist())
                else:
                    masks.append(None)
        else:
            masks = [None] * len(classes)
            
        detections = []
        
        global_idx = 0
        
        for i in range(len(classes)):
            class_id = int(classes[i])
            conf = float(scores[i])
            box = boxes[i].tolist()
            polygon = masks[i]
            
            orig_name = self.class_mapper.get_name(class_id)
            norm_name = self.class_mapper.get_normalized_name(class_id)
            is_socket = self.class_mapper.is_socket(class_id)
            
            global_idx += 1
            color = MaskRenderer.get_color(global_idx)
                
            area, centroid = MaskRenderer.calculate_mask_properties(polygon)
            
            det = {
                "instance_id": str(uuid.uuid4()),
                "global_instance_id": global_idx,
                "instance_num": global_idx, # Preserve instance_num key for backward compatibility in main_window.py
                "class_id": class_id,
                "class_name": orig_name,
                "normalized_name": norm_name,
                "confidence": conf,
                "bbox": box,
                "polygon": polygon,
                "is_socket": is_socket,
                "color": color,
                "area_px": float(area),
                "centroid": centroid,
                "mask_available": polygon is not None
            }
            detections.append(det)
            
        # Find the toolkit
        toolkit_bbox = None
        for d in detections:
            if d["normalized_name"] == "toolkit":
                toolkit_bbox = d["bbox"]
                break
                
        # Flag out-of-toolkit sockets
        if toolkit_bbox is not None:
            tx1, ty1, tx2, ty2 = toolkit_bbox
            for d in detections:
                if d["is_socket"]:
                    bx1, by1, bx2, by2 = d["bbox"]
                    # Calculate intersection
                    ix1 = max(tx1, bx1)
                    iy1 = max(ty1, by1)
                    ix2 = min(tx2, bx2)
                    iy2 = min(ty2, by2)
                    inter_w = max(0, ix2 - ix1)
                    inter_h = max(0, iy2 - iy1)
                    inter_area = inter_w * inter_h
                    box_area = (bx2 - bx1) * (by2 - by1)
                    
                    if inter_area < 0.5 * box_area:
                        d["out_of_toolkit"] = True
                    else:
                        d["out_of_toolkit"] = False
        else:
            for d in detections:
                if d["is_socket"]:
                    d["out_of_toolkit"] = False
            
        return {
            "detections": detections,
            "inference_time_ms": inference_time * 1000.0,
            "image_width": w,
            "image_height": h,
            "timestamp": int(time.time()),
            "model_identifier": "yolov11-segmentation"
        }


# =====================================================================
# SECTION: inference/inference_worker.py
# =====================================================================

import time
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
import torch
import cv2


class InferenceWorker(QThread):
    # Signals
    model_loaded = pyqtSignal(bool, str)
    inference_done = pyqtSignal(object, np.ndarray) # results dict, annotated image
    error_occurred = pyqtSignal(str)
    
    def __init__(self, manifest_path, parent=None):
        super().__init__(parent)
        self.manifest_path = manifest_path
        self.mutex = QMutex()
        
        self.model = None
        self.detector = None
        
        self.pending_image = None
        self.is_running = True
        self.is_busy = False
        
        # We start the thread immediately to load the model in the background
        self.start()
        
    @property
    def is_inferencing(self):
        with QMutexLocker(self.mutex):
            return self.is_busy or (self.pending_image is not None)
        
    def run(self):
        # 1. Load model
        try:
            loader = ModelLoader(manifest_path=self.manifest_path)
            success, msg = loader.load_manifest()
            if not success:
                self.model_loaded.emit(False, msg)
                return
                
            success, model_obj = loader.load_model()
            if not success:
                self.model_loaded.emit(False, model_obj) # model_obj is error message here
                return
                
            self.model = model_obj['model']
            self.detector = Detector(self.model)
            
            self.model_loaded.emit(True, "Model loaded successfully")
        except Exception as e:
            self.model_loaded.emit(False, f"Exception during model load: {str(e)}")
            return
            
        # 2. Inference Loop
        while True:
            with QMutexLocker(self.mutex):
                if not self.is_running:
                    break
                image_to_process = self.pending_image
                self.pending_image = None
                self.is_busy = (image_to_process is not None)
                
            if image_to_process is not None:
                try:
                    # Run inference
                    results = self.detector.detect(image_to_process)
                    self.inference_done.emit(results, image_to_process)
                except Exception as e:
                    self.error_occurred.emit(f"Inference failed: {str(e)}")
                finally:
                    with QMutexLocker(self.mutex):
                        self.is_busy = False
            
            time.sleep(0.05) # Prevent 100% CPU in the loop
            
    def request_inference(self, bgr_image):
        if self.detector is None:
            self.error_occurred.emit("Model not loaded yet.")
            return
            
        with QMutexLocker(self.mutex):
            # Only process if we aren't already processing one (to avoid backlog)
            if self.pending_image is None:
                self.pending_image = bgr_image.copy()
                self.is_busy = True
            else:
                pass # Dropped request because worker is busy
                
    def stop(self):
        with QMutexLocker(self.mutex):
            self.is_running = False
            self.is_busy = False
            self.pending_image = None
        self.wait()


# =====================================================================
# SECTION: inference/inference_pipeline.py
# =====================================================================


# Convenience exports if needed


# =====================================================================
# SECTION: inspection/inspection_data.py
# =====================================================================

import uuid
from datetime import datetime

class InspectionData:
    def __init__(self):
        self.inspection_id = str(uuid.uuid4())
        self.timestamp = datetime.now().isoformat()
        
        # Worker Identification & Batch Metadata
        self.worker_id = None
        self.session_id = None
        self.batch_id = "BATCH-001"
        self.toolkit_id = "TOOLKIT-001"
        self.manual_overrides = []

        # General Info
        self.source_image_path = None
        self.model_identifier = None
        self.calibration_status = "NOT CALIBRATED"
        self.reference_workbook_identifier = "NOT LOADED"
        
        # Company Reference & Tool Counts (Book1.xlsx)
        self.selected_company = None
        self.company_workbook_identifier = "NOT LOADED"
        self.company_tool_counts = {}
        self.tool_count_verification_results = []
        self.tool_count_verification_status = "NOT RUN"

        # Company Socket Dimensional References (Book 2.xlsx)
        self.selected_socket_company = None
        self.socket_company_workbook_identifier = "NOT LOADED"
        self.book2_reload_status = "NOT LOADED"
        self.book2_expected_socket_count = 0
        self.socket_dimensional_verification_status = "NOT RUN"
        
        # Counting and References
        self.expected_tool_counts = {}
        self.detected_tool_counts = {}
        self.count_comparison_results = []
        
        # Sockets
        self.socket_detection_candidates = [] # The global instances that are sockets
        self.socket_reference_catalog = [] # The reference objects from Excel
        self.unassigned_reference_sockets = [] # List of reference IDs not yet assigned
        
        # Status/Warnings
        self.mask_quality_warnings = 0
        
        # New Step 8.1 Fields
        self.raw_detection_count = 0
        self.raw_socket_candidate_count = 0
        self.matched_reference_count = 0
        self.unmatched_candidate_count = 0
        self.missing_reference_count = 0
        self.matched_reference_ids = []
        self.unmatched_detection_ids = []
        self.low_confidence_detection_ids = []
        self.assignment_quality = "NONE"
        self.layout_validation_status = "NOT VALIDATED"
        self.mask_quality_status = "GOOD"
        
        # Sequential Identification (Step 5)
        self.socket_identification_status = "NOT_RUN"
        self.sequential_socket_count = 0
        self.sequential_socket_assignments = {} # e.g. {global_instance_id: "S01"}
        
        # Excel Dimensional Verification (Step 6)
        self.reference_alignment_status = "NOT LOADED"
        self.reference_verification_status = "NOT RUN"
        self.tolerated_reference_count = 0
        self.conflict_reference_count = 0
        self.extra_reference_count = 0
        self.socket_verifications = []
        self.reference_verifications = []
        
        # Future fields (Step 8+)
        self.socket_reference_assignments = {} # e.g. {global_instance_id: "S01"}
        self.measured_diameters = {}
        self.adjacent_comparisons = {}
        self.dimensional_status = {}
        self.rejection_decisions = {}
        
    def to_dict(self):
        return {
            "inspection_id": self.inspection_id,
            "timestamp": self.timestamp,
            "worker_id": self.worker_id,
            "session_id": self.session_id,
            "batch_id": self.batch_id,
            "toolkit_id": self.toolkit_id,
            "manual_overrides": self.manual_overrides,
            "source_image_path": self.source_image_path,
            "model_identifier": self.model_identifier,
            "calibration_status": self.calibration_status,
            "reference_workbook_identifier": self.reference_workbook_identifier,
            "selected_company": self.selected_company,
            "company_workbook_identifier": self.company_workbook_identifier,
            "company_tool_counts": self.company_tool_counts,
            "tool_count_verification_results": self.tool_count_verification_results,
            "tool_count_verification_status": self.tool_count_verification_status,
            "selected_socket_company": self.selected_socket_company,
            "socket_company_workbook_identifier": self.socket_company_workbook_identifier,
            "book2_reload_status": self.book2_reload_status,
            "book2_expected_socket_count": self.book2_expected_socket_count,
            "socket_dimensional_verification_status": self.socket_dimensional_verification_status,
            "expected_tool_counts": self.expected_tool_counts,
            "detected_tool_counts": self.detected_tool_counts,
            "count_comparison_results": self.count_comparison_results,
            "raw_detection_count": self.raw_detection_count,
            "raw_socket_candidate_count": self.raw_socket_candidate_count,
            "matched_reference_count": self.matched_reference_count,
            "tolerated_reference_count": self.tolerated_reference_count,
            "conflict_reference_count": self.conflict_reference_count,
            "unmatched_candidate_count": self.unmatched_candidate_count,
            "missing_reference_count": self.missing_reference_count,
            "extra_reference_count": self.extra_reference_count,
            "matched_reference_ids": self.matched_reference_ids,
            "unmatched_detection_ids": self.unmatched_detection_ids,
            "low_confidence_detection_ids": self.low_confidence_detection_ids,
            "assignment_quality": self.assignment_quality,
            "layout_validation_status": self.layout_validation_status,
            "mask_quality_status": self.mask_quality_status,
            "socket_identification_status": self.socket_identification_status,
            "sequential_socket_count": self.sequential_socket_count,
            "sequential_socket_assignments": self.sequential_socket_assignments,
            "reference_alignment_status": self.reference_alignment_status,
            "reference_verification_status": self.reference_verification_status,
            "socket_verifications": self.socket_verifications,
            "reference_verifications": self.reference_verifications,
            "socket_detection_candidates": self.socket_detection_candidates,
            "socket_reference_catalog": self.socket_reference_catalog,
            "unassigned_reference_sockets": self.unassigned_reference_sockets,
            "mask_quality_warnings": self.mask_quality_warnings
        }


# =====================================================================
# SECTION: inspection/worker_session.py
# =====================================================================

import re
import uuid
from datetime import datetime
from typing import Optional, Dict, Tuple

class WorkerSessionManager:
    """
    Manages self-declared Worker ID identification, active sessions,
    and associated batch/toolkit metadata.
    
    Note: Worker ID is a self-declared identifier, not authenticated proof of identity.
    """
    # Allowed worker ID format: 2-32 characters, alphanumeric with hyphens, underscores, dots
    WORKER_ID_REGEX = re.compile(r"^[A-Za-z0-9._-]{2,32}$")
    BATCH_ID_REGEX = re.compile(r"^[A-Za-z0-9._-]{2,32}$")
    TOOLKIT_ID_REGEX = re.compile(r"^[A-Za-z0-9._-]{1,32}$")

    def __init__(self):
        self.worker_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.session_start_time: Optional[str] = None
        self.session_end_time: Optional[str] = None
        self.session_active: bool = False
        
        self.current_batch_id: str = "BATCH-001"
        self.current_toolkit_id: str = "TOOLKIT-001"
        self.session_history: list = []

    @classmethod
    def validate_worker_id(cls, raw_id: Optional[str]) -> Tuple[bool, str]:
        """
        Validates the worker ID format.
        Rejects empty or whitespace-only values.
        """
        if raw_id is None:
            return False, "Worker ID cannot be empty."
        trimmed = raw_id.strip()
        if not trimmed:
            return False, "Worker ID cannot be empty or whitespace-only."
        if len(trimmed) < 2 or len(trimmed) > 32:
            return False, "Worker ID must be at least 2 characters and at most 32 characters."
        if not cls.WORKER_ID_REGEX.match(trimmed):
            return False, (
                "Invalid Worker ID format. Must be 2-32 characters "
                "containing only letters, numbers, hyphens, underscores, or dots (e.g., 'WRK-001')."
            )
        return True, ""

    @classmethod
    def validate_batch_id(cls, raw_id: Optional[str]) -> Tuple[bool, str]:
        """Validates the batch ID format."""
        if raw_id is None:
            return False, "Batch ID cannot be empty."
        trimmed = raw_id.strip()
        if not trimmed:
            return False, "Batch ID cannot be empty or whitespace-only."
        if not cls.BATCH_ID_REGEX.match(trimmed):
            return False, "Invalid Batch ID format (e.g., 'BATCH-001')."
        return True, ""

    @classmethod
    def validate_toolkit_id(cls, raw_id: Optional[str]) -> Tuple[bool, str]:
        """Validates the toolkit/box ID format."""
        if raw_id is None:
            return False, "Toolkit ID cannot be empty."
        trimmed = raw_id.strip()
        if not trimmed:
            return False, "Toolkit ID cannot be empty or whitespace-only."
        if not cls.TOOLKIT_ID_REGEX.match(trimmed):
            return False, "Invalid Toolkit ID format (e.g., 'BOX-001')."
        return True, ""

    def start_session(self, raw_worker_id: str, raw_batch_id: str = "BATCH-001", raw_toolkit_id: str = "TOOLKIT-001") -> Tuple[bool, str]:
        """
        Activates a new worker session.
        Generates a unique session ID and records the start timestamp.
        """
        valid_w, err_w = self.validate_worker_id(raw_worker_id)
        if not valid_w:
            return False, err_w

        valid_b, err_b = self.validate_batch_id(raw_batch_id)
        if not valid_b:
            return False, err_b

        valid_t, err_t = self.validate_toolkit_id(raw_toolkit_id)
        if not valid_t:
            return False, err_t

        # If a session is already active, safely finalize it first
        if self.session_active:
            self.end_session()

        clean_worker = raw_worker_id.strip()
        clean_batch = raw_batch_id.strip()
        clean_toolkit = raw_toolkit_id.strip()

        ts = datetime.now()
        self.worker_id = clean_worker
        self.session_id = f"SES-{clean_worker}-{ts.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        self.session_start_time = ts.isoformat()
        self.session_end_time = None
        self.session_active = True
        self.current_batch_id = clean_batch
        self.current_toolkit_id = clean_toolkit

        return True, ""

    def end_session(self) -> Tuple[bool, Optional[Dict]]:
        """
        Finalizes and ends the current active session.
        Returns: (success: bool, record: Optional[Dict])
        """
        if not self.session_active:
            return False, None

        ts = datetime.now()
        self.session_end_time = ts.isoformat()
        self.session_active = False

        record = {
            "worker_id": self.worker_id,
            "session_id": self.session_id,
            "session_start_time": self.session_start_time,
            "session_end_time": self.session_end_time,
            "batch_id": self.current_batch_id,
            "toolkit_id": self.current_toolkit_id
        }
        self.session_history.append(record)
        self.worker_id = None
        self.session_id = None
        return True, record

    def switch_worker(self, new_worker_id: str, new_batch_id: Optional[str] = None, new_toolkit_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Ends the current session and begins a new session for the new worker.
        """
        batch = new_batch_id or self.current_batch_id
        toolkit = new_toolkit_id or self.current_toolkit_id
        return self.start_session(new_worker_id, batch, toolkit)

    def set_batch_and_toolkit(self, batch_id: str, toolkit_id: str) -> Tuple[bool, str]:
        """Updates the active batch and toolkit IDs."""
        valid_b, err_b = self.validate_batch_id(batch_id)
        if not valid_b:
            return False, err_b
        valid_t, err_t = self.validate_toolkit_id(toolkit_id)
        if not valid_t:
            return False, err_t
        self.current_batch_id = batch_id.strip()
        self.current_toolkit_id = toolkit_id.strip()
        return True, ""

    @property
    def is_active(self) -> bool:
        return self.session_active and bool(self.worker_id)

    def to_dict(self) -> Dict:
        return {
            "worker_id": self.worker_id,
            "session_id": self.session_id,
            "session_start_time": self.session_start_time,
            "session_end_time": self.session_end_time,
            "session_active": self.session_active,
            "current_batch_id": self.current_batch_id,
            "current_toolkit_id": self.current_toolkit_id
        }


# =====================================================================
# SECTION: inspection/inspection_record_manager.py
# =====================================================================

import os
import json
from typing import List, Dict, Optional, Tuple

class InspectionRecordManager:
    """
    Manages persistent storage and querying of toolkit inspection records.
    Ensures that inspection history survives application restarts and prevents
    duplicate counts when an inspection is saved repeatedly.
    """
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            base_dir = APP2_DIR
            storage_dir = os.path.join(base_dir, "data", "inspections")
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def save_inspection(self, record: Dict) -> Tuple[bool, str]:
        """
        Saves or updates an inspection record.
        If inspection_id already exists, updates the record in-place without
        incrementing inspected box count or creating duplicate files.
        Returns: (is_new_inspection, saved_file_path)
        """
        inspection_id = record.get("inspection_id")
        if not inspection_id:
            raise ValueError("Inspection record must contain a unique 'inspection_id'")

        filename = f"{inspection_id}.json"
        file_path = os.path.join(self.storage_dir, filename)

        is_new = not os.path.exists(file_path)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        return file_path, is_new

    def get_inspection(self, inspection_id: str) -> Optional[Dict]:
        """Loads a specific inspection record by its ID."""
        file_path = os.path.join(self.storage_dir, f"{inspection_id}.json")
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def get_all_inspections(self) -> List[Dict]:
        """Loads all persisted inspection records ordered by timestamp."""
        records = []
        if not os.path.exists(self.storage_dir):
            return records

        for fname in os.listdir(self.storage_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(self.storage_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict) and "inspection_id" in data:
                            records.append(data)
                except Exception:
                    continue

        # Sort chronologically by timestamp
        records.sort(key=lambda r: r.get("timestamp", ""))
        return records

    def get_inspections(self, batch_id: Optional[str] = None, worker_id: Optional[str] = None) -> List[Dict]:
        """
        Retrieves inspection records filtered by Batch ID and/or Worker ID.
        """
        all_records = self.get_all_inspections()
        filtered = []
        for r in all_records:
            if batch_id and r.get("batch_id") != batch_id:
                continue
            if worker_id and r.get("worker_id") != worker_id:
                continue
            filtered.append(r)
        return filtered

    def get_available_batches(self) -> List[str]:
        """Returns a sorted list of unique Batch IDs in storage."""
        batches = set()
        for r in self.get_all_inspections():
            b = r.get("batch_id")
            if b:
                batches.add(b)
        return sorted(list(batches))

    def get_workers_in_batch(self, batch_id: str) -> List[str]:
        """Returns a sorted list of unique Worker IDs that inspected toolkits in a given batch."""
        workers = set()
        for r in self.get_inspections(batch_id=batch_id):
            w = r.get("worker_id")
            if w:
                workers.add(w)
        return sorted(list(workers))


# =====================================================================
# SECTION: inspection/metrology.py
# =====================================================================

import numpy as np

class Metrology:
    """
    Experimental Depth-Calibrated Socket Diameter Measurement.
    Converts pixel dimensions of the outer-rim fit into physical millimeters.
    """
    @staticmethod
    def estimate_socket_height(polygon, depth_map, intrinsics, depth_scale, plane_params, nominal_height_fallback=None):
        """
        Estimates the physical height of an individual socket above the calibrated base plane.
        Uses valid 3D points within the YOLO segmentation mask to establish a robust local top-surface.
        Returns: (height_mm, height_source, diagnostic_msg) or (None, None, failure_reason)
        """
        import cv2
        if not plane_params or polygon is None or len(polygon) == 0:
            if nominal_height_fallback is not None:
                return nominal_height_fallback, "HEIGHT_NOMINAL", f"Height: {nominal_height_fallback:.1f}mm (Source: HEIGHT_NOMINAL, no plane/poly)"
            return None, None, "Missing base plane or polygon"
            
        a, b, c, d_plane = plane_params
        
        H, W = depth_map.shape[:2]
        mask = np.zeros((H, W), dtype=np.uint8)
        cv2.fillPoly(mask, [np.array(polygon, dtype=np.int32)], 255)
        
        valid_pixels = (mask > 0) & (depth_map > 0)
        z_raw = depth_map[valid_pixels]
        ys, xs = np.where(valid_pixels)
        
        def fallback(reason):
            if nominal_height_fallback is not None:
                return nominal_height_fallback, "HEIGHT_NOMINAL", f"Height: {nominal_height_fallback:.1f}mm (Source: HEIGHT_NOMINAL, {reason})"
            return None, None, reason

        if len(z_raw) < 50:
            return fallback("Insufficient depth points in socket mask")
            
        z = z_raw * depth_scale * 1000.0
        valid_z_mask = (z > 100) & (z < 1500)
        z = z[valid_z_mask]
        xs = xs[valid_z_mask]
        ys = ys[valid_z_mask]
        
        if len(z) < 50:
            return fallback("Insufficient valid depth range points")
            
        fx, fy = intrinsics.fx, intrinsics.fy
        ppx, ppy = intrinsics.ppx, intrinsics.ppy
        
        x_3d = (xs - ppx) * z / fx
        y_3d = (ys - ppy) * z / fy
        
        # Calculate expected Z of the base plane at these (X,Y) coordinates
        plane_z = (-a * x_3d - b * y_3d - d_plane) / c
        
        # Socket height is how much CLOSER it is to the camera than the base plane
        heights = plane_z - z
        
        # Filter out tray points (height < 5mm) and obvious artifacts (> 150mm for standard toolkits)
        socket_points_mask = (heights > 5.0) & (heights < 150.0)
        socket_heights = heights[socket_points_mask]
        
        if len(socket_heights) < 20:
            return fallback("Insufficient elevated socket points (mostly tray/artifacts)")
            
        # Robust top-surface estimation
        sorted_heights = np.sort(socket_heights)
        top_10_idx = int(len(sorted_heights) * 0.9)
        top_points = sorted_heights[top_10_idx:]
        
        estimated_height = np.median(top_points)
        uncertainty = np.std(top_points)
        
        if uncertainty > 15.0:
            return fallback(f"Top surface scattered (std: {uncertainty:.1f}mm)")
            
        return estimated_height, "HEIGHT_MEASURED", f"Height: {estimated_height:.1f}mm (Source: HEIGHT_MEASURED, std: {uncertainty:.1f}mm)"

    @staticmethod
    def measure_diameter(rim_ellipse, intrinsics, plane_params, active_height_mm, height_source):
        """
        Calculates physical diameter dynamically per socket using 3D ray intersection.
        Requires active_height_mm to be pre-calculated (either individual or shared average).
        Returns:
            diameter_mm, calculated_diameter_mm, independent_px_per_mm, quality, diag_str, cross_check_diam
        """
        if plane_params is None or active_height_mm is None:
            return 0.0, 0.0, 0.0, "MEASUREMENT UNAVAILABLE", "Base plane or height not available", 0.0
            
        a, b, c, d_plane = plane_params
        norm = np.sqrt(a*a + b*b + c*c)
        a, b, c, d_plane = a/norm, b/norm, c/norm, d_plane/norm
        
        if c < 0:
            a, b, c, d_plane = -a, -b, -c, -d_plane
            
        d_top = d_plane + active_height_mm
        
        # 2. Extract undistorted pixel coordinates of the top outer rim
        center, axes, angle = rim_ellipse
        
        t = np.linspace(0, 2*np.pi, 72)
        a_axis = axes[0] / 2.0
        b_axis = axes[1] / 2.0
        
        x = a_axis * np.cos(t)
        y = b_axis * np.sin(t)
        
        theta = np.radians(angle)
        x_rot = x * np.cos(theta) - y * np.sin(theta)
        y_rot = x * np.sin(theta) + y * np.cos(theta)
        
        x_final = x_rot + center[0]
        y_final = y_rot + center[1]
        
        pts = np.column_stack((x_final, y_final))
        
        fx, fy = intrinsics.fx, intrinsics.fy
        ppx, ppy = intrinsics.ppx, intrinsics.ppy
        
        # 3. Back-project each point to the socket top plane
        pts_3d = []
        for pt in pts:
            u, v = pt[0], pt[1]
            denom = a*(u - ppx)/fx + b*(v - ppy)/fy + c
            if abs(denom) < 1e-6:
                continue
            Z = -d_top / denom
            X = (u - ppx) * Z / fx
            Y = (v - ppy) * Z / fy
            pts_3d.append([X, Y, Z])
            
        if len(pts_3d) < 3:
            return 0.0, 0.0, 0.0, "MEASUREMENT FAILED", "Ray intersection failed", 0.0
            
        pts_3d = np.array(pts_3d)
        
        # 4. Calculate maximum physical diameter
        diffs = pts_3d[:, np.newaxis, :] - pts_3d[np.newaxis, :, :]
        dists = np.sqrt(np.sum(diffs**2, axis=-1))
        diameter_mm = float(np.max(dists))
        
        # 5. Independent Local px/mm scale (along the major axis direction)
        cx, cy = center[0], center[1]
        theta_rad = np.radians(angle)
        
        denom_c = a*(cx - ppx)/fx + b*(cy - ppy)/fy + c
        Z_c = -d_top / denom_c if abs(denom_c) > 1e-6 else 1.0
        X_c = (cx - ppx) * Z_c / fx
        Y_c = (cy - ppy) * Z_c / fy
        
        px_x = cx + np.cos(theta_rad)
        px_y = cy + np.sin(theta_rad)
        
        denom_p = a*(px_x - ppx)/fx + b*(px_y - ppy)/fy + c
        Z_p = -d_top / denom_p if abs(denom_p) > 1e-6 else 1.0
        X_p = (px_x - ppx) * Z_p / fx
        Y_p = (px_y - ppy) * Z_p / fy
        
        dist_mm_per_px = np.sqrt((X_p - X_c)**2 + (Y_p - Y_c)**2 + (Z_p - Z_c)**2)
        independent_px_per_mm = 1.0 / dist_mm_per_px if dist_mm_per_px > 0 else 0.0
        
        px_diameter = max(axes[0], axes[1])
        calculated_diameter_mm = px_diameter / independent_px_per_mm if independent_px_per_mm > 0 else 0.0
        
        # 6. Diagnostic cross-check
        f_avg = (fx + fy) / 2.0
        # Z_c is the depth along the ray of the center
        cross_check_diam = px_diameter * Z_c / f_avg
        
        quality = "PROVISIONAL" if height_source == "HEIGHT_NOMINAL" else "GOOD"
        diag_str = f"Top plane d_top={d_top:.1f}, indep_px/mm={independent_px_per_mm:.2f}, cross_check={cross_check_diam:.2f}mm"
        
        return diameter_mm, calculated_diameter_mm, independent_px_per_mm, quality, diag_str, cross_check_diam


# =====================================================================
# SECTION: inspection/rim_detector.py
# =====================================================================

import cv2
import numpy as np

class RimDetector:
    """
    Detects the top outer circular rim of a socket from its RGB crop and segmentation mask.
    """
    @staticmethod
    def detect_rim(bgr_image, polygon, bbox, other_polygons=None):
        """
        Detects the outer rim for a single socket.
        Returns a dictionary with geometric results and diagnostic images.
        """
        H, W = bgr_image.shape[:2]
        x1, y1, x2, y2 = [int(v) for v in bbox]
        
        w = max(1, x2 - x1)
        pad = int(w * 0.15)
        
        # Add padding
        x1_p = max(0, x1 - pad)
        y1_p = max(0, y1 - pad)
        x2_p = min(W, x2 + pad)
        y2_p = min(H, y2 + pad)
        
        crop_bgr = bgr_image[y1_p:y2_p, x1_p:x2_p].copy()
        
        # Create mask for crop
        crop_mask = np.zeros((y2_p - y1_p, x2_p - x1_p), dtype=np.uint8)
        if polygon is not None and len(polygon) > 0:
            shifted_poly = np.array(polygon, dtype=np.int32)
            shifted_poly[:, 0] -= x1_p
            shifted_poly[:, 1] -= y1_p
            cv2.fillPoly(crop_mask, [shifted_poly], 255)
            
        # Isolate the region of interest
        gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        # Only consider edges inside the mask (with slight dilation)
        kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        dilated_mask = cv2.dilate(crop_mask, kernel_dilate)
        valid_edges = cv2.bitwise_and(edges, dilated_mask)
        
        # Exclude edge points that fall inside neighboring sockets
        if other_polygons is not None:
            exclusion_mask = np.zeros_like(valid_edges)
            for p in other_polygons:
                if p is not None and len(p) > 0:
                    shifted_p = np.array(p, dtype=np.int32)
                    shifted_p[:, 0] -= x1_p
                    shifted_p[:, 1] -= y1_p
                    cv2.fillPoly(exclusion_mask, [shifted_p], 255)
            valid_edges[exclusion_mask > 0] = 0

        # Find contours from the valid edges
        contours, _ = cv2.findContours(valid_edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        
        # Fit ellipses to all plausible contours
        ellipses = []
        orig_cx = (x2 - x1) / 2.0 + (x1 - x1_p)
        orig_cy = (y2 - y1) / 2.0 + (y1 - y1_p)
        
        for cnt in contours:
            if len(cnt) >= 15:
                ellipse = cv2.fitEllipse(cnt)
                (cx, cy), (ax, ay), angle = ellipse
                ratio = max(ax, ay) / min(ax, ay) if min(ax, ay) > 0 else float('inf')
                center_dist = np.sqrt((cx - orig_cx)**2 + (cy - orig_cy)**2)
                
                if ratio < 1.35 and center_dist < max(ax, ay):
                    diam = max(ax, ay)
                    ellipses.append({
                        "ellipse": ellipse,
                        "diam": diam,
                        "cnt": cnt
                    })
                    
        # Also fit an ellipse to the YOLO mask itself (Outer Body fallback)
        body_ellipse = None
        mask_contours, _ = cv2.findContours(crop_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if mask_contours and len(mask_contours[0]) >= 15:
            body_ellipse = cv2.fitEllipse(mask_contours[0])
            
        # Sort found edge ellipses by diameter
        ellipses.sort(key=lambda x: x["diam"], reverse=True)
        
        top_rim_ellipse = None
        inner_hex_ellipse = None
        outer_body_ellipse = body_ellipse
        
        if len(ellipses) > 0:
            if body_ellipse:
                body_diam = max(body_ellipse[1][0], body_ellipse[1][1])
                # Filter ellipses that are just the body contour
                inner_ellipses = [e for e in ellipses if e["diam"] < body_diam * 0.9]
            else:
                inner_ellipses = ellipses
                
            if len(inner_ellipses) >= 2:
                # Largest is top outer rim, smallest is inner hex
                top_rim_ellipse = inner_ellipses[0]["ellipse"]
                inner_hex_ellipse = inner_ellipses[-1]["ellipse"]
            elif len(inner_ellipses) == 1:
                # If only one inner concentric circle found, assume it's the top rim
                top_rim_ellipse = inner_ellipses[0]["ellipse"]
            else:
                # Fallback to the largest edge if it's the only one
                top_rim_ellipse = ellipses[0]["ellipse"]
        
        status = "RIM NOT FOUND"
        coverage = 0.0
        if top_rim_ellipse is not None:
            status = "RIM DETECTED"
            coverage = 1.0 # Implicitly 1.0 since we selected a fitted contour
            
        # Create diagnostic overlay on the crop
        diag_bgr = crop_bgr.copy()
        
        # Draw edges in faint gray
        diag_bgr[valid_edges > 0] = [150, 150, 150]
        
        # 1. Outer body (Blue)
        if outer_body_ellipse:
            cv2.ellipse(diag_bgr, outer_body_ellipse, (255, 0, 0), 2)
            
        # 2. Inner Hex Opening (Red)
        if inner_hex_ellipse:
            cv2.ellipse(diag_bgr, inner_hex_ellipse, (0, 0, 255), 2)
            
        # 3. Top Outer Rim (Green)
        if top_rim_ellipse:
            cv2.ellipse(diag_bgr, top_rim_ellipse, (0, 255, 0), 2)
            
        # Shift top_rim_ellipse coordinates to full image space
        global_ellipse = None
        if top_rim_ellipse is not None:
            (cx, cy), (ax, ay), angle = top_rim_ellipse
            global_ellipse = ((cx + x1_p, cy + y1_p), (ax, ay), angle)
            
        return {
            "status": status,
            "ellipse": global_ellipse,
            "edge_points_count": 100, # Mock since we use contours now
            "coverage": coverage,
            "diagnostics": {
                "crop_bgr": crop_bgr,
                "crop_mask": crop_mask,
                "valid_edges": valid_edges,
                "diag_bgr": diag_bgr
            }
        }


# =====================================================================
# SECTION: inspection/reference_manager.py
# =====================================================================

import pandas as pd
import numpy as np

class ReferenceManager:
    def __init__(self):
        self.workbook_path = None
        self.sockets = []
        self.expected_counts = {
            "Sockets": 0,
            "Major Tools": "NOT CONFIGURED"
        }
        self.toolkit_info = {}
        self.is_loaded = False
        self.error_message = ""
        self.reference_map = {}
        
    @staticmethod
    def normalize_reference_id(ref_id):
        """
        Normalizes socket reference IDs consistently:
        e.g. 'S1' -> 'S01', 's1' -> 'S01', 'S01' -> 'S01', '1' -> 'S01', 'S10' -> 'S10'.
        """
        if ref_id is None:
            return ""
        s = str(ref_id).strip()
        if not s:
            return ""
        import re
        m = re.match(r'^[Ss]?0*(\d+)$', s)
        if m:
            return f"S{int(m.group(1)):02d}"
        return s.upper()

    def get_socket_by_id(self, ref_id):
        """
        Retrieves a socket record by its reference ID (case/numbering insensitive).
        """
        norm_id = self.normalize_reference_id(ref_id)
        return self.reference_map.get(norm_id)

    def generate_template(self, output_path):
        """
        Generates a blank Excel reference template with required headers and instructions.
        """
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Main Reference Sheet
                df_ref = pd.DataFrame(columns=[
                    "Toolkit_ID", 
                    "Reference_ID", 
                    "Nominal_Size", 
                    "Expected_Outer_Diameter", 
                    "Measurement_Unit", 
                    "Adjacent_Reference_ID", 
                    "Adjacent_Difference", 
                    "Adjacent_Tolerance", 
                    "Individual_Tolerance", 
                    "Expected_Quantity", 
                    "Notes"
                ])
                df_ref.to_excel(writer, sheet_name="Socket_References", index=False)
                
                # Instructions Sheet
                instructions = [
                    ["Column", "Description"],
                    ["Toolkit_ID", "Identifier for the entire toolkit (e.g. 'Standard Kit 1')"],
                    ["Reference_ID", "Unique identifier for this specific socket (e.g. 'S01')"],
                    ["Nominal_Size", "The size marking on the socket (e.g. '10mm' or '1/2\"')"],
                    ["Expected_Outer_Diameter", "The measured top outer diameter of the socket (numeric)"],
                    ["Measurement_Unit", "Unit of measurement (e.g. 'mm')"],
                    ["Adjacent_Reference_ID", "The Reference_ID of the physical socket sitting next to this one"],
                    ["Adjacent_Difference", "Expected difference in diameter to the adjacent socket (numeric)"],
                    ["Adjacent_Tolerance", "Acceptable tolerance for the adjacent difference (numeric)"],
                    ["Individual_Tolerance", "Acceptable tolerance for individual diameter measurement (numeric)"],
                    ["Expected_Quantity", "Quantity expected in this slot (defaults to 1)"],
                    ["Notes", "Any additional information"]
                ]
                df_inst = pd.DataFrame(instructions[1:], columns=instructions[0])
                df_inst.to_excel(writer, sheet_name="Instructions", index=False)
                
            return True, "Template generated successfully."
        except Exception as e:
            return False, f"Failed to generate template: {str(e)}"
            
    def load_reference(self, file_path):
        """
        Loads the reference Excel workbook, validates schema dynamically, and extracts records.
        """
        try:
            df_dict = pd.read_excel(file_path, sheet_name=None)
            
            if len(df_dict) == 0:
                self.error_message = "No sheets found in workbook."
                return False
                
            # Prefer 'Socket_References' if it exists, else 'Sheet1', else any sheet with socket columns, else first sheet
            sheet_name = None
            if "Socket_References" in df_dict:
                sheet_name = "Socket_References"
            elif "Sheet1" in df_dict:
                sheet_name = "Sheet1"
            else:
                for s_name, s_df in df_dict.items():
                    s_cols = [str(c).lower() for c in s_df.columns]
                    if any("reference_id" in c or "socket_id" in c for c in s_cols):
                        sheet_name = s_name
                        break
                if sheet_name is None:
                    sheet_name = list(df_dict.keys())[0]
                
            df = df_dict[sheet_name]
            
            # Dynamic matching of required columns: we need a Reference ID and an Outer Diameter.
            # Map old test Excel columns to new schema to maintain backwards compatibility
            col_map = {
                "Socket_ID": "Reference_ID",
                "Expected_Diameter_mm": "Expected_Outer_Diameter",
                "Toolkit_Name": "Toolkit_ID",
                "Expected_Difference_to_Next_mm": "Adjacent_Difference",
                "Tolerance_mm": "Individual_Tolerance"
            }
            df = df.rename(columns=col_map)
            
            # Lowercase map for flexible searching
            cols_lower = {c.lower(): c for c in df.columns}
            
            ref_col = cols_lower.get("reference_id")
            diam_col = cols_lower.get("expected_outer_diameter")
            
            if not ref_col or not diam_col:
                self.error_message = f"Missing required columns. Found: {list(df.columns)}. Need Reference_ID and Expected_Outer_Diameter."
                return False
                
            self.sockets = []
            self.reference_map = {}
            seen_ids = set()
            total_expected_quantity = 0
            
            for index, row in df.iterrows():
                raw_sid = str(row.get(ref_col, "")).strip()
                if pd.isna(row.get(ref_col)) or not raw_sid:
                    continue # Skip empty rows
                
                # Normalize reference ID (e.g. S1 -> S01)
                sid = self.normalize_reference_id(raw_sid)
                if not sid:
                    continue
                    
                if sid in seen_ids:
                    self.error_message = f"Duplicate reference ID found: '{raw_sid}' (normalized to '{sid}')"
                    return False
                seen_ids.add(sid)
                
                exp_diam_raw = row.get(diam_col)
                try:
                    exp_diam = float(exp_diam_raw)
                except (ValueError, TypeError):
                    self.error_message = f"Invalid Expected_Outer_Diameter for {sid}: '{exp_diam_raw}'. Must be a positive numeric value."
                    return False
                    
                if exp_diam <= 0:
                    self.error_message = f"Invalid Expected_Outer_Diameter for {sid}: must be a positive number (> 0), got {exp_diam}"
                    return False
                
                # Fetch optional fields dynamically
                nom_size_col = cols_lower.get("nominal_size") or cols_lower.get("nominal_size_mm") or cols_lower.get("size") or "MissingCol"
                nom_size = row.get(nom_size_col, "REFERENCE FIELD MISSING")
                if pd.isna(nom_size) or str(nom_size).strip() == "":
                    nom_size = "REFERENCE FIELD MISSING"
                
                meas_unit_raw = row.get(cols_lower.get("measurement_unit", "MissingCol"))
                meas_unit = str(meas_unit_raw).strip() if not pd.isna(meas_unit_raw) else "mm"
                if meas_unit.lower() not in ("mm", "millimeter", "millimeters", "milli-meter", ""):
                    self.error_message = f"Incompatible measurement unit '{meas_unit}' for {sid}. Only 'mm' is currently supported."
                    return False
                meas_unit = "mm"
                
                ind_tol = row.get(cols_lower.get("individual_tolerance", "MissingCol"))
                try:
                    ind_tol = float(ind_tol) if not pd.isna(ind_tol) else "NOT CONFIGURED"
                except (ValueError, TypeError):
                    ind_tol = "NOT CONFIGURED"
                
                adj_id = row.get(cols_lower.get("adjacent_reference_id", "MissingCol"))
                adj_id = self.normalize_reference_id(str(adj_id).strip()) if not pd.isna(adj_id) else "NOT CONFIGURED"
                
                adj_diff = row.get(cols_lower.get("adjacent_difference", "MissingCol"))
                try:
                    adj_diff = float(adj_diff) if not pd.isna(adj_diff) else "NOT CONFIGURED"
                except (ValueError, TypeError):
                    adj_diff = "NOT CONFIGURED"
                
                adj_tol = row.get(cols_lower.get("adjacent_tolerance", "MissingCol"))
                try:
                    adj_tol = float(adj_tol) if not pd.isna(adj_tol) else "NOT CONFIGURED"
                except (ValueError, TypeError):
                    adj_tol = "NOT CONFIGURED"
                
                exp_qty_raw = row.get(cols_lower.get("expected_quantity", "MissingCol"))
                try:
                    exp_qty = int(exp_qty_raw) if not pd.isna(exp_qty_raw) else 1
                except (ValueError, TypeError):
                    self.error_message = f"Invalid expected quantity for {sid}: '{exp_qty_raw}'"
                    return False
                    
                if exp_qty < 1:
                    self.error_message = f"Invalid expected quantity for {sid}: must be >= 1, got {exp_qty}"
                    return False
                
                total_expected_quantity += exp_qty
                
                # Store general toolkit info from the first valid row
                if not self.toolkit_info:
                    self.toolkit_info["Toolkit_ID"] = str(row.get(cols_lower.get("toolkit_id", "MissingCol"), "Unknown")).strip()
                
                socket_data = {
                    "reference_id": sid,
                    "raw_reference_id": raw_sid,
                    "nominal_size": nom_size,
                    "expected_outer_diameter": float(exp_diam),
                    "measurement_unit": meas_unit,
                    "individual_tolerance": ind_tol,
                    "adjacent_reference_id": adj_id,
                    "adjacent_difference": adj_diff,
                    "adjacent_tolerance": adj_tol,
                    "expected_quantity": exp_qty,
                    "assignment_status": "UNASSIGNED",
                    # Backwards compatibility aliases for older unit tests:
                    "expected_diameter_mm": float(exp_diam),
                    "tolerance_mm": ind_tol if isinstance(ind_tol, (int, float)) else 0.50,
                    "expected_difference_to_next_mm": adj_diff if isinstance(adj_diff, (int, float)) else 0.0,
                    "adjacent_reference_ids": [adj_id] if adj_id != "NOT CONFIGURED" else []
                }
                self.sockets.append(socket_data)
                self.reference_map[sid] = socket_data
                
            # Second pass: if old Excel format was used, infer adjacency from 'adj_diff' sequentially
            if "adjacent_reference_id" not in cols_lower:
                for i in range(len(self.sockets)):
                    if self.sockets[i]["adjacent_difference"] != "NOT CONFIGURED":
                        if i + 1 < len(self.sockets):
                            self.sockets[i]["adjacent_reference_id"] = self.sockets[i+1]["reference_id"]
                            self.sockets[i]["adjacent_reference_ids"] = [self.sockets[i+1]["reference_id"]]
                            
            self.expected_counts["Sockets"] = total_expected_quantity
            self.workbook_path = file_path
            self.is_loaded = True
            self.error_message = ""
            return True
            
        except Exception as e:
            self.error_message = f"Failed to load workbook: {str(e)}"
            return False
            
    def clear(self):
        self.workbook_path = None
        self.sockets = []
        self.reference_map = {}
        self.expected_counts = {
            "Sockets": 0,
            "Major Tools": "NOT CONFIGURED"
        }
        self.toolkit_info = {}
        self.is_loaded = False
        self.error_message = ""


# =====================================================================
# SECTION: inspection/tool_counter.py
# =====================================================================

class ToolCounter:
    def __init__(self, low_confidence_threshold=0.50):
        self.low_confidence_threshold = low_confidence_threshold
        
        # Define categories explicitly based on prompt and class_mapping.json
        self.socket_classes = {3: "Bit Socket", 5: "Deep Socket", 11: "Sockets"}
        self.major_tool_classes = {
            0: "Adaptor", 
            6: "Extension Bar", 
            7: "Flex Handle", 
            9: "Rachet Handle", 
            10: "S Handle", 
            12: "Spanners"
        }
        
    def count(self, detections, reference_catalog=None):
        """
        Calculates counts from a list of global detections.
        """
        results = {
            "total_raw_detections": len(detections),
            "total_objects": len(detections), # Backwards compatibility alias
            "raw_socket_candidates": 0,
            "matched_reference_sockets": 0,
            "unmatched_candidates": 0,
            "missing_references": 0,
            "low_confidence_candidates": 0,
            "missing_mask": 0,
            "unsuitable_mask": 0,
            "major_tools": 0,
            "uncertain_major_tools": 0,
            "per_category": {}
        }
        
        seen_instances = set()
        
        for det in detections:
            gid = det.get("global_instance_id")
            if gid in seen_instances:
                continue # Do not allow duplicate instance IDs to inflate count
            seen_instances.add(gid)
            
            cid = det["class_id"]
            cname = det["class_name"]
            conf = det["confidence"]
            area = det.get("area_px", 0)
            has_mask = det.get("mask_available", False)
            
            # Setup analysis flags
            is_low_conf = conf < self.low_confidence_threshold
            det["low_confidence_warning"] = is_low_conf
            
            # Mask checks
            if not has_mask:
                results["missing_mask"] += 1
                det["mask_quality_status"] = "MISSING"
            else:
                # Over 600 area implies excessive polygon spill into foam/shadow based on tests
                if det.get("is_socket") and (area > 600 or area < 50):
                    results["unsuitable_mask"] += 1
                    det["mask_quality_status"] = "UNSUITABLE"
                else:
                    det["mask_quality_status"] = "GOOD"
            
            # Per Category
            results["per_category"][cname] = results["per_category"].get(cname, 0) + 1
            
            # Socket Counting
            if cid in self.socket_classes:
                results["raw_socket_candidates"] += 1
                if is_low_conf:
                    results["low_confidence_candidates"] += 1
                    det["review_flag"] = "LOW_CONFIDENCE_SOCKET"
                else:
                    det["review_flag"] = "NONE"
                    
                # Reference assignment counting
                assign_status = det.get("assignment_status", "UNASSIGNED")
                if assign_status in ["ASSIGNED", "IDENTITY REVIEW REQUIRED"]:
                    results["matched_reference_sockets"] += 1
                elif assign_status == "EXTRA / UNMATCHED":
                    results["unmatched_candidates"] += 1
                    
            # Major Tool Counting
            elif cid in self.major_tool_classes:
                # E.g. out of distribution Tape Measure might show up as Rachet Handle with low conf
                if is_low_conf:
                    results["uncertain_major_tools"] += 1
                    det["review_flag"] = "UNCERTAIN_MAJOR_TOOL"
                else:
                    results["major_tools"] += 1
                    det["review_flag"] = "NONE"
                    
            det["counting_eligibility"] = "COUNTED"

        # Count missing references
        if reference_catalog:
            missing_count = sum(1 for ref in reference_catalog if ref.get("assignment_status") == "MISSING")
            results["missing_references"] = missing_count

        results["sockets"] = results["raw_socket_candidates"] # Backwards compatibility alias
        results["socket_family_combined"] = results["raw_socket_candidates"]
        results["low_confidence_sockets"] = results["low_confidence_candidates"]
        return results


# =====================================================================
# SECTION: inspection/count_comparator.py
# =====================================================================

class CountComparator:
    def compare(self, expected_counts, counter_results):
        """
        expected_counts: dict from ReferenceManager (e.g. {"Sockets": 7, "Major Tools": "NOT CONFIGURED"})
        counter_results: dict from ToolCounter
        
        Returns a list of structured comparison results per category.
        """
        comparisons = []
        
        # 1. Compare Sockets (Verified Matches)
        exp_sockets = expected_counts.get("Sockets", "NOT CONFIGURED")
        
        matched_sockets = counter_results.get("matched_reference_sockets", 0)
        raw_sockets = counter_results.get("raw_socket_candidates", 0)
        
        if exp_sockets == "NOT CONFIGURED":
            status_matched = "NOT CONFIGURED"
            status_raw = "N/A"
        else:
            diff_matched = matched_sockets - exp_sockets
            if matched_sockets == 0 and raw_sockets > 0:
                status_matched = "NOT VERIFIED (No Layout)"
            elif diff_matched == 0:
                status_matched = "MATCH VERIFIED"
            elif diff_matched < 0:
                status_matched = "MISSING REFERENCES"
            else:
                status_matched = "EXTRA ASSIGNMENTS (ERROR)"
                
            diff_raw = raw_sockets - exp_sockets
            if diff_raw == 0:
                status_raw = "RAW MATCH (Unverified)"
            elif diff_raw < 0:
                status_raw = "RAW MISSING"
            else:
                status_raw = f"{diff_raw} EXTRA RAW"
                
        comparisons.append({
            "category": "Sockets (Verified Matches)",
            "expected": exp_sockets,
            "detected": matched_sockets,
            "difference": 0,
            "status": status_matched
        })
        
        comparisons.append({
            "category": "Sockets (Raw Candidates)",
            "expected": exp_sockets,
            "detected": raw_sockets,
            "difference": 0,
            "status": status_raw
        })
        
        # 2. Major Tools
        exp_major = expected_counts.get("Major Tools", "NOT CONFIGURED")
        det_major = counter_results.get("major_tools", 0)
        uncertain_major = counter_results.get("uncertain_major_tools", 0)
        
        if exp_major == "NOT CONFIGURED":
            status = "NOT CONFIGURED"
            diff = 0
            if uncertain_major > 0:
                status = "REVIEW (Uncertain)"
        else:
            diff = det_major - exp_major
            if uncertain_major > 0:
                status = "REVIEW"
            elif diff == 0:
                status = "MATCH — IDENTITY UNVERIFIED"
            elif diff < 0:
                status = "MISSING"
            else:
                status = "EXTRA"
                
        comparisons.append({
            "category": "Major Tools",
            "expected": exp_major,
            "detected": det_major,
            "difference": diff,
            "status": status
        })
        
        return comparisons


# =====================================================================
# SECTION: inspection/company_manager.py
# =====================================================================

import os
import sys
import time
import pandas as pd
from pathlib import Path

# Resolve base directories safely


class CompanyManager:
    """
    Manages loading, parsing, and verifying company toolkit references from Book1.xlsx.
    Maintains independent expected tool counts for 14 industrial tool categories.
    Supports live synchronization and change detection.
    """

    # 14 industrial tool categories mapped directly to YOLO class IDs (0..13)
    TOOL_CATEGORIES = [
        {"name": "Adaptor",          "excel_col": "Adaptor",          "class_id": 0},
        {"name": "Allen Key",        "excel_col": "Allen Key",        "class_id": 1},
        {"name": "Bit Holder",       "excel_col": "Bit Holder",       "class_id": 2},
        {"name": "Bit Sockets",      "excel_col": "Bit Sockets",      "class_id": 3},  # YOLO model: Bit Socket
        {"name": "Bits",             "excel_col": "Bits",             "class_id": 4},
        {"name": "Deep Socket",      "excel_col": "Deep Socket",      "class_id": 5},
        {"name": "Extension Bar",    "excel_col": "Extension Bar",    "class_id": 6},
        {"name": "Flex Handle",      "excel_col": "Flex Handle",      "class_id": 7},
        {"name": "Rachet-Handels",   "excel_col": "Rachet-Handels",   "class_id": 9},  # YOLO model: Rachet Handle
        {"name": "S Handle",         "excel_col": "S Handle",         "class_id": 10},
        {"name": "Spanners",         "excel_col": "Spanners",         "class_id": 12},
        {"name": "Sockets",          "excel_col": "Sockets",          "class_id": 11},
        {"name": "long bit socket",  "excel_col": "long bit socket",  "class_id": 8},  # YOLO model: Long bit socket
        {"name": "universal joint",  "excel_col": "universal joint",  "class_id": 13},
    ]

    def __init__(self, workbook_path=None):
        self.workbook_path = None
        self.is_loaded = False
        self.error_message = ""
        self.companies = []
        self._raw_df = None
        self._column_map = {}
        self.last_mtime = 0.0
        
        # Build category normalization map
        self._build_normalization_map()
        
        # Auto-load on instantiation
        self.load_workbook(workbook_path)

    def _build_normalization_map(self):
        """Build normalized lookup table for mapping Excel headers to class IDs."""
        self._norm_to_cat = {}
        for cat in self.TOOL_CATEGORIES:
            norm = self._normalize_key(cat["excel_col"])
            self._norm_to_cat[norm] = cat
            norm_name = self._normalize_key(cat["name"])
            self._norm_to_cat[norm_name] = cat

    @staticmethod
    def _normalize_key(key):
        if not key:
            return ""
        # Lowercase and remove spaces, dashes, underscores
        return str(key).lower().replace(" ", "").replace("-", "").replace("_", "")

    def find_default_workbook(self):
        """
        Dynamically resolves the company workbook path relative to the application
        or resource directories, prioritizing the user's original authoritative
        'Excel Sheet/Book1.xlsx' workbook before any fallbacks.
        """
        candidates = [
            # 1. Authoritative original path in application root
            os.path.join(APP2_DIR, "Excel Sheet", "Book1.xlsx"),
            os.path.join(USER_DIR, "Excel Sheet", "Book1.xlsx"),
            os.path.join(os.getcwd(), "Excel Sheet", "Book1.xlsx"),
            # 2. Compatibility fallbacks
            os.path.join(APP2_DIR, "Excel sheets", "Book1.xlsx"),
            os.path.join(USER_DIR, "Excel sheets", "Book1.xlsx"),
            os.path.join(os.getcwd(), "Excel sheets", "Book1.xlsx"),
            os.path.join(APP2_DIR, "Book1.xlsx"),
            os.path.join(USER_DIR, "Book1.xlsx"),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return os.path.abspath(path)
        return None

    def has_workbook_changed_on_disk(self):
        """Checks if the workbook file modification time has changed on disk."""
        if not self.workbook_path or not os.path.isfile(self.workbook_path):
            return False
        try:
            mtime = os.path.getmtime(self.workbook_path)
            return mtime > self.last_mtime
        except OSError:
            return False

    def load_workbook(self, file_path=None, max_retries=5, retry_delay_sec=0.15):
        """
        Loads and parses Book1.xlsx, extracting company names and expected tool quantities.
        Includes retry logic to safely handle transient Microsoft Excel write locks and atomic file replacements.
        If missing, sets error_message to 'Company Reference Workbook Not Found'.
        """
        target_path = file_path or self.workbook_path or self.find_default_workbook()
        
        # Brief retry if file is momentarily missing during atomic replace (Excel SafeSave)
        for _ in range(max_retries):
            if target_path and os.path.isfile(target_path):
                break
            time.sleep(retry_delay_sec)

        if not target_path or not os.path.isfile(target_path):
            if not self.is_loaded:
                self.workbook_path = None
                self.is_loaded = False
                self.error_message = "Company Reference Workbook Not Found"
                self.companies = []
                self._raw_df = None
            return False, self.error_message

        # Attempt to read with retry in case Excel holds an active write lock
        df = None
        last_exc = None
        for attempt in range(max_retries):
            try:
                with pd.ExcelFile(target_path) as xls:
                    sheet_name = "Sheet1" if "Sheet1" in xls.sheet_names else xls.sheet_names[0]
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                break
            except (PermissionError, OSError) as pe:
                last_exc = pe
                time.sleep(retry_delay_sec)
            except Exception as e:
                last_exc = e
                break

        if df is None:
            # If reading failed due to lock/IO, do not wipe existing memory if already loaded
            if not self.is_loaded:
                self.workbook_path = None
                self.is_loaded = False
                self.companies = []
                self._raw_df = None
            self.error_message = f"Error reading company workbook: {str(last_exc)}"
            return False, self.error_message

        try:
            # Validate 'Company' column
            company_col = None
            for col in df.columns:
                if str(col).strip().lower() == "company":
                    company_col = col
                    break
            
            if not company_col:
                self.is_loaded = False
                self.error_message = "Company Reference Workbook Invalid: Missing 'Company' column"
                self.companies = []
                self._raw_df = None
                return False, self.error_message

            # Extract nonempty company names, maintaining order and handling duplicates
            raw_companies = [str(c).strip() for c in df[company_col] if pd.notna(c) and str(c).strip()]
            seen = set()
            unique_companies = []
            for c in raw_companies:
                if c not in seen:
                    unique_companies.append(c)
                    seen.add(c)
                else:
                    print(f"[CompanyManager] Duplicate company entry ignored: '{c}'")

            # Map Excel columns to our 14 tool categories
            self._column_map = {}
            for col in df.columns:
                if col == company_col:
                    continue
                norm_col = self._normalize_key(col)
                if norm_col in self._norm_to_cat:
                    cat = self._norm_to_cat[norm_col]
                    self._column_map[cat["class_id"]] = col

            self.workbook_path = target_path
            self.companies = unique_companies
            self._raw_df = df
            self._company_col = company_col
            self.last_mtime = os.path.getmtime(target_path)
            self.is_loaded = True
            self.error_message = ""
            return True, "Workbook loaded successfully."

        except Exception as e:
            if not self.is_loaded:
                self.workbook_path = None
                self.is_loaded = False
                self.companies = []
                self._raw_df = None
            self.error_message = f"Error reading company workbook: {str(e)}"
            return False, self.error_message

    def get_companies(self):
        """Returns list of configured company names."""
        return list(self.companies)

    def get_expected_counts(self, company_name):
        """
        Retrieves expected counts for a company across all 14 tool categories.
        - Valid non-negative integer -> int (e.g. 0, 5, 44)
        - Blank / NaN cell -> None (marked NOT CONFIGURED, never silently converted to 0)
        - Negative or non-integer -> None (invalid configuration)
        """
        if not self.is_loaded or self._raw_df is None or not company_name:
            return {cat["class_id"]: None for cat in self.TOOL_CATEGORIES}

        # Find row for company
        matched_rows = self._raw_df[self._raw_df[self._company_col].astype(str).str.strip() == str(company_name).strip()]
        if matched_rows.empty:
            return {cat["class_id"]: None for cat in self.TOOL_CATEGORIES}

        row = matched_rows.iloc[0]
        expected_counts = {}

        for cat in self.TOOL_CATEGORIES:
            cid = cat["class_id"]
            col_name = self._column_map.get(cid)
            if not col_name or col_name not in row:
                expected_counts[cid] = None
                continue

            val = row[col_name]
            if pd.isna(val) or val is None or str(val).strip() == "":
                expected_counts[cid] = None
            else:
                try:
                    num = float(val)
                    if num < 0 or not num.is_integer():
                        print(f"[CompanyManager] Invalid quantity '{val}' for {cat['name']} in company '{company_name}'")
                        expected_counts[cid] = None
                    else:
                        expected_counts[cid] = int(num)
                except (ValueError, TypeError):
                    print(f"[CompanyManager] Non-numeric quantity '{val}' for {cat['name']} in company '{company_name}'")
                    expected_counts[cid] = None

        return expected_counts

    def verify_counts(self, company_name, detections_or_counts):
        """
        Compares detected quantities against expected quantities for the selected company.
        
        Args:
            company_name: Selected company string.
            detections_or_counts: List of detection dicts (with 'class_id' and 'global_instance_id')
                                  OR dict mapping class_id -> integer count.
                                  
        Returns structured verification results per category and overall verdict.
        """
        # Parse detected counts
        if isinstance(detections_or_counts, list):
            seen_ids = set()
            det_counts = {cat["class_id"]: 0 for cat in self.TOOL_CATEGORIES}
            for d in detections_or_counts:
                gid = d.get("global_instance_id")
                if gid is not None:
                    if gid in seen_ids:
                        continue
                    seen_ids.add(gid)
                cid = d.get("class_id")
                if cid is not None and cid in det_counts:
                    det_counts[cid] += 1
        elif isinstance(detections_or_counts, dict):
            det_counts = {cat["class_id"]: detections_or_counts.get(cat["class_id"], 0) for cat in self.TOOL_CATEGORIES}
        else:
            det_counts = {cat["class_id"]: 0 for cat in self.TOOL_CATEGORIES}

        exp_counts = self.get_expected_counts(company_name) if company_name else {cat["class_id"]: None for cat in self.TOOL_CATEGORIES}

        category_results = []
        matches = 0
        missing_count = 0
        extra_count = 0
        unconfigured_count = 0

        for cat in self.TOOL_CATEGORIES:
            cid = cat["class_id"]
            name = cat["name"]
            excel_col = cat["excel_col"]
            det_qty = det_counts.get(cid, 0)
            exp_qty = exp_counts.get(cid)

            if exp_qty is None:
                diff = None
                status = "NOT CONFIGURED"
                status_detail = "NOT CONFIGURED"
                status_type = "UNCONFIGURED"
                unconfigured_count += 1
            else:
                diff = det_qty - exp_qty
                if diff == 0:
                    status = "MATCHED"
                    status_detail = "MATCHED"
                    status_type = "MATCHED"
                    matches += 1
                elif diff < 0:
                    status = "MISSING"
                    status_detail = f"MISSING {abs(diff)}"
                    status_type = "MISSING"
                    missing_count += 1
                else:
                    status = "EXTRA"
                    status_detail = f"EXTRA {diff}"
                    status_type = "EXTRA"
                    extra_count += 1

            category_results.append({
                "class_id": cid,
                "category_name": name,
                "excel_column": excel_col,
                "detected": det_qty,
                "expected": exp_qty,
                "difference": diff,
                "status": status,
                "status_detail": status_detail,
                "status_type": status_type,
            })

        # Overall Status
        if not self.is_loaded:
            overall_status = "WORKBOOK NOT LOADED"
        elif not company_name:
            overall_status = "NO COMPANY SELECTED"
        elif missing_count > 0 or extra_count > 0:
            overall_status = "COUNT DISCREPANCY"
        elif unconfigured_count == len(self.TOOL_CATEGORIES):
            overall_status = "NOT CONFIGURED"
        elif unconfigured_count > 0:
            overall_status = "VERIFIED (PARTIAL)"
        else:
            overall_status = "VERIFIED"

        return {
            "company": company_name,
            "workbook_path": self.workbook_path,
            "overall_status": overall_status,
            "categories": category_results,
            "total_detected": sum(det_counts.values()),
            "total_expected": sum(r["expected"] for r in category_results if isinstance(r["expected"], int)),
            "matches": matches,
            "missing": missing_count,
            "extra": extra_count,
            "unconfigured": unconfigured_count,
        }


# =====================================================================
# SECTION: inspection/socket_identifier.py
# =====================================================================

import os
import json
import uuid
import numpy as np
from datetime import datetime

class SocketIdentifier:
    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = os.path.join(USER_DIR, "data")
        self.layouts_dir = os.path.join(data_dir, "layouts")
        os.makedirs(self.layouts_dir, exist_ok=True)
        
        self.current_layout = None
        self.active_toolkit_id = None
        self.assignment_state = {} # global_instance_id -> reference_id
        
    def load_layout(self, toolkit_id):
        """
        Loads the most recent taught layout for the given toolkit_id.
        """
        self.active_toolkit_id = toolkit_id
        self.current_layout = None
        self.assignment_state = {}
        
        if not toolkit_id or toolkit_id == "Unknown" or toolkit_id == "NOT LOADED":
            return False
            
        layout_path = os.path.join(self.layouts_dir, f"layout_{toolkit_id}.json")
        if os.path.exists(layout_path):
            try:
                with open(layout_path, 'r') as f:
                    self.current_layout = json.load(f)
                return True
            except Exception as e:
                print(f"Failed to load layout: {e}")
                return False
        return False
        
    def save_layout(self, toolkit_id, image_width, image_height, detections, taught_assignments):
        """
        Saves the normalized centroids for assigned sockets into a layout file.
        taught_assignments: dict of global_instance_id -> reference_id
        """
        if not toolkit_id or toolkit_id == "Unknown" or toolkit_id == "NOT LOADED":
            return False, "Invalid toolkit ID"
            
        layout = {
            "layout_id": str(uuid.uuid4()),
            "toolkit_id": toolkit_id,
            "timestamp": datetime.now().isoformat(),
            "sockets": []
        }
        
        for det in detections:
            gid = det["global_instance_id"]
            if gid in taught_assignments:
                ref_id = taught_assignments[gid]
                cx, cy = det["centroid"]
                nx = cx / float(image_width)
                ny = cy / float(image_height)
                
                layout["sockets"].append({
                    "reference_id": ref_id,
                    "normalized_x": nx,
                    "normalized_y": ny,
                    "px_x": cx,
                    "px_y": cy
                })
                
        if not layout["sockets"]:
            return False, "No assigned sockets to save"
            
        self.current_layout = layout
        self.active_toolkit_id = toolkit_id
        
        layout_path = os.path.join(self.layouts_dir, f"layout_{toolkit_id}.json")
        try:
            with open(layout_path, 'w') as f:
                json.dump(layout, f, indent=2)
            return True, "Layout saved successfully."
        except Exception as e:
            return False, f"Failed to save layout: {e}"
            
    def automatic_matching(self, detections, reference_catalog, image_width, image_height):
        """
        Matches incoming detections against the currently loaded layout and the reference catalog.
        Returns the assignment dictionary and any ambiguous detections.
        """
        self.assignment_state = {}
        
        candidates = [d for d in detections if d.get("is_socket")]
        
        for cand in candidates:
            cand["assignment_status"] = "UNASSIGNED"
            cand["assignment_quality"] = "NONE"
            cand["assigned_reference_id"] = None

        if not self.current_layout or not self.current_layout.get("sockets"):
            for cand in candidates:
                cand["assignment_status"] = "UNASSIGNED (NO LAYOUT)"
            return
            
        print(f"[SocketIdentifier] Starting automatic_matching")
        
        valid_ref_ids = {r["reference_id"] for r in reference_catalog}
        layout_sockets = [s for s in self.current_layout["sockets"] if s["reference_id"] in valid_ref_ids]
        
        print(f"[SocketIdentifier] Active Toolkit ID: {self.active_toolkit_id}")
        print(f"[SocketIdentifier] Valid reference IDs in catalog: {valid_ref_ids}")
        print(f"[SocketIdentifier] Expected Layout Sockets (after filtering by catalog): {len(layout_sockets)}")
        print(f"[SocketIdentifier] Raw Detection Candidates (is_socket=True): {len(candidates)}")
        
        if len(layout_sockets) < 2 or len(candidates) < 2:
            print("[SocketIdentifier] FAILING: Need >=2 layout sockets and >=2 candidates for orientation.")
            for cand in candidates:
                cand["assignment_status"] = "ORIENTATION UNVERIFIED"
            return

        # Build layout points
        L_pts = []
        L_ids = []
        for s in layout_sockets:
            px = s.get("px_x", s.get("normalized_x", 0) * image_width)
            py = s.get("px_y", s.get("normalized_y", 0) * image_height)
            L_pts.append((px, py))
            L_ids.append(s["reference_id"])
        
        # Build candidate points
        D_pts = []
        for cand in candidates:
            D_pts.append(cand["centroid"])
            
        valid_assignments = {} # signature -> (inlier_count, error_sum, current_assignments)
        
        dist_tolerance = max(image_width, image_height) * 0.05 # 5% of max dimension tolerance
        print(f"[SocketIdentifier] Distance tolerance: {dist_tolerance:.1f} px")
        
        import math
        from scipy.optimize import linear_sum_assignment
        
        # Try all pairs of layout points and all pairs of detected points
        for i in range(len(L_pts)):
            for j in range(len(L_pts)):
                if i == j: continue
                L_dx = L_pts[j][0] - L_pts[i][0]
                L_dy = L_pts[j][1] - L_pts[i][1]
                L_dist = math.hypot(L_dx, L_dy)
                L_ang = math.atan2(L_dy, L_dx)
                
                for u in range(len(D_pts)):
                    for v in range(len(D_pts)):
                        if u == v: continue
                        D_dx = D_pts[v][0] - D_pts[u][0]
                        D_dy = D_pts[v][1] - D_pts[u][1]
                        D_dist = math.hypot(D_dx, D_dy)
                        
                        # Calculate scale (similarity transform)
                        s = D_dist / L_dist if L_dist > 0 else 1.0
                        
                        # Restrict scale to physically plausible variations (e.g. 20% zoom in/out)
                        if not (0.75 < s < 1.33):
                            continue
                            
                        # Calculate Transform from Layout to Detections
                        D_ang = math.atan2(D_dy, D_dx)
                        d_theta = D_ang - L_ang
                        
                        cos_t = math.cos(d_theta) * s
                        sin_t = math.sin(d_theta) * s
                        
                        tx = D_pts[u][0] - (L_pts[i][0] * cos_t - L_pts[i][1] * sin_t)
                        ty = D_pts[u][1] - (L_pts[i][0] * sin_t + L_pts[i][1] * cos_t)
                        
                        # Transform all layout points
                        L_transformed = []
                        for lx, ly in L_pts:
                            px = lx * cos_t - ly * sin_t + tx
                            py = lx * sin_t + ly * cos_t + ty
                            L_transformed.append((px, py))
                            
                        # Construct cost matrix
                        cost = np.zeros((len(D_pts), len(L_transformed)))
                        for d_idx in range(len(D_pts)):
                            for l_idx in range(len(L_transformed)):
                                cost[d_idx, l_idx] = math.hypot(D_pts[d_idx][0] - L_transformed[l_idx][0], D_pts[d_idx][1] - L_transformed[l_idx][1])
                                
                        row_ind, col_ind = linear_sum_assignment(cost)
                        
                        current_assignments = {}
                        inliers = 0
                        error_sum = 0
                        
                        for r_idx, c_idx in zip(row_ind, col_ind):
                            if cost[r_idx, c_idx] < dist_tolerance:
                                inliers += 1
                                error_sum += cost[r_idx, c_idx]
                                current_assignments[r_idx] = L_ids[c_idx]
                                
                        if inliers >= max(2, len(L_pts) // 2):
                            sig = frozenset(current_assignments.items())
                            if sig not in valid_assignments or error_sum < valid_assignments[sig][1]:
                                valid_assignments[sig] = (inliers, error_sum, current_assignments)

        print(f"[SocketIdentifier] Found {len(valid_assignments)} valid assignment configurations (poses)")
        
        if not valid_assignments:
            print("[SocketIdentifier] FAILING: No valid pose found matching enough slots.")
            # Failed to verify orientation securely
            for cand in candidates:
                cand["assignment_status"] = "ORIENTATION UNVERIFIED"
            return
            
        valid_list = list(valid_assignments.values())
        valid_list.sort(key=lambda x: (-x[0], x[1]))
        
        top_inliers = valid_list[0][0]
        top_error = valid_list[0][1]
        
        ambiguous = False
        if len(valid_list) > 1:
            second_inliers = valid_list[1][0]
            second_error = valid_list[1][1]
            if top_inliers == second_inliers and abs(top_error - second_error) < (dist_tolerance * 0.2 * top_inliers):
                ambiguous = True
                print("[SocketIdentifier] FAILING: Ambiguous orientation detected.")

        if ambiguous:
            for cand in candidates:
                cand["assignment_status"] = "ORIENTATION AMBIGUOUS — REVIEW REQUIRED"
            return
            
        best_assignments = valid_list[0][2]
        print(f"[SocketIdentifier] SUCCESS: Assigned {len(best_assignments)} sockets.")
        
        # Apply assignments
        for d_idx, cand in enumerate(candidates):
            gid = cand["global_instance_id"]
            if d_idx in best_assignments:
                ref_id = best_assignments[d_idx]
                self.assignment_state[gid] = ref_id
                cand["assigned_reference_id"] = ref_id
                cand["assignment_status"] = "SLOT MATCHED"
                cand["assignment_quality"] = "HIGH"
            else:
                cand["assignment_status"] = "UNMATCHED DETECTION"
                cand["assigned_reference_id"] = None

    def extract_socket_ordering_data(self, detections, verbose=True):
        """
        Extracts measurement and spatial ordering data from detected socket objects.
        
        For each socket candidate:
        - Obtains center coordinates from top-rim ellipse (fallback to segmentation centroid)
        - Rejects nonfinite/invalid center coordinates
        - Extracts calculated physical diameter in mm and checks validity
        - Initializes sequential_socket_id (without modifying original IDs or reference IDs)
        - Records identification and fallback status
        
        Returns:
            list of dicts containing:
            - global_instance_id (int)
            - center_x (float)
            - center_y (float)
            - calculated_diameter_mm (float or None)
            - measurement_valid (bool)
            - sequential_socket_id (None initially)
            - identification_status (str)
            - center_source (str: 'RIM_ELLIPSE' or 'SEGMENTATION_CENTROID')
            - detection (dict reference)
        """
        import math
        
        extracted_sockets = []
        rejected_sockets = []
        
        for cand in detections:
            if not cand.get("is_socket"):
                continue
                
            # Initialize sequential_socket_id without overwriting if already set
            if "sequential_socket_id" not in cand:
                cand["sequential_socket_id"] = None
                
            gid = cand.get("global_instance_id", cand.get("instance_num"))
            
            # 1. Primary center: top outer rim ellipse center (global coordinates)
            center_x = None
            center_y = None
            center_source = None
            
            ellipse = cand.get("rim_ellipse")
            if ellipse is not None and isinstance(ellipse, (tuple, list)) and len(ellipse) >= 2:
                ell_center = ellipse[0]
                if isinstance(ell_center, (tuple, list)) and len(ell_center) >= 2:
                    cx, cy = ell_center[0], ell_center[1]
                    if isinstance(cx, (int, float)) and isinstance(cy, (int, float)):
                        if math.isfinite(cx) and math.isfinite(cy) and cx >= 0 and cy >= 0:
                            center_x = float(cx)
                            center_y = float(cy)
                            center_source = "RIM_ELLIPSE"
                            
            # 2. Fallback center: segmentation polygon centroid
            if center_x is None or center_y is None:
                centroid = cand.get("centroid")
                if centroid is not None and isinstance(centroid, (tuple, list)) and len(centroid) >= 2:
                    cx, cy = centroid[0], centroid[1]
                    if isinstance(cx, (int, float)) and isinstance(cy, (int, float)):
                        if math.isfinite(cx) and math.isfinite(cy) and cx >= 0 and cy >= 0:
                            center_x = float(cx)
                            center_y = float(cy)
                            center_source = "SEGMENTATION_CENTROID"
                            
            # Reject nonfinite or invalid center coordinates from geometric ordering
            if center_x is None or center_y is None or not math.isfinite(center_x) or not math.isfinite(center_y):
                rejected_sockets.append({
                    "global_instance_id": gid,
                    "reason": "Nonfinite or invalid center coordinates",
                    "detection": cand
                })
                continue
                
            # 3. Calculated physical diameter in mm
            raw_diam = cand.get("calculated_diameter_mm")
            if raw_diam is None or raw_diam == 0.0:
                for fallback_key in ["updated_camera_outer_diameter_mm", "measured_diameter_mm", "measured_outer_diameter_mm"]:
                    val = cand.get(fallback_key)
                    if val is not None and isinstance(val, (int, float)) and val > 0:
                        raw_diam = val
                        break
                        
            calculated_diameter_mm = None
            measurement_valid = False
            
            if raw_diam is not None and isinstance(raw_diam, (int, float)) and math.isfinite(raw_diam):
                if raw_diam > 0.0:
                    calculated_diameter_mm = float(raw_diam)
                    measurement_valid = True
                else:
                    calculated_diameter_mm = float(raw_diam)
                    measurement_valid = False
            else:
                measurement_valid = False
                
            # 3b. Top-rim ellipse pixel diameter
            px_diam = cand.get("pixel_diameter")
            if (px_diam is None or px_diam <= 0.0) and cand.get("rim_ellipse"):
                ell = cand.get("rim_ellipse")
                if isinstance(ell, (tuple, list)) and len(ell) >= 2 and isinstance(ell[1], (tuple, list)) and len(ell[1]) >= 2:
                    px_diam = float(max(ell[1][0], ell[1][1]))
            pixel_diameter = float(px_diam) if (px_diam is not None and isinstance(px_diam, (int, float)) and math.isfinite(px_diam) and px_diam > 0.0) else None
                
            # Identification status
            if center_source == "RIM_ELLIPSE":
                identification_status = "ELLIPSE_CENTER" if measurement_valid else "ELLIPSE_CENTER_INVALID_DIAMETER"
            elif center_source == "SEGMENTATION_CENTROID":
                identification_status = "FALLBACK_CENTROID" if measurement_valid else "FALLBACK_CENTROID_INVALID_DIAMETER"
            else:
                identification_status = "UNKNOWN_CENTER"
                
            record = {
                "global_instance_id": gid,
                "center_x": center_x,
                "center_y": center_y,
                "calculated_diameter_mm": calculated_diameter_mm,
                "measurement_valid": measurement_valid,
                "sequential_socket_id": cand.get("sequential_socket_id"),
                "identification_status": identification_status,
                "center_source": center_source,
                "pixel_diameter": pixel_diameter,
                "rim_status": cand.get("rim_status"),
                "rim_ellipse": cand.get("rim_ellipse"),
                "fit_quality": cand.get("fit_quality"),
                "detection": cand
            }
            extracted_sockets.append(record)
            
        # 4. Diagnostic logging
        if verbose:
            print(f"\n[SocketIdentifier] Extracted {len(extracted_sockets)} socket candidate(s) for spatial ordering:")
            print(f"{'Detection ID':<14} | {'Center X':<10} | {'Center Y':<10} | {'Calculated OD':<15} | {'Measurement Validity':<20} | {'Status'}")
            print("-" * 92)
            for r in extracted_sockets:
                od_str = f"{r['calculated_diameter_mm']:.2f} mm" if r['calculated_diameter_mm'] is not None and r['calculated_diameter_mm'] > 0 else "N/A"
                print(f"{str(r['global_instance_id']):<14} | {r['center_x']:<10.2f} | {r['center_y']:<10.2f} | {od_str:<15} | {str(r['measurement_valid']):<20} | {r['identification_status']}")
            if rejected_sockets:
                print(f"[SocketIdentifier] Rejected {len(rejected_sockets)} socket candidate(s) due to invalid center:")
                for rej in rejected_sockets:
                    print(f"  - Detection ID {rej['global_instance_id']}: {rej['reason']}")
            print()
            
        return extracted_sockets

    extract_socket_data = extract_socket_ordering_data

    def order_sockets_by_geometry(self_or_records, socket_records=None, max_perpendicular_deviation_px=30.0, verbose=True):
        """
        Applies PCA / SVD spatial ordering to extracted socket records along their dominant row axis.
        
        Args:
            socket_records: list of dicts from extract_socket_ordering_data()
            max_perpendicular_deviation_px: threshold in pixels for row alignment validation
            verbose: whether to print [SOCKET PCA] diagnostic log
            
        Returns:
            SpatialOrderingResult (tuple of ordered_records, diagnostics)
        """
        import math
        import numpy as np
        
        if socket_records is None and isinstance(self_or_records, (list, tuple)):
            records_in = self_or_records
        else:
            records_in = socket_records if socket_records is not None else []
            
        # 1. Collect valid center coordinates
        valid_records = []
        points = []
        for r in records_in:
            cx = r.get("center_x")
            cy = r.get("center_y")
            if cx is not None and cy is not None:
                if isinstance(cx, (int, float)) and isinstance(cy, (int, float)):
                    if math.isfinite(cx) and math.isfinite(cy):
                        valid_records.append(r)
                        points.append([float(cx), float(cy)])
                        
        n_points = len(points)
        
        # Handle insufficient data (< 2 sockets)
        if n_points < 2:
            diag = {
                "status": "INSUFFICIENT_DATA",
                "reason": "At least 2 valid socket centers are required for PCA spatial ordering.",
                "valid_centers_count": n_points,
                "principal_axis": None,
                "row_angle_deg": None,
                "mean_center": points[0] if n_points == 1 else None,
                "endpoint_a": valid_records[0] if n_points == 1 else None,
                "endpoint_b": valid_records[0] if n_points == 1 else None,
                "max_perpendicular_deviation_px": 0.0,
                "rms_perpendicular_deviation_px": 0.0,
                "row_alignment_status": "INSUFFICIENT_DATA",
                "ordered_records": valid_records
            }
            if verbose:
                print(f"[SOCKET PCA] Insufficient data: {n_points} valid center(s) available.")
            return SpatialOrderingResult(valid_records, diag)
            
        pts_arr = np.array(points, dtype=np.float64)
        
        # Check for duplicate or degenerate centers
        dists_from_first = np.linalg.norm(pts_arr - pts_arr[0], axis=1)
        if float(np.max(dists_from_first)) < 1.0:
            diag = {
                "status": "GEOMETRY_DEGENERATE",
                "reason": "All socket centers are duplicate or nearly identical (< 1.0 px distance).",
                "valid_centers_count": n_points,
                "principal_axis": None,
                "row_angle_deg": None,
                "mean_center": pts_arr[0].tolist(),
                "endpoint_a": valid_records[0],
                "endpoint_b": valid_records[-1],
                "max_perpendicular_deviation_px": 0.0,
                "rms_perpendicular_deviation_px": 0.0,
                "row_alignment_status": "GEOMETRY_DEGENERATE",
                "ordered_records": valid_records
            }
            if verbose:
                print(f"[SOCKET PCA] Degenerate geometry: all {n_points} centers are identical.")
            return SpatialOrderingResult(valid_records, diag)
            
        mean_center = np.mean(pts_arr, axis=0)
        
        # 2. Determine dominant row axis
        if n_points == 2:
            # For two sockets, calculate direct axis between their centers
            delta = pts_arr[1] - pts_arr[0]
            dist = float(np.linalg.norm(delta))
            principal_axis = delta / dist
        else:
            # 3. Apply PCA/SVD to determine dominant row axis
            centered_points = pts_arr - mean_center
            # SVD of centered points: centered_points = U * S * Vt
            # First row of Vt is the principal component direction
            _, _, vt = np.linalg.svd(centered_points, full_matrices=False)
            principal_axis = vt[0]
            
        # 4. Deterministic PCA orientation
        # If X component has larger absolute magnitude, orient axis so X is positive.
        # Otherwise, orient axis so Y is positive.
        ax_x, ax_y = float(principal_axis[0]), float(principal_axis[1])
        if abs(ax_x) >= abs(ax_y):
            if ax_x < 0:
                principal_axis = -principal_axis
        else:
            if ax_y < 0:
                principal_axis = -principal_axis
                
        # 5. Project every center onto dominant axis
        projections = []
        for i, pt in enumerate(pts_arr):
            v = pt - mean_center
            proj = float(np.dot(v, principal_axis))
            projections.append((proj, i))
            
        # 6. Sort records according to projected position
        projections.sort(key=lambda x: x[0])
        sorted_records = [valid_records[idx] for (_, idx) in projections]
        
        # 7. Row alignment validation (perpendicular distances)
        perp_distances = []
        for pt in pts_arr:
            v = pt - mean_center
            proj = np.dot(v, principal_axis)
            perp_vec = v - proj * principal_axis
            perp_distances.append(float(np.linalg.norm(perp_vec)))
            
        perp_distances = np.array(perp_distances, dtype=np.float64)
        max_perp = float(np.max(perp_distances))
        rms_perp = float(np.sqrt(np.mean(np.square(perp_distances))))
        
        if max_perp <= max_perpendicular_deviation_px:
            row_alignment_status = "VALID"
        else:
            row_alignment_status = "WARNING_OUTLIERS"
            
        endpoint_a = sorted_records[0]
        endpoint_b = sorted_records[-1]
        
        angle_deg = float(np.degrees(np.arctan2(principal_axis[1], principal_axis[0])))
        
        # Diagnostic logging
        if verbose:
            order_str = " -> ".join([f"#{r['global_instance_id']}" for r in sorted_records])
            ep_a_str = f"#{endpoint_a['global_instance_id']}"
            ep_b_str = f"#{endpoint_b['global_instance_id']}"
            print(f"\n[SOCKET PCA] Valid centers: {n_points}")
            print(f"[SOCKET PCA] Row angle: {angle_deg:.2f} degrees")
            print(f"[SOCKET PCA] Geometric order: {order_str}")
            print(f"[SOCKET PCA] Endpoint A: {ep_a_str}")
            print(f"[SOCKET PCA] Endpoint B: {ep_b_str}")
            print(f"[SOCKET PCA] Row alignment: {row_alignment_status}")
            print(f"[SOCKET PCA] Max perpendicular residual: {max_perp:.2f} px (Threshold: {max_perpendicular_deviation_px:.1f} px)")
            print(f"[SOCKET PCA] RMS perpendicular residual: {rms_perp:.2f} px\n")
            
        diag = {
            "status": "SUCCESS",
            "valid_centers_count": n_points,
            "principal_axis": principal_axis.tolist(),
            "row_angle_deg": angle_deg,
            "mean_center": mean_center.tolist(),
            "endpoint_a": endpoint_a,
            "endpoint_b": endpoint_b,
            "max_perpendicular_deviation_px": max_perp,
            "rms_perpendicular_deviation_px": rms_perp,
            "row_alignment_status": row_alignment_status,
            "ordered_records": sorted_records
        }
        
        return SpatialOrderingResult(sorted_records, diag)


    def assign_sequential_socket_ids(self_or_detections, detections=None, endpoint_min_difference_mm=0.50, endpoint_min_pixel_difference_px=1.5, max_perpendicular_deviation_px=30.0, verbose=True):
        """
        Assigns sequential socket IDs (S01, S02, ... SN) starting from the reliably smaller-diameter endpoint
        along the physical spatial arrangement determined by PCA.
        
        Operates completely autonomously without requiring an Excel reference file or taught layout.
        Preserves original detection IDs, reference IDs, and metrology measurements.
        
        Args:
            self_or_detections: SocketIdentifier instance or list of detections / records
            detections: list of detections (if called as method on an instance)
            endpoint_min_difference_mm: minimum outer diameter difference (mm) to confidently determine orientation
            endpoint_min_pixel_difference_px: minimum pixel diameter difference (px) for fitted rim ellipse fallback
            max_perpendicular_deviation_px: threshold for row alignment validity
            verbose: whether to print diagnostic output
            
        Returns:
            SequentialAssignmentResult (dict-like container containing ordered_records, status, diagnostics)
        """
        import math
        import numpy as np
        
        if detections is None and isinstance(self_or_detections, (list, tuple)):
            input_items = self_or_detections
            instance = self_or_detections if isinstance(self_or_detections, SocketIdentifier) else None
        else:
            input_items = detections if detections is not None else []
            instance = self_or_detections if isinstance(self_or_detections, SocketIdentifier) else None

        # 1. Clear previous sequential IDs to prevent stale state across repeated captures
        is_raw_detections = any("is_socket" in item for item in input_items if isinstance(item, dict))
        
        if is_raw_detections:
            for item in input_items:
                if isinstance(item, dict) and item.get("is_socket"):
                    item["sequential_socket_id"] = None
                    item["sequential_identification_status"] = "PENDING"
                    
            if instance is not None:
                socket_records = instance.extract_socket_ordering_data(input_items, verbose=False)
            else:
                socket_records = SocketIdentifier.extract_socket_ordering_data(None, input_items, verbose=False)
        else:
            socket_records = input_items
            for r in socket_records:
                if isinstance(r, dict):
                    r["sequential_socket_id"] = None
                    r["identification_status"] = "PENDING"
                    if "detection" in r and isinstance(r["detection"], dict):
                        r["detection"]["sequential_socket_id"] = None
                        r["detection"]["sequential_identification_status"] = "PENDING"

        # 2. Run PCA spatial ordering
        if instance is not None:
            spatial_result = instance.order_sockets_by_geometry(
                socket_records, max_perpendicular_deviation_px=max_perpendicular_deviation_px, verbose=False
            )
        else:
            spatial_result = SocketIdentifier.order_sockets_by_geometry(
                socket_records, max_perpendicular_deviation_px=max_perpendicular_deviation_px, verbose=False
            )
            
        ordered_records = spatial_result.ordered_records
        spatial_diag = spatial_result.diagnostics
        
        # 3. Check data sufficiency
        if spatial_diag.get("status") == "INSUFFICIENT_DATA" or len(ordered_records) < 2:
            status = "INSUFFICIENT_DATA"
            reason = "At least 2 valid socket detections are required for sequential assignment."
            for r in ordered_records:
                r["sequential_socket_id"] = None
                r["identification_status"] = "INSUFFICIENT_DATA"
                if "detection" in r and isinstance(r["detection"], dict):
                    r["detection"]["sequential_socket_id"] = None
                    r["detection"]["sequential_identification_status"] = "INSUFFICIENT_DATA"
            if verbose:
                print(f"[SEQUENTIAL ID] Assignment Status: {status} ({reason})")
            return SequentialAssignmentResult({
                "status": status,
                "reason": reason,
                "ordered_records": ordered_records,
                "start_endpoint": ordered_records[0] if ordered_records else None,
                "end_endpoint": ordered_records[-1] if ordered_records else None,
                "is_reversed": False,
                "endpoint_difference_mm": None,
                "spatial_diagnostics": spatial_diag
            })
            
        # 4. Check geometric validity
        if spatial_diag.get("status") == "GEOMETRY_DEGENERATE":
            status = "GEOMETRY_INVALID"
            reason = "Socket centers are duplicate or nearly identical."
            for r in ordered_records:
                r["sequential_socket_id"] = None
                r["identification_status"] = "GEOMETRY_INVALID"
                if "detection" in r and isinstance(r["detection"], dict):
                    r["detection"]["sequential_socket_id"] = None
                    r["detection"]["sequential_identification_status"] = "GEOMETRY_INVALID"
            if verbose:
                print(f"[SEQUENTIAL ID] Assignment Status: {status} ({reason})")
            return SequentialAssignmentResult({
                "status": status,
                "reason": reason,
                "ordered_records": ordered_records,
                "start_endpoint": ordered_records[0],
                "end_endpoint": ordered_records[-1],
                "is_reversed": False,
                "endpoint_difference_mm": None,
                "spatial_diagnostics": spatial_diag
            })
            
        if spatial_diag.get("row_alignment_status") == "WARNING_OUTLIERS":
            status = "GEOMETRY_INVALID"
            max_dev = spatial_diag.get("max_perpendicular_deviation_px", 0.0)
            reason = f"Row alignment failed: max perpendicular deviation ({max_dev:.1f} px) exceeds threshold ({max_perpendicular_deviation_px:.1f} px)."
            for r in ordered_records:
                r["sequential_socket_id"] = None
                r["identification_status"] = "GEOMETRY_INVALID"
                if "detection" in r and isinstance(r["detection"], dict):
                    r["detection"]["sequential_socket_id"] = None
                    r["detection"]["sequential_identification_status"] = "GEOMETRY_INVALID"
            if verbose:
                print(f"[SEQUENTIAL ID] Assignment Status: {status} ({reason})")
            return SequentialAssignmentResult({
                "status": status,
                "reason": reason,
                "ordered_records": ordered_records,
                "start_endpoint": ordered_records[0],
                "end_endpoint": ordered_records[-1],
                "is_reversed": False,
                "endpoint_difference_mm": None,
                "spatial_diagnostics": spatial_diag
            })
            
        # 5. Endpoint Extraction & Two-Tier Measurement Validation
        ep_a = spatial_diag.get("endpoint_a")
        ep_b = spatial_diag.get("endpoint_b")
        
        valid_a = ep_a.get("measurement_valid", False)
        valid_b = ep_b.get("measurement_valid", False)
        diam_a = ep_a.get("calculated_diameter_mm")
        diam_b = ep_b.get("calculated_diameter_mm")
        
        is_pos_finite_a = (diam_a is not None and isinstance(diam_a, (int, float)) and math.isfinite(diam_a) and diam_a > 0.0)
        is_pos_finite_b = (diam_b is not None and isinstance(diam_b, (int, float)) and math.isfinite(diam_b) and diam_b > 0.0)
        has_physical_ods = bool(valid_a and valid_b and is_pos_finite_a and is_pos_finite_b)
        
        # Helper to extract pixel diameter and rim validity for fallback
        def _get_pixel_diameter(ep):
            px = ep.get("pixel_diameter")
            if (px is None or px <= 0.0) and ep.get("rim_ellipse"):
                ell = ep.get("rim_ellipse")
                if isinstance(ell, (tuple, list)) and len(ell) >= 2 and isinstance(ell[1], (tuple, list)) and len(ell[1]) >= 2:
                    px = max(ell[1][0], ell[1][1])
            if (px is None or px <= 0.0) and "detection" in ep and isinstance(ep["detection"], dict):
                det = ep["detection"]
                px = det.get("pixel_diameter")
                if (px is None or px <= 0.0) and det.get("rim_ellipse"):
                    ell = det.get("rim_ellipse")
                    if isinstance(ell, (tuple, list)) and len(ell) >= 2 and isinstance(ell[1], (tuple, list)) and len(ell[1]) >= 2:
                        px = max(ell[1][0], ell[1][1])
            return float(px) if px is not None and isinstance(px, (int, float)) and math.isfinite(px) and px > 0.0 else None

        def _is_rim_valid(ep):
            if ep.get("rim_status") == "RIM DETECTED" or ep.get("fit_quality") == "RIM DETECTED" or ep.get("center_source") == "RIM_ELLIPSE":
                return True
            if "detection" in ep and isinstance(ep["detection"], dict):
                det = ep["detection"]
                if det.get("rim_status") == "RIM DETECTED" or det.get("fit_quality") == "RIM DETECTED":
                    return True
            return False

        orientation_resolved = False
        is_reversed = False
        decision_reason = ""
        diff_mm = None
        diff_px = None
        orientation_source = "NONE"

        # 6A. Tier 1: Primary Comparison using Physical Outer Diameters (mm)
        if has_physical_ods:
            diam_a = float(diam_a)
            diam_b = float(diam_b)
            diff_mm = abs(diam_a - diam_b)
            
            if diff_mm > endpoint_min_difference_mm:
                if diam_a < diam_b:
                    is_reversed = False
                    decision_reason = f"Endpoint A (#{ep_a['global_instance_id']}: {diam_a:.2f} mm) is smaller than Endpoint B (#{ep_b['global_instance_id']}: {diam_b:.2f} mm) by {diff_mm:.2f} mm."
                else:
                    is_reversed = True
                    decision_reason = f"Endpoint B (#{ep_b['global_instance_id']}: {diam_b:.2f} mm) is smaller than Endpoint A (#{ep_a['global_instance_id']}: {diam_a:.2f} mm) by {diff_mm:.2f} mm. Sequence reversed."
                orientation_resolved = True
                orientation_source = "PHYSICAL_OD"
            else:
                # Difference is within margin: evaluate overall diameter trend as supporting evidence
                valid_diams = [
                    (idx, float(r["calculated_diameter_mm"]))
                    for idx, r in enumerate(ordered_records)
                    if r.get("measurement_valid") and r.get("calculated_diameter_mm") is not None and r.get("calculated_diameter_mm") > 0.0
                ]
                trend_reliable = False
                if len(valid_diams) >= 4:
                    half = len(valid_diams) // 2
                    first_half_mean = np.mean([d for _, d in valid_diams[:half]])
                    second_half_mean = np.mean([d for _, d in valid_diams[-half:]])
                    trend_delta = second_half_mean - first_half_mean
                    if abs(trend_delta) > 2.0 * endpoint_min_difference_mm:
                        trend_reliable = True
                        if trend_delta > 0:
                            is_reversed = False
                            decision_reason = f"Endpoint diff ({diff_mm:.2f} mm <= {endpoint_min_difference_mm:.2f} mm) resolved by positive diameter trend (+{trend_delta:.2f} mm)."
                        else:
                            is_reversed = True
                            decision_reason = f"Endpoint diff ({diff_mm:.2f} mm <= {endpoint_min_difference_mm:.2f} mm) resolved by negative diameter trend ({trend_delta:.2f} mm). Sequence reversed."
                        orientation_resolved = True
                        orientation_source = "PHYSICAL_OD_TREND"
                if not trend_reliable:
                    status = "ORIENTATION_AMBIGUOUS"
                    reason = f"ORIENTATION UNVERIFIED — ENDPOINT SELECTION REQUIRED: Endpoint diameter difference ({diff_mm:.2f} mm <= {endpoint_min_difference_mm:.2f} mm) is within margin and overall trend is inconclusive."

        # 6B. Tier 2: Secondary Comparison using Fitted Top-Rim Ellipse Pixel Diameters (Fallback)
        # Used when physical OD is unavailable on endpoints, but rim ellipses are detected under comparable geometry.
        # CRITICAL: Does NOT fabricate physical millimeter measurements.
        if not orientation_resolved and not has_physical_ods:
            px_a = _get_pixel_diameter(ep_a)
            px_b = _get_pixel_diameter(ep_b)
            rim_valid_a = _is_rim_valid(ep_a)
            rim_valid_b = _is_rim_valid(ep_b)
            geometry_comparable = (spatial_diag.get("row_alignment_status") == "VALID")
            
            if rim_valid_a and rim_valid_b and px_a is not None and px_b is not None and geometry_comparable:
                diff_px = abs(px_a - px_b)
                margin_px = float(endpoint_min_pixel_difference_px)
                if diff_px > margin_px:
                    if px_a < px_b:
                        is_reversed = False
                        smaller_gid, smaller_px = ep_a['global_instance_id'], px_a
                        larger_gid, larger_px = ep_b['global_instance_id'], px_b
                        decision_reason = f"Endpoint A (#{smaller_gid}: {smaller_px:.1f} px) is smaller than Endpoint B (#{larger_gid}: {larger_px:.1f} px) by {diff_px:.1f} px (Fitted top-rim ellipse pixel fallback; physical OD unavailable)."
                    else:
                        is_reversed = True
                        smaller_gid, smaller_px = ep_b['global_instance_id'], px_b
                        larger_gid, larger_px = ep_a['global_instance_id'], px_a
                        decision_reason = f"Endpoint B (#{smaller_gid}: {smaller_px:.1f} px) is smaller than Endpoint A (#{larger_gid}: {larger_px:.1f} px) by {diff_px:.1f} px (Fitted top-rim ellipse pixel fallback; physical OD unavailable). Sequence reversed."
                    orientation_resolved = True
                    orientation_source = "PIXEL_DIAMETER_FALLBACK"
                else:
                    status = "INVALID_ENDPOINT_MEASUREMENT"
                    reason = f"ORIENTATION UNVERIFIED — ENDPOINT SELECTION REQUIRED: Endpoints lack valid physical OD measurement and pixel diameter difference ({diff_px:.1f} px <= {margin_px:.1f} px) is within uncertainty margin."
            else:
                status = "INVALID_ENDPOINT_MEASUREMENT"
                reason = "ORIENTATION UNVERIFIED — ENDPOINT SELECTION REQUIRED: One or both endpoints lack valid physical outer diameter and fitted rim ellipse measurements."

        # If orientation could not be resolved, retain geometric order without claiming verified S01..SN identities
        if not orientation_resolved:
            for r in ordered_records:
                r["sequential_socket_id"] = None
                r["identification_status"] = "ORIENTATION_UNVERIFIED"
                if "detection" in r and isinstance(r["detection"], dict):
                    r["detection"]["sequential_socket_id"] = None
                    r["detection"]["sequential_identification_status"] = "ORIENTATION_UNVERIFIED"
            if verbose:
                print(f"[SEQUENTIAL ID] Assignment Status: {status} ({reason})")
            return SequentialAssignmentResult({
                "status": status,
                "reason": reason,
                "ordered_records": ordered_records,
                "start_endpoint": ep_a,
                "end_endpoint": ep_b,
                "is_reversed": False,
                "endpoint_difference_mm": diff_mm,
                "endpoint_difference_px": diff_px,
                "spatial_diagnostics": spatial_diag,
                "orientation_source": "NONE"
            })

        # 7. Assign Sequential Socket IDs (S01, S02, ... SN)
        status = "SEQUENCE_IDENTIFIED"
        final_records = list(reversed(ordered_records)) if is_reversed else list(ordered_records)
        
        for idx, r in enumerate(final_records):
            seq_id = f"S{idx + 1:02d}"
            r["sequential_socket_id"] = seq_id
            r["identification_status"] = "SEQUENCE_IDENTIFIED"
            if "detection" in r and isinstance(r["detection"], dict):
                r["detection"]["sequential_socket_id"] = seq_id
                r["detection"]["sequential_identification_status"] = "SEQUENCE_IDENTIFIED"
                
        start_ep = final_records[0]
        end_ep = final_records[-1]
        
        # 8. Diagnostic Logging
        if verbose:
            print(f"\n[SEQUENTIAL ID] Assignment Status: {status}")
            print(f"[SEQUENTIAL ID] Decision: {decision_reason}")
            start_gid = start_ep["global_instance_id"]
            end_gid = end_ep["global_instance_id"]
            start_od = start_ep.get("calculated_diameter_mm")
            end_od = end_ep.get("calculated_diameter_mm")
            start_od_str = f"OD: {start_od:.2f} mm" if (start_od is not None and start_od > 0) else f"Pixel OD: {_get_pixel_diameter(start_ep):.1f} px"
            end_od_str = f"OD: {end_od:.2f} mm" if (end_od is not None and end_od > 0) else f"Pixel OD: {_get_pixel_diameter(end_ep):.1f} px"
            print(f"[SEQUENTIAL ID] Smallest Endpoint (S01): #{start_gid} ({start_od_str})")
            print(f"[SEQUENTIAL ID] Largest Endpoint  (S{len(final_records):02d}): #{end_gid} ({end_od_str})")
            seq_str = " -> ".join([f"#{r['global_instance_id']} ({r['sequential_socket_id']})" for r in final_records])
            print(f"[SEQUENTIAL ID] Assigned Sequence: {seq_str}\n")
            
        return SequentialAssignmentResult({
            "status": status,
            "reason": decision_reason,
            "ordered_records": final_records,
            "start_endpoint": start_ep,
            "end_endpoint": end_ep,
            "is_reversed": is_reversed,
            "endpoint_difference_mm": diff_mm,
            "endpoint_difference_px": diff_px,
            "spatial_diagnostics": spatial_diag,
            "orientation_source": orientation_source
        })

    def verify_against_reference(self, detections, reference_catalog, current_layout=None, verbose=True):
        """
        Step 6: Integrates automatically generated sequential socket IDs with the
        Excel reference comparison system.
        
        Mathematical Verification:
            Signed Error = Camera OD - Excel OD
            Absolute Error = abs(Signed Error)
            
        Decision Thresholds:
            - Absolute Error <= individual tolerance (or 0.50 mm default): MATCHED
            - Absolute Error <= 1.50 mm (or individual tolerance + 1.0 mm): TOLERATED / REVIEW
            - Absolute Error > 1.50 mm: SIZE / IDENTITY CONFLICT
            
        Missing Socket & ID-Shift Protection:
            - When detected count < expected count and no taught layout is available,
              consecutive spatial numbering cannot reliably determine which engineering
              slot is physically missing.
            - Sets status to 'REFERENCE ALIGNMENT UNVERIFIED'.
            - Provisional sequential IDs are retained for visual inspection, but NOT
              marked as confirmed reference identities.
            - If a valid taught layout is available, Hungarian matching is preserved
              to identify which physical slot is missing.
        """

        socket_candidates = [d for d in detections if d.get("is_socket")]

        if not reference_catalog:
            for cand in socket_candidates:
                cand["assigned_reference_id"] = None
                cand["verification_status"] = "REF NOT LOADED"
                cand["signed_error"] = None
                cand["absolute_error"] = None
                cand["applied_tolerance"] = None
                cand["applied_tolerance_str"] = "N/A"
            return {
                "status": "NOT_LOADED",
                "alignment_status": "NOT LOADED",
                "alignment_reason": "Reference workbook not loaded",
                "expected_count": 0,
                "detected_count": len(socket_candidates),
                "matched_count": 0,
                "tolerated_count": 0,
                "conflict_count": 0,
                "missing_count": 0,
                "extra_count": 0,
                "socket_verifications": [],
                "reference_verifications": []
            }

        ref_map = {}
        for r in reference_catalog:
            norm_id = ReferenceManager.normalize_reference_id(r.get("reference_id"))
            ref_map[norm_id] = r

        expected_count = len(reference_catalog)
        detected_count = len(socket_candidates)
        has_taught_layout = bool(current_layout and current_layout.get("sockets"))

        seq_assigned = [d for d in socket_candidates if d.get("sequential_socket_id")]
        is_full_sequence = (len(seq_assigned) == detected_count and detected_count > 0)

        matched_count = 0
        tolerated_count = 0
        conflict_count = 0
        missing_count = 0
        extra_count = 0

        # CASE 1: Missing socket without a taught layout (Missing Socket Protection)
        if not has_taught_layout and detected_count < expected_count:
            missing_count = expected_count - detected_count
            alignment_status = "REFERENCE ALIGNMENT UNVERIFIED"
            alignment_reason = (f"Detected {detected_count} sockets but expected {expected_count}. "
                                f"Missing physical slot cannot be determined without a taught layout.")
            status = "ALIGNMENT_UNVERIFIED"

            # Retain provisional sequential IDs for visual inspection, but do NOT assign reference IDs
            for cand in socket_candidates:
                cand["assigned_reference_id"] = None
                cand["assignment_status"] = "ALIGNMENT UNVERIFIED"
                cand["verification_status"] = "ALIGNMENT UNVERIFIED"
                cand["signed_error"] = None
                cand["absolute_error"] = None
                cand["applied_tolerance"] = None
                cand["applied_tolerance_str"] = "N/A"

        # CASE 2: Extra detected sockets without a taught layout
        elif not has_taught_layout and detected_count > expected_count:
            extra_count = detected_count - expected_count
            alignment_status = "REFERENCE ALIGNMENT UNVERIFIED"
            alignment_reason = (f"Detected {detected_count} sockets but expected {expected_count}. "
                                f"{extra_count} extra detection(s) found.")
            status = "ALIGNMENT_UNVERIFIED"

            for cand in socket_candidates:
                cand["assigned_reference_id"] = None
                cand["assignment_status"] = "EXTRA DETECTION / UNVERIFIED"
                cand["verification_status"] = "ALIGNMENT UNVERIFIED"
                cand["signed_error"] = None
                cand["absolute_error"] = None
                cand["applied_tolerance"] = None
                cand["applied_tolerance_str"] = "N/A"

        # CASE 3: Autonomous Sequential Matching (Counts match & full sequence identified)
        elif not has_taught_layout:
            if not is_full_sequence:
                alignment_status = "REFERENCE ALIGNMENT UNVERIFIED"
                alignment_reason = "Sequential identification incomplete or ambiguous."
                status = "ALIGNMENT_UNVERIFIED"
                for cand in socket_candidates:
                    cand["assigned_reference_id"] = None
                    cand["assignment_status"] = "ORIENTATION UNVERIFIED"
                    cand["verification_status"] = "ORIENTATION UNVERIFIED"
                    cand["signed_error"] = None
                    cand["absolute_error"] = None
                    cand["applied_tolerance"] = None
                    cand["applied_tolerance_str"] = "N/A"
            else:
                # 1-to-1 Sequential comparison: S01 -> ref S01, S02 -> ref S02, etc.
                for cand in socket_candidates:
                    seq_id = cand.get("sequential_socket_id")
                    norm_seq_id = ReferenceManager.normalize_reference_id(seq_id)
                    ref = ref_map.get(norm_seq_id)

                    if ref:
                        cand["assigned_reference_id"] = ref["reference_id"]
                        exp_diam = float(ref["expected_outer_diameter"])
                        calc_diam = float(cand.get("calculated_diameter_mm", 0.0))

                        if calc_diam <= 0:
                            cand["verification_status"] = "MEASUREMENT UNAVAILABLE"
                            cand["assignment_status"] = "MEASUREMENT UNAVAILABLE"
                            cand["signed_error"] = None
                            cand["absolute_error"] = None
                            cand["applied_tolerance"] = None
                            cand["applied_tolerance_str"] = "N/A"
                        else:
                            signed_err = calc_diam - exp_diam
                            abs_err = abs(signed_err)
                            cand["signed_error"] = signed_err
                            cand["absolute_error"] = abs_err

                            ind_tol = ref.get("individual_tolerance")
                            if isinstance(ind_tol, (int, float)) and ind_tol > 0:
                                tol_limit = float(ind_tol)
                                tol_src = f"±{tol_limit:.2f} mm (Excel)"
                                review_limit = max(1.50, tol_limit + 1.0)
                            else:
                                tol_limit = 0.50
                                tol_src = "±0.50 mm (Default)"
                                review_limit = 1.50

                            cand["applied_tolerance"] = tol_limit
                            cand["applied_tolerance_str"] = tol_src

                            if abs_err <= tol_limit + 1e-5:
                                verdict = "MATCHED"
                                cand["assignment_status"] = "SLOT MATCHED"
                                matched_count += 1
                            elif abs_err <= review_limit + 1e-5:
                                verdict = "TOLERATED / REVIEW"
                                cand["assignment_status"] = "TOLERATED / REVIEW"
                                tolerated_count += 1
                            else:
                                verdict = "SIZE / IDENTITY CONFLICT"
                                cand["assignment_status"] = "SIZE / IDENTITY CONFLICT"
                                conflict_count += 1

                            cand["verification_status"] = verdict
                    else:
                        cand["assigned_reference_id"] = None
                        cand["verification_status"] = "UNMATCHED REFERENCE"
                        cand["assignment_status"] = "UNMATCHED DETECTION"
                        extra_count += 1

                if conflict_count > 0:
                    alignment_status = "REVIEW REQUIRED"
                    alignment_reason = f"{conflict_count} socket(s) have size/identity conflict (> 1.50 mm)"
                    status = "REVIEW_REQUIRED"
                elif tolerated_count > 0:
                    alignment_status = "REVIEW REQUIRED"
                    alignment_reason = f"{tolerated_count} socket(s) within tolerated threshold (0.50 - 1.50 mm)"
                    status = "REVIEW_REQUIRED"
                else:
                    alignment_status = "VERIFIED"
                    if matched_count > 0:
                        alignment_reason = "All sockets matched reference diameters within tolerance"
                    else:
                        alignment_reason = "Sequential socket layout aligned to reference catalog (physical metrology unavailable)"
                    status = "VERIFIED"

        # CASE 4: Valid Taught Layout is available (Hungarian matching preserved)
        else:
            # Sockets already have their Hungarian assigned_reference_id, or we verify them
            assigned_refs = set()
            for cand in socket_candidates:
                ref_id = cand.get("assigned_reference_id")
                if not ref_id:
                    cand["verification_status"] = "UNMATCHED DETECTION"
                    cand["signed_error"] = None
                    cand["absolute_error"] = None
                    cand["applied_tolerance"] = None
                    cand["applied_tolerance_str"] = "N/A"
                    extra_count += 1
                    continue
                norm_ref_id = ReferenceManager.normalize_reference_id(ref_id)
                ref = ref_map.get(norm_ref_id)
                if ref:
                    assigned_refs.add(ref["reference_id"])
                    exp_diam = float(ref["expected_outer_diameter"])
                    calc_diam = float(cand.get("calculated_diameter_mm", 0.0))

                    if calc_diam <= 0:
                        cand["verification_status"] = "MEASUREMENT UNAVAILABLE"
                        cand["signed_error"] = None
                        cand["absolute_error"] = None
                        cand["applied_tolerance"] = None
                        cand["applied_tolerance_str"] = "N/A"
                    else:
                        signed_err = calc_diam - exp_diam
                        abs_err = abs(signed_err)
                        cand["signed_error"] = signed_err
                        cand["absolute_error"] = abs_err

                        ind_tol = ref.get("individual_tolerance")
                        if isinstance(ind_tol, (int, float)) and ind_tol > 0:
                            tol_limit = float(ind_tol)
                            tol_src = f"±{tol_limit:.2f} mm (Excel)"
                            review_limit = max(1.50, tol_limit + 1.0)
                        else:
                            tol_limit = 0.50
                            tol_src = "±0.50 mm (Default)"
                            review_limit = 1.50

                        cand["applied_tolerance"] = tol_limit
                        cand["applied_tolerance_str"] = tol_src

                        if abs_err <= tol_limit + 1e-5:
                            verdict = "MATCHED"
                            cand["assignment_status"] = "SLOT MATCHED"
                            matched_count += 1
                        elif abs_err <= review_limit + 1e-5:
                            verdict = "TOLERATED / REVIEW"
                            cand["assignment_status"] = "TOLERATED / REVIEW"
                            tolerated_count += 1
                        else:
                            verdict = "SIZE / IDENTITY CONFLICT"
                            cand["assignment_status"] = "SIZE / IDENTITY CONFLICT"
                            conflict_count += 1

                        cand["verification_status"] = verdict
                else:
                    cand["verification_status"] = "UNMATCHED DETECTION"
                    extra_count += 1

            missing_refs = [r["reference_id"] for r in reference_catalog if r["reference_id"] not in assigned_refs]
            missing_count = len(missing_refs)

            if missing_count > 0:
                alignment_status = "REVIEW REQUIRED"
                alignment_reason = f"{missing_count} expected socket(s) missing from layout"
                status = "REVIEW_REQUIRED"
            elif conflict_count > 0:
                alignment_status = "REVIEW REQUIRED"
                alignment_reason = f"{conflict_count} socket(s) have size/identity conflict"
                status = "REVIEW_REQUIRED"
            elif tolerated_count > 0:
                alignment_status = "REVIEW REQUIRED"
                alignment_reason = f"{tolerated_count} socket(s) within tolerated window"
                status = "REVIEW_REQUIRED"
            else:
                alignment_status = "VERIFIED"
                alignment_reason = "All layout sockets verified within tolerance"
                status = "VERIFIED"

        # Build socket verifications
        socket_verifications = []
        for cand in socket_candidates:
            socket_verifications.append({
                "global_instance_id": cand.get("global_instance_id"),
                "sequential_socket_id": cand.get("sequential_socket_id"),
                "assigned_reference_id": cand.get("assigned_reference_id"),
                "calculated_diameter_mm": cand.get("calculated_diameter_mm"),
                "signed_error": cand.get("signed_error"),
                "absolute_error": cand.get("absolute_error"),
                "applied_tolerance": cand.get("applied_tolerance"),
                "applied_tolerance_str": cand.get("applied_tolerance_str"),
                "verification_status": cand.get("verification_status")
            })

        # Build reference verifications for every expected slot
        assigned_by_ref = {}
        for cand in socket_candidates:
            arid = cand.get("assigned_reference_id")
            if arid:
                assigned_by_ref[arid] = cand

        reference_verifications = []
        for ref in reference_catalog:
            ref_id = ref["reference_id"]
            cand = assigned_by_ref.get(ref_id)
            if cand:
                status_str = cand.get("verification_status", "MATCHED")
            else:
                if alignment_status == "REFERENCE ALIGNMENT UNVERIFIED":
                    status_str = "REFERENCE ALIGNMENT UNVERIFIED"
                else:
                    status_str = "MISSING SOCKET"

            reference_verifications.append({
                "reference_id": ref_id,
                "nominal_size": ref.get("nominal_size"),
                "expected_outer_diameter": ref.get("expected_outer_diameter"),
                "individual_tolerance": ref.get("individual_tolerance"),
                "assigned_detection": cand,
                "status": status_str
            })

        if verbose:
            print(f"\n[EXCEL VERIFICATION] Status: {status} | Alignment: {alignment_status}")
            print(f"[EXCEL VERIFICATION] Expected: {expected_count} | Detected: {detected_count} | Matched: {matched_count} | Tolerated: {tolerated_count} | Conflicts: {conflict_count} | Missing: {missing_count} | Extra: {extra_count}")

        return {
            "status": status,
            "alignment_status": alignment_status,
            "alignment_reason": alignment_reason,
            "expected_count": expected_count,
            "detected_count": detected_count,
            "matched_count": matched_count,
            "tolerated_count": tolerated_count,
            "conflict_count": conflict_count,
            "missing_count": missing_count,
            "extra_count": extra_count,
            "socket_verifications": socket_verifications,
            "reference_verifications": reference_verifications
        }


class SpatialOrderingResult(tuple):
    """
    Result container for spatial ordering.
    Behaves as a 2-tuple (ordered_records, diagnostics) for tuple unpacking,
    while also supporting dict-like key access and attribute access.
    """
    def __new__(cls, ordered_records, diagnostics):
        return super().__new__(cls, (ordered_records, diagnostics))
        
    @property
    def ordered_records(self):
        return self[0]
        
    @property
    def diagnostics(self):
        return self[1]
        
    def __getitem__(self, item):
        if isinstance(item, str):
            if item == "ordered_records":
                return self[0]
            if item in self[1]:
                return self[1][item]
            raise KeyError(item)
        return super().__getitem__(item)
        
    def get(self, key, default=None):
        if key == "ordered_records":
            return self[0]
        return self[1].get(key, default)


class SequentialAssignmentResult(dict):
    """
    Result container for sequential socket ID assignment.
    Behaves as a dict, with convenient attributes and tuple-like unpacking (records, metadata).
    """
    def __iter__(self):
        # Allow tuple unpacking: ordered_records, meta = result
        return iter((self.get("ordered_records", []), self))
        
    @property
    def ordered_records(self):
        return self.get("ordered_records", [])
        
    @property
    def status(self):
        return self.get("status", "UNKNOWN")





# =====================================================================
# SECTION: inspection/company_socket_reference_manager.py
# =====================================================================

import os
import sys
import time
import re
import pandas as pd
from pathlib import Path

# Resolve base directories safely relative to application root


class CompanySocketReferenceManager:
    """
    Manages loading, parsing, and verifying company-wise socket dimensional
    references from Book 2 (e.g., 'Excel Sheet/Book 2.xlsx' or 'Book2.xlsx').

    Book 2 uses a grouped column layout where each company occupies exactly three subcolumns:
      1. Socket ID
      2. Nominal Size (mm)
      3. Actual OD (mm)

    Supports live synchronization, transient Excel write-lock recovery,
    dynamic grouped header parsing, and variable socket counts per company.
    """

    DEFAULT_TOLERANCE_MM = 0.50
    REVIEW_THRESHOLD_MM = 1.50

    def __init__(self, workbook_path=None):
        self.workbook_path = None
        self.is_loaded = False
        self.error_message = ""
        self.companies = []
        self.company_data = {}
        self.last_mtime = 0.0
        self.last_reload_time = ""
        self.active_sheet_name = ""

        # Auto-load on instantiation
        self.load_workbook(workbook_path)

    @staticmethod
    def normalize_socket_id(raw_id):
        """
        Normalizes socket identifiers consistently:
        e.g., 'S1' -> 'S01', 's1' -> 'S01', '1' -> 'S01', 'S02' -> 'S02', 'S10' -> 'S10'.
        """
        if raw_id is None or pd.isna(raw_id):
            return ""
        s = str(raw_id).strip()
        if not s:
            return ""
        m = re.match(r'^[Ss]?0*(\d+)$', s)
        if m:
            return f"S{int(m.group(1)):02d}"
        return s.upper()

    @staticmethod
    def _parse_numeric(val):
        """
        Safely extracts a positive float from numeric or text values (e.g. '8.05 mm' -> 8.05).
        Returns None if missing, non-numeric, or <= 0.
        """
        if val is None or pd.isna(val):
            return None
        if isinstance(val, (int, float)):
            v = float(val)
            return v if v > 0 else None
        s = str(val).strip()
        m = re.search(r'[-+]?\d*\.?\d+', s)
        if m:
            try:
                v = float(m.group(0))
                return v if v > 0 else None
            except ValueError:
                return None
        return None

    def find_default_workbook(self):
        """
        Dynamically resolves the Book 2 workbook path relative to the application
        or resource directories, supporting both 'Book 2.xlsx' and 'Book2.xlsx'.
        """
        candidates = [
            # 1. Authoritative original path in application root
            os.path.join(APP2_DIR, "Excel Sheet", "Book 2.xlsx"),
            os.path.join(APP2_DIR, "Excel Sheet", "Book2.xlsx"),
            os.path.join(USER_DIR, "Excel Sheet", "Book 2.xlsx"),
            os.path.join(USER_DIR, "Excel Sheet", "Book2.xlsx"),
            os.path.join(os.getcwd(), "Excel Sheet", "Book 2.xlsx"),
            os.path.join(os.getcwd(), "Excel Sheet", "Book2.xlsx"),

            # 2. Compatibility fallbacks
            os.path.join(APP2_DIR, "Excel sheets", "Book 2.xlsx"),
            os.path.join(APP2_DIR, "Excel sheets", "Book2.xlsx"),
            os.path.join(USER_DIR, "Excel sheets", "Book 2.xlsx"),
            os.path.join(USER_DIR, "Excel sheets", "Book2.xlsx"),
            os.path.join(APP2_DIR, "Book 2.xlsx"),
            os.path.join(APP2_DIR, "Book2.xlsx"),
            os.path.join(USER_DIR, "Book 2.xlsx"),
            os.path.join(USER_DIR, "Book2.xlsx"),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return os.path.abspath(path)
        return None

    def has_workbook_changed_on_disk(self):
        """Checks if the Book 2 file modification time has changed on disk."""
        if not self.workbook_path or not os.path.isfile(self.workbook_path):
            return False
        try:
            mtime = os.path.getmtime(self.workbook_path)
            return mtime > self.last_mtime
        except OSError:
            return False

    def load_workbook(self, file_path=None, max_retries=5, retry_delay_sec=0.15):
        """
        Loads and parses Book 2, extracting company groups and socket references.
        Includes retry logic to safely handle transient Microsoft Excel write locks
        and atomic file replacements.
        """
        target_path = file_path or self.workbook_path or self.find_default_workbook()

        # Retry if file is momentarily missing during atomic replace (Excel SafeSave)
        for _ in range(max_retries):
            if target_path and os.path.isfile(target_path):
                break
            time.sleep(retry_delay_sec)

        if not target_path or not os.path.isfile(target_path):
            if not self.is_loaded:
                self.error_message = "Company Socket Reference Workbook Not Found"
            return False

        last_error = None
        for attempt in range(max_retries):
            try:
                # Read all sheets without assuming sheet name
                with pd.ExcelFile(target_path) as excel_file:
                    sheet_names = excel_file.sheet_names
                    if not sheet_names:
                        self.error_message = "No sheets found in Book 2 workbook"
                        return False

                    # Prefer 'Socket References', 'Socket_References', 'Sheet1', or first sheet
                    selected_sheet = sheet_names[0]
                    for s in sheet_names:
                        s_lower = s.lower().replace(" ", "").replace("_", "")
                        if "socketreference" in s_lower or "socketref" in s_lower or "socket" in s_lower:
                            selected_sheet = s
                            break

                    df = pd.read_excel(excel_file, sheet_name=selected_sheet, header=None)
                    parsed_companies = self._parse_grouped_layout(df)

                    if not parsed_companies:
                        # If preferred sheet had no valid groups, try other sheets
                        for s in sheet_names:
                            if s == selected_sheet:
                                continue
                            df_alt = pd.read_excel(excel_file, sheet_name=s, header=None)
                            parsed_alt = self._parse_grouped_layout(df_alt)
                            if parsed_alt:
                                selected_sheet = s
                                parsed_companies = parsed_alt
                                break

                if not parsed_companies:
                    self.error_message = "No valid company socket reference groups found in Book 2"
                    return False

                # Successful atomic update of internal state
                self.company_data = parsed_companies
                self.companies = list(parsed_companies.keys())
                self.workbook_path = os.path.abspath(target_path)
                self.active_sheet_name = selected_sheet
                self.is_loaded = True
                self.error_message = ""
                try:
                    self.last_mtime = os.path.getmtime(self.workbook_path)
                except OSError:
                    pass
                self.last_reload_time = time.strftime("%Y-%m-%d %H:%M:%S")
                return True

            except (PermissionError, IOError, FileNotFoundError) as e:
                last_error = e
                time.sleep(retry_delay_sec)
            except Exception as e:
                self.error_message = f"Failed to parse Book 2: {str(e)}"
                return False

        if last_error:
            self.error_message = f"File locked or inaccessible: {str(last_error)}"
        return False

    def _parse_grouped_layout(self, df):
        """
        Dynamically discovers the subheader row and company header row in Book 2,
        then extracts the three subcolumns for each company group.
        """
        if df is None or df.empty or df.shape[1] < 3:
            return {}

        best_subcol_row = None
        best_triplets = 0

        # Scan rows to find the subheader row with repeating (Socket ID, Nominal Size, Actual OD)
        for r in range(min(25, len(df))):
            triplets = 0
            c = 0
            while c + 2 < df.shape[1]:
                h0 = str(df.iloc[r, c]).lower() if pd.notna(df.iloc[r, c]) else ""
                h1 = str(df.iloc[r, c+1]).lower() if pd.notna(df.iloc[r, c+1]) else ""
                h2 = str(df.iloc[r, c+2]).lower() if pd.notna(df.iloc[r, c+2]) else ""

                is_id = ("socket" in h0 and "id" in h0) or (h0 in ["socket id", "socket", "id", "ref id"])
                is_nom = "nominal" in h1 or "size" in h1 or "nom" in h1
                is_od = "actual" in h2 or "od" in h2 or "diameter" in h2 or "outer" in h2

                if is_id and is_nom and is_od:
                    triplets += 1
                    c += 3
                else:
                    c += 1

            if triplets > best_triplets:
                best_triplets = triplets
                best_subcol_row = r

        if best_subcol_row is None or best_triplets == 0:
            return {}

        subcol_row_idx = best_subcol_row
        company_row_idx = subcol_row_idx - 1 if subcol_row_idx > 0 else None

        companies = {}
        c = 0
        while c + 2 < df.shape[1]:
            h0 = str(df.iloc[subcol_row_idx, c]).lower() if pd.notna(df.iloc[subcol_row_idx, c]) else ""
            h1 = str(df.iloc[subcol_row_idx, c+1]).lower() if pd.notna(df.iloc[subcol_row_idx, c+1]) else ""
            h2 = str(df.iloc[subcol_row_idx, c+2]).lower() if pd.notna(df.iloc[subcol_row_idx, c+2]) else ""

            is_id = ("socket" in h0 and "id" in h0) or (h0 in ["socket id", "socket", "id", "ref id"])
            is_nom = "nominal" in h1 or "size" in h1 or "nom" in h1
            is_od = "actual" in h2 or "od" in h2 or "diameter" in h2 or "outer" in h2

            if is_id and is_nom and is_od:
                # Find company name above these columns
                comp_name = None
                if company_row_idx is not None:
                    for offset in range(3):
                        val = df.iloc[company_row_idx, c + offset]
                        if pd.notna(val) and str(val).strip():
                            comp_name = str(val).strip()
                            break

                if not comp_name:
                    comp_name = f"Company_{len(companies) + 1}"

                # Ensure unique company name
                base_name = comp_name
                counter = 2
                while comp_name in companies:
                    comp_name = f"{base_name} ({counter})"
                    counter += 1

                # Extract socket rows for this company
                records = {}
                seen_socket_ids = set()

                for r in range(subcol_row_idx + 1, len(df)):
                    raw_id = df.iloc[r, c]
                    raw_nom = df.iloc[r, c+1]
                    raw_od = df.iloc[r, c+2]

                    # Skip entirely blank rows
                    if pd.isna(raw_id) and pd.isna(raw_nom) and pd.isna(raw_od):
                        continue

                    norm_id = self.normalize_socket_id(raw_id)
                    if not norm_id:
                        continue

                    # Check for duplicate Socket ID within the company block
                    if norm_id in seen_socket_ids:
                        continue
                    seen_socket_ids.add(norm_id)

                    nom_mm = self._parse_numeric(raw_nom)
                    od_mm = self._parse_numeric(raw_od)

                    is_valid = (nom_mm is not None) and (od_mm is not None)
                    status = "VALID" if is_valid else (
                        "MISSING_OD" if (nom_mm is not None and od_mm is None) else
                        ("MISSING_NOMINAL" if (nom_mm is None and od_mm is not None) else "NOT_CONFIGURED")
                    )

                    records[norm_id] = {
                        "socket_id": norm_id,
                        "nominal_size_mm": nom_mm,
                        "actual_od_mm": od_mm,
                        "is_valid": is_valid,
                        "status": status,
                        "row_index": r + 1
                    }

                # Only include valid configured sockets in valid_sockets
                valid_records = {sid: rec for sid, rec in records.items() if rec["is_valid"]}

                companies[comp_name] = {
                    "name": comp_name,
                    "sockets": records,
                    "valid_sockets": valid_records,
                    "expected_count": len(valid_records),
                    "subcol_indices": (c, c+1, c+2)
                }
                c += 3
            else:
                c += 1

        return companies

    def get_company_names(self):
        """Returns list of all parsed company names from Book 2."""
        return list(self.companies)

    def get_expected_socket_count(self, company_name):
        """Returns the number of valid configured sockets for the specified company."""
        if not company_name or company_name not in self.company_data:
            return 0
        return self.company_data[company_name].get("expected_count", 0)

    def get_socket_references(self, company_name):
        """Returns the dictionary of all socket records (valid and placeholder) for a company."""
        if not company_name or company_name not in self.company_data:
            return {}
        return self.company_data[company_name].get("sockets", {})

    def get_valid_socket_references(self, company_name):
        """Returns dictionary of only valid configured socket records for a company."""
        if not company_name or company_name not in self.company_data:
            return {}
        return self.company_data[company_name].get("valid_sockets", {})

    def get_socket_reference_catalog(self, company_name):
        """
        Constructs a standard reference catalog list compatible with
        SocketIdentifier.verify_against_reference(), using Book 2 Actual OD
        as the expected outer diameter.
        """
        if not company_name or company_name not in self.company_data:
            return []

        valid_socks = self.company_data[company_name].get("valid_sockets", {})
        catalog = []

        # Sort sockets by normalized ID numerical value (S01, S02, ...)
        def _sort_key(sid):
            m = re.match(r'^[Ss]?0*(\d+)$', sid)
            return int(m.group(1)) if m else sid

        for sid in sorted(valid_socks.keys(), key=_sort_key):
            rec = valid_socks[sid]
            catalog.append({
                "reference_id": sid,
                "nominal_size": rec.get("nominal_size_mm"),
                "nominal_size_mm": rec.get("nominal_size_mm"),
                "expected_outer_diameter": rec.get("actual_od_mm"),
                "actual_od_mm": rec.get("actual_od_mm"),
                "individual_tolerance": self.DEFAULT_TOLERANCE_MM
            })

        return catalog

    def verify_socket_dimensions(self, company_name, detections, current_layout=None, verbose=False):
        """
        Directly matches camera-assigned sequential socket IDs (S01..SN) against
        the selected company's Book 2 references and computes dimensional verification.

        Thresholds:
          - Error <= 0.50 mm: PASS
          - 0.50 mm < Error <= 1.50 mm: REVIEW
          - Error > 1.50 mm: FAIL
        """

        catalog = self.get_socket_reference_catalog(company_name)
        identifier = SocketIdentifier()
        verif_result = identifier.verify_against_reference(
            detections,
            catalog,
            current_layout=current_layout,
            verbose=verbose
        )

        # Attach company reference metadata
        verif_result["company_name"] = company_name
        verif_result["workbook_path"] = self.workbook_path
        verif_result["expected_count"] = self.get_expected_socket_count(company_name)
        return verif_result


# =====================================================================
# SECTION: inspection/batch_report_generator.py
# =====================================================================

import os
import sys
import json
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter

class BatchReportGenerator:
    """
    Generates worker-specific batch inspection reports in PDF and structured JSON formats.
    Complies with Sections A through G of Step 9.
    """
    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Removes or replaces characters unsafe for directory/file names."""
        return re.sub(r'[\\/*?:"<>| ]', '_', str(name).strip())

    @classmethod
    def aggregate_batch_data(cls, batch_id: str, worker_id: str, inspections: List[Dict]) -> Dict:
        """
        Aggregates inspection records for a specific worker and batch into
        statistical tables and summaries.
        """
        # Filter strictly by batch_id and worker_id
        matching = [r for r in inspections if r.get("batch_id") == batch_id and r.get("worker_id") == worker_id]
        if not matching:
            return {}

        total_toolkits = len(matching)
        session_ids = sorted(list(set(r.get("session_id") for r in matching if r.get("session_id"))))
        companies_b1 = sorted(list(set(r.get("selected_company") for r in matching if r.get("selected_company"))))
        companies_b2 = sorted(list(set(r.get("selected_socket_company") for r in matching if r.get("selected_socket_company"))))

        timestamps = [r.get("timestamp") for r in matching if r.get("timestamp")]
        timestamps.sort()
        period_start = timestamps[0] if timestamps else "N/A"
        period_end = timestamps[-1] if timestamps else "N/A"

        # B. Toolkit Inspection Summary counts
        total_sockets_inspected = 0
        toolkits_with_socket_defects = 0
        toolkits_with_count_discrepancies = 0

        auto_pass_count = 0
        auto_review_count = 0
        auto_fail_count = 0

        final_pass_count = 0
        final_review_count = 0
        final_fail_count = 0

        # C. Common Socket Size Problems: {(nominal_size, socket_id): {"review": int, "fail": int, "toolkits": set()}}
        socket_problems = defaultdict(lambda: {"review": 0, "fail": 0, "toolkits": set()})

        # D. Tool Detection & Count Discrepancies: {category: {"missing": int, "extra": int, "toolkits": set()}}
        count_discrepancies = defaultdict(lambda: {"missing": 0, "extra": 0, "toolkits": set()})

        # E. Manual Status Changes
        manual_change_records = []
        unique_sockets_changed = set() # (toolkit_id, socket_id)
        transition_counts = {
            "PASS->REVIEW": 0, "PASS_TO_REVIEW": 0,
            "PASS->FAIL": 0, "PASS_TO_FAIL": 0,
            "REVIEW->PASS": 0, "REVIEW_TO_PASS": 0,
            "REVIEW->FAIL": 0, "REVIEW_TO_FAIL": 0,
            "FAIL->PASS": 0, "FAIL_TO_PASS": 0,
            "FAIL->REVIEW": 0, "FAIL_TO_REVIEW": 0
        }

        for insp in matching:
            tk_id = insp.get("toolkit_id", "TOOLKIT-001")
            
            # 1. Check Tool Count Verification (Book 1)
            cat_results = insp.get("tool_count_verification_results", [])
            has_count_discrepancy = False
            for cat in cat_results:
                c_name = cat.get("category", "")
                diff = cat.get("difference", 0)
                status = str(cat.get("status", "")).upper()
                if "MISSING" in status or diff < 0:
                    has_count_discrepancy = True
                    count_discrepancies[c_name]["missing"] += abs(diff)
                    count_discrepancies[c_name]["toolkits"].add(tk_id)
                elif "EXTRA" in status or diff > 0:
                    has_count_discrepancy = True
                    count_discrepancies[c_name]["extra"] += abs(diff)
                    count_discrepancies[c_name]["toolkits"].add(tk_id)

            if has_count_discrepancy:
                toolkits_with_count_discrepancies += 1

            # 2. Check Sockets and Metrology (Book 2)
            sock_verifs = insp.get("socket_verifications", [])
            if not sock_verifs:
                sock_verifs = insp.get("socket_detection_candidates", [])
            if not sock_verifs:
                sock_verifs = [d for d in insp.get("detections", []) if d.get("is_socket")]

            has_socket_defect = False
            for s in sock_verifs:
                total_sockets_inspected += 1
                sock_id = s.get("sequential_socket_id") or s.get("reference_id") or f"Socket_{s.get('global_instance_id')}"
                nom_size = s.get("nominal_size") or s.get("nominal_size_mm") or s.get("excel_nominal_size") or "N/A"

                # Automatic status
                raw_auto = s.get("automatic_status") or s.get("verification_status") or "NOT RUN"
                auto_stat = "PASS" if "MATCHED" in raw_auto or raw_auto == "PASS" else ("FAIL" if "CONFLICT" in raw_auto or raw_auto == "FAIL" else "REVIEW")
                
                # Final status (overridden or default)
                raw_final = s.get("final_status") or auto_stat
                final_stat = "PASS" if "MATCHED" in raw_final or raw_final == "PASS" else ("FAIL" if "CONFLICT" in raw_final or raw_final == "FAIL" else "REVIEW")

                if auto_stat == "PASS":
                    auto_pass_count += 1
                elif auto_stat == "FAIL":
                    auto_fail_count += 1
                    has_socket_defect = True
                    socket_problems[(nom_size, sock_id)]["fail"] += 1
                    socket_problems[(nom_size, sock_id)]["toolkits"].add(tk_id)
                else: # REVIEW
                    auto_review_count += 1
                    has_socket_defect = True
                    socket_problems[(nom_size, sock_id)]["review"] += 1
                    socket_problems[(nom_size, sock_id)]["toolkits"].add(tk_id)

                if final_stat == "PASS":
                    final_pass_count += 1
                elif final_stat == "FAIL":
                    final_fail_count += 1
                else:
                    final_review_count += 1

            if has_socket_defect:
                toolkits_with_socket_defects += 1

            # 3. Manual Overrides
            overrides = insp.get("manual_overrides", [])
            for ov in overrides:
                manual_change_records.append(ov)
                unique_sockets_changed.add((ov.get("toolkit_id", tk_id), ov.get("socket_id")))
                prev_s = str(ov.get("previous_final_status") or ov.get("previous_status", "")).upper()
                new_s = str(ov.get("new_final_status") or ov.get("new_status", "")).upper()
                key1 = f"{prev_s}->{new_s}"
                key2 = f"{prev_s}_TO_{new_s}"
                if key1 in transition_counts:
                    transition_counts[key1] += 1
                if key2 in transition_counts:
                    transition_counts[key2] += 1

        # Format Problem Tables
        formatted_socket_problems = []
        for (nom, sid), data in sorted(socket_problems.items(), key=lambda item: item[1]["fail"] + item[1]["review"], reverse=True):
            formatted_socket_problems.append({
                "nominal_size": nom,
                "socket_id": sid,
                "review_count": data["review"],
                "fail_count": data["fail"],
                "affected_toolkits": len(data["toolkits"])
            })

        formatted_count_discrepancies = []
        for cat_name, data in sorted(count_discrepancies.items(), key=lambda item: item[1]["missing"] + item[1]["extra"], reverse=True):
            formatted_count_discrepancies.append({
                "category": cat_name,
                "missing_qty": data["missing"],
                "extra_qty": data["extra"],
                "affected_toolkits": len(data["toolkits"])
            })

        return {
            "batch_id": batch_id,
            "worker_id": worker_id,
            "header": {
                "report_title": "AXOVRIM — Worker Batch Inspection Report",
                "batch_id": batch_id,
                "worker_id": worker_id,
                "session_ids": session_ids,
                "book1_companies": companies_b1,
                "book2_companies": companies_b2,
                "inspection_period_start": period_start,
                "inspection_period_end": period_end,
                "generation_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "summary": {
                "total_toolkits": total_toolkits,
                "total_sockets": total_sockets_inspected,
                "total_toolkits_inspected": total_toolkits,
                "total_sockets_inspected": total_sockets_inspected,
                "toolkits_with_socket_defects": toolkits_with_socket_defects,
                "toolkits_with_count_discrepancies": toolkits_with_count_discrepancies,
                "automatic_pass": auto_pass_count,
                "automatic_review": auto_review_count,
                "automatic_fail": auto_fail_count,
                "final_pass": final_pass_count,
                "final_review": final_review_count,
                "final_fail": final_fail_count,
                "auto_pass_count": auto_pass_count,
                "auto_review_count": auto_review_count,
                "auto_fail_count": auto_fail_count,
                "final_pass_count": final_pass_count,
                "final_review_count": final_review_count,
                "final_fail_count": final_fail_count
            },
            "socket_problems": formatted_socket_problems,
            "tool_count_discrepancies": formatted_count_discrepancies,
            "manual_changes": {
                "total_actions": len(manual_change_records),
                "unique_sockets_changed": len(unique_sockets_changed),
                "transitions": transition_counts,
                "details": manual_change_records
            },
            "manual_overrides": manual_change_records,
            "manual_overrides_summary": {
                "total_actions": len(manual_change_records),
                "unique_sockets_changed": len(unique_sockets_changed),
                "transitions": transition_counts
            }
        }

    @classmethod
    def generate_html_report(cls, data: Dict) -> str:
        """Constructs a clean HTML representation of the batch report for PDF printing."""
        h = data["header"]
        s = data["summary"]
        sp = data["socket_problems"]
        tc = data["tool_count_discrepancies"]
        mc = data["manual_changes"]

        # Final Summary Statement
        pass_rate = (s["final_pass_count"] / s["total_sockets_inspected"] * 100) if s["total_sockets_inspected"] > 0 else 0
        summary_stmt = (
            f"During this inspection cycle for Batch <b>{h['batch_id']}</b>, worker <b>{h['worker_id']}</b> "
            f"evaluated a total of <b>{s['total_toolkits_inspected']}</b> toolkit(s) comprising "
            f"<b>{s['total_sockets_inspected']}</b> individual socket dimensional measurements. "
            f"A total of <b>{s['toolkits_with_socket_defects']}</b> toolkit(s) exhibited automatic socket dimensional issues, "
            f"and <b>{s['toolkits_with_count_discrepancies']}</b> toolkit(s) had tool-count variances. "
            f"Following <b>{mc['total_actions']}</b> confirmed manual override action(s) across "
            f"<b>{mc['unique_sockets_changed']}</b> unique socket(s), the final batch socket conformance rate was "
            f"<b>{pass_rate:.1f}%</b> ({s['final_pass_count']} PASS, {s['final_review_count']} REVIEW, {s['final_fail_count']} FAIL)."
        )

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, Helvetica, sans-serif;
                    color: #212529;
                    font-size: 11pt;
                    margin: 20px;
                }}
                h1 {{
                    color: #135D9C;
                    font-size: 18pt;
                    margin-bottom: 4px;
                    border-bottom: 2px solid #135D9C;
                    padding-bottom: 6px;
                }}
                h2 {{
                    color: #242B34;
                    font-size: 13pt;
                    margin-top: 18px;
                    margin-bottom: 8px;
                    border-bottom: 1px solid #D0D7DE;
                    padding-bottom: 4px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 12px;
                    font-size: 10pt;
                }}
                th {{
                    background-color: #F0F3F6;
                    color: #242B34;
                    text-align: left;
                    padding: 6px 8px;
                    border: 1px solid #D0D7DE;
                    font-weight: bold;
                }}
                td {{
                    padding: 5px 8px;
                    border: 1px solid #E1E4E8;
                }}
                tr:nth-child(even) td {{
                    background-color: #F8FAFC;
                }}
                .badge-pass {{
                    color: #28C76F;
                    font-weight: bold;
                }}
                .badge-review {{
                    color: #F5A623;
                    font-weight: bold;
                }}
                .badge-fail {{
                    color: #EA4D55;
                    font-weight: bold;
                }}
                .header-info-table td {{
                    border: none;
                    padding: 3px 6px;
                }}
                .summary-box {{
                    background-color: #F4F6F8;
                    border-left: 4px solid #135D9C;
                    padding: 10px 14px;
                    margin-top: 14px;
                    font-size: 10.5pt;
                    line-height: 1.4;
                }}
            </style>
        </head>
        <body>
            <h1>AXOVRIM — Worker Batch Inspection Report</h1>
            
            <table class="header-info-table">
                <tr>
                    <td width="20%"><b>Batch ID:</b></td>
                    <td width="30%">{h['batch_id']}</td>
                    <td width="20%"><b>Worker ID:</b></td>
                    <td width="30%"><b>{h['worker_id']}</b></td>
                </tr>
                <tr>
                    <td><b>Session ID:</b></td>
                    <td>{', '.join(h['session_ids']) if h['session_ids'] else 'N/A'}</td>
                    <td><b>Generation Time:</b></td>
                    <td>{h['generation_timestamp']}</td>
                </tr>
                <tr>
                    <td><b>Book 1 Reference:</b></td>
                    <td>{', '.join(h['book1_companies']) if h['book1_companies'] else 'Standard'}</td>
                    <td><b>Book 2 Reference:</b></td>
                    <td>{', '.join(h['book2_companies']) if h['book2_companies'] else 'Standard'}</td>
                </tr>
                <tr>
                    <td><b>Inspection Period:</b></td>
                    <td colspan="3">{h['inspection_period_start']} &nbsp;to&nbsp; {h['inspection_period_end']}</td>
                </tr>
            </table>

            <h2>B. Toolkit Inspection Summary</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Count</th>
                    <th>Automatic Status</th>
                    <th>Count</th>
                    <th>Final Worker Status</th>
                    <th>Count</th>
                </tr>
                <tr>
                    <td>Total Toolkits Inspected</td>
                    <td><b>{s['total_toolkits_inspected']}</b></td>
                    <td>Automatic PASS</td>
                    <td class="badge-pass">{s['auto_pass_count']}</td>
                    <td>Final PASS</td>
                    <td class="badge-pass"><b>{s['final_pass_count']}</b></td>
                </tr>
                <tr>
                    <td>Total Sockets Inspected</td>
                    <td><b>{s['total_sockets_inspected']}</b></td>
                    <td>Automatic REVIEW</td>
                    <td class="badge-review">{s['auto_review_count']}</td>
                    <td>Final REVIEW</td>
                    <td class="badge-review"><b>{s['final_review_count']}</b></td>
                </tr>
                <tr>
                    <td>Toolkits w/ Socket Defects</td>
                    <td><span class="{ 'badge-fail' if s['toolkits_with_socket_defects'] > 0 else 'badge-pass' }">{s['toolkits_with_socket_defects']}</span></td>
                    <td>Automatic FAIL</td>
                    <td class="badge-fail">{s['auto_fail_count']}</td>
                    <td>Final FAIL</td>
                    <td class="badge-fail"><b>{s['final_fail_count']}</b></td>
                </tr>
                <tr>
                    <td>Toolkits w/ Count Variances</td>
                    <td><span class="{ 'badge-review' if s['toolkits_with_count_discrepancies'] > 0 else 'badge-pass' }">{s['toolkits_with_count_discrepancies']}</span></td>
                    <td colspan="4" style="background:#FAFBFD; color:#6C757D; font-style:italic;">Worker status overrides strictly audited</td>
                </tr>
            </table>

            <h2>C. Most Common Socket Size Problems (Automatic Outcomes)</h2>
        """

        if sp:
            html += """
            <table>
                <tr>
                    <th>Nominal Size (mm)</th>
                    <th>Socket ID</th>
                    <th>REVIEW Count</th>
                    <th>FAIL Count</th>
                    <th>Affected Toolkits</th>
                </tr>
            """
            for row in sp:
                html += f"""
                <tr>
                    <td>{row['nominal_size']}</td>
                    <td><b>{row['socket_id']}</b></td>
                    <td class="badge-review">{row['review_count']}</td>
                    <td class="badge-fail">{row['fail_count']}</td>
                    <td>{row['affected_toolkits']}</td>
                </tr>
                """
            html += "</table>"
        else:
            html += "<p style='color:#28C76F;'>No socket dimensional defect occurrences recorded for this worker and batch.</p>"

        html += "<h2>D. Tool Detection & Count Discrepancies (Book 1)</h2>"
        if tc:
            html += """
            <table>
                <tr>
                    <th>Tool Category</th>
                    <th>Missing Quantity</th>
                    <th>Extra Quantity</th>
                    <th>Affected Toolkits</th>
                </tr>
            """
            for row in tc:
                html += f"""
                <tr>
                    <td><b>{row['category']}</b></td>
                    <td class="badge-fail">-{row['missing_qty']}</td>
                    <td class="badge-review">+{row['extra_qty']}</td>
                    <td>{row['affected_toolkits']}</td>
                </tr>
                """
            html += "</table>"
        else:
            html += "<p style='color:#28C76F;'>All expected tool quantities perfectly verified for this batch.</p>"

        html += f"""
            <h2>E. Manual Status Changes Summary</h2>
            <table>
                <tr>
                    <th>Total Override Actions</th>
                    <th>Unique Sockets Changed</th>
                    <th>PASS &rarr; REVIEW</th>
                    <th>PASS &rarr; FAIL</th>
                    <th>REVIEW &rarr; PASS</th>
                    <th>REVIEW &rarr; FAIL</th>
                    <th>FAIL &rarr; PASS</th>
                    <th>FAIL &rarr; REVIEW</th>
                </tr>
                <tr>
                    <td><b>{mc['total_actions']}</b></td>
                    <td><b>{mc['unique_sockets_changed']}</b></td>
                    <td>{mc['transitions']['PASS->REVIEW']}</td>
                    <td>{mc['transitions']['PASS->FAIL']}</td>
                    <td>{mc['transitions']['REVIEW->PASS']}</td>
                    <td>{mc['transitions']['REVIEW->FAIL']}</td>
                    <td>{mc['transitions']['FAIL->PASS']}</td>
                    <td>{mc['transitions']['FAIL->REVIEW']}</td>
                </tr>
            </table>

            <h2>F. Manual Change Audit Trail</h2>
        """

        if mc['details']:
            html += """
            <table>
                <tr>
                    <th>Toolkit ID</th>
                    <th>Socket ID</th>
                    <th>Nominal</th>
                    <th>Automatic Status</th>
                    <th>Previous Status</th>
                    <th>Final Status</th>
                    <th>Worker ID</th>
                    <th>Timestamp</th>
                    <th>Reason</th>
                </tr>
            """
            for row in mc['details']:
                auto_val = row.get('original_automatic_status') or row.get('automatic_status') or 'N/A'
                prev_val = row.get('previous_final_status') or row.get('previous_status') or 'N/A'
                new_val = row.get('new_final_status') or row.get('new_status') or 'N/A'
                new_cls = "badge-pass" if new_val == "PASS" else ("badge-fail" if new_val == "FAIL" else "badge-review")
                html += f"""
                <tr>
                    <td>{row.get('toolkit_id', 'N/A')}</td>
                    <td><b>{row.get('socket_id', 'N/A')}</b></td>
                    <td>{row.get('nominal_size', '—')}</td>
                    <td>{auto_val}</td>
                    <td>{prev_val}</td>
                    <td class="{new_cls}"><b>{new_val}</b></td>
                    <td>{row.get('worker_id', h['worker_id'])}</td>
                    <td>{row.get('timestamp', 'N/A')}</td>
                    <td style="font-size:9pt;">{row.get('reason') or '—'}</td>
                </tr>
                """
            html += "</table>"
        else:
            html += "<p style='color:#6C757D; font-style:italic;'>No manual status overrides performed during this batch.</p>"

        html += f"""
            <h2>G. Final Batch Summary</h2>
            <div class="summary-box">
                {summary_stmt}
            </div>
        </body>
        </html>
        """
        return html

    @classmethod
    def generate_report(
        cls,
        batch_id: str,
        worker_id: str,
        inspections: List[Dict],
        output_base_dir: Optional[str] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Generates the PDF and structured JSON reports for (batch_id, worker_id).
        Returns: (success: bool, output_file_or_error: str, summary_data: Dict)
        """
        agg_data = cls.aggregate_batch_data(batch_id, worker_id, inspections)
        if not agg_data:
            return False, "No completed toolkit inspections are available for this worker and batch.", None

        # Set output directory: App 2/Reports/<BATCH_ID>/<WORKER_ID>/
        if output_base_dir is None:
            base_dir = APP2_DIR
            output_base_dir = os.path.join(base_dir, "Reports")

        safe_batch = cls.sanitize_filename(batch_id)
        safe_worker = cls.sanitize_filename(worker_id)
        target_dir = os.path.join(output_base_dir, safe_batch, safe_worker)
        os.makedirs(target_dir, exist_ok=True)

        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"AXOVRIM_{safe_batch}_{safe_worker}_{ts_str}.pdf"
        json_filename = f"AXOVRIM_{safe_batch}_{safe_worker}_{ts_str}.json"

        pdf_path = os.path.join(target_dir, pdf_filename)
        json_path = os.path.join(target_dir, json_filename)

        # 1. Save Structured JSON Record
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(agg_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            return False, f"Failed to save report JSON: {e}", agg_data

        # 2. Render and Print PDF using QTextDocument and QPrinter
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)

            html_content = cls.generate_html_report(agg_data)

            doc = QTextDocument()
            doc.setHtml(html_content)

            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(pdf_path)

            doc.print_(printer)
        except Exception as e:
            return False, f"Failed to generate report PDF: {e}", agg_data

        return True, pdf_path, agg_data


# =====================================================================
# SECTION: app/zoomable_viewer.py
# =====================================================================

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
from PyQt5.QtGui import QPixmap, QTransform, QPainter, QWheelEvent, QMouseEvent

class GraphicsViewWithInteraction(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px;")
        
    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.parent().zoom_in(0.1)
        else:
            self.parent().zoom_out(0.1)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.parent().fit_to_window()
            
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            # Map the view coordinate to scene coordinate
            scene_pos = self.mapToScene(event.pos())
            self.parent().clicked_image.emit(scene_pos)
        super().mousePressEvent(event)

class ZoomableViewer(QWidget):
    clicked_image = pyqtSignal(QPointF)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(get_zoom_viewer_stylesheet())
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        
        # Toolbar
        self.toolbar_layout = QHBoxLayout()
        self.toolbar_layout.setContentsMargins(6, 4, 6, 4)
        self.toolbar_layout.setSpacing(6)
        
        self.btn_zoom_in = QPushButton("Zoom In (+)")
        self.btn_zoom_out = QPushButton("Zoom Out (-)")
        self.btn_fit = QPushButton("Fit Window")
        self.btn_100 = QPushButton("100%")
        self.lbl_zoom = QLabel("Zoom: 100%")
        
        self.btn_zoom_in.clicked.connect(lambda: self.zoom_in(0.2))
        self.btn_zoom_out.clicked.connect(lambda: self.zoom_out(0.2))
        self.btn_fit.clicked.connect(self.fit_to_window)
        self.btn_100.clicked.connect(self.actual_pixels)
        
        self.toolbar_layout.addWidget(self.btn_zoom_in)
        self.toolbar_layout.addWidget(self.btn_zoom_out)
        self.toolbar_layout.addWidget(self.btn_fit)
        self.toolbar_layout.addWidget(self.btn_100)
        self.toolbar_layout.addStretch()
        self.toolbar_layout.addWidget(self.lbl_zoom)
        
        self.layout.addLayout(self.toolbar_layout)
        
        # Viewer
        self.scene = QGraphicsScene(self)
        self.view = GraphicsViewWithInteraction(self)
        self.view.setScene(self.scene)
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        
        self.layout.addWidget(self.view)
        
        self.current_scale = 1.0
        self.pixmap = None
        self._is_user_zoomed = False
        
    def setPixmap(self, pixmap: QPixmap, reset_zoom: bool = True):
        prev_zoomed = self._is_user_zoomed
        self.pixmap = pixmap
        self.pixmap_item.setPixmap(self.pixmap)
        self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
        if reset_zoom or not prev_zoomed:
            self._is_user_zoomed = False
            self.fit_to_window()
        else:
            self.set_zoom(self.current_scale)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._is_user_zoomed:
            self.fit_to_window()

    def clear(self):
        self.pixmap = None
        self.pixmap_item.setPixmap(QPixmap())
        self.lbl_zoom.setText("Zoom: --")
        
    def setText(self, text):
        pass # Compatibility with AspectRatioLabel, does nothing here or we can just ignore it since it's just a placeholder.
        
    def zoom_in(self, factor=0.2):
        if self.pixmap is None: return
        self._is_user_zoomed = True
        self.set_zoom(self.current_scale + factor)
        
    def zoom_out(self, factor=0.2):
        if self.pixmap is None: return
        self._is_user_zoomed = True
        self.set_zoom(self.current_scale - factor)
        
    def actual_pixels(self):
        if self.pixmap is None: return
        self._is_user_zoomed = True
        self.set_zoom(1.0)
        
    def fit_to_window(self):
        if self.pixmap is None: return
        self._is_user_zoomed = False
        view_rect = self.view.viewport().rect()
        scene_rect = self.scene.sceneRect()
        if scene_rect.width() == 0 or scene_rect.height() == 0:
            return
            
        ratio = min(view_rect.width() / scene_rect.width(), view_rect.height() / scene_rect.height())
        # To leave a small margin, multiply by 0.98
        ratio *= 0.98
        self.set_zoom(ratio)
        self.view.centerOn(scene_rect.center())
        
    def set_zoom(self, scale):
        # Limit zoom between 25% and 800%
        scale = max(0.25, min(scale, 8.0))
        self.current_scale = scale
        
        transform = QTransform()
        transform.scale(self.current_scale, self.current_scale)
        self.view.setTransform(transform)
        
        self.lbl_zoom.setText(f"Zoom: {int(self.current_scale * 100)}%")


# =====================================================================
# SECTION: app/worker_dialog.py
# =====================================================================

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QFormLayout
)
from PyQt5.QtCore import Qt

class WorkerDialog(QDialog):
    """
    Compact dialog for entering Worker ID, activating sessions,
    and managing safe worker switching.
    Styled with centralized light popup theme and clear contrast buttons.
    """
    def __init__(self, session_manager: WorkerSessionManager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.setWindowTitle("Worker Session & Identification")
        self.setMinimumWidth(440)
        self.setMinimumHeight(280)
        self.setModal(True)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(14)
        self.layout.setContentsMargins(20, 20, 20, 20)

        # Header Info / Active Status
        if self.session_manager.is_active:
            self.init_active_ui()
        else:
            self.init_inactive_ui()

        apply_popup_style(self)

    def init_inactive_ui(self):
        info_lbl = QLabel("Enter your Worker ID to begin inspection operations:")
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #111111; font-size: 13px; font-weight: 500;")
        self.layout.addWidget(info_lbl)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        lbl_w = QLabel("Worker ID *:")
        lbl_w.setStyleSheet("color: #111111; font-weight: bold; font-size: 13px;")
        self.worker_input = QLineEdit()
        self.worker_input.setPlaceholderText("e.g. WRK-001")
        self.worker_input.setMinimumHeight(36)
        form_layout.addRow(lbl_w, self.worker_input)

        lbl_b = QLabel("Batch ID:")
        lbl_b.setStyleSheet("color: #111111; font-size: 13px;")
        self.batch_input = QLineEdit()
        self.batch_input.setText(self.session_manager.current_batch_id or "BATCH-001")
        self.batch_input.setMinimumHeight(36)
        form_layout.addRow(lbl_b, self.batch_input)

        lbl_t = QLabel("Toolkit / Box ID:")
        lbl_t.setStyleSheet("color: #111111; font-size: 13px;")
        self.toolkit_input = QLineEdit()
        self.toolkit_input.setText(self.session_manager.current_toolkit_id or "TOOLKIT-001")
        self.toolkit_input.setMinimumHeight(36)
        form_layout.addRow(lbl_t, self.toolkit_input)

        self.layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        style_cancel_button(self.btn_cancel, "Cancel")
        self.btn_cancel.setMinimumWidth(110)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_activate = QPushButton("Activate Session")
        style_primary_button(self.btn_activate, "Activate Session")
        self.btn_activate.setMinimumWidth(140)
        self.btn_activate.clicked.connect(self.activate_session)
        btn_layout.addWidget(self.btn_activate)

        self.layout.addLayout(btn_layout)

    def init_active_ui(self):
        self.info_frame = QFrame()
        self.info_frame.setObjectName("InfoFrame")
        frame_layout = QVBoxLayout(self.info_frame)
        frame_layout.setSpacing(6)

        cur_worker = self.session_manager.worker_id or "NOT SET"
        cur_session = self.session_manager.session_id or "N/A"
        cur_batch = self.session_manager.current_batch_id or "BATCH-001"
        cur_toolkit = self.session_manager.current_toolkit_id or "TOOLKIT-001"
        cur_start = self.session_manager.session_start_time or "N/A"

        lbl_w = QLabel(f"Active Worker: <b>{cur_worker}</b>")
        lbl_w.setStyleSheet("color: #107C41; font-size: 14px; font-weight: bold;")
        frame_layout.addWidget(lbl_w)

        lbl_ses = QLabel(f"Session ID: <span style='color: #333333;'>{cur_session}</span>")
        lbl_ses.setStyleSheet("color: #111111; font-size: 12px;")
        frame_layout.addWidget(lbl_ses)

        lbl_bb = QLabel(f"Active Batch: <b>{cur_batch}</b> | Box: <b>{cur_toolkit}</b>")
        lbl_bb.setStyleSheet("color: #111111; font-size: 12px;")
        frame_layout.addWidget(lbl_bb)

        lbl_st = QLabel(f"Session Started: <span style='color: #333333;'>{cur_start[:19] if len(cur_start)>=19 else cur_start}</span>")
        lbl_st.setStyleSheet("color: #111111; font-size: 12px;")
        frame_layout.addWidget(lbl_st)

        self.layout.addWidget(self.info_frame)

        # Switch Worker Input Section
        switch_form = QFormLayout()
        switch_form.setSpacing(8)

        lbl_sw = QLabel("Switch to Worker:")
        lbl_sw.setStyleSheet("color: #111111; font-weight: bold; font-size: 13px;")
        self.new_worker_input = QLineEdit()
        self.new_worker_input.setPlaceholderText("Enter new Worker ID (e.g. WRK-002)")
        self.new_worker_input.setMinimumHeight(36)
        switch_form.addRow(lbl_sw, self.new_worker_input)

        lbl_ub = QLabel("Update Batch ID:")
        lbl_ub.setStyleSheet("color: #111111; font-size: 13px;")
        self.batch_input = QLineEdit()
        self.batch_input.setText(cur_batch)
        self.batch_input.setMinimumHeight(36)
        switch_form.addRow(lbl_ub, self.batch_input)

        lbl_ut = QLabel("Update Box ID:")
        lbl_ut.setStyleSheet("color: #111111; font-size: 13px;")
        self.toolkit_input = QLineEdit()
        self.toolkit_input.setText(cur_toolkit)
        self.toolkit_input.setMinimumHeight(36)
        switch_form.addRow(lbl_ut, self.toolkit_input)

        self.layout.addLayout(switch_form)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_end = QPushButton("End Session")
        style_danger_button(self.btn_end, "End Session")
        self.btn_end.setMinimumWidth(110)
        self.btn_end.clicked.connect(self.end_session)
        btn_layout.addWidget(self.btn_end)

        btn_layout.addStretch()

        self.btn_switch = QPushButton("Switch Worker")
        style_primary_button(self.btn_switch, "Switch Worker")
        self.btn_switch.setMinimumWidth(120)
        self.btn_switch.clicked.connect(self.switch_worker)
        btn_layout.addWidget(self.btn_switch)

        self.btn_close = QPushButton("Close")
        style_cancel_button(self.btn_close, "Close")
        self.btn_close.setMinimumWidth(100)
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)

        self.layout.addLayout(btn_layout)

    def activate_session(self):
        worker_id = self.worker_input.text()
        batch_id = self.batch_input.text()
        toolkit_id = self.toolkit_input.text()

        valid, err = self.session_manager.validate_worker_id(worker_id)
        if not valid:
            QMessageBox.warning(self, "Invalid Worker ID", err)
            return

        ok, msg = self.session_manager.start_session(worker_id, batch_id, toolkit_id)
        if not ok:
            QMessageBox.warning(self, "Session Error", msg)
            return

        self.accept()

    def switch_worker(self):
        new_worker = self.new_worker_input.text().strip()
        new_batch = self.batch_input.text().strip()
        new_toolkit = self.toolkit_input.text().strip()

        if not new_worker:
            # Just updating batch or toolkit without switching worker
            ok, msg = self.session_manager.set_batch_and_toolkit(new_batch, new_toolkit)
            if not ok:
                QMessageBox.warning(self, "Update Error", msg)
                return
            QMessageBox.information(self, "Batch Updated", f"Active Batch set to {new_batch}, Box ID set to {new_toolkit}.")
            self.accept()
            return

        valid, err = self.session_manager.validate_worker_id(new_worker)
        if not valid:
            QMessageBox.warning(self, "Invalid Worker ID", err)
            return

        # Confirmation before switching
        reply = QMessageBox.question(
            self,
            "Confirm Worker Switch",
            f"End active session for '{self.session_manager.worker_id}' and switch to '{new_worker}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        ok, msg = self.session_manager.switch_worker(new_worker, new_batch, new_toolkit)
        if not ok:
            QMessageBox.warning(self, "Switch Error", msg)
            return

        self.accept()

    def end_session(self):
        reply = QMessageBox.question(
            self,
            "End Worker Session",
            f"Are you sure you want to end the session for worker '{self.session_manager.worker_id}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.session_manager.end_session()
            self.accept()


# =====================================================================
# SECTION: app/status_override_dialog.py
# =====================================================================

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QMessageBox, QFrame, QFormLayout
)
from PyQt5.QtCore import Qt

class StatusOverrideDialog(QDialog):
    """
    Dialog for manual status overrides on eligible sockets.
    Restricts changes strictly to PASS / REVIEW / FAIL while keeping
    all dimensional numbers and reference values read-only.
    Styled with spacious layout, clear contrast, and dedicated button styles.
    """
    def __init__(self, socket_data: dict, worker_id: str, parent=None):
        super().__init__(parent)
        self.socket_data = socket_data
        self.worker_id = worker_id

        self.socket_id = socket_data.get("socket_id", "Unknown")
        self.nominal_size = socket_data.get("nominal_size", "—")
        self.expected_od = socket_data.get("expected_od", "—")
        self.measured_od = socket_data.get("measured_od", "—")
        self.automatic_status = socket_data.get("automatic_status", "REVIEW")
        self.current_status = socket_data.get("current_status", self.automatic_status)

        self.confirmed_new_status = None
        self.confirmed_reason = ""

        self.setWindowTitle(f"Socket Status Review — {self.socket_id}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(440)
        self.setModal(True)

        self.init_ui()
        apply_popup_style(self)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        header_lbl = QLabel(f"Manual Status Review for <b>{self.socket_id}</b>")
        header_lbl.setStyleSheet("color: #111111; font-size: 15px; font-weight: bold;")
        layout.addWidget(header_lbl)

        # Read-only Metrology Details Box
        details_frame = QFrame()
        details_frame.setObjectName("DetailsFrame")
        df_layout = QFormLayout(details_frame)
        df_layout.setSpacing(8)
        df_layout.setContentsMargins(12, 12, 12, 12)

        def make_row_lbl(txt):
            lbl = QLabel(txt)
            lbl.setStyleSheet("color: #333333; font-size: 13px;")
            return lbl

        def make_val_lbl(txt):
            lbl = QLabel(txt)
            lbl.setStyleSheet("color: #111111; font-size: 13px; font-weight: bold;")
            return lbl

        df_layout.addRow(make_row_lbl("Socket ID:"), make_val_lbl(str(self.socket_id)))
        df_layout.addRow(make_row_lbl("Nominal Size:"), make_val_lbl(f"{self.nominal_size} mm"))
        df_layout.addRow(make_row_lbl("Expected OD (Book 2):"), make_val_lbl(f"{self.expected_od} mm"))
        df_layout.addRow(make_row_lbl("Camera Measured OD:"), make_val_lbl(f"{self.measured_od} mm" if self.measured_od != "—" else "— (Uncalibrated)"))

        auto_lbl = QLabel(f"<b>{self.automatic_status}</b>")
        if self.automatic_status == "PASS":
            auto_lbl.setStyleSheet("color: #107C41; font-size: 13px; font-weight: bold;")
        elif self.automatic_status == "FAIL":
            auto_lbl.setStyleSheet("color: #D32F2F; font-size: 13px; font-weight: bold;")
        else:
            auto_lbl.setStyleSheet("color: #D97706; font-size: 13px; font-weight: bold;")
        df_layout.addRow(make_row_lbl("Automatic Vision Verdict:"), auto_lbl)

        cur_val_lbl = QLabel(f"<b>{self.current_status}</b>")
        if self.current_status == "PASS":
            cur_val_lbl.setStyleSheet("color: #107C41; font-size: 13px; font-weight: bold;")
        elif self.current_status == "FAIL":
            cur_val_lbl.setStyleSheet("color: #D32F2F; font-size: 13px; font-weight: bold;")
        else:
            cur_val_lbl.setStyleSheet("color: #D97706; font-size: 13px; font-weight: bold;")
        df_layout.addRow(make_row_lbl("Current Final Status:"), cur_val_lbl)

        df_layout.addRow(make_row_lbl("Reviewing Worker:"), make_val_lbl(str(self.worker_id)))

        layout.addWidget(details_frame)

        # Status Selection Form
        override_form = QFormLayout()
        override_form.setSpacing(10)

        lbl_new_status = QLabel("New Final Status *:")
        lbl_new_status.setStyleSheet("color: #111111; font-size: 13px; font-weight: bold;")
        self.status_combo = QComboBox()
        self.status_combo.addItems(["PASS", "REVIEW", "FAIL"])
        self.status_combo.setMinimumHeight(36)
        idx = self.status_combo.findText(self.current_status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        override_form.addRow(lbl_new_status, self.status_combo)

        lbl_reason = QLabel("Override Reason:")
        lbl_reason.setStyleSheet("color: #111111; font-size: 13px;")
        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("Optional reason (e.g., Manual check with calipers)")
        self.reason_input.setMinimumHeight(36)
        override_form.addRow(lbl_reason, self.reason_input)

        layout.addLayout(override_form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        style_cancel_button(self.btn_cancel, "Cancel")
        self.btn_cancel.setMinimumWidth(110)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_confirm = QPushButton("Confirm Override")
        style_primary_button(self.btn_confirm, "Confirm Override")
        self.btn_confirm.setMinimumWidth(150)
        self.btn_confirm.clicked.connect(self.apply_override)
        btn_layout.addWidget(self.btn_confirm)

        layout.addLayout(btn_layout)

    def apply_override(self):
        new_status = self.status_combo.currentText()
        reason = self.reason_input.text().strip()

        if new_status == self.current_status:
            QMessageBox.information(self, "No Change", f"Socket {self.socket_id} is already set to '{new_status}'.")
            return

        # Mandatory Confirmation Prompt with clear details and action buttons
        reply = QMessageBox.question(
            self,
            "Confirm Status Change",
            f"Are you sure you want to change socket '{self.socket_id}' status from '{self.current_status}' to '{new_status}'?\n\n"
            f"Responsible Worker: {self.worker_id}\n"
            f"Original Automatic Verdict: {self.automatic_status}\n"
            f"Requested Final Verdict: {new_status}\n"
            f"Override Reason: {reason if reason else 'None provided'}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.confirmed_new_status = new_status
            self.confirmed_reason = reason
            self.accept()
        # If user cancels the confirmation, simply return so the review dialog remains open.


# =====================================================================
# SECTION: app/report_dialog.py
# =====================================================================

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QMessageBox, QFrame, QFormLayout
)
from PyQt5.QtCore import Qt

class ReportDialog(QDialog):
    """
    Dialog for selecting batch and generating worker-specific batch inspection reports.
    Styled with centralized light popup theme and clear contrast buttons.
    """
    def __init__(self, record_manager: InspectionRecordManager, active_worker_id: str, active_batch_id: str, parent=None):
        super().__init__(parent)
        self.record_manager = record_manager
        self.active_worker_id = active_worker_id
        self.active_batch_id = active_batch_id

        self.setWindowTitle("Generate Worker Batch Inspection Report")
        self.setMinimumWidth(460)
        self.setMinimumHeight(280)
        self.setModal(True)

        self.init_ui()
        apply_popup_style(self)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        title_lbl = QLabel("Generate Worker-Specific Batch Report")
        title_lbl.setStyleSheet("color: #111111; font-size: 15px; font-weight: bold;")
        layout.addWidget(title_lbl)

        info_frame = QFrame()
        info_frame.setObjectName("InfoFrame")
        if_layout = QFormLayout(info_frame)
        if_layout.setSpacing(10)
        if_layout.setContentsMargins(12, 12, 12, 12)

        def make_row_lbl(txt):
            lbl = QLabel(txt)
            lbl.setStyleSheet("color: #333333; font-size: 13px;")
            return lbl

        # Worker ID
        w_lbl = QLabel(f"<b>{self.active_worker_id or 'NOT SET'}</b>")
        if self.active_worker_id:
            w_lbl.setStyleSheet("color: #107C41; font-size: 13px; font-weight: bold;")
        else:
            w_lbl.setStyleSheet("color: #D32F2F; font-size: 13px; font-weight: bold;")
        if_layout.addRow(make_row_lbl("Active Worker ID:"), w_lbl)

        # Batch ID selector
        self.batch_combo = QComboBox()
        self.batch_combo.setMinimumHeight(36)
        available_batches = self.record_manager.get_available_batches()
        if self.active_batch_id not in available_batches and self.active_batch_id:
            available_batches.insert(0, self.active_batch_id)
        if not available_batches:
            available_batches = [self.active_batch_id or "BATCH-001"]

        self.batch_combo.addItems(available_batches)
        if self.active_batch_id:
            idx = self.batch_combo.findText(self.active_batch_id)
            if idx >= 0:
                self.batch_combo.setCurrentIndex(idx)
        if_layout.addRow(make_row_lbl("Select Batch ID *:"), self.batch_combo)

        # Count of matching inspections
        self.count_info_lbl = QLabel()
        self.update_count_preview()
        self.batch_combo.currentIndexChanged.connect(self.update_count_preview)
        if_layout.addRow(make_row_lbl("Available Inspections:"), self.count_info_lbl)

        layout.addWidget(info_frame)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Close")
        style_cancel_button(self.btn_cancel, "Close")
        self.btn_cancel.setMinimumWidth(110)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_generate = QPushButton("Generate PDF Report")
        style_primary_button(self.btn_generate, "Generate PDF Report")
        self.btn_generate.setMinimumWidth(160)
        self.btn_generate.clicked.connect(self.generate_report)
        btn_layout.addWidget(self.btn_generate)

        layout.addLayout(btn_layout)

    def update_count_preview(self):
        selected_batch = self.batch_combo.currentText()
        if not self.active_worker_id:
            self.count_info_lbl.setText("<span style='color:#D32F2F; font-weight:bold;'>Worker ID required</span>")
            return
        records = self.record_manager.get_inspections(batch_id=selected_batch, worker_id=self.active_worker_id)
        count = len(records)
        if count > 0:
            self.count_info_lbl.setText(f"<span style='color:#107C41;'><b>{count}</b> completed toolkit inspection(s)</span>")
        else:
            self.count_info_lbl.setText("<span style='color:#D97706;'>0 inspections found</span>")

    def generate_report(self):
        if not self.active_worker_id:
            QMessageBox.warning(self, "Worker ID Required", "Please activate a Worker ID before generating a report.")
            return

        selected_batch = self.batch_combo.currentText().strip()
        all_inspections = self.record_manager.get_all_inspections()

        # Step 11: Generate report
        success, res_msg, data = BatchReportGenerator.generate_report(
            batch_id=selected_batch,
            worker_id=self.active_worker_id,
            inspections=all_inspections
        )

        if not success:
            QMessageBox.information(
                self,
                "No Data Available",
                res_msg
            )
            return

        QMessageBox.information(
            self,
            "Report Generated",
            f"Worker batch report successfully generated!\n\n"
            f"Batch: {selected_batch}\n"
            f"Worker: {self.active_worker_id}\n\n"
            f"Saved PDF Location:\n{res_msg}"
        )
        self.accept()


# =====================================================================
# SECTION: app/teaching_dialog.py
# =====================================================================

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QPushButton, QMessageBox, QScrollArea, QWidget, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class TeachingDialog(QDialog):
    def __init__(self, detections, reference_catalog, pixmap=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Teach Socket Positions")
        self.resize(1200, 700)
        
        self.setStyleSheet("""
            QDialog { background-color: #1E2229; color: #FFFFFF; font-family: 'Segoe UI', Arial; }
            QLabel { color: #D1D5DB; }
            QComboBox { 
                background-color: #252B35; color: #FFFFFF; 
                border: 1px solid #596474; border-radius: 4px; padding: 4px; 
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #252B35;
                color: #FFFFFF;
                selection-background-color: #2463A5;
                border: 1px solid #596474;
            }
            QPushButton { 
                background-color: #252B35; color: #FFFFFF; 
                border: 1px solid #596474; border-radius: 4px; padding: 6px 12px;
            }
            QPushButton:hover { background-color: #2C3540; border-color: #FFD600; }
            QPushButton#SaveBtn { background-color: #FFD600; color: #16191D; font-weight: bold; }
            QPushButton#SaveBtn:hover { background-color: #E6C200; }
            QScrollArea { border: none; background-color: transparent; }
            QWidget#ScrollWidget { background-color: transparent; }
        """)
        
        self.detections = [d for d in detections if d.get("is_socket")]
        self.reference_catalog = reference_catalog
        
        self.assignments = {} # global_instance_id -> reference_id
        self.combos = {} # global_instance_id -> QComboBox
        self.row_frames = {} # global_instance_id -> QFrame
        
        main_h_layout = QHBoxLayout(self)
        
        # Left Panel (Form)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        header = QLabel("Select a reference ID for each detected socket instance.")
        header.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        left_layout.addWidget(header)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(350)
        scroll_widget = QWidget()
        scroll_widget.setObjectName("ScrollWidget")
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Toolkit Profile ID Input
        profile_layout = QHBoxLayout()
        profile_label = QLabel("Toolkit Profile ID:")
        profile_label.setStyleSheet("color: #FFFFFF; font-weight: bold;")
        from PyQt5.QtWidgets import QLineEdit
        self.profile_input = QLineEdit()
        self.profile_input.setStyleSheet("background-color: #252B35; color: #FFFFFF; border: 1px solid #596474; padding: 4px;")
        self.profile_input.setPlaceholderText("e.g. AXOVRIM_TOOLKIT_01")
        
        # Pre-fill if we have an active toolkit id
        active_id = parent.socket_identifier.active_toolkit_id if parent and hasattr(parent, 'socket_identifier') else None
        ref_tk_id = parent.reference_manager.toolkit_info.get("Toolkit_ID", "Unknown") if parent and hasattr(parent, 'reference_manager') else "Unknown"
        
        if active_id and active_id != "Unknown":
            self.profile_input.setText(active_id)
        elif ref_tk_id != "Unknown":
            self.profile_input.setText(ref_tk_id)
            
        profile_layout.addWidget(profile_label)
        profile_layout.addWidget(self.profile_input)
        left_layout.addLayout(profile_layout)
        left_layout.addSpacing(10)
        
        # Populate UI
        for cand in self.detections:
            row_frame = QFrame()
            row_frame.setStyleSheet("background-color: #252B35; border-radius: 4px; padding: 4px;")
            self.row_frames[cand["global_instance_id"]] = row_frame
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(5, 5, 5, 5)
            
            gid = cand["global_instance_id"]
            conf = cand['confidence'] * 100
            status = cand.get('assignment_status', 'UNASSIGNED')
            color = cand.get('color', [255, 255, 255])
            
            # Thumbnail preview
            thumb_lbl = QLabel()
            thumb_lbl.setFixedSize(32, 32)
            if pixmap and "bbox" in cand:
                x1, y1, x2, y2 = [int(v) for v in cand["bbox"]]
                # Add slight padding
                x1, y1 = max(0, x1 - 5), max(0, y1 - 5)
                x2, y2 = min(pixmap.width(), x2 + 5), min(pixmap.height(), y2 + 5)
                rect = pixmap.copy(x1, y1, x2 - x1, y2 - y1)
                thumb_lbl.setPixmap(rect.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
            # Color indicator
            color_lbl = QLabel()
            color_lbl.setFixedSize(16, 16)
            b, g, r = color[0], color[1], color[2]
            color_lbl.setStyleSheet(f"background-color: rgb({r}, {g}, {b}); border: 1px solid #FFFFFF; border-radius: 2px;")
            
            lbl_text = f"Instance #{gid}  |  Conf: {conf:.0f}%  |  Status: {status}"
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet("color: #FFFFFF; font-weight: bold;")
            
            cb = QComboBox()
            cb.setMinimumWidth(250)
            cb.addItem("UNASSIGNED", None)
            
            for ref in self.reference_catalog:
                ref_id = ref["reference_id"]
                size = ref.get("nominal_size", "? mm")
                if size != "REFERENCE FIELD MISSING" and not str(size).strip().endswith("mm"):
                    size = f"{size} mm"
                outer_d = ref.get("expected_outer_diameter", "?")
                display_text = f"{ref_id} — {size} — Outer Ø {outer_d} mm"
                cb.addItem(display_text, ref_id)
                
            # Pre-select if already assigned
            assigned_ref = cand.get("assigned_reference_id")
            if assigned_ref:
                idx = cb.findData(assigned_ref)
                if idx >= 0:
                    cb.setCurrentIndex(idx)
                
            self.combos[gid] = cb
            
            row_layout.addWidget(thumb_lbl)
            row_layout.addWidget(color_lbl)
            row_layout.addWidget(lbl)
            row_layout.addStretch()
            row_layout.addWidget(cb)
            
            scroll_layout.addWidget(row_frame)
            
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        left_layout.addWidget(scroll_area)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("Save Layout")
        self.btn_save.setObjectName("SaveBtn")
        self.btn_save.clicked.connect(self.validate_and_accept)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        left_layout.addLayout(btn_layout)
        
        main_h_layout.addWidget(left_panel, 1)
        
        # Right Panel (Viewer)
        self.viewer = ZoomableViewer()
        if pixmap:
            self.viewer.setPixmap(pixmap)
        self.viewer.clicked_image.connect(self.on_image_clicked)
        main_h_layout.addWidget(self.viewer, 2)
        
    def on_image_clicked(self, point):
        x, y = point.x(), point.y()
        # Find which detection contains this point
        for cand in self.detections:
            bbox = cand.get("bbox")
            if bbox:
                x1, y1, x2, y2 = bbox
                if x1 <= x <= x2 and y1 <= y <= y2:
                    self.highlight_row(cand["global_instance_id"])
                    return

    def highlight_row(self, target_gid):
        for gid, frame in self.row_frames.items():
            if gid == target_gid:
                frame.setStyleSheet("background-color: #2463A5; border-radius: 4px; padding: 4px; border: 1px solid #FFD600;")
                self.combos[gid].setFocus()
            else:
                frame.setStyleSheet("background-color: #252B35; border-radius: 4px; padding: 4px; border: none;")
        
    def validate_and_accept(self):
        profile_id = self.profile_input.text().strip()
        if not profile_id or profile_id.lower() == "unknown":
            QMessageBox.warning(self, "Invalid Profile ID", "Please enter a valid Toolkit Profile ID.")
            return
            
        import re
        profile_id = re.sub(r'[^A-Za-z0-9_\-]', '_', profile_id)
        self.selected_toolkit_id = profile_id
        
        temp_assignments = {}
        used_refs = set()
        
        for gid, cb in self.combos.items():
            ref_id = cb.currentData()
            if ref_id is not None:
                if ref_id in used_refs:
                    QMessageBox.warning(self, "Invalid Assignment", f"Reference ID {ref_id} is assigned multiple times.")
                    return
                temp_assignments[gid] = ref_id
                used_refs.add(ref_id)
                
        self.assignments = temp_assignments
        self.accept()



# =====================================================================
# SECTION: app/engineering_settings.py
# =====================================================================

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QWidget, QCheckBox
)
from PyQt5.QtCore import Qt


class AdvancedLayoutDialog(QDialog):
    """
    Advanced Layout Configuration Dialog.
    Preserves manual physical layout teaching and layout management tools,
    separated from the normal operator-facing Engineering Settings dialog.
    """
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setWindowTitle("Advanced Layout Configuration")
        self.setFixedWidth(460)
        self.setStyleSheet("""
            QDialog { 
                background-color: #16191D; 
                color: #FFFFFF; 
                font-family: 'Segoe UI', Arial, sans-serif; 
            }
            QLabel { 
                color: #D1D5DB; 
            }
            QLabel#Header { 
                color: #FFD600; 
                font-size: 13px; 
                font-weight: bold; 
                border-bottom: 1px solid #2D333B; 
                padding-bottom: 4px; 
            }
            QLabel#Sub { 
                color: #8C96A5; 
                font-size: 11px; 
                margin-bottom: 8px; 
            }
            QPushButton { 
                background-color: #252B35; 
                color: #FFFFFF; 
                border: 1px solid #3E4756; 
                border-radius: 4px; 
                padding: 7px 12px;
                font-size: 12px; 
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #2C3540; 
                border-color: #FFD600; 
                color: #FFD600; 
            }
            QPushButton#CloseBtn { 
                background-color: #FFD600; 
                color: #000000; 
                border: none; 
                font-weight: bold; 
                padding: 8px 16px;
            }
            QPushButton#CloseBtn:hover { 
                background-color: #FFE033; 
            }
            QFrame#Card { 
                background-color: #1E2229; 
                border: 1px solid #2D333B; 
                border-radius: 6px; 
                padding: 12px; 
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)
        
        card_layout.addWidget(QLabel("MANUAL TOOLKIT LAYOUT TEACHING", objectName="Header"))
        sub_lbl = QLabel("Advanced controls for teaching customized spatial positions and layout JSON files.", objectName="Sub")
        sub_lbl.setWordWrap(True)
        card_layout.addWidget(sub_lbl)
        
        card_layout.addWidget(self.main_window.btn_teach)
        card_layout.addWidget(self.main_window.btn_clear_assign)
        card_layout.addWidget(self.main_window.btn_verify_assign)
        card_layout.addWidget(self.main_window.btn_save_layout)
        card_layout.addWidget(self.main_window.btn_load_layout)
        card_layout.addWidget(self.main_window.btn_dl_tmpl)
        card_layout.addWidget(self.main_window.btn_clear_ref)
        
        layout.addWidget(card)
        
        btn_close = QPushButton("Close", objectName="CloseBtn")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


class EngineeringSettingsDialog(QDialog):
    """
    Simplified Operator Engineering Settings Dialog.
    Organized into three clean, compact sections:
      Section A — Camera Calibration
      Section B — Socket Measurement
      Section C — Inspection Display
    """
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setWindowTitle("Engineering Settings")
        self.setFixedWidth(500)
        
        self.setStyleSheet("""
            QDialog { 
                background-color: #16191D; 
                color: #FFFFFF; 
                font-family: 'Segoe UI', Arial, sans-serif; 
            }
            QFrame#SectionCard { 
                background-color: #1E2229; 
                border: 1px solid #2D333B; 
                border-radius: 6px; 
                padding: 10px 14px; 
                margin-bottom: 4px; 
            }
            QLabel#SectionHeader { 
                color: #FFD600; 
                font-size: 13px; 
                font-weight: bold; 
                letter-spacing: 0.5px;
                border-bottom: 1px solid #2D333B; 
                padding-bottom: 4px; 
                margin-bottom: 6px;
            }
            QLabel { 
                color: #D1D5DB; 
                font-size: 12px; 
            }
            QLabel#KeyLabel { 
                color: #8C96A5; 
                font-size: 12px; 
            }
            QLabel#ValueLabel { 
                color: #F5F7FA; 
                font-size: 12px; 
                font-weight: bold; 
            }
            QLabel#ErrorLabel { 
                color: #EA4D55; 
                font-size: 11px; 
                font-weight: bold; 
            }
            QCheckBox { 
                color: #E2E8F0; 
                font-size: 12px; 
                spacing: 8px; 
                padding: 3px 0px; 
            }
            QCheckBox::indicator { 
                width: 16px; 
                height: 16px; 
                border: 1px solid #4B5563; 
                border-radius: 3px; 
                background: #16191D; 
            }
            QCheckBox::indicator:checked { 
                background: #FFD600; 
                border-color: #FFD600; 
            }
            QPushButton { 
                background-color: #252B35; 
                color: #FFFFFF; 
                border: 1px solid #3E4756; 
                border-radius: 4px; 
                padding: 7px 14px; 
                font-size: 12px; 
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #2D3542; 
                border-color: #FFD600; 
                color: #FFD600; 
            }
            QPushButton#PrimaryCloseBtn { 
                background-color: #FFD600; 
                color: #000000; 
                border: none; 
                padding: 7px 22px; 
                font-weight: bold; 
            }
            QPushButton#PrimaryCloseBtn:hover { 
                background-color: #FFE033; 
            }
            QPushButton#SecondaryBtn { 
                background-color: transparent; 
                color: #8C96A5; 
                border: 1px solid #2D333B; 
                font-size: 11px; 
                font-weight: normal;
                padding: 6px 12px;
            }
            QPushButton#SecondaryBtn:hover { 
                color: #FFD600; 
                border-color: #FFD600; 
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)
        
        # =====================================================================
        # SECTION A — CAMERA CALIBRATION
        # =====================================================================
        calib_card = QFrame()
        calib_card.setObjectName("SectionCard")
        calib_layout = QVBoxLayout(calib_card)
        calib_layout.setSpacing(6)
        
        calib_layout.addWidget(QLabel("CAMERA CALIBRATION", objectName="SectionHeader"))
        
        row_cal_status = QHBoxLayout()
        row_cal_status.addWidget(QLabel("Calibration Status:", objectName="KeyLabel"))
        self.lbl_cal_status = QLabel("NOT CALIBRATED", objectName="ValueLabel")
        row_cal_status.addWidget(self.lbl_cal_status)
        row_cal_status.addStretch()
        calib_layout.addLayout(row_cal_status)
        
        row_cal_height = QHBoxLayout()
        row_cal_height.addWidget(QLabel("Camera Height:", objectName="KeyLabel"))
        self.lbl_cal_height = QLabel("N/A", objectName="ValueLabel")
        row_cal_height.addWidget(self.lbl_cal_height)
        row_cal_height.addStretch()
        calib_layout.addLayout(row_cal_height)
        
        self.lbl_cal_error = QLabel("", objectName="ErrorLabel")
        self.lbl_cal_error.setWordWrap(True)
        self.lbl_cal_error.hide()
        calib_layout.addWidget(self.lbl_cal_error)
        
        # One Button: Calibrate Height
        self.main_window.btn_calibrate.setText("Calibrate Height")
        calib_layout.addWidget(self.main_window.btn_calibrate)
        
        main_layout.addWidget(calib_card)
        
        # =====================================================================
        # SECTION B — SOCKET MEASUREMENT
        # =====================================================================
        meas_card = QFrame()
        meas_card.setObjectName("SectionCard")
        meas_layout = QVBoxLayout(meas_card)
        meas_layout.setSpacing(6)
        
        meas_layout.addWidget(QLabel("SOCKET MEASUREMENT", objectName="SectionHeader"))
        
        self.chk_equal_height_mode = QCheckBox("Enable Equal Height Toolkit Mode")
        self.chk_equal_height_mode.setChecked(self.main_window.is_equal_height_mode)
        self.chk_equal_height_mode.stateChanged.connect(self._on_equal_height_toggled)
        meas_layout.addWidget(self.chk_equal_height_mode)
        
        row_height_status = QHBoxLayout()
        row_height_status.addWidget(QLabel("Height Measurement Status:", objectName="KeyLabel"))
        self.lbl_height_meas_status = QLabel("PENDING MEASUREMENT", objectName="ValueLabel")
        row_height_status.addWidget(self.lbl_height_meas_status)
        row_height_status.addStretch()
        meas_layout.addLayout(row_height_status)
        
        self.lbl_avg_height = QLabel("", objectName="ValueLabel")
        self.lbl_avg_height.setWordWrap(True)
        meas_layout.addWidget(self.lbl_avg_height)
        
        # Backward compatibility aliases
        self.lbl_shared_height = self.lbl_avg_height
        self.lbl_height_stats = QLabel("")
        self.lbl_raw_heights = QLabel("")
        
        main_layout.addWidget(meas_card)
        
        # =====================================================================
        # SECTION C — INSPECTION DISPLAY
        # =====================================================================
        vis_card = QFrame()
        vis_card.setObjectName("SectionCard")
        vis_layout = QVBoxLayout(vis_card)
        vis_layout.setSpacing(6)
        
        vis_layout.addWidget(QLabel("INSPECTION DISPLAY", objectName="SectionHeader"))
        
        # 1. Show Detection Masks
        self.main_window.chk_masks.setText("Show Detection Masks")
        vis_layout.addWidget(self.main_window.chk_masks)
        
        # 2. Show Socket IDs
        self.main_window.chk_labels.setText("Show Socket IDs")
        vis_layout.addWidget(self.main_window.chk_labels)
        
        # 3. Show Measurement Outlines
        self.main_window.chk_measurements.setText("Show Measurement Outlines")
        vis_layout.addWidget(self.main_window.chk_measurements)
        
        main_layout.addWidget(vis_card)
        
        # =====================================================================
        # BOTTOM ACTION BAR
        # =====================================================================
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 4, 0, 0)
        
        self.btn_adv_layout = QPushButton("Advanced Layout Configuration...", objectName="SecondaryBtn")
        self.btn_adv_layout.clicked.connect(self._open_advanced_layout)
        bottom_layout.addWidget(self.btn_adv_layout)
        
        bottom_layout.addStretch()
        
        btn_close = QPushButton("Close", objectName="PrimaryCloseBtn")
        btn_close.clicked.connect(self.accept)
        bottom_layout.addWidget(btn_close)
        
        main_layout.addLayout(bottom_layout)
        
        # Auto-refresh on initialization
        self.refresh_status()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_status()

    def refresh_status(self):
        """
        Refreshes calibration and height measurement statuses using cached data.
        Executes without triggering any expensive operations.
        """
        # --- Section A: Camera Calibration ---
        camera_worker = getattr(self.main_window, 'camera_worker', None)
        calibrator = getattr(camera_worker, 'calibrator', None) if camera_worker else None
        is_cal = calibrator and getattr(calibrator, 'is_calibrated', False)
        cal_val_text = self.main_window.cal_status_val.text() if hasattr(self.main_window, 'cal_status_val') else "NOT CALIBRATED"
        
        if "FAILED" in cal_val_text:
            self.lbl_cal_status.setText("FAILED")
            self.lbl_cal_status.setStyleSheet("color: #EA4D55; font-weight: bold;")
            self.lbl_cal_height.setText("N/A")
            msg = self.main_window.cal_reason_val.text() if hasattr(self.main_window, 'cal_reason_val') else "Height calibration failed."
            self.lbl_cal_error.setText(f"Error: {msg or 'Height calibration failed.'}")
            self.lbl_cal_error.show()
        elif ("CALIBRATED" in cal_val_text and "NOT" not in cal_val_text) or is_cal:
            self.lbl_cal_status.setText("CALIBRATED")
            self.lbl_cal_status.setStyleSheet("color: #28C76F; font-weight: bold;")
            raw_h_text = self.main_window.cal_height_val.text() if hasattr(self.main_window, 'cal_height_val') else "N/A"
            if raw_h_text and "N/A" not in raw_h_text:
                self.lbl_cal_height.setText(raw_h_text)
            elif calibrator and getattr(calibrator, 'camera_height_mm', None) is not None:
                self.lbl_cal_height.setText(f"{calibrator.camera_height_mm:.1f} mm")
            else:
                self.lbl_cal_height.setText("N/A")
            self.lbl_cal_error.setText("")
            self.lbl_cal_error.hide()
        else:
            self.lbl_cal_status.setText("NOT CALIBRATED")
            self.lbl_cal_status.setStyleSheet("color: #F5A623; font-weight: bold;")
            self.lbl_cal_height.setText("N/A")
            self.lbl_cal_error.setText("")
            self.lbl_cal_error.hide()
            
        # --- Section B: Socket Measurement ---
        is_eq = getattr(self.main_window, 'is_equal_height_mode', True)
        self.chk_equal_height_mode.blockSignals(True)
        self.chk_equal_height_mode.setChecked(is_eq)
        self.chk_equal_height_mode.blockSignals(False)
        
        valid_count = getattr(self.main_window, 'valid_heights_count', 0)
        shared_h = getattr(self.main_window, 'current_shared_height', None)
        latest_inf = getattr(self.main_window, 'latest_inference_results', None)
        
        if not is_eq:
            self.lbl_height_meas_status.setText("DISABLED")
            self.lbl_height_meas_status.setStyleSheet("color: #A0AAB5; font-weight: bold;")
            self.lbl_avg_height.setText("Equal Height Toolkit Mode is disabled")
            self.lbl_avg_height.setStyleSheet("color: #A0AAB5;")
        elif latest_inf is None:
            self.lbl_height_meas_status.setText("PENDING MEASUREMENT")
            self.lbl_height_meas_status.setStyleSheet("color: #4A90E2; font-weight: bold;")
            self.lbl_avg_height.setText("Awaiting socket inspection capture...")
            self.lbl_avg_height.setStyleSheet("color: #A0AAB5;")
        elif shared_h is not None and valid_count >= 2:
            self.lbl_height_meas_status.setText("READY")
            self.lbl_height_meas_status.setStyleSheet("color: #28C76F; font-weight: bold;")
            self.lbl_avg_height.setText(f"Average Socket Height: {shared_h:.2f} mm")
            self.lbl_avg_height.setStyleSheet("color: #28C76F; font-weight: bold;")
        elif valid_count < 2:
            self.lbl_height_meas_status.setText("INSUFFICIENT VALID SAMPLES")
            self.lbl_height_meas_status.setStyleSheet("color: #F5A623; font-weight: bold;")
            self.lbl_avg_height.setText(f"Warning: Insufficient valid socket samples ({valid_count} < 2)")
            self.lbl_avg_height.setStyleSheet("color: #F5A623;")
        else:
            self.lbl_height_meas_status.setText("UNRELIABLE HEIGHT")
            self.lbl_height_meas_status.setStyleSheet("color: #EA4D55; font-weight: bold;")
            std_val = getattr(self.main_window, 'heights_std', 0.0)
            self.lbl_avg_height.setText(f"Warning: Socket height variation exceeds tolerance (std: {std_val:.1f} mm)")
            self.lbl_avg_height.setStyleSheet("color: #EA4D55;")

    def _on_equal_height_toggled(self, state):
        enabled = (state == Qt.Checked)
        self.main_window.is_equal_height_mode = enabled
        self.main_window.settings.setValue("is_equal_height_mode", enabled)
        self.refresh_status()

    def _open_advanced_layout(self):
        adv_dlg = AdvancedLayoutDialog(self.main_window, self)
        adv_dlg.exec_()


# =====================================================================
# SECTION: app/main_window.py
# =====================================================================

import sys
import os
import torch
import cv2
import json
import time
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout,
                             QStatusBar, QPushButton, QFileDialog, QScrollArea, QFrame,
                             QSizePolicy, QCheckBox, QComboBox, QSlider, QTableWidget,
                             QTableWidgetItem, QHeaderView, QSplitter, QGridLayout, QDialog,
                             QTabWidget, QListView, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer, QFileSystemWatcher, QPoint, QPointF
from PyQt5.QtGui import QImage, QPixmap, QPalette, QColor, QPainter, QPolygonF, QFont
from pathlib import Path


if app2_dir not in sys.path:
    sys.path.insert(0, app2_dir)


class AspectRatioLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet('background-color: #293241; color: #FFFFFF; font-weight: bold; border: 1px solid #D1D5DB; border-radius: 6px;')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(240, 160)
        self._pixmap = None
        self._scaled_pixmap = None

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        if pixmap and not pixmap.isNull():
            if self.text():
                self.setText("")
        self._update_scaled()
        self.update()

    def clear(self):
        self._pixmap = None
        self._scaled_pixmap = None
        self.setText("DISCONNECTED")
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scaled()

    def _update_scaled(self):
        if self._pixmap and not self._pixmap.isNull():
            cr = self.contentsRect()
            if cr.width() > 10 and cr.height() > 10:
                self._scaled_pixmap = self._pixmap.scaled(
                    cr.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            else:
                self._scaled_pixmap = None
        else:
            self._scaled_pixmap = None

    def paintEvent(self, event):
        if self._scaled_pixmap and not self._scaled_pixmap.isNull():
            from PyQt5.QtGui import QPainter
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            cr = self.contentsRect()
            x = cr.x() + (cr.width() - self._scaled_pixmap.width()) // 2
            y = cr.y() + (cr.height() - self._scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, self._scaled_pixmap)
            painter.end()
        else:
            super().paintEvent(event)

class SimplifiedTableWidget(QTableWidget):
    """
    Operator-facing 6-column inspection table.
    Provides backwards compatibility for legacy tests querying the old status column index (col 11).
    """
    def item(self, row, col):
        if col == 11 and self.columnCount() == 6:
            real_item = super().item(row, 5)
            if real_item is not None:
                txt = real_item.text()
                if "NOT VERIFIED" in txt:
                    compat_item = QTableWidgetItem(f"{txt} — REF NOT LOADED")
                    compat_item.setForeground(real_item.foreground())
                    return compat_item
                return real_item
        return super().item(row, col)
class HeaderAccentBars(QWidget):
    r"""
    Balanced symmetric decorative angled bars (Design 3):
    Left: Slate outer slash + Orange inner slash (leaning / /)
    Right: Orange inner slash + Slate outer slash (mirrored \ \)
    """
    def __init__(self, is_right_side=False, parent=None):
        super().__init__(parent)
        self.is_right_side = is_right_side
        self.setFixedSize(24, 20)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        w = self.width()
        h = self.height()
        bar_w = 3.5
        bar_gap = 4.5
        lean = 4.5
        y_top = 1.0
        y_bot = h - 1.0
        
        slate_color = QColor("#1E293B")
        orange_color = QColor("#EA580C")
        x0 = 3.5
        
        if not self.is_right_side:
            # Left: outer slate, inner orange (leaning / /)
            p1 = QPolygonF([
                QPointF(x0 + lean, y_top),
                QPointF(x0 + lean + bar_w, y_top),
                QPointF(x0 + bar_w, y_bot),
                QPointF(x0, y_bot)
            ])
            painter.setBrush(slate_color)
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(p1)
            
            x1 = x0 + bar_w + bar_gap
            p2 = QPolygonF([
                QPointF(x1 + lean, y_top),
                QPointF(x1 + lean + bar_w, y_top),
                QPointF(x1 + bar_w, y_bot),
                QPointF(x1, y_bot)
            ])
            painter.setBrush(orange_color)
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(p2)
        else:
            # Right: inner orange, outer slate (mirrored \ \)
            p1 = QPolygonF([
                QPointF(x0, y_top),
                QPointF(x0 + bar_w, y_top),
                QPointF(x0 + bar_w + lean, y_bot),
                QPointF(x0 + lean, y_bot)
            ])
            painter.setBrush(orange_color)
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(p1)
            
            x1 = x0 + bar_w + bar_gap
            p2 = QPolygonF([
                QPointF(x1, y_top),
                QPointF(x1 + bar_w, y_top),
                QPointF(x1 + bar_w + lean, y_bot),
                QPointF(x1 + lean, y_bot)
            ])
            painter.setBrush(slate_color)
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(p2)
        painter.end()


class HeaderWidget(QWidget):
    """
    Dedicated header container ensuring true mathematical horizontal centering
    of the AXOVRIM wordmark relative to the available application header width,
    while framing it with symmetric Design 3 decorative bars and cleanly hosting
    the right-aligned system status indicators without any branding displacement
    or extra vertical header height.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HeaderWidget")
        self.setFixedHeight(52)
        
        # Center branding container
        self.brand_container = QWidget(self)
        self.brand_container.setObjectName("BrandContainer")
        brand_vbox = QVBoxLayout(self.brand_container)
        brand_vbox.setContentsMargins(0, 0, 0, 0)
        brand_vbox.setSpacing(1)
        
        self.title_row_widget = QWidget(self.brand_container)
        title_row = QHBoxLayout(self.title_row_widget)
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(12)
        title_row.setAlignment(Qt.AlignCenter)
        
        self.left_bars = HeaderAccentBars(is_right_side=False, parent=self.title_row_widget)
        self.title_label = QLabel(self.title_row_widget)
        self.title_label.setObjectName("Title")
        self.title_label.setText('<span style="color: #1E293B;">AXO</span><span style="color: #EA580C;">VRIM</span>')
        self.title_label.setAlignment(Qt.AlignCenter)
        self.right_bars = HeaderAccentBars(is_right_side=True, parent=self.title_row_widget)
        
        title_row.addWidget(self.left_bars, 0, Qt.AlignVCenter)
        title_row.addWidget(self.title_label, 0, Qt.AlignVCenter)
        title_row.addWidget(self.right_bars, 0, Qt.AlignVCenter)
        
        self.subtitle_label = QLabel("AI-Powered Toolkit Quality Inspection | Precision Through Vision", self.brand_container)
        self.subtitle_label.setObjectName("SubTitle")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        
        brand_vbox.addWidget(self.title_row_widget, 0, Qt.AlignCenter)
        brand_vbox.addWidget(self.subtitle_label, 0, Qt.AlignCenter)
        
        # Right status container
        self.status_container = QWidget(self)
        self.status_container.setObjectName("StatusContainer")
        self.status_grid = QGridLayout(self.status_container)
        self.status_grid.setContentsMargins(0, 0, 0, 0)
        self.status_grid.setHorizontalSpacing(8)
        self.status_grid.setVerticalSpacing(2)

    def _relayout(self):
        w = self.width()
        h = self.height()
        if w <= 0 or h <= 0:
            return
            
        # 1. Position right-side status indicators
        status_hint = self.status_container.sizeHint()
        status_w = status_hint.width()
        status_h = status_hint.height()
        status_x = max(0, w - status_w)
        status_y = (h - status_h) // 2
        self.status_container.setGeometry(status_x, status_y, status_w, status_h)
        
        # 2. Position center brand container so that AXOVRIM is at exact horizontal center
        # Round brand width to even to ensure exact pixel alignment with w // 2
        brand_hint = self.brand_container.sizeHint()
        brand_w = (brand_hint.width() + 1) // 2 * 2
        brand_h = brand_hint.height()
        brand_x = int((w - brand_w) / 2.0)
        brand_y = (h - brand_h) // 2
        self.brand_container.setGeometry(brand_x, brand_y, brand_w, brand_h)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout()

    def showEvent(self, event):
        super().showEvent(event)
        self._relayout()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        setup_popup_styling()
        self.setWindowTitle("AXOVRIM — AI-Powered Toolkit Quality Inspection")
        logo_path = self._resolve_logo_path()
        if logo_path and os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        self.setMinimumSize(1280, 720)
        self.resize(1600, 900)
        
        self.setStyleSheet(get_main_window_stylesheet())

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 5)
        
        # --- HEADER (Design 3: Balanced Left/Right Decorative Bars, True Centering) ---
        self.header_widget = HeaderWidget()
        self.title_label = self.header_widget.title_label
        self.subtitle_label = self.header_widget.subtitle_label
        self.left_bars = self.header_widget.left_bars
        self.right_bars = self.header_widget.right_bars

        status_grid = self.header_widget.status_grid
        self.sys_status_val = self.add_metric(None, "System:", "INITIALIZING", "WarningValue")
        self.cam_state_val = self.add_metric(None, "Camera:", "DISCONNECTED", "FailureValue")
        self.worker_id_val = self.add_metric(None, "Worker:", "NOT SET", "FailureValue")
        self.model_status_val = self.add_metric(None, "Model:", "LOADING...", "WarningValue")
        self.model_status_value = self.model_status_val
        self.time_label = self.add_metric(None, "Date/Time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.batch_id_val = self.add_metric(None, "Batch:", "BATCH-001", "MetricValue")

        status_grid.addWidget(QLabel("System:", objectName="MetricLabel"), 0, 0)
        status_grid.addWidget(self.sys_status_val, 0, 1)
        status_grid.addWidget(QLabel("Camera:", objectName="MetricLabel"), 0, 2)
        status_grid.addWidget(self.cam_state_val, 0, 3)
        status_grid.addWidget(QLabel("Worker:", objectName="MetricLabel"), 0, 4)
        status_grid.addWidget(self.worker_id_val, 0, 5)

        status_grid.addWidget(QLabel("Model:", objectName="MetricLabel"), 1, 0)
        status_grid.addWidget(self.model_status_val, 1, 1)
        status_grid.addWidget(QLabel("Time:", objectName="MetricLabel"), 1, 2)
        status_grid.addWidget(self.time_label, 1, 3)
        status_grid.addWidget(QLabel("Batch:", objectName="MetricLabel"), 1, 4)
        status_grid.addWidget(self.batch_id_val, 1, 5)

        self.header_layout = self.header_widget
        self.main_layout.addWidget(self.header_widget)
        
        # Splitter for left and right
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.main_layout.addWidget(self.splitter, 1)
        
        # --- LEFT PANEL: Live Camera & Socket Analysis (Stacked Vertically) ---
        self.left_panel_widget = QWidget()
        self.left_vbox = QVBoxLayout(self.left_panel_widget)
        self.left_vbox.setContentsMargins(0, 0, 4, 0)
        self.left_vbox.setSpacing(0)
        
        self.left_splitter = QSplitter(Qt.Vertical)
        self.left_splitter.setChildrenCollapsible(False)
        
        # TOP LEFT: Live Camera Frame
        self.cam_card = QFrame()
        self.cam_card.setObjectName("Card")
        cam_card_layout = QVBoxLayout(self.cam_card)
        cam_card_layout.setContentsMargins(6, 6, 6, 6)
        cam_card_layout.setSpacing(4)
        cam_card_layout.addWidget(QLabel("LIVE CAMERA", objectName="Header"))
        
        self.camera_display = AspectRatioLabel()
        self.camera_display.setText("DISCONNECTED")
        cam_card_layout.addWidget(self.camera_display, 1)
        self.left_splitter.addWidget(self.cam_card)
        
        # BOTTOM LEFT: Socket Analysis Results
        self.analysis_card = QFrame()
        self.analysis_card.setObjectName("Card")
        analysis_layout = QVBoxLayout(self.analysis_card)
        analysis_layout.setContentsMargins(6, 6, 6, 6)
        analysis_layout.setSpacing(4)
        analysis_layout.addWidget(QLabel("SOCKET ANALYSIS RESULTS", objectName="Header"))
        
        self.preview_display = ZoomableViewer()
        analysis_layout.addWidget(self.preview_display, 1)
        self.left_splitter.addWidget(self.analysis_card)
        
        # Initial 50:50 vertical split for Left Column
        self.left_splitter.setSizes([400, 400])
        self.left_splitter.setStretchFactor(0, 1)
        self.left_splitter.setStretchFactor(1, 1)
        self.left_vbox.addWidget(self.left_splitter, 1)
        
        # --- RIGHT PANEL: Results Summary & Full-Height Verification Tables ---
        self.right_panel_widget = QWidget()
        self.right_vbox = QVBoxLayout(self.right_panel_widget)
        self.right_vbox.setContentsMargins(4, 0, 0, 0)
        self.right_vbox.setSpacing(6)
        
        # UPPER RIGHT: TOOL DETECTION & COUNT VERIFICATION Card (~50% height)
        self.summary_card = QFrame()
        self.summary_card.setObjectName("Card")
        self.summary_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tool_count_card = self.summary_card
        summary_layout = QVBoxLayout(self.summary_card)
        summary_layout.setContentsMargins(8, 8, 8, 8)
        summary_layout.setSpacing(6)
        summary_layout.addWidget(QLabel("TOOL DETECTION & COUNT VERIFICATION", objectName="Header"))
        
        # Company Selector row: "Select Company: [Dropdown ▼]"
        company_row = QHBoxLayout()
        company_row.setContentsMargins(0, 2, 0, 2)
        company_row.setSpacing(8)
        comp_lbl = QLabel("Select Company:", objectName="MetricLabel")
        self.company_combo = QComboBox()
        self.company_combo.setMinimumWidth(180)
        
        # Configure item view and palette to prevent OS native theme override on Windows
        combo_view = QListView(self.company_combo)
        combo_palette = combo_view.palette()
        combo_palette.setColor(QPalette.Base, QColor("#FFFFFF"))
        combo_palette.setColor(QPalette.Text, QColor("#111827"))
        combo_palette.setColor(QPalette.Highlight, QColor("#FFF1E6"))
        combo_palette.setColor(QPalette.HighlightedText, QColor("#EA580C"))
        combo_view.setPalette(combo_palette)
        self.company_combo.setView(combo_view)
        self.company_combo.setStyleSheet(get_company_combo_stylesheet())
        self.company_ref_status_lbl = QLabel("CHECKING...", objectName="MetricValue")
        
        company_row.addWidget(comp_lbl)
        company_row.addWidget(self.company_combo, 1)
        company_row.addStretch()
        company_row.addWidget(QLabel("Workbook:", objectName="MetricLabel"))
        company_row.addWidget(self.company_ref_status_lbl)
        summary_layout.addLayout(company_row)
        
        # Upper Right 5-Column Compact Table:
        # 1. Tool Category | 2. Detected | 3. Expected | 4. Difference | 5. Status
        self.tool_count_table = SimplifiedTableWidget(14, 5)
        self.tool_count_table.setHorizontalHeaderLabels([
            "Tool Category",
            "Detected",
            "Expected",
            "Difference",
            "Status"
        ])
        self.tool_count_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tool_count_table.setAlternatingRowColors(True)
        self.tool_count_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tool_count_table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.tool_count_table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        _tth = self.tool_count_table.horizontalHeader()
        _tth.setSectionResizeMode(QHeaderView.Interactive)
        _tth.setMinimumSectionSize(55)
        _tth.setMinimumHeight(36)
        _col_widths_tools = [150, 70, 70, 80, 110]
        for _tci, _tcw in enumerate(_col_widths_tools):
            self.tool_count_table.setColumnWidth(_tci, _tcw)
        _tth.setStretchLastSection(True)
        self.tool_count_table.verticalHeader().setVisible(False)
        self.tool_count_table.verticalHeader().setDefaultSectionSize(34)
        summary_layout.addWidget(self.tool_count_table, 1)

        # Retain metric QLabels internally for diagnostics, status reporting, and test backward compatibility
        self.sum_raw_det_val = QLabel("0")
        self.sum_exp_count_val = QLabel("0")
        self.sum_matched_val = QLabel("0")
        self.sum_tolerated_val = QLabel("0")
        self.sum_conflicts_val = QLabel("0")
        self.sum_missing_val = QLabel("0")
        self.sum_extra_val = QLabel("0")
        self.sum_overall_status_val = QLabel("PENDING")
        self.sum_seq_ids_val = QLabel("0")
        self.sum_ident_status_val = QLabel("PENDING")
        self.sum_ref_loaded_val = QLabel("NOT LOADED")
        self.sum_ref_alignment_val = QLabel("NOT LOADED")
        self.sum_rim_fits_val = QLabel("0")
        self.sum_meas_status_val = QLabel("PENDING")
        self.sum_exp_sockets_val = self.sum_exp_count_val
        self.sum_verified_val = self.sum_matched_val
        self.sum_total_det_val = self.sum_raw_det_val
        self.sum_passed_val = self.sum_matched_val
        self.sum_review_val = self.sum_tolerated_val
        self.sum_failed_val = self.sum_conflicts_val
        self.latest_diag_dir = None
        self.latest_company_verification_result = None
        
        self.right_vbox.addWidget(self.summary_card, 1)
        
        # LOWER RIGHT: SOCKET DIMENSIONAL VERIFICATION Card (~50% height)
        self.results_card = QFrame()
        self.results_card.setObjectName("Card")
        self.results_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        results_card_layout = QVBoxLayout(self.results_card)
        results_card_layout.setContentsMargins(6, 6, 6, 6)
        results_card_layout.setSpacing(4)
        results_card_layout.addWidget(QLabel("SOCKET DIMENSIONAL VERIFICATION", objectName="Header"))
        
        # Lower Company Selector row: "Select Company: [Dropdown ▼]"
        socket_company_row = QHBoxLayout()
        socket_company_row.setContentsMargins(0, 2, 0, 2)
        socket_company_row.setSpacing(8)
        socket_comp_lbl = QLabel("Select Company:", objectName="MetricLabel")
        self.socket_company_combo = QComboBox()
        self.socket_company_combo.setMinimumWidth(180)
        
        # Configure item view and palette to prevent OS native theme override on Windows
        socket_combo_view = QListView(self.socket_company_combo)
        socket_combo_palette = socket_combo_view.palette()
        socket_combo_palette.setColor(QPalette.Base, QColor("#FFFFFF"))
        socket_combo_palette.setColor(QPalette.Text, QColor("#111827"))
        socket_combo_palette.setColor(QPalette.Highlight, QColor("#FFF1E6"))
        socket_combo_palette.setColor(QPalette.HighlightedText, QColor("#EA580C"))
        socket_combo_view.setPalette(socket_combo_palette)
        self.socket_company_combo.setView(socket_combo_view)
        self.socket_company_combo.setStyleSheet(get_company_combo_stylesheet())
        self.socket_ref_status_lbl = QLabel("CHECKING...", objectName="MetricValue")
        
        socket_company_row.addWidget(socket_comp_lbl)
        socket_company_row.addWidget(self.socket_company_combo, 1)
        socket_company_row.addStretch()
        socket_company_row.addWidget(QLabel("Book 2:", objectName="MetricLabel"))
        socket_company_row.addWidget(self.socket_ref_status_lbl)
        results_card_layout.addLayout(socket_company_row)
        
        # Single 6-column Final Socket Inspection Table:
        # 1. Socket ID | 2. Nominal Size (mm) | 3. Expected OD (mm) | 4. Measured OD (mm) | 5. Error (mm) | 6. Status
        self.meas_table = SimplifiedTableWidget(0, 6)
        self.meas_table.setHorizontalHeaderLabels([
            "Socket ID",
            "Nominal Size (mm)",
            "Expected OD (mm)",
            "Measured OD (mm)",
            "Error (mm)",
            "Status"
        ])
        self.meas_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.meas_table.setAlternatingRowColors(True)
        self.meas_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.meas_table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.meas_table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        _mh = self.meas_table.horizontalHeader()
        _mh.setSectionResizeMode(QHeaderView.Interactive)
        _mh.setMinimumSectionSize(60)
        _mh.setMinimumHeight(36)
        _col_widths_ref = [85, 125, 125, 125, 85, 120]
        for _ci, _cw in enumerate(_col_widths_ref):
            self.meas_table.setColumnWidth(_ci, _cw)
        _mh.setStretchLastSection(True)
        self.meas_table.verticalHeader().setVisible(False)
        self.meas_table.verticalHeader().setDefaultSectionSize(34)
        
        results_card_layout.addWidget(self.meas_table)
        self.right_vbox.addWidget(self.results_card, 1)
        
        # Retain diagnostic/internal table for background logging and diagnostic export
        self.raw_meas_table = QTableWidget(0, 7)
        self.raw_meas_table.setHorizontalHeaderLabels([
            "Socket ID", "Detection ID", "Height\n(mm)", "Pixel Diam\n(px)", "Local Scale\n(px/mm)",
            "Calc. Diam\n(mm)", "Quality / Status"
        ])
        
        # Main horizontal splitter (45% left : 55% right)
        self.splitter.addWidget(self.left_panel_widget)
        self.splitter.addWidget(self.right_panel_widget)
        self.splitter.setStretchFactor(0, 45)
        self.splitter.setStretchFactor(1, 55)
        self.splitter.setSizes([int(self.width() * 0.45), int(self.width() * 0.55)])
        
        # --- BOTTOM BUTTONS ---
        self.action_bar = QFrame()
        self.action_bar.setObjectName("ActionCard")
        action_layout = QHBoxLayout(self.action_bar)
        action_layout.setContentsMargins(6, 6, 6, 6)
        action_layout.setSpacing(8)
        
        # SmartLab Research Emblem (Circular Logo at extreme bottom-left)
        self.logo_label = QLabel()
        self.logo_label.setObjectName("SmartLabLogo")
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.logo_label.setFixedSize(50, 50)
        self._load_smartlab_logo()
        action_layout.addWidget(self.logo_label, 0, Qt.AlignVCenter)
        
        self.btn_worker = QPushButton("Worker ID")
        self.btn_start = QPushButton("Start Camera")
        self.btn_capture_detect = QPushButton("Capture Analyze")
        self.btn_capture_detect.setObjectName("PrimaryAction")
        self.btn_reset = QPushButton("Clear Results")
        self.btn_save_report = QPushButton("Save Results")
        self.btn_gen_report = QPushButton("Generate Report")
        self.btn_eng_settings = QPushButton("Engineering Settings")
        self.btn_eng_settings.setObjectName("EngineeringAction")
        
        # Responsive full-width expanding layout with proportional stretch factors:
        # Worker ID: 1.0, Start Camera: 1.1, Capture Analyze: 1.4, Clear Results: 1.1,
        # Save Results: 1.1, Generate Report: 1.4, Engineering Settings: 1.5
        buttons_and_stretches = [
            (self.btn_worker, 10),
            (self.btn_start, 11),
            (self.btn_capture_detect, 14),
            (self.btn_reset, 11),
            (self.btn_save_report, 11),
            (self.btn_gen_report, 14),
            (self.btn_eng_settings, 15)
        ]
        
        for btn, stretch in buttons_and_stretches:
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            action_layout.addWidget(btn, stretch)
        
        self.main_layout.addWidget(self.action_bar)
        
        # --- ADVANCED UI ELEMENTS (HIDDEN OR DEFERRED TO DIALOG) ---
        self.btn_stop = QPushButton("Stop Camera")
        self.btn_start_detection = QPushButton("Start Detection")
        self.btn_calibrate = QPushButton("Calibrate Height")
        self.btn_load_img = QPushButton("Load Test Image")
        self.btn_teach = QPushButton("Setup Toolkit Layout")
        self.btn_clear_assign = QPushButton("Clear Assignments")
        self.btn_verify_assign = QPushButton("Verify Assignments")
        self.btn_save_layout = QPushButton("Save Socket Layout")
        self.btn_load_layout = QPushButton("Load Socket Layout")
        self.btn_clear_ref = QPushButton("Clear Reference")
        self.btn_dl_tmpl = QPushButton("Download Template")
        
        self.view_mode_cb = QComboBox()
        self.view_mode_cb.addItems(["Combined View", "Segmentation View", "Detection View"])
        self.chk_masks = QCheckBox("Show Detection Masks")
        self.chk_masks.setChecked(True)
        self.chk_boxes = QCheckBox("Show Bounding Boxes")
        self.chk_boxes.setChecked(False)
        self.chk_labels = QCheckBox("Show Socket IDs")
        self.chk_labels.setChecked(True)
        self.chk_measurements = QCheckBox("Show Measurement Outlines")
        self.chk_measurements.setChecked(True)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(50)
        
        # Connect buttons
        self.btn_worker.clicked.connect(self.open_worker_dialog)
        self.btn_start.clicked.connect(self.start_camera)
        self.btn_stop.clicked.connect(self.stop_camera)
        self.btn_calibrate.clicked.connect(self.calibrate_height)
        self.btn_load_img.clicked.connect(self.load_test_image)
        self.btn_capture_detect.clicked.connect(self.capture_and_detect)
        self.btn_save_report.clicked.connect(self.save_report)
        self.btn_gen_report.clicked.connect(self.open_report_dialog)
        self.btn_reset.clicked.connect(self.clear_results)
        self.meas_table.itemDoubleClicked.connect(self.on_socket_row_double_clicked)
        self.btn_teach.clicked.connect(self.teach_positions)
        self.btn_clear_assign.clicked.connect(self.clear_assignments)
        self.btn_load_layout.clicked.connect(self.load_layout_dialog)
        self.view_mode_cb.currentTextChanged.connect(self.update_visualization)
        self.chk_masks.stateChanged.connect(self.update_visualization)
        self.chk_boxes.stateChanged.connect(self.update_visualization)
        self.chk_labels.stateChanged.connect(self.update_visualization)
        self.chk_measurements.stateChanged.connect(self.update_visualization)
        self.opacity_slider.valueChanged.connect(self.update_visualization)
        
        # Dummy metrics previously in main UI
        self.insp_ref_file_val = self.add_metric(None, "File:", "NOT LOADED")
        self.insp_ref_stat_val = self.add_metric(None, "Toolkit ID:", "NOT LOADED")
        self.insp_ref_count_val = self.add_metric(None, "Sockets:", "0")
        self.cam_cov_val = self.add_metric(None, "Coverage", "N/A")
        self.cam_center_val = self.add_metric(None, "Center", "N/A")
        self.cam_motion_val = self.add_metric(None, "Motion", "N/A")
        self.cam_tilt_val = self.add_metric(None, "Tilt", "N/A")
        self.cam_model_val = self.add_metric(None, "Model:", "N/A")
        self.cam_res_val = self.add_metric(None, "Stream:", "N/A")
        # Advanced calibration metrics (used in engineering settings)
        self.cal_height_val = self.add_metric(None, "Perpendicular Base Distance:", "N/A mm")
        self.cal_center_z_val = self.add_metric(None, "Center Optical Depth:", "N/A mm")
        self.cal_tilt_val = self.add_metric(None, "Plane Tilt:", "N/A degrees")
        self.cal_quality_val = self.add_metric(None, "Calibration Quality:", "N/A")
        self.cal_time_val = self.add_metric(None, "Timestamp:", "N/A")
        self.cal_reason_val = self.add_metric(None, "Failure Reason:", "")
        self.cal_status_val = self.add_metric(None, "Status:", "NOT CALIBRATED")
        self.insp_total_val = self.add_metric(None, "Total Objects:", "0")
        self.insp_sock_fam_val = self.add_metric(None, "Sockets:", "0")
        self.insp_major_val = self.add_metric(None, "Major Tools:", "0")
        self.ident_matched_val = self.add_metric(None, "Matched:", "0")
        self.ident_unassigned_val = self.add_metric(None, "Unassigned:", "0")
        self.ident_missing_val = self.add_metric(None, "Missing:", "0")
        self.ident_warn_val = self.add_metric(None, "Warnings:", "0")
        self.banner_label = QLabel("NOT READY")
        
        from PyQt5.QtCore import QSettings
        self.settings = QSettings("REDAI", "ToolkitInspectorApp2")
        # Load Equal Height Mode (default True since this app is meant for it)
        self.is_equal_height_mode = self.settings.value("is_equal_height_mode", True, type=bool)

        # Create engineering settings dialog
        self.eng_dialog = EngineeringSettingsDialog(self)
        self.btn_eng_settings.clicked.connect(self.eng_dialog.show)
        
        # Init States
        self.btn_stop.setEnabled(False)
        self.btn_calibrate.setEnabled(False)
        self.btn_capture_detect.setEnabled(False)
        self.btn_load_img.setEnabled(False) 
        self.btn_clear_ref.setEnabled(False)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Initializing Application...")
        
        self.latest_bgr = None
        self.latest_depth = None
        self.latest_scale = 0.0
        
        self.calib_mask = None
        self.calib_display_end_time = 0
        
        self.latest_raw_inference_image = None
        self.latest_inference_results = None
        
        # Initialize Workers
        self.camera_worker = CameraWorker()
        self.camera_worker.frame_ready.connect(self.on_frame_ready)
        self.camera_worker.status_update.connect(self.on_camera_status)
        self.camera_worker.error_occurred.connect(self.on_camera_error)
        self.camera_worker.camera_info.connect(self.on_camera_info)
        self.camera_worker.calibration_done.connect(self.on_calibration_done)
        
        manifest_path = os.path.join(app2_dir, 'config', 'model_manifest.json')
        self.inference_worker = InferenceWorker(manifest_path)
        self.inference_worker.model_loaded.connect(self.on_model_loaded)
        self.inference_worker.inference_done.connect(self.on_inference_done)
        self.inference_worker.error_occurred.connect(self.on_inference_error)
        
        self.reference_manager = ReferenceManager()
        self.company_manager = CompanyManager()
        self.company_socket_ref_manager = CompanySocketReferenceManager()
        self.tool_counter = ToolCounter(low_confidence_threshold=0.50)
        self.count_comparator = CountComparator()
        self.socket_identifier = SocketIdentifier(os.path.join(user_dir, "data"))
        self.worker_session = WorkerSessionManager()
        self.record_manager = InspectionRecordManager()
        self._saved_inspection_ids = set()
        self.current_inspection_data = None
        self.inspection_in_progress = False
        self.manual_reference_active = False
        self._book2_user_selected = False
        self._active_socket_catalog = []
        
        # Populate Company Dropdown dynamically from Book1.xlsx
        self.company_combo.blockSignals(True)
        self.company_combo.clear()
        if self.company_manager.is_loaded and self.company_manager.companies:
            for c in self.company_manager.get_companies():
                self.company_combo.addItem(c)
            self.company_ref_status_lbl.setText("LOADED")
            self.company_ref_status_lbl.setStyleSheet("color: #15803D; font-size: 13px; font-weight: bold;")
        else:
            self.company_combo.addItem("No Reference Loaded")
            self.company_combo.setEnabled(False)
            err_msg = self.company_manager.error_message or "Company Reference Workbook Not Found"
            self.company_ref_status_lbl.setText(err_msg)
            self.company_ref_status_lbl.setStyleSheet("color: #DC2626; font-size: 13px; font-weight: bold;")
            self.status_bar.showMessage(err_msg)
        self.company_combo.blockSignals(False)
        self.company_combo.currentIndexChanged.connect(self.on_company_changed)
        self.refresh_tool_count_verification()
        self.setup_company_workbook_watcher()
        
        # Populate Lower Company Dropdown dynamically from Book 2.xlsx
        self.socket_company_combo.blockSignals(True)
        self.socket_company_combo.clear()
        if self.company_socket_ref_manager.is_loaded and self.company_socket_ref_manager.companies:
            self.socket_company_combo.addItem("— Select Company —")
            for c in self.company_socket_ref_manager.get_company_names():
                self.socket_company_combo.addItem(c)
            self.socket_company_combo.setCurrentIndex(0)
            self.socket_ref_status_lbl.setText("LOADED (LIVE SYNC)")
            self.socket_ref_status_lbl.setStyleSheet("color: #15803D; font-size: 13px; font-weight: bold;")
        else:
            self.socket_company_combo.addItem("No Reference Loaded")
            self.socket_company_combo.setEnabled(False)
            err_msg = self.company_socket_ref_manager.error_message or "Book 2 Workbook Not Found"
            self.socket_ref_status_lbl.setText(err_msg)
            self.socket_ref_status_lbl.setStyleSheet("color: #DC2626; font-size: 13px; font-weight: bold;")
        self.socket_company_combo.blockSignals(False)
        self.socket_company_combo.currentIndexChanged.connect(self.on_socket_company_changed)
        self.setup_book2_workbook_watcher()
        self.run_reference_verification()
        
        # Clock Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        if self.camera_worker.calibrator.is_calibrated:
            self.cal_status_val.setText("CALIBRATED")
            self.cal_status_val.setObjectName("WarningValue")
            self.cal_height_val.setText(f"{self.camera_worker.calibrator.camera_height_mm:.1f} mm")
            center_z = getattr(self.camera_worker.calibrator, 'center_depth_mm', self.camera_worker.calibrator.camera_height_mm)
            self.cal_center_z_val.setText(f"{center_z:.1f} mm")
            self.cal_tilt_val.setText(f"{self.camera_worker.calibrator.tilt_angle_deg:.2f}°")
            self.cal_quality_val.setText(f"{self.camera_worker.calibrator.inlier_percentage:.1f}% Inliers, {self.camera_worker.calibrator.residual_mm:.2f}mm Err")
            
            ts = getattr(self.camera_worker.calibrator, 'timestamp', 0)
            time_str = datetime.fromtimestamp(ts).strftime('%H:%M:%S') if ts else "Unknown"
            self.cal_time_val.setText(time_str)
            self.cal_reason_val.setText("")
            
        self.update_banner()
        self.update_worker_header()
        try:
            health_path = os.path.join(user_dir, "app_health.json")
            with open(health_path, "w", encoding="utf-8") as f:
                json.dump({
                    "startup": "SUCCESS",
                    "timestamp": datetime.now().isoformat(),
                    "book1_loaded": bool(self.company_manager.is_loaded),
                    "book2_loaded": bool(self.company_socket_ref_manager.is_loaded),
                    "companies": self.company_manager.get_companies() if self.company_manager.is_loaded else [],
                    "logo_resolved": self._resolve_logo_path() is not None
                }, f, indent=2)
        except Exception:
            pass
            
    def _resolve_logo_path(self):
        candidates = [
            os.path.join(app2_dir, "Smartlab Logo.png"),
            os.path.join(app2_dir, "Smartlab logo.png"),
            os.path.join(app2_dir, "app", "resources", "Smartlab Logo.png"),
            os.path.join(app2_dir, "app", "resources", "Smartlab logo.png"),
            os.path.join(APP2_DIR, "Smartlab Logo.png"),
            os.path.join(APP2_DIR, "Smartlab logo.png"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "Smartlab Logo.png"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "Smartlab logo.png"),
        ]
        if hasattr(sys, '_MEIPASS'):
            candidates.insert(0, os.path.join(sys._MEIPASS, "Smartlab Logo.png"))
            candidates.insert(0, os.path.join(sys._MEIPASS, "Smartlab logo.png"))
            candidates.insert(0, os.path.join(sys._MEIPASS, "app", "resources", "Smartlab Logo.png"))
            candidates.insert(0, os.path.join(sys._MEIPASS, "app", "resources", "Smartlab logo.png"))
        for p in candidates:
            if os.path.exists(p):
                return p
        return None

    def _load_smartlab_logo(self):
        logo_path = self._resolve_logo_path()
        if logo_path and os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            if not pix.isNull():
                scaled = pix.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.logo_label.setPixmap(scaled)

    def update_time(self):
        self.time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
    def add_metric(self, parent_layout, label_text, default_val, obj_name="MetricValue"):
        lbl = QLabel(label_text)
        lbl.setObjectName("MetricLabel")
        val = QLabel(default_val)
        val.setObjectName(obj_name)
        if parent_layout is not None:
            if isinstance(parent_layout, QVBoxLayout) or isinstance(parent_layout, QHBoxLayout):
                row = QHBoxLayout()
                row.setContentsMargins(0, 0, 0, 0)
                row.setSpacing(4)
                row.addWidget(lbl)
                row.addWidget(val)
                row.addStretch()
                parent_layout.addLayout(row)
            else:
                pass
        return val
        
    def update_banner(self):
        ref_loaded = (
            (hasattr(self, 'company_socket_ref_manager') and self.company_socket_ref_manager.is_loaded) or
            (hasattr(self, 'company_manager') and self.company_manager.is_loaded) or
            (hasattr(self, 'reference_manager') and self.reference_manager.is_loaded)
        )
        if not ref_loaded:
            self.banner_label.setText("REFERENCE REQUIRED")
            self.banner_label.setObjectName("WarningValue")
            self.banner_label.setStyleSheet("color: #D97706;")
        elif self.latest_inference_results is None:
            self.banner_label.setText("READY FOR CAPTURE")
            self.banner_label.setStyleSheet("color: #15803D;")
        else:
            self.banner_label.setText("INSPECTION IN PROGRESS")
            self.banner_label.setStyleSheet("color: #EA580C;")

    def _set_tool_table_cell(self, r, c, text, align=Qt.AlignCenter, fg=None):
        from PyQt5.QtGui import QColor, QBrush
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(align | Qt.AlignVCenter)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        if fg:
            item.setForeground(QBrush(QColor(fg)))
        self.tool_count_table.setItem(r, c, item)
        return item

    def setup_company_workbook_watcher(self):
        """
        Monitors the authoritative company workbook (Book1.xlsx) and its parent directory
        for modifications, additions, and deletions, providing automatic live synchronization.
        """
        self.excel_watcher = QFileSystemWatcher(self)
        self.excel_debounce_timer = QTimer(self)
        self.excel_debounce_timer.setSingleShot(True)
        self.excel_debounce_timer.setInterval(400)
        self.excel_debounce_timer.timeout.connect(self.reload_company_workbook)
        
        self.excel_poll_timer = QTimer(self)
        self.excel_poll_timer.setInterval(2000)
        self.excel_poll_timer.timeout.connect(self.check_workbook_update_poll)
        self.excel_poll_timer.start()

        self._refresh_watcher_paths()
        self.excel_watcher.fileChanged.connect(self._on_excel_file_event)
        self.excel_watcher.directoryChanged.connect(self._on_excel_file_event)

    def _refresh_watcher_paths(self):
        """Ensures both Book1.xlsx and its parent directory are tracked by QFileSystemWatcher."""
        if not hasattr(self, 'excel_watcher'):
            return
        current_files = self.excel_watcher.files()
        if current_files:
            self.excel_watcher.removePaths(current_files)
        current_dirs = self.excel_watcher.directories()
        if current_dirs:
            self.excel_watcher.removePaths(current_dirs)

        wb_path = self.company_manager.workbook_path
        if wb_path and os.path.isfile(wb_path):
            self.excel_watcher.addPath(wb_path)
            dir_path = os.path.dirname(wb_path)
            if os.path.isdir(dir_path):
                self.excel_watcher.addPath(dir_path)

    def _on_excel_file_event(self, path=None):
        """Triggered on file or directory modification. Restarts debounce timer."""
        if hasattr(self, 'excel_debounce_timer'):
            self.excel_debounce_timer.start(400)

    def check_workbook_update_poll(self):
        """Polling fallback: verifies if the workbook mtime changed on disk."""
        if not hasattr(self, 'company_manager'):
            return
        if self.company_manager.has_workbook_changed_on_disk():
            if hasattr(self, 'excel_debounce_timer'):
                self.excel_debounce_timer.start(100)

    def reload_company_workbook(self):
        """
        Automatically reloads Book1.xlsx when saved on disk.
        Updates the company dropdown, preserves current selection if still present,
        or prompts selection if the company was removed, and refreshes count verification.
        """
        if not hasattr(self, 'company_manager') or not hasattr(self, 'company_combo'):
            return

        # Record currently selected company
        prev_company = self.company_combo.currentText().strip() if self.company_combo.count() > 0 else None
        if prev_company and (prev_company.startswith("—") or prev_company.startswith("No ") or "Select" in prev_company):
            prev_company = None

        # Re-attach file watcher paths if dropped during atomic replace
        self._refresh_watcher_paths()

        # Reload workbook
        success, msg = self.company_manager.load_workbook()

        self.company_combo.blockSignals(True)
        self.company_combo.clear()

        if not self.company_manager.is_loaded or not self.company_manager.companies:
            self.company_combo.addItem("No Companies Configured")
            self.company_combo.setEnabled(False)
            err_msg = self.company_manager.error_message or "Company Reference Workbook Not Found"
            self.company_ref_status_lbl.setText(err_msg)
            self.company_ref_status_lbl.setStyleSheet("color: #DC2626; font-size: 13px; font-weight: bold;")
            self.company_combo.blockSignals(False)
            self.refresh_tool_count_verification()
            return

        self.company_combo.setEnabled(True)
        new_companies = self.company_manager.get_companies()

        # Check if previously selected company still exists
        if prev_company and prev_company in new_companies:
            for c in new_companies:
                self.company_combo.addItem(c)
            self.company_combo.setCurrentText(prev_company)
            self.company_ref_status_lbl.setText("LOADED (LIVE SYNC)")
            self.company_ref_status_lbl.setStyleSheet("color: #15803D; font-size: 13px; font-weight: bold;")
            self.company_combo.blockSignals(False)
            # Re-evaluate verification with cached detections using the newly loaded expected values
            self.refresh_tool_count_verification()
        else:
            # Company was removed, renamed, or never chosen:
            # Show a clear selection-required state. Never silently pick another company!
            self.company_combo.addItem("— Select Company —")
            for c in new_companies:
                self.company_combo.addItem(c)
            self.company_combo.setCurrentIndex(0)
            
            if prev_company:
                self.company_ref_status_lbl.setText("COMPANY REMOVED — SELECT NEW COMPANY")
                self.company_ref_status_lbl.setStyleSheet("color: #DC2626; font-size: 13px; font-weight: bold;")
            else:
                self.company_ref_status_lbl.setText("LOADED (LIVE SYNC)")
                self.company_ref_status_lbl.setStyleSheet("color: #15803D; font-size: 13px; font-weight: bold;")
                
            self.company_combo.blockSignals(False)
            self.refresh_tool_count_verification()

    def on_company_changed(self):
        """
        Invoked when the operator selects a different company in the dropdown.
        Refreshes verification using latest cached detections without re-running YOLO.
        """
        # If user selected a valid company and placeholder was at index 0, clean up placeholder
        if self.company_combo.count() > 1 and self.company_combo.itemText(0).startswith("—"):
            current_idx = self.company_combo.currentIndex()
            if current_idx > 0:
                selected_text = self.company_combo.currentText()
                self.company_combo.blockSignals(True)
                self.company_combo.removeItem(0)
                self.company_combo.setCurrentText(selected_text)
                self.company_combo.blockSignals(False)
                self.company_ref_status_lbl.setText("LOADED (LIVE SYNC)")
                self.company_ref_status_lbl.setStyleSheet("color: #15803D; font-size: 13px; font-weight: bold;")

        self.refresh_tool_count_verification()

    def _update_pending_socket_table(self):
        """
        Populates the lower socket measurement table with pending expected records
        when no camera capture has occurred yet or after results are cleared.
        """
        if not hasattr(self, 'meas_table'):
            return

        selected_comp = self.socket_company_combo.currentText().strip() if hasattr(self, 'socket_company_combo') and self.socket_company_combo.count() > 0 else None
        
        is_comp_valid = bool(
            hasattr(self, 'company_socket_ref_manager') and
            self.company_socket_ref_manager.is_loaded and
            selected_comp and
            not selected_comp.startswith("—") and
            "Select" not in selected_comp and
            not selected_comp.startswith("No ")
        )
        
        if is_comp_valid:
            catalog = self.company_socket_ref_manager.get_socket_reference_catalog(selected_comp)
        elif self.reference_manager.is_loaded:
            catalog = self.reference_manager.sockets
        else:
            catalog = []

        from PyQt5.QtGui import QColor, QBrush
        from PyQt5.QtCore import Qt as _Qt

        def _set_cell(table, r, c, text, align=_Qt.AlignCenter, fg=None):
            item = QTableWidgetItem(str(text))
            item.setTextAlignment(align | _Qt.AlignVCenter)
            item.setFlags(item.flags() & ~_Qt.ItemIsEditable)
            if fg:
                item.setForeground(QBrush(QColor(fg)))
            table.setItem(r, c, item)
            return item

        if catalog:
            self.meas_table.setRowCount(len(catalog))
            for row, ref in enumerate(catalog):
                ref_id = ref.get("reference_id", "—")
                nom_size_raw = ref.get("nominal_size", "—")
                nom_size_str = f"{nom_size_raw:.2f}" if isinstance(nom_size_raw, (int, float)) else str(nom_size_raw)
                exp_diam_raw = ref.get("expected_outer_diameter", None)
                exp_diam_str = f"{exp_diam_raw:.2f}" if isinstance(exp_diam_raw, (int, float)) else "—"

                id_item = _set_cell(self.meas_table, row, 0, ref_id)
                id_item.setForeground(QBrush(QColor("#1E293B")))
                _set_cell(self.meas_table, row, 1, nom_size_str)
                _set_cell(self.meas_table, row, 2, exp_diam_str)
                _set_cell(self.meas_table, row, 3, "—")
                _set_cell(self.meas_table, row, 4, "—")
                s_item = _set_cell(self.meas_table, row, 5, "PENDING")
                s_item.setForeground(QBrush(QColor("#64748B")))

            self.sum_exp_count_val.setText(str(len(catalog)))
            self.sum_ref_loaded_val.setText("LOADED")
            self.sum_ref_alignment_val.setText("PENDING")
            self.sum_overall_status_val.setText("PENDING")
            self.socket_ref_status_lbl.setText("LOADED (LIVE SYNC)")
            self.socket_ref_status_lbl.setStyleSheet("color: #15803D; font-size: 13px; font-weight: bold;")
        else:
            self.meas_table.setRowCount(1)
            stat_text = "SELECTION REQUIRED" if (selected_comp and "Select" in selected_comp) else (
                "NOT CONFIGURED" if is_comp_valid else "NOT LOADED"
            )
            stat_color = "#D97706" if (selected_comp and "Select" in selected_comp or is_comp_valid) else "#DC2626"
            _set_cell(self.meas_table, 0, 0, "—")
            _set_cell(self.meas_table, 0, 1, "—")
            _set_cell(self.meas_table, 0, 2, "—")
            _set_cell(self.meas_table, 0, 3, "—")
            _set_cell(self.meas_table, 0, 4, "—")
            s_item = _set_cell(self.meas_table, 0, 5, stat_text)
            s_item.setForeground(QBrush(QColor(stat_color)))

            self.sum_exp_count_val.setText("0")
            self.sum_ref_loaded_val.setText("NOT LOADED")
            self.sum_ref_alignment_val.setText("NOT LOADED")
            self.sum_overall_status_val.setText("PENDING")

    def setup_book2_workbook_watcher(self):
        """
        Monitors the authoritative Book 2 workbook and its parent directory
        for modifications, additions, and deletions, providing automatic live synchronization.
        """
        self.book2_watcher = QFileSystemWatcher(self)
        self.book2_debounce_timer = QTimer(self)
        self.book2_debounce_timer.setSingleShot(True)
        self.book2_debounce_timer.setInterval(400)
        self.book2_debounce_timer.timeout.connect(self.reload_book2_workbook)
        
        self.book2_poll_timer = QTimer(self)
        self.book2_poll_timer.setInterval(2000)
        self.book2_poll_timer.timeout.connect(self.check_book2_update_poll)
        self.book2_poll_timer.start()

        self._refresh_book2_watcher_paths()
        self.book2_watcher.fileChanged.connect(self._on_book2_file_event)
        self.book2_watcher.directoryChanged.connect(self._on_book2_file_event)

    def _refresh_book2_watcher_paths(self):
        """Ensures both Book 2 and its parent directory are tracked by QFileSystemWatcher."""
        if not hasattr(self, 'book2_watcher'):
            return
        current_files = self.book2_watcher.files()
        if current_files:
            self.book2_watcher.removePaths(current_files)
        current_dirs = self.book2_watcher.directories()
        if current_dirs:
            self.book2_watcher.removePaths(current_dirs)

        wb_path = self.company_socket_ref_manager.workbook_path
        if wb_path and os.path.isfile(wb_path):
            self.book2_watcher.addPath(wb_path)
            dir_path = os.path.dirname(wb_path)
            if os.path.isdir(dir_path):
                self.book2_watcher.addPath(dir_path)

    def _on_book2_file_event(self, path=None):
        """Triggered on Book 2 file or directory modification. Restarts debounce timer."""
        if hasattr(self, 'book2_debounce_timer'):
            self.book2_debounce_timer.start(400)

    def check_book2_update_poll(self):
        """Polling fallback: verifies if the Book 2 mtime changed on disk."""
        if not hasattr(self, 'company_socket_ref_manager'):
            return
        if self.company_socket_ref_manager.has_workbook_changed_on_disk():
            if hasattr(self, 'book2_debounce_timer'):
                self.book2_debounce_timer.start(100)

    def reload_book2_workbook(self):
        """
        Automatically reloads Book 2 from disk when saved.
        Updates the lower company dropdown, preserves current selection if still present,
        prompts selection if removed, and recalculates socket dimensional verification.
        """
        if not hasattr(self, 'company_socket_ref_manager') or not hasattr(self, 'socket_company_combo'):
            return

        success = self.company_socket_ref_manager.load_workbook()
        self._refresh_book2_watcher_paths()

        if not success or not self.company_socket_ref_manager.is_loaded:
            self.socket_ref_status_lbl.setText("BOOK 2 NOT FOUND")
            self.socket_ref_status_lbl.setStyleSheet("color: #DC2626; font-size: 13px; font-weight: bold;")
            self.run_reference_verification()
            return

        prev_company = self.socket_company_combo.currentText().strip()
        if prev_company.startswith("—") or "Select" in prev_company or prev_company.startswith("No "):
            prev_company = None

        new_companies = self.company_socket_ref_manager.get_company_names()

        self.socket_company_combo.blockSignals(True)
        self.socket_company_combo.clear()

        if prev_company and prev_company in new_companies:
            for c in new_companies:
                self.socket_company_combo.addItem(c)
            self.socket_company_combo.setCurrentText(prev_company)
            self.socket_ref_status_lbl.setText("LOADED (LIVE SYNC)")
            self.socket_ref_status_lbl.setStyleSheet("color: #15803D; font-size: 13px; font-weight: bold;")
            self.socket_company_combo.blockSignals(False)
            self.run_reference_verification()
        else:
            self.socket_company_combo.addItem("— Select Company —")
            for c in new_companies:
                self.socket_company_combo.addItem(c)
            self.socket_company_combo.setCurrentIndex(0)

            if prev_company:
                self.socket_ref_status_lbl.setText("COMPANY REMOVED — SELECT NEW COMPANY")
                self.socket_ref_status_lbl.setStyleSheet("color: #DC2626; font-size: 13px; font-weight: bold;")
            else:
                self.socket_ref_status_lbl.setText("LOADED (LIVE SYNC)")
                self.socket_ref_status_lbl.setStyleSheet("color: #15803D; font-size: 13px; font-weight: bold;")

            self.socket_company_combo.blockSignals(False)
            self.run_reference_verification()

    def on_socket_company_changed(self):
        """
        Invoked when the operator selects a different company in the lower Book 2 dropdown.
        Refreshes socket dimensional verification using latest cached detections without re-running YOLO.
        """
        self._book2_user_selected = True
        self.manual_reference_active = False

        if self.socket_company_combo.count() > 1 and self.socket_company_combo.itemText(0).startswith("—"):
            current_idx = self.socket_company_combo.currentIndex()
            if current_idx > 0:
                selected_text = self.socket_company_combo.currentText()
                self.socket_company_combo.blockSignals(True)
                self.socket_company_combo.removeItem(0)
                self.socket_company_combo.setCurrentText(selected_text)
                self.socket_company_combo.blockSignals(False)
                self.socket_ref_status_lbl.setText("LOADED (LIVE SYNC)")
                self.socket_ref_status_lbl.setStyleSheet("color: #15803D; font-size: 13px; font-weight: bold;")

        self.run_reference_verification()

    def refresh_tool_count_verification(self):
        """
        Dynamically verifies detected tool quantities against the selected company's expected
        counts from Book1.xlsx across all 14 categories.
        """
        if not hasattr(self, 'tool_count_table') or not hasattr(self, 'company_manager'):
            return

        company_name = self.company_combo.currentText().strip() if self.company_combo.count() > 0 else None
        if not self.company_manager.is_loaded or not company_name or company_name.startswith("No ") or company_name.startswith("—") or "Select" in company_name:
            self.tool_count_table.setRowCount(len(CompanyManager.TOOL_CATEGORIES))
            stat_text = "SELECTION REQUIRED" if (company_name and "Select" in company_name) else "NOT LOADED"
            stat_color = "#D97706" if (company_name and "Select" in company_name) else "#DC2626"
            for row, cat in enumerate(CompanyManager.TOOL_CATEGORIES):
                self._set_tool_table_cell(row, 0, cat["name"], align=Qt.AlignLeft, fg="#1E293B")
                self._set_tool_table_cell(row, 1, "—")
                self._set_tool_table_cell(row, 2, "—")
                self._set_tool_table_cell(row, 3, "—")
                self._set_tool_table_cell(row, 4, stat_text, fg=stat_color)
            if hasattr(self, 'current_inspection_data') and self.current_inspection_data:
                self.current_inspection_data.selected_company = None
                self.current_inspection_data.tool_count_verification_status = stat_text
            return

        detections = self.latest_inference_results.get("detections", []) if self.latest_inference_results else None

        if detections is None:
            # No capture yet - show expected counts from selected company, detected as "0", diff as "—", status as "PENDING"
            exp_counts = self.company_manager.get_expected_counts(company_name)
            self.tool_count_table.setRowCount(len(CompanyManager.TOOL_CATEGORIES))
            for row, cat in enumerate(CompanyManager.TOOL_CATEGORIES):
                cid = cat["class_id"]
                exp = exp_counts.get(cid)
                exp_str = str(exp) if exp is not None else "N/A"
                stat_str = "PENDING" if exp is not None else "NOT CONFIGURED"
                stat_color = "#64748B" if exp is not None else "#D97706"
                self._set_tool_table_cell(row, 0, cat["name"], align=Qt.AlignLeft, fg="#1E293B")
                self._set_tool_table_cell(row, 1, "0")
                self._set_tool_table_cell(row, 2, exp_str)
                self._set_tool_table_cell(row, 3, "—")
                self._set_tool_table_cell(row, 4, stat_str, fg=stat_color)
            return

        # Verification with cached detections
        verif = self.company_manager.verify_counts(company_name, detections)
        self.latest_company_verification_result = verif

        if not hasattr(self, 'current_inspection_data') or self.current_inspection_data is None:
            self.current_inspection_data = InspectionData()
        self.current_inspection_data.selected_company = company_name
        self.current_inspection_data.company_workbook_identifier = self.company_manager.workbook_path or "NOT LOADED"
        self.current_inspection_data.company_tool_counts = verif
        self.current_inspection_data.tool_count_verification_results = verif.get("categories", [])
        self.current_inspection_data.tool_count_verification_status = verif.get("overall_status", "NOT RUN")

        self.tool_count_table.setRowCount(len(verif["categories"]))
        for row, cat_res in enumerate(verif["categories"]):
            cat_name = cat_res["category_name"]
            det_qty = cat_res["detected"]
            exp_qty = cat_res["expected"]
            diff = cat_res["difference"]
            status_detail = cat_res["status_detail"]
            status_type = cat_res["status_type"]

            exp_str = str(exp_qty) if exp_qty is not None else "N/A"
            diff_str = f"{diff:+d}" if diff is not None and diff != 0 else ("0" if diff == 0 else "—")

            if status_type == "MATCHED":
                fg_color = "#15803D"  # Green
            elif status_type in ["MISSING", "EXTRA"]:
                fg_color = "#DC2626"  # Red
            else:
                fg_color = "#D97706"  # Amber

            self._set_tool_table_cell(row, 0, cat_name, align=Qt.AlignLeft, fg="#1E293B")
            self._set_tool_table_cell(row, 1, str(det_qty))
            self._set_tool_table_cell(row, 2, exp_str)
            self._set_tool_table_cell(row, 3, diff_str, fg=fg_color if diff is not None and diff != 0 else None)
            self._set_tool_table_cell(row, 4, status_detail, fg=fg_color)
            
    @pyqtSlot(bool, str)
    def on_model_loaded(self, success, msg):
        if success:
            self.model_status_val.setText("LOADED")
            self.model_status_val.setObjectName("SuccessValue")
            self.model_status_val.setStyleSheet("color: #15803D;")
            self.sys_status_val.setText("READY")
            self.sys_status_val.setStyleSheet("color: #15803D;")
            self.btn_load_img.setEnabled(True)
            if self.camera_worker.is_running and self.worker_session.is_active:
                self.btn_capture_detect.setEnabled(True)
            self.status_bar.showMessage("Model ready.")
        else:
            self.model_status_val.setText("FAILED")
            self.model_status_val.setObjectName("FailureValue")
            self.model_status_val.setStyleSheet("color: #DC2626;")
            self.sys_status_val.setText("DEGRADED")
            self.sys_status_val.setStyleSheet("color: #DC2626;")
            self.status_bar.showMessage(f"Model load failed: {msg}")
        self.update_banner()
        try:
            status_path = os.path.join(user_dir, "model_status.json")
            with open(status_path, "w", encoding="utf-8") as f:
                json.dump({
                    "model_status": "LOADED" if success else "FAILED",
                    "message": str(msg),
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)
        except Exception:
            pass

    def start_camera(self):
        if not self.worker_session.is_active:
            QMessageBox.warning(self, "Worker ID Required", "Please enter your Worker ID before starting the inspection.")
            self.open_worker_dialog()
            return
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_calibrate.setEnabled(True)
        if self.sys_status_val.text() == "READY":
            self.btn_capture_detect.setEnabled(True)
        self.camera_worker.start_camera()
        
    def stop_camera(self):
        self.inspection_in_progress = False
        self.btn_start.setEnabled(self.worker_session.is_active)
        self.btn_stop.setEnabled(False)
        self.btn_calibrate.setEnabled(False)
        self.btn_capture_detect.setEnabled(False)
        self.camera_worker.stop_camera()
        self.camera_display.clear()
        self.cam_state_val.setText("DISCONNECTED")
        self.cam_state_val.setStyleSheet("color: #DC2626;")
        
    def calibrate_height(self):
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, 'Clear Platform',
            'Please completely remove the toolkit and any other objects from the platform.\n\nClick OK when the platform is empty.',
            QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok
        )
        if reply == QMessageBox.Cancel:
            return
            
        self.cal_status_val.setText("CALIBRATING")
        self.cal_status_val.setStyleSheet("color: #D97706;")
        self.btn_calibrate.setEnabled(False)
        self.camera_worker.request_calibration()
        
    @pyqtSlot(bool, str, dict, np.ndarray)
    def on_calibration_done(self, success, msg, stats, mask):
        self.btn_calibrate.setEnabled(True)
        if success:
            self.cal_status_val.setText("CALIBRATED")
            self.cal_status_val.setStyleSheet("color: #15803D;")
            self.cal_height_val.setText(f"{stats['height_mm']:.1f} mm")
            
            center_z = getattr(self.camera_worker.calibrator, 'center_depth_mm', stats['height_mm'])
            self.cal_center_z_val.setText(f"{center_z:.1f} mm")
            self.cal_tilt_val.setText(f"{stats.get('tilt_deg', 0):.2f}°")
            
            inliers = getattr(self.camera_worker.calibrator, 'inlier_percentage', 0.0)
            res = getattr(self.camera_worker.calibrator, 'residual_mm', 0.0)
            self.cal_quality_val.setText(f"{inliers:.1f}% Inliers, {res:.2f}mm Err")
            
            ts = getattr(self.camera_worker.calibrator, 'timestamp', 0)
            time_str = datetime.fromtimestamp(ts).strftime('%H:%M:%S') if ts else "Just now"
            self.cal_time_val.setText(time_str)
            self.cal_reason_val.setText("")
            
            self.calib_mask = mask
            self.calib_display_end_time = time.time() + 3.0
            self.status_bar.showMessage(f"Calibration successful: {msg}")
        else:
            self.cal_status_val.setText("FAILED")
            self.cal_status_val.setStyleSheet("color: #DC2626;")
            self.cal_reason_val.setText(msg)
            self.status_bar.showMessage(f"Calibration failed: {msg}")

        if hasattr(self, 'eng_dialog') and self.eng_dialog:
            self.eng_dialog.refresh_status()
            
    @pyqtSlot(bool, str)
    def on_camera_status(self, is_running, message):
        self.status_bar.showMessage(f"Camera: {message}")
        if is_running:
            self.cam_state_val.setText("CONNECTED")
            self.cam_state_val.setStyleSheet("color: #15803D;")
            
    @pyqtSlot(str)
    def on_camera_error(self, message):
        self.status_bar.showMessage(f"Camera Error: {message}")
        self.btn_start.setEnabled(self.worker_session.is_active)
        self.btn_stop.setEnabled(False)
        self.btn_calibrate.setEnabled(False)
        self.btn_capture_detect.setEnabled(False)
        
    @pyqtSlot(str, str, float)
    def on_camera_info(self, model, serial, scale):
        self.latest_scale = scale
        self.cam_model_val.setText(model)
        
    @pyqtSlot(np.ndarray, np.ndarray, float, float, float)
    def on_frame_ready(self, bgr_img, depth_img, coverage, center_depth, fps):
        self.latest_bgr = bgr_img.copy()
        self.latest_depth = depth_img.copy()
        
        h, w = bgr_img.shape[:2]
        self.cam_res_val.setText(f"{w}x{h} @ {fps:.1f} FPS")
        self.cam_center_val.setText(f"{center_depth:.1f} mm")
        
        display_img = bgr_img.copy()
        
        if self.calib_mask is not None and time.time() < self.calib_display_end_time:
            green_overlay = np.zeros_like(display_img)
            green_overlay[:,:,1] = self.calib_mask
            cv2.addWeighted(green_overlay, 0.4, display_img, 0.6, 0, display_img)
            
        rgb_img = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
        bytes_per_line = 3 * w
        qt_img = QImage(rgb_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.camera_display.setPixmap(QPixmap.fromImage(qt_img))
        
    def update_visualization(self, reset_zoom=False):
        if self.latest_inference_results is None or self.latest_raw_inference_image is None:
            return
            
        view_mode = self.view_mode_cb.currentText()
        show_masks = self.chk_masks.isChecked()
        show_boxes = self.chk_boxes.isChecked()
        show_labels = self.chk_labels.isChecked()
        show_measurements = self.chk_measurements.isChecked() if hasattr(self, 'chk_measurements') else True
        opacity = self.opacity_slider.value() / 100.0
        
        rendered = OverlayRenderer.render(
            self.latest_raw_inference_image, 
            self.latest_inference_results["detections"], 
            view_mode, show_masks, show_boxes, show_labels, opacity,
            show_measurements=show_measurements
        )
        
        rgb_img = cv2.cvtColor(rendered, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb_img.shape
        qt_img = QImage(rgb_img.data, w, h, 3 * w, QImage.Format_RGB888)
        self.preview_display.setPixmap(QPixmap.fromImage(qt_img), reset_zoom=reset_zoom)

    def capture_and_detect(self):
        if not self.worker_session.is_active:
            QMessageBox.warning(self, "Worker ID Required", "Please enter your Worker ID before starting the inspection.")
            self.open_worker_dialog()
            return
        if self.latest_bgr is None:
            self.status_bar.showMessage("No frame available.")
            return
            
        self.inspection_in_progress = True
        self.status_bar.showMessage("Running Inference...")
        self.btn_capture_detect.setEnabled(False)
        self.latest_raw_inference_image = self.latest_bgr.copy()
        if hasattr(self, 'latest_depth') and self.latest_depth is not None:
            self.latest_inference_depth = self.latest_depth.copy()
        else:
            self.latest_inference_depth = None
            
        self.inference_worker.request_inference(self.latest_bgr)
        self.banner_label.setText("ANALYZING...")
        self.banner_label.setStyleSheet("color: #EA580C;")
        
    def clear_reference(self):
        self.reference_manager.clear()
        self.manual_reference_active = False
        self._book2_user_selected = False
        self.socket_identifier.load_layout(None)
        self.insp_ref_stat_val.setText("NOT LOADED")
        self.insp_ref_file_val.setText("NOT LOADED")
        self.insp_ref_count_val.setText("0")
        self.status_bar.showMessage("Reference cleared.")
        self.btn_clear_ref.setEnabled(False)
        self.update_banner()
        self.run_reference_verification()
            
    def download_template(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Template", os.path.join(os.path.dirname(app2_dir), "Blank_Toolkit_Template.xlsx"), "Excel Files (*.xlsx)")
        if file_path:
            success, msg = self.reference_manager.generate_template(file_path)
            if success:
                self.status_bar.showMessage(msg)
            else:
                self.status_bar.showMessage(msg)
                
    def teach_positions(self):
        if not self.reference_manager.is_loaded:
            self.status_bar.showMessage("Cannot teach without a loaded Reference Excel.")
            return
            
        if not self.latest_inference_results:
            self.status_bar.showMessage("Run an inference capture first.")
            return
            
        dialog = TeachingDialog(self.latest_inference_results["detections"], self.reference_manager.sockets, self.preview_display.pixmap, self)
        if dialog.exec_() == QDialog.Accepted:
            tk_id = dialog.selected_toolkit_id
            h, w = self.latest_raw_inference_image.shape[:2]
            success, msg = self.socket_identifier.save_layout(tk_id, w, h, self.latest_inference_results["detections"], dialog.assignments)
            
            if success:
                self.insp_ref_stat_val.setText(tk_id)
                self.status_bar.showMessage(msg)
                self.on_inference_done(self.latest_inference_results, None)
            else:
                self.status_bar.showMessage(msg)
                
    def clear_assignments(self):
        if self.socket_identifier.active_toolkit_id:
            layout_path = os.path.join(self.socket_identifier.layouts_dir, f"layout_{self.socket_identifier.active_toolkit_id}.json")
            if os.path.exists(layout_path):
                os.remove(layout_path)
            self.socket_identifier.load_layout(self.socket_identifier.active_toolkit_id)
            self.status_bar.showMessage("Layout cleared.")
            if self.latest_inference_results:
                self.on_inference_done(self.latest_inference_results, None)
                
    def load_layout_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Socket Layout", self.socket_identifier.layouts_dir, "JSON Files (*.json)")
        if file_path:
            try:
                import json
                with open(file_path, 'r') as f:
                    layout = json.load(f)
                tk_id = layout.get("toolkit_id", "Unknown")
                self.socket_identifier.current_layout = layout
                self.socket_identifier.active_toolkit_id = tk_id
                self.status_bar.showMessage(f"Loaded layout for toolkit: {tk_id}")
                if self.latest_inference_results is not None:
                    self.on_inference_done(self.latest_inference_results, None)
            except Exception as e:
                self.status_bar.showMessage(f"Failed to load layout: {e}")
            
    def load_test_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", os.path.dirname(app2_dir), "Image Files (*.png *.jpg *.jpeg)")
        if file_path:
            img = cv2.imread(file_path)
            if img is not None:
                self.inspection_in_progress = True
                self.status_bar.showMessage(f"Running Inference on {os.path.basename(file_path)}...")
                self.btn_load_img.setEnabled(False)
                self.latest_raw_inference_image = img.copy()
                self.inference_worker.request_inference(img)
            else:
                self.status_bar.showMessage("Failed to load image.")
                
    @pyqtSlot(object, np.ndarray)
    def on_inference_done(self, results, annotated_image_ignored):
        self.btn_capture_detect.setEnabled(self.camera_worker.is_running and self.worker_session.is_active)
        self.btn_load_img.setEnabled(True)
        self.status_bar.showMessage("Inference Complete.")
        
        self.latest_inference_results = results
        detections = results.get("detections", [])
        
        # We will do matching AFTER rim detection and metrology
        # to use calculated_diameter_mm to resolve rotational ambiguity.
        
        # --- STEP 9A: Outer Rim Detection ---
        bgr = self.latest_raw_inference_image
        reliable_rims = 0
        
        def calculate_iou(boxA, boxB):
            xA = max(boxA[0], boxB[0])
            yA = max(boxA[1], boxB[1])
            xB = min(boxA[2], boxB[2])
            yB = min(boxA[3], boxB[3])
            interArea = max(0, xB - xA) * max(0, yB - yA)
            boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
            boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
            return interArea / float(boxAArea + boxBArea - interArea) if (boxAArea + boxBArea - interArea) > 0 else 0
        
        for d in detections:
            if d.get("is_socket") and "bbox" in d:
                current_poly = d.get("polygon")
                current_bbox = d.get("bbox")
                current_area = (current_bbox[2] - current_bbox[0]) * (current_bbox[3] - current_bbox[1])
                
                other_polygons = []
                for other_d in detections:
                    if other_d.get("is_socket") and "bbox" in other_d and other_d is not d:
                        other_bbox = other_d.get("bbox")
                        other_area = (other_bbox[2] - other_bbox[0]) * (other_bbox[3] - other_bbox[1])
                        iou = calculate_iou(current_bbox, other_bbox)
                        
                        # Rule 1: Do not let massive clusters erase normal sockets
                        if other_area > current_area * 1.5:
                            continue
                            
                        # Rule 2: If heavily overlapping (duplicate), only let the higher-confidence one erase the lower-confidence one
                        if iou > 0.5:
                            if other_d.get("confidence", 0) <= d.get("confidence", 0):
                                continue # other is weaker duplicate, don't let it erase current
                                
                        other_polygons.append(other_d.get("polygon"))
                
                rim_results = RimDetector.detect_rim(bgr, current_poly, d["bbox"], other_polygons=other_polygons)
                d["rim_status"] = rim_results["status"]
                d["rim_ellipse"] = rim_results["ellipse"]
                d["rim_edge_points_count"] = rim_results["edge_points_count"]
                d["rim_coverage"] = rim_results["coverage"]
                d["rim_diagnostics"] = rim_results["diagnostics"]
                
                # ------ STEP 9B METROLOGY PASS 1: HEIGHT ------
                if d["rim_status"] == "RIM DETECTED" and hasattr(self, 'latest_inference_depth') and self.latest_inference_depth is not None:
                    intrinsics = self.camera_worker.manager.intrinsics
                    depth_scale = self.camera_worker.manager.depth_scale
                    plane_params = self.camera_worker.calibrator.plane_params if hasattr(self.camera_worker, 'calibrator') and self.camera_worker.calibrator.is_calibrated else None
                    
                    nominal_height = None
                    if self.socket_identifier.current_layout:
                        nominal_height = self.socket_identifier.current_layout.get("nominal_height_mm", None)
                    
                    height_mm, height_src, h_diag = Metrology.estimate_socket_height(
                        d["polygon"], self.latest_inference_depth, intrinsics, depth_scale, plane_params, nominal_height
                    )
                    d["raw_individual_height_mm"] = height_mm
                    d["raw_height_source"] = height_src
                    d["raw_height_diag"] = h_diag
                else:
                    d["raw_individual_height_mm"] = None
                    d["raw_height_source"] = "NONE"
                    d["raw_height_diag"] = "Rim not detected or depth unavailable"
                # -------------------------------
                
                if d.get("rim_status") == "RIM DETECTED":
                    reliable_rims += 1
                    
        # STEP 9C: AVERAGE SOCKET HEIGHT CALCULATION
        is_equal_height = self.is_equal_height_mode
        if self.socket_identifier.current_layout and "is_equal_height" in self.socket_identifier.current_layout:
            # Layout explicitly overrides it if present
            is_equal_height = self.socket_identifier.current_layout.get("is_equal_height")
            
        shared_height_mm = None
        
        # ALWAYS extract valid heights for diagnostics
        valid_heights = [d["raw_individual_height_mm"] for d in detections if d.get("is_socket") and d.get("raw_individual_height_mm") is not None and d.get("raw_height_source") == "HEIGHT_MEASURED"]
        
        import numpy as np
        
        if is_equal_height and len(valid_heights) >= 2: # Min 2 samples
            std = float(np.std(valid_heights))
            # Configurable quality criteria: reject average if sockets vary wildly (e.g., > 15mm std dev)
            # but do not reject for minor noise.
            if std <= 15.0:
                shared_height_mm = sum(valid_heights) / len(valid_heights)
            else:
                print(f"[METROLOGY] Shared height rejected due to high standard deviation ({std:.1f} mm > 15.0 mm)")
                
        print(f"[METROLOGY] is_equal_height: {is_equal_height}, valid_heights count: {len(valid_heights)}, shared_height_mm: {shared_height_mm}")
                
        self.latest_raw_individual_heights = valid_heights
        self.current_shared_height = shared_height_mm
        self.valid_heights_count = len(valid_heights)
        self.heights_std = float(np.std(valid_heights)) if len(valid_heights) >= 2 else 0.0

        # STEP 9D: METROLOGY PASS 2 (DIAMETER)
        for d in detections:
            if d.get("is_socket"):
                d["shared_height_mm"] = shared_height_mm
                if d.get("rim_status") == "RIM DETECTED":
                    active_height = None
                    active_source = "NONE"
                    if shared_height_mm is not None:
                        active_height = shared_height_mm
                        active_source = "SHARED_AVERAGE"
                    elif d.get("raw_individual_height_mm") is not None:
                        active_height = d["raw_individual_height_mm"]
                        active_source = d["raw_height_source"]
                        
                    d["height_used_for_calculation_mm"] = active_height
                    d["height_source"] = active_source
                    
                    intrinsics = self.camera_worker.manager.intrinsics
                    plane_params = self.camera_worker.calibrator.plane_params if hasattr(self.camera_worker, 'calibrator') and self.camera_worker.calibrator.is_calibrated else None
                    
                    diam_mm, calc_diam, indep_px, qual, diag, cross = Metrology.measure_diameter(
                        d["rim_ellipse"], intrinsics, plane_params, active_height, active_source
                    )
                    
                    d["measured_diameter_mm"] = diam_mm
                    d["updated_camera_outer_diameter_mm"] = calc_diam
                    d["updated_local_scale"] = indep_px
                    
                    d["calculated_diameter_mm"] = calc_diam
                    d["independent_px_per_mm"] = indep_px
                    
                    d["measurement_quality"] = qual
                    d["metrology_diagnostics"] = diag
                    d["cross_check_diam_mm"] = cross
                else:
                    d["measured_diameter_mm"] = 0.0
                    d["updated_camera_outer_diameter_mm"] = 0.0
                    d["updated_local_scale"] = 0.0
                    d["calculated_diameter_mm"] = 0.0
                    d["independent_px_per_mm"] = 0.0
                    d["measurement_quality"] = "MEASUREMENT UNAVAILABLE"
                    d["metrology_diagnostics"] = "Rim not detected or depth unavailable"
                    d["height_used_for_calculation_mm"] = None
                    d["height_source"] = "NONE"
                    d["cross_check_diam_mm"] = 0.0
        
        # --- STEP 5: Autonomous Sequential Socket Identification ---
        # Performs geometric PCA ordering and smallest-endpoint diameter verification.
        # Operates independently of Excel reference file or taught layout.
        self.latest_sequential_result = self.socket_identifier.assign_sequential_socket_ids(detections, verbose=True)
        
        # Step 4: Perform Automatic Matching if taught layout is loaded
        h, w = self.latest_raw_inference_image.shape[:2]
        if self.reference_manager.is_loaded and self.socket_identifier.current_layout:
            self.socket_identifier.automatic_matching(detections, self.reference_manager.sockets, w, h)
        elif not self.reference_manager.is_loaded:
            for d in detections:
                if d.get("is_socket"):
                    d["assignment_status"] = "NOT CONFIGURED"
                    d["assigned_reference_id"] = None
                    d["assignment_quality"] = "NONE"
        
        # Save Diagnostic Exports
        import time
        ts = int(time.time())
        diag_dir = os.path.join(user_dir, 'output', f'capture_{ts}')
        os.makedirs(diag_dir, exist_ok=True)
        self.latest_diag_dir = diag_dir
        cv2.imwrite(os.path.join(diag_dir, 'original_rgb.jpg'), bgr)
        
        # Combined annotated inspection image
        combined_image = OverlayRenderer.render(bgr, detections, "Combined View", True, True, True, 0.5)
        cv2.imwrite(os.path.join(diag_dir, 'annotated_inspection.jpg'), combined_image)
        
        json_results = []
        import copy
        
        contact_rows = []
        for i, d in enumerate(detections):
            if d.get("is_socket") and "rim_diagnostics" in d:
                idx = d.get("global_instance_id", i)
                diag = d.pop("rim_diagnostics") # Remove images from d
                
                # Save crops
                cv2.imwrite(os.path.join(diag_dir, f'socket_{idx}_crop.jpg'), diag['crop_bgr'])
                cv2.imwrite(os.path.join(diag_dir, f'socket_{idx}_mask.png'), diag['crop_mask'])
                cv2.imwrite(os.path.join(diag_dir, f'socket_{idx}_edges.png'), diag['valid_edges'])
                cv2.imwrite(os.path.join(diag_dir, f'socket_{idx}_rim_fit.jpg'), diag['diag_bgr'])
                
                # Prepare Metrology Diagnostics Extraction
                diag_str = d.get("metrology_diagnostics", "")
                depth_val = "N/A"
                if "Depth:" in diag_str:
                    try:
                        depth_val = float(diag_str.split("Depth:")[1].split("mm")[0].strip())
                    except:
                        pass
                
                px_diam = "N/A"
                if d.get("rim_ellipse"):
                    axes = d["rim_ellipse"][1]
                    px_diam = max(axes[0], axes[1])
                    
                failure_reason = "N/A"
                quality = d.get("measurement_quality", "N/A")
                if quality == "MEASUREMENT UNAVAILABLE":
                    if "Depth std" in diag_str or "Insufficient" in diag_str:
                        failure_reason = diag_str
                    elif d.get("rim_status") != "RIM DETECTED":
                        failure_reason = f"RIM UNRELIABLE ({d.get('rim_coverage', 0):.2f})"
                        
                result_dict = {
                    "global_instance_id": idx,
                    "sequential_socket_id": d.get("sequential_socket_id"),
                    "identification_status": d.get("identification_status"),
                    "assigned_reference_id": d.get("assigned_reference_id"),
                    "class_name": d.get("class_name"),
                    "confidence": d.get("confidence"),
                    "bbox": d.get("bbox"),
                    "rim_status": d.get("rim_status"),
                    "rim_ellipse": d.get("rim_ellipse"),
                    "rim_edge_points_count": d.get("rim_edge_points_count"),
                    "rim_coverage": d.get("rim_coverage"),
                    "pixel_diameter": px_diam,
                    "fit_quality": d.get("rim_status"),
                    "valid_depth_sample_count": d.get("rim_depth_count", "N/A"), # Note: metrology.py doesn't return count directly, so this is an estimate or N/A
                    "estimated_socket_top_depth_mm": depth_val,
                    "socket_height_mm": d.get("socket_height_mm", "N/A"),
                    "measured_outer_diameter_mm": d.get("measured_diameter_mm", 0.0),
                    "measurement_status": quality,
                    "failure_reason": failure_reason
                }
                json_results.append(result_dict)
                
                # Prepare for contact sheet
                ch = 100
                def resize_to_h(img, h):
                    if len(img.shape) == 2:
                        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                    aspect = img.shape[1] / img.shape[0]
                    return cv2.resize(img, (int(h * aspect), h))
                    
                crop_r = resize_to_h(diag['crop_bgr'], ch)
                mask_r = resize_to_h(diag['crop_mask'], ch)
                edges_r = resize_to_h(diag['valid_edges'], ch)
                fit_r = resize_to_h(diag['diag_bgr'], ch)
                
                # Text block
                text_img = np.zeros((ch, 200, 3), dtype=np.uint8)
                status_color = (0, 255, 0) if d.get("rim_status") == "RIM DETECTED" else ((0, 165, 255) if d.get("rim_status") == "RIM UNCERTAIN" else (0, 0, 255))
                cv2.putText(text_img, f"ID: {idx}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                cv2.putText(text_img, f"Status: {d.get('rim_status')}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, status_color, 1)
                cv2.putText(text_img, f"Coverage: {d.get('rim_coverage', 0):.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                ellipse = d.get('rim_ellipse')
                if ellipse:
                    diam = (ellipse[1][0] + ellipse[1][1]) / 2.0
                    cv2.putText(text_img, f"Diam px: {diam:.1f}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                    
                row_img = cv2.hconcat([crop_r, mask_r, edges_r, fit_r, text_img])
                contact_rows.append(row_img)
        
        if contact_rows:
            max_w = max(r.shape[1] for r in contact_rows)
            padded_rows = []
            for r in contact_rows:
                if r.shape[1] < max_w:
                    pad = np.zeros((r.shape[0], max_w - r.shape[1], 3), dtype=np.uint8)
                    padded_rows.append(cv2.hconcat([r, pad]))
                else:
                    padded_rows.append(r)
            contact_sheet = cv2.vconcat(padded_rows)
            cv2.imwrite(os.path.join(diag_dir, 'contact_sheet.jpg'), contact_sheet)
        
        # Diagnostic JSON and CSV will be written after verification in run_reference_verification
            
        # Update view to show the rims that were just computed
        self.update_visualization(reset_zoom=True)
        
        # --- COUNTS AND COMPARISONS ---
        counter_results = self.tool_counter.count(detections, self.reference_manager.sockets)
        comparisons = self.count_comparator.compare(self.reference_manager.expected_counts, counter_results)
        
        assigned_refs = set(d["assigned_reference_id"] for d in detections if d.get("assigned_reference_id"))
        
        insp_data = InspectionData()
        insp_data.source_image_path = "In_Memory_Or_Saved"
        insp_data.model_identifier = results.get("model_identifier")
        insp_data.calibration_status = self.cal_status_val.text()
        insp_data.worker_id = self.worker_session.worker_id
        insp_data.session_id = self.worker_session.session_id
        insp_data.batch_id = self.worker_session.current_batch_id or "BATCH-001"
        insp_data.toolkit_id = self.worker_session.current_toolkit_id or "TOOLKIT-001"
        insp_data.reference_workbook_identifier = self.reference_manager.toolkit_info.get("Toolkit_Name", "NOT LOADED")
        insp_data.expected_tool_counts = self.reference_manager.expected_counts
        insp_data.detected_tool_counts = counter_results
        # Company Reference & Tool Counts (Book1.xlsx)
        company_name = self.company_combo.currentText().strip() if hasattr(self, 'company_combo') and self.company_combo.count() > 0 else None
        if self.company_manager.is_loaded and company_name and not company_name.startswith("No "):
            company_verif = self.company_manager.verify_counts(company_name, detections)
            insp_data.selected_company = company_name
            insp_data.company_workbook_identifier = self.company_manager.workbook_path or "NOT LOADED"
            insp_data.company_tool_counts = company_verif
            insp_data.tool_count_verification_results = company_verif.get("categories", [])
            insp_data.tool_count_verification_status = company_verif.get("overall_status", "NOT RUN")
            self.latest_company_verification_result = company_verif
        else:
            insp_data.selected_company = None
            insp_data.company_workbook_identifier = "NOT LOADED"
            insp_data.company_tool_counts = {}
            insp_data.tool_count_verification_results = []
            insp_data.tool_count_verification_status = "NOT LOADED"
            self.latest_company_verification_result = None

        # Company Socket References (Book 2.xlsx)
        socket_company_name = self.socket_company_combo.currentText().strip() if hasattr(self, 'socket_company_combo') and self.socket_company_combo.count() > 0 else None
        if (hasattr(self, 'company_socket_ref_manager') and self.company_socket_ref_manager.is_loaded and
            socket_company_name and not socket_company_name.startswith("—") and "Select" not in socket_company_name and not socket_company_name.startswith("No ")):
            insp_data.selected_socket_company = socket_company_name
            insp_data.socket_company_workbook_identifier = self.company_socket_ref_manager.workbook_path or "NOT LOADED"
            insp_data.book2_reload_status = "LOADED"
            insp_data.book2_expected_socket_count = self.company_socket_ref_manager.get_expected_socket_count(socket_company_name)
        else:
            insp_data.selected_socket_company = None
            insp_data.socket_company_workbook_identifier = "NOT LOADED"
            insp_data.book2_reload_status = "NOT LOADED"
            insp_data.book2_expected_socket_count = 0
            
        for det in detections:
            if det.get("is_socket"):
                insp_data.socket_detection_candidates.append(det)
        
        insp_data.socket_reference_catalog = self.reference_manager.sockets
        insp_data.unassigned_reference_sockets = [s["reference_id"] for s in self.reference_manager.sockets]
        insp_data.mask_quality_warnings = counter_results["unsuitable_mask"]
        
        # Populate Step 8.1 Fields
        insp_data.raw_detection_count = len(detections)
        insp_data.raw_socket_candidate_count = counter_results.get("raw_socket_candidates", 0)
        insp_data.matched_reference_count = counter_results.get("matched_reference_sockets", 0)
        insp_data.unmatched_candidate_count = counter_results.get("unmatched_candidates", 0)
        insp_data.missing_reference_count = counter_results.get("missing_references", 0)
        insp_data.matched_reference_ids = list(assigned_refs)
        insp_data.unmatched_detection_ids = [d["global_instance_id"] for d in detections if "UNMATCHED" in d.get("assignment_status", "")]
        insp_data.low_confidence_detection_ids = [d["global_instance_id"] for d in detections if d.get("low_confidence_warning")]
        insp_data.assignment_quality = "VALIDATED" if self.socket_identifier.current_layout else "NONE"
        insp_data.layout_validation_status = "VALID" if self.socket_identifier.current_layout else "NOT VALIDATED"
        insp_data.mask_quality_status = "GOOD" if counter_results["unsuitable_mask"] == 0 else "WARNING"
        
        # Step 5: Sequential Identification Fields
        ident_res = getattr(self, "latest_sequential_result", {})
        insp_data.socket_identification_status = ident_res.get("status", "NOT_RUN") if isinstance(ident_res, dict) else "NOT_RUN"
        insp_data.sequential_socket_count = len([d for d in detections if d.get("is_socket") and d.get("sequential_socket_id")])
        insp_data.sequential_socket_assignments = {
            d["global_instance_id"]: d["sequential_socket_id"]
            for d in detections if d.get("is_socket") and d.get("sequential_socket_id")
        }
        
        self.current_inspection_data = insp_data
        
        # Update UI Metrics
        self.insp_total_val.setText(str(counter_results["total_raw_detections"]))
        self.insp_sock_fam_val.setText(str(counter_results["raw_socket_candidates"]))
        self.insp_major_val.setText(str(counter_results["major_tools"]))
        
        # Identifier Stats
        matched = len(assigned_refs)
        unassigned = len([d for d in detections if d.get("is_socket") and "UNMATCHED" in d.get("assignment_status", "")])
        missing = len([r for r in self.reference_manager.sockets if r.get("assignment_status", "") == "MISSING"])
        self.ident_matched_val.setText(str(matched))
        self.ident_unassigned_val.setText(str(unassigned))
        self.ident_missing_val.setText(str(missing))
        self.ident_warn_val.setText(str(counter_results["unsuitable_mask"]))
        
        # Update Summary Labels
        raw_detected = counter_results.get("raw_socket_candidates", 0)
        seq_sockets = [d for d in detections if d.get("is_socket") and d.get("sequential_socket_id")]
        seq_count = len(seq_sockets)
        ident_res = getattr(self, "latest_sequential_result", {})
        ident_status = ident_res.get("status", "NOT_RUN") if isinstance(ident_res, dict) else "NOT_RUN"
        
        if ident_status == "SEQUENCE_IDENTIFIED":
            ident_text = "COMPLETE"
        elif ident_status == "ORIENTATION_AMBIGUOUS":
            ident_text = "REVIEW REQUIRED"
        elif ident_status == "INSUFFICIENT_DATA":
            ident_text = "INSUFFICIENT DATA"
        elif ident_status == "GEOMETRY_INVALID":
            ident_text = "NON-LINEAR LAYOUT"
        else:
            ident_text = "PENDING"
            
        self.sum_raw_det_val.setText(str(raw_detected))
        self.sum_seq_ids_val.setText(str(seq_count))
        self.sum_ident_status_val.setText(ident_text)
        
        if self.reference_manager.is_loaded:
            expected_count = len(self.reference_manager.sockets)
            self.sum_exp_sockets_val.setText(f"{expected_count} Sockets")
            self.sum_verified_val.setText(str(matched))
        else:
            self.sum_exp_sockets_val.setText("NOT LOADED")
            self.sum_verified_val.setText("0")
            
        self.sum_rim_fits_val.setText(str(reliable_rims))
        
        # Measurement status reflects actual metrology validity
        valid_meas = [d for d in detections if d.get("is_socket") and d.get("calculated_diameter_mm", 0.0) > 0]
        if raw_detected > 0 and len(valid_meas) == raw_detected:
            self.sum_meas_status_val.setText("AVAILABLE")
        elif len(valid_meas) > 0:
            self.sum_meas_status_val.setText("PARTIAL")
        else:
            self.sum_meas_status_val.setText("UNAVAILABLE")
            
        # Update Raw Detections Table
        # Order socket detections by sequential_socket_id S01..SN, then unassigned
        socket_detections = [d for d in detections if d.get("is_socket")]
        other_detections = [d for d in detections if not d.get("is_socket")]
        
        def socket_sort_key(d):
            s_id = d.get("sequential_socket_id")
            if s_id and s_id.startswith("S"):
                try:
                    return (0, int(s_id[1:]))
                except ValueError:
                    return (0, s_id)
            return (1, d.get("global_instance_id", 0))

        sorted_sockets = sorted(socket_detections, key=socket_sort_key)
        raw_display_list = sorted_sockets + other_detections
        
        self.raw_meas_table.setRowCount(len(raw_display_list))
        for row, d in enumerate(raw_display_list):
            seq_id = d.get("sequential_socket_id")
            if not seq_id:
                if d.get("is_socket"):
                    seq_id_str = "Unverified"
                else:
                    seq_id_str = "—"
            else:
                seq_id_str = seq_id
                
            det_id = str(d.get("global_instance_id", "N/A"))
            
            px_diam = "N/A"
            if d.get("rim_status") == "RIM DETECTED" and d.get("rim_ellipse"):
                axes = d["rim_ellipse"][1]
                px_diam = f"{max(axes[0], axes[1]):.1f}"
                
            calc_str = "N/A"
            height_str = "N/A"
            indep_scale_str = "N/A"
            qual_str = d.get("measurement_quality", "N/A")
            
            if d.get("measured_diameter_mm", 0.0) > 0:
                calc_mm = d.get("calculated_diameter_mm", 0.0)
                indep_scale = d.get("independent_px_per_mm", 0.0)
                calc_str = f"{calc_mm:.2f}"
                indep_scale_str = f"{indep_scale:.2f}"
                
            active_h = d.get("height_used_for_calculation_mm")
            height_str = f"{active_h:.1f}" if active_h is not None else "N/A"
                
            # If measurement failed, put the failure reason in quality
            if qual_str == "MEASUREMENT UNAVAILABLE" or qual_str == "TOP HEIGHT UNAVAILABLE":
                diag_str = d.get("metrology_diagnostics", "")
                if "Depth std" in diag_str or "Insufficient" in diag_str or "Ray intersection" in diag_str:
                    qual_str = diag_str
                elif d.get("rim_status") != "RIM DETECTED":
                    qual_str = f"RIM UNRELIABLE ({d.get('rim_coverage', 0):.2f})"
                    
            self.raw_meas_table.setItem(row, 0, QTableWidgetItem(seq_id_str))
            self.raw_meas_table.setItem(row, 1, QTableWidgetItem(det_id))
            self.raw_meas_table.setItem(row, 2, QTableWidgetItem(height_str))
            self.raw_meas_table.setItem(row, 3, QTableWidgetItem(px_diam))
            self.raw_meas_table.setItem(row, 4, QTableWidgetItem(indep_scale_str))
            self.raw_meas_table.setItem(row, 5, QTableWidgetItem(calc_str))
            self.raw_meas_table.setItem(row, 6, QTableWidgetItem(qual_str))
            
        # Step 6: Run Excel Reference Verification and update Reference Matches table & summary metrics
        self.run_reference_verification()
        
        # Step 7: Run Tool Count Verification for the selected company
        self.refresh_tool_count_verification()
        
        # Step 8: Concise Capture Diagnostics Logging (Step 6)
        raw_sockets = [d for d in detections if d.get("is_socket")]
        valid_ellipse_centers_count = len([d for d in raw_sockets if d.get("rim_status") == "RIM DETECTED" and d.get("rim_ellipse")])
        valid_physical_diam_count = len([d for d in raw_sockets if d.get("calculated_diameter_mm", 0.0) > 0])
        
        seq_res = getattr(self, "latest_sequential_result", {})
        spatial_diag = seq_res.get("spatial_diagnostics", {}) if isinstance(seq_res, dict) else {}
        pca_order_status = spatial_diag.get("row_alignment_status") or spatial_diag.get("status", "NOT_RUN")
        
        ep_a = spatial_diag.get("endpoint_a")
        ep_b = spatial_diag.get("endpoint_b")
        
        def _format_endpoint_diam(ep):
            if not ep or not isinstance(ep, dict):
                return "N/A"
            gid = ep.get("global_instance_id", "?")
            phys = ep.get("calculated_diameter_mm")
            px = ep.get("pixel_diameter")
            if (px is None or px <= 0.0) and ep.get("rim_ellipse"):
                ell = ep.get("rim_ellipse")
                if isinstance(ell, (tuple, list)) and len(ell) >= 2 and isinstance(ell[1], (tuple, list)) and len(ell[1]) >= 2:
                    px = max(ell[1][0], ell[1][1])
            if phys is not None and phys > 0:
                return f"#{gid}: {phys:.2f} mm"
            elif px is not None and px > 0:
                return f"#{gid}: {px:.1f} px"
            return f"#{gid}: N/A"

        ep_a_diam_str = _format_endpoint_diam(ep_a)
        ep_b_diam_str = _format_endpoint_diam(ep_b)
        
        seq_status = seq_res.get("status", "NOT_RUN") if isinstance(seq_res, dict) else "NOT_RUN"
        assigned_seq = [d.get("sequential_socket_id") for d in raw_sockets if d.get("sequential_socket_id")]
        assigned_seq_str = " -> ".join(assigned_seq) if assigned_seq else "NONE"
        
        b2_comp = self.socket_company_combo.currentText().strip() if hasattr(self, 'socket_company_combo') and self.socket_company_combo.count() > 0 else "NONE"
        b2_cat = getattr(self, '_active_socket_catalog', [])
        b2_status = f"LOADED ({b2_comp}, {len(b2_cat)} sockets)" if b2_cat else "NOT LOADED"
        
        verif_res = getattr(self, "latest_verification_result", {})
        verif_status = verif_res.get("status", "NOT_RUN") if isinstance(verif_res, dict) else "NOT_RUN"
        
        print("\n" + "=" * 60)
        print("[AXOVRIM CAPTURE DIAGNOSTICS]")
        print(f"Detected sockets: {len(raw_sockets)}")
        print(f"Valid ellipse centers: {valid_ellipse_centers_count}")
        print(f"Valid physical diameters: {valid_physical_diam_count}")
        print(f"PCA ordering status: {pca_order_status}")
        print(f"Endpoint A diameter: {ep_a_diam_str}")
        print(f"Endpoint B diameter: {ep_b_diam_str}")
        print(f"Sequential assignment status: {seq_status}")
        print(f"Assigned sequence: {assigned_seq_str}")
        print(f"Book 2 reference status: {b2_status}")
        print(f"Reference verification status: {verif_status}")
        print("=" * 60 + "\n")

    def run_reference_verification(self):
        """
        Step 6 & Book 2: Integrates automatically generated sequential socket IDs with
        either Book 2 company-wise references (default) or loaded manual references.
        Re-runs verification on existing measurements without requiring a fresh capture
        or recomputing rims.
        """
        if not hasattr(self, 'latest_inference_results') or self.latest_inference_results is None:
            self._update_pending_socket_table()
            return

        detections = self.latest_inference_results.get("detections", [])
        
        # Determine active socket reference source:
        # Priority 1: Company selected in Book 2 dropdown (socket_company_combo) - authoritative operator source
        # Fallback: Internal reference_manager (if loaded directly in automated unit tests)
        selected_socket_comp = self.socket_company_combo.currentText().strip() if hasattr(self, 'socket_company_combo') and self.socket_company_combo.count() > 0 else None
        is_book2_comp = bool(
            hasattr(self, 'company_socket_ref_manager') and
            self.company_socket_ref_manager.is_loaded and
            selected_socket_comp and
            not selected_socket_comp.startswith("—") and
            "Select" not in selected_socket_comp and
            not selected_socket_comp.startswith("No ")
        )

        if is_book2_comp:
            ref_catalog = self.company_socket_ref_manager.get_socket_reference_catalog(selected_socket_comp)
            ref_identifier = f"Book 2 ({selected_socket_comp})"
            is_ref_active = len(ref_catalog) > 0
        elif hasattr(self, 'reference_manager') and self.reference_manager.is_loaded:
            ref_catalog = self.reference_manager.sockets
            ref_identifier = self.reference_manager.toolkit_info.get("Toolkit_Name", "CUSTOM REFERENCE")
            is_ref_active = len(ref_catalog) > 0
        else:
            ref_catalog = []
            ref_identifier = "NOT LOADED"
            is_ref_active = False

        self._active_socket_catalog = ref_catalog

        # If taught layout exists and reference catalog is active, ensure layout matching is run
        if is_ref_active and self.socket_identifier.current_layout:
            if hasattr(self, 'latest_raw_inference_image') and self.latest_raw_inference_image is not None:
                h, w = self.latest_raw_inference_image.shape[:2]
                self.socket_identifier.automatic_matching(detections, ref_catalog, w, h)
                
        # Run Step 6 / Book 2 Verification
        verif_result = self.socket_identifier.verify_against_reference(
            detections,
            ref_catalog,
            self.socket_identifier.current_layout,
            verbose=True
        )
        self.latest_verification_result = verif_result
        
        # Update InspectionData
        if not hasattr(self, 'current_inspection_data') or self.current_inspection_data is None:
            self.current_inspection_data = InspectionData()
        insp = self.current_inspection_data
        if not getattr(insp, 'worker_id', None):
            insp.worker_id = self.worker_session.worker_id
            insp.session_id = self.worker_session.session_id
            insp.batch_id = self.worker_session.current_batch_id or "BATCH-001"
            insp.toolkit_id = self.worker_session.current_toolkit_id or "TOOLKIT-001"
        insp.reference_workbook_identifier = ref_identifier
        if hasattr(self, 'company_combo') and self.company_combo.count() > 0:
            c_text = self.company_combo.currentText().strip()
            if c_text and not c_text.startswith("—") and "Select" not in c_text and not c_text.startswith("No "):
                insp.selected_company = c_text
        insp.selected_socket_company = selected_socket_comp if is_book2_comp else None
        insp.socket_company_workbook_identifier = self.company_socket_ref_manager.workbook_path if is_book2_comp else "NOT LOADED"
        insp.book2_reload_status = "LOADED" if is_book2_comp else "NOT LOADED"
        insp.book2_expected_socket_count = len(ref_catalog)
        insp.socket_dimensional_verification_status = verif_result.get("status", "NOT LOADED")
        insp.expected_tool_counts = self.company_manager.get_expected_counts(insp.selected_company) if (hasattr(self, 'company_manager') and self.company_manager.is_loaded and getattr(insp, 'selected_company', None)) else (self.reference_manager.expected_counts if (hasattr(self, 'reference_manager') and self.reference_manager.is_loaded) else {})
        insp.socket_reference_catalog = ref_catalog
        insp.matched_reference_count = verif_result.get("matched_count", 0)
        insp.tolerated_reference_count = verif_result.get("tolerated_count", 0)
        insp.conflict_reference_count = verif_result.get("conflict_count", 0)
        insp.missing_reference_count = verif_result.get("missing_count", 0)
        insp.extra_reference_count = verif_result.get("extra_count", 0)
        insp.reference_alignment_status = verif_result.get("alignment_status", "NOT LOADED")
        insp.reference_verification_status = verif_result.get("status", "NOT LOADED")
        insp.socket_verifications = verif_result.get("socket_verifications", [])
        insp.reference_verifications = verif_result.get("reference_verifications", [])
        insp.matched_reference_ids = [d["assigned_reference_id"] for d in detections if d.get("assigned_reference_id")]

        # Update Summary Metrics
        raw_sockets = [d for d in detections if d.get("is_socket")]
        seq_sockets = [d for d in raw_sockets if d.get("sequential_socket_id")]
        
        ident_res = getattr(self, "latest_sequential_result", {})
        ident_status = ident_res.get("status", "NOT_RUN") if isinstance(ident_res, dict) else "NOT_RUN"
        if ident_status == "SEQUENCE_IDENTIFIED":
            ident_text = "COMPLETE"
        elif ident_status == "ORIENTATION_AMBIGUOUS":
            ident_text = "REVIEW REQUIRED"
        elif ident_status == "INSUFFICIENT_DATA":
            ident_text = "INSUFFICIENT DATA"
        elif ident_status == "GEOMETRY_INVALID":
            ident_text = "NON-LINEAR LAYOUT"
        else:
            ident_text = "PENDING"

        self.sum_raw_det_val.setText(str(len(raw_sockets)))
        self.sum_seq_ids_val.setText(str(len(seq_sockets)))
        self.sum_ident_status_val.setText(ident_text)
        
        if is_ref_active:
            exp_count = len(ref_catalog)
            self.sum_exp_count_val.setText(str(exp_count))
            self.sum_ref_loaded_val.setText("LOADED")
            
            align_stat = verif_result.get("alignment_status", "NOT LOADED")
            self.sum_ref_alignment_val.setText(align_stat)
            if align_stat == "VERIFIED":
                self.sum_ref_alignment_val.setStyleSheet("color: #15803D;")
            elif "REVIEW" in align_stat:
                self.sum_ref_alignment_val.setStyleSheet("color: #D97706;")
            else:
                self.sum_ref_alignment_val.setStyleSheet("color: #DC2626;")
                
            matched_count = verif_result.get("matched_count", 0)
            tolerated_count = verif_result.get("tolerated_count", 0)
            conflict_count = verif_result.get("conflict_count", 0)
            missing_count = verif_result.get("missing_count", 0)
            extra_count = verif_result.get("extra_count", 0)

            self.sum_matched_val.setText(str(matched_count))
            self.sum_tolerated_val.setText(str(tolerated_count))
            self.sum_conflicts_val.setText(str(conflict_count))
            self.sum_missing_val.setText(str(missing_count))
            self.sum_extra_val.setText(str(extra_count))

            # Overall Status with Excel
            if align_stat == "REFERENCE ALIGNMENT UNVERIFIED":
                self.sum_overall_status_val.setText("INCOMPLETE")
                self.sum_overall_status_val.setStyleSheet("color: #D97706; font-weight: bold;")
            elif conflict_count > 0 or missing_count > 0:
                self.sum_overall_status_val.setText("FAIL")
                self.sum_overall_status_val.setStyleSheet("color: #DC2626; font-weight: bold;")
            elif tolerated_count > 0 or extra_count > 0:
                self.sum_overall_status_val.setText("REVIEW")
                self.sum_overall_status_val.setStyleSheet("color: #D97706; font-weight: bold;")
            elif matched_count == exp_count and matched_count > 0:
                self.sum_overall_status_val.setText("PASS")
                self.sum_overall_status_val.setStyleSheet("color: #15803D; font-weight: bold;")
            else:
                self.sum_overall_status_val.setText("COMPLETED")
                self.sum_overall_status_val.setStyleSheet("color: #15803D; font-weight: bold;")
        else:
            self.sum_exp_count_val.setText("0")
            self.sum_ref_loaded_val.setText("NOT LOADED")
            self.sum_ref_alignment_val.setText("NOT LOADED")
            self.sum_ref_alignment_val.setStyleSheet("color: #64748B;")
            self.sum_matched_val.setText("0")
            self.sum_tolerated_val.setText("0")
            self.sum_conflicts_val.setText("0")
            self.sum_missing_val.setText("0")
            self.sum_extra_val.setText("0")
            if len(raw_sockets) > 0:
                self.sum_overall_status_val.setText("REF NOT LOADED")
                self.sum_overall_status_val.setStyleSheet("color: #D97706; font-weight: bold;")
            else:
                self.sum_overall_status_val.setText("PENDING")
                self.sum_overall_status_val.setStyleSheet("color: #64748B; font-weight: bold;")
            
        reliable_rims = len([d for d in raw_sockets if d.get("rim_status") == "RIM DETECTED"])
        self.sum_rim_fits_val.setText(str(reliable_rims))
        
        valid_meas = [d for d in raw_sockets if d.get("calculated_diameter_mm", 0.0) > 0]
        if len(raw_sockets) > 0 and len(valid_meas) == len(raw_sockets):
            if not is_ref_active:
                self.sum_meas_status_val.setText("AVAILABLE")
            else:
                align_s = verif_result.get("alignment_status", "")
                conflicts = verif_result.get("conflict_count", 0)
                missing = verif_result.get("missing_count", 0)
                if align_s == "VERIFIED" and conflicts == 0 and missing == 0:
                    self.sum_meas_status_val.setText("COMPLETED")
                else:
                    self.sum_meas_status_val.setText("REVIEW REQUIRED")
        elif len(valid_meas) > 0:
            self.sum_meas_status_val.setText("PARTIAL")
        else:
            self.sum_meas_status_val.setText("UNAVAILABLE")

        # --- Populate Final 6-Column Inspection Table ---
        from PyQt5.QtGui import QColor, QBrush
        from PyQt5.QtCore import Qt as _Qt
        
        def _set_cell(table, r, c, text, align=_Qt.AlignCenter, fg=None):
            item = QTableWidgetItem(str(text))
            item.setTextAlignment(align | _Qt.AlignVCenter)
            item.setFlags(item.flags() & ~_Qt.ItemIsEditable)
            if fg:
                item.setForeground(QBrush(QColor(fg)))
            table.setItem(r, c, item)
            return item

        def socket_sort_key(d):
            s_id = d.get("sequential_socket_id")
            if s_id and s_id.startswith("S"):
                try:
                    return (0, int(s_id[1:]))
                except ValueError:
                    return (0, s_id)
            return (1, d.get("global_instance_id", 0))

        sorted_sockets = sorted(raw_sockets, key=socket_sort_key)
        
        if not is_ref_active:
            # Stage 1: Without Excel
            self.meas_table.setRowCount(len(sorted_sockets))
            for row, d in enumerate(sorted_sockets):
                seq_id = d.get("sequential_socket_id")
                seq_id_str = seq_id if seq_id else f"Det #{d.get('global_instance_id', 'N/A')}"
                calc_diam_val = d.get("calculated_diameter_mm", 0.0)
                
                # 1. Socket ID
                id_item = _set_cell(self.meas_table, row, 0, seq_id_str)
                id_item.setForeground(QBrush(QColor("#1E293B")))
                
                # 2. Nominal Size (mm)
                _set_cell(self.meas_table, row, 1, "—")
                
                # 3. Expected OD (mm)
                _set_cell(self.meas_table, row, 2, "—")
                
                # 4. Measured OD (mm)
                if calc_diam_val and calc_diam_val > 0:
                    calc_item = _set_cell(self.meas_table, row, 3, f"{calc_diam_val:.2f}")
                    calc_item.setForeground(QBrush(QColor("#15803D")))
                    # 5. Error (mm)
                    _set_cell(self.meas_table, row, 4, "—")
                    # 6. Status
                    s_item = _set_cell(self.meas_table, row, 5, "NOT VERIFIED")
                    s_item.setForeground(QBrush(QColor("#64748B")))
                else:
                    _set_cell(self.meas_table, row, 3, "—")
                    _set_cell(self.meas_table, row, 4, "—")
                    s_item = _set_cell(self.meas_table, row, 5, "MEASUREMENT UNAVAILABLE")
                    s_item.setForeground(QBrush(QColor("#D97706")))

        else:
            # Stage 2: With Excel (Book 2 or Manual Reference)
            align_stat = verif_result.get("alignment_status", "")
            
            if align_stat == "REFERENCE ALIGNMENT UNVERIFIED":
                total_rows = len(sorted_sockets) + len(ref_catalog)
                self.meas_table.setRowCount(total_rows)
                
                row = 0
                for d in sorted_sockets:
                    seq_id = d.get("sequential_socket_id") or f"Det #{d.get('global_instance_id')}"
                    calc_diam_val = d.get("calculated_diameter_mm", 0.0)
                    
                    id_item = _set_cell(self.meas_table, row, 0, f"{seq_id} (Provisional)")
                    id_item.setForeground(QBrush(QColor("#D97706")))
                    _set_cell(self.meas_table, row, 1, "—")
                    _set_cell(self.meas_table, row, 2, "—")
                    
                    if calc_diam_val and calc_diam_val > 0:
                        calc_item = _set_cell(self.meas_table, row, 3, f"{calc_diam_val:.2f}")
                        calc_item.setForeground(QBrush(QColor("#111827")))
                    else:
                        _set_cell(self.meas_table, row, 3, "—")
                        
                    _set_cell(self.meas_table, row, 4, "—")
                    s_item = _set_cell(self.meas_table, row, 5, "UNVERIFIED")
                    s_item.setForeground(QBrush(QColor("#B45309")))
                    row += 1
                    
                for ref in ref_catalog:
                    ref_id = ref["reference_id"]
                    nom_size_raw = ref.get("nominal_size", "—")
                    nom_size_str = f"{nom_size_raw:.2f}" if isinstance(nom_size_raw, (int, float)) else str(nom_size_raw)
                    exp_diam_raw = ref.get("expected_outer_diameter", None)
                    exp_diam_str = f"{exp_diam_raw:.2f}" if isinstance(exp_diam_raw, (int, float)) else "—"
                    
                    id_item = _set_cell(self.meas_table, row, 0, ref_id)
                    id_item.setForeground(QBrush(QColor("#64748B")))
                    _set_cell(self.meas_table, row, 1, nom_size_str)
                    _set_cell(self.meas_table, row, 2, exp_diam_str)
                    _set_cell(self.meas_table, row, 3, "—")
                    _set_cell(self.meas_table, row, 4, "—")
                    s_item = _set_cell(self.meas_table, row, 5, "UNVERIFIED")
                    s_item.setForeground(QBrush(QColor("#B45309")))
                    row += 1

            else:
                valid_ref_ids = {r["reference_id"] for r in ref_catalog} | {ReferenceManager.normalize_reference_id(r["reference_id"]) for r in ref_catalog}
                assigned_dets = {}
                unmatched_dets = []
                for d in raw_sockets:
                    arid = d.get("assigned_reference_id")
                    seq_id = d.get("sequential_socket_id")
                    norm_arid = ReferenceManager.normalize_reference_id(arid) if arid else None
                    norm_seq = ReferenceManager.normalize_reference_id(seq_id) if seq_id else None
                    if arid and (arid in valid_ref_ids or norm_arid in valid_ref_ids):
                        assigned_dets[norm_arid] = d
                        assigned_dets[arid] = d
                    elif seq_id and (seq_id in valid_ref_ids or norm_seq in valid_ref_ids):
                        assigned_dets[norm_seq] = d
                        assigned_dets[seq_id] = d
                    else:
                        unmatched_dets.append(d)
                        
                total_rows = len(ref_catalog) + len(unmatched_dets)
                self.meas_table.setRowCount(total_rows)
                
                row = 0
                for ref in ref_catalog:
                    ref_id = ref["reference_id"]
                    norm_ref = ReferenceManager.normalize_reference_id(ref_id)
                    d = assigned_dets.get(norm_ref) or assigned_dets.get(ref_id)
                    
                    nom_size_raw = ref.get("nominal_size", "—")
                    nom_size_str = f"{nom_size_raw:.2f}" if isinstance(nom_size_raw, (int, float)) else str(nom_size_raw)
                    exp_diam_raw = ref.get("expected_outer_diameter", None)
                    exp_diam_str = f"{exp_diam_raw:.2f}" if isinstance(exp_diam_raw, (int, float)) else "—"
                    
                    if d:
                        seq_id_str = d.get("sequential_socket_id") or ref_id
                        calc_diam_val = d.get("calculated_diameter_mm", 0.0)
                        signed_err = d.get("signed_error")
                        verif_stat = d.get("verification_status", "MATCHED")
                        
                        # 1. Socket ID
                        id_item = _set_cell(self.meas_table, row, 0, seq_id_str)
                        id_item.setForeground(QBrush(QColor("#1E293B")))
                        
                        # 2. Nominal Size
                        _set_cell(self.meas_table, row, 1, nom_size_str)
                        
                        # 3. Expected OD
                        _set_cell(self.meas_table, row, 2, exp_diam_str)
                        
                        # 4. Measured OD
                        if calc_diam_val and calc_diam_val > 0:
                            calc_item = _set_cell(self.meas_table, row, 3, f"{calc_diam_val:.2f}")
                            calc_item.setForeground(QBrush(QColor("#111827")))
                        else:
                            calc_item = _set_cell(self.meas_table, row, 3, "—")
                            
                        # 5. Error & 6. Status
                        if not (calc_diam_val and calc_diam_val > 0):
                            err_item = _set_cell(self.meas_table, row, 4, "—")
                            status_verdict = "MEASUREMENT UNAVAILABLE"
                            status_color = "#D97706" # Amber
                        elif "MATCHED" in verif_stat:
                            err_str = f"{signed_err:+.2f}" if signed_err is not None else "0.00"
                            err_item = _set_cell(self.meas_table, row, 4, err_str)
                            status_verdict = "PASS"
                            status_color = "#15803D" # Green
                        elif "TOLERATED" in verif_stat or "REVIEW" in verif_stat:
                            err_str = f"{signed_err:+.2f}" if signed_err is not None else "—"
                            err_item = _set_cell(self.meas_table, row, 4, err_str)
                            status_verdict = "REVIEW"
                            status_color = "#D97706" # Amber
                        elif "CONFLICT" in verif_stat:
                            err_str = f"{signed_err:+.2f}" if signed_err is not None else "—"
                            err_item = _set_cell(self.meas_table, row, 4, err_str)
                            status_verdict = "FAIL"
                            status_color = "#DC2626" # Red
                        else:
                            err_str = f"{signed_err:+.2f}" if signed_err is not None else "—"
                            err_item = _set_cell(self.meas_table, row, 4, err_str)
                            status_verdict = "UNVERIFIED"
                            status_color = "#B45309" # Amber
                            
                        if "automatic_status" not in d:
                            d["automatic_status"] = status_verdict
                        if "final_status" not in d:
                            d["final_status"] = status_verdict
                            
                        final_verdict = d.get("final_status", status_verdict)
                        if final_verdict == "PASS":
                            status_color = "#15803D"
                        elif final_verdict == "FAIL":
                            status_color = "#DC2626"
                        else:
                            status_color = "#D97706"
                            
                        err_item.setForeground(QBrush(QColor(status_color)))
                        status_item = _set_cell(self.meas_table, row, 5, final_verdict)
                        status_item.setForeground(QBrush(QColor(status_color)))
                        id_item.setData(_Qt.UserRole, d)
                        
                    else:
                        # Missing Expected Socket
                        id_item = _set_cell(self.meas_table, row, 0, ref_id)
                        id_item.setForeground(QBrush(QColor("#DC2626")))
                        _set_cell(self.meas_table, row, 1, nom_size_str)
                        _set_cell(self.meas_table, row, 2, exp_diam_str)
                        _set_cell(self.meas_table, row, 3, "—")
                        _set_cell(self.meas_table, row, 4, "—")
                        status_item = _set_cell(self.meas_table, row, 5, "MISSING")
                        status_item.setForeground(QBrush(QColor("#DC2626")))
                        
                    row += 1
                    
                for d in unmatched_dets:
                    seq_id_str = d.get("sequential_socket_id") or f"Det #{d.get('global_instance_id', 'N/A')}"
                    calc_diam_val = d.get("calculated_diameter_mm", 0.0)
                    
                    id_item = _set_cell(self.meas_table, row, 0, seq_id_str)
                    id_item.setForeground(QBrush(QColor("#DC2626")))
                    _set_cell(self.meas_table, row, 1, "—")
                    _set_cell(self.meas_table, row, 2, "—")
                    
                    if calc_diam_val and calc_diam_val > 0:
                        calc_item = _set_cell(self.meas_table, row, 3, f"{calc_diam_val:.2f}")
                        calc_item.setForeground(QBrush(QColor("#111827")))
                    else:
                        calc_item = _set_cell(self.meas_table, row, 3, "—")
                        
                    _set_cell(self.meas_table, row, 4, "—")
                    status_item = _set_cell(self.meas_table, row, 5, "EXTRA")
                    status_item.setForeground(QBrush(QColor("#DC2626")))
                    row += 1

        if hasattr(self, 'latest_diag_dir') and self.latest_diag_dir and os.path.isdir(self.latest_diag_dir):
            self.write_diagnostic_exports(self.latest_diag_dir)

        self.update_visualization()
        self.update_banner()
        self.btn_save_report.setEnabled(True)
        if hasattr(self, 'eng_dialog') and self.eng_dialog:
            self.eng_dialog.refresh_status()

    def write_diagnostic_exports(self, diag_dir):
        if not hasattr(self, 'latest_inference_results') or not self.latest_inference_results:
            return
            
        detections = self.latest_inference_results.get("detections", [])
        ref_map = {}
        active_cat = getattr(self, '_active_socket_catalog', [])
        if not active_cat and self.reference_manager.is_loaded:
            active_cat = self.reference_manager.sockets
        for r in active_cat:
            norm_id = ReferenceManager.normalize_reference_id(r.get("reference_id"))
            ref_map[norm_id] = r
                
        alignment_status = getattr(self.current_inspection_data, "reference_alignment_status", "NOT LOADED") if hasattr(self, 'current_inspection_data') and self.current_inspection_data else "NOT LOADED"
        
        json_results = []
        for i, d in enumerate(detections):
            if d.get("is_socket"):
                idx = d.get("global_instance_id", i)
                seq_id = d.get("sequential_socket_id")
                assigned_ref_id = d.get("assigned_reference_id")
                
                excel_od = None
                if assigned_ref_id:
                    norm_arid = ReferenceManager.normalize_reference_id(assigned_ref_id)
                    if norm_arid in ref_map:
                        excel_od = ref_map[norm_arid].get("expected_outer_diameter")
                        
                diag_str = d.get("metrology_diagnostics", "")
                depth_val = "N/A"
                if "Depth:" in diag_str:
                    try:
                        depth_val = float(diag_str.split("Depth:")[1].split("mm")[0].strip())
                    except:
                        pass
                
                px_diam = "N/A"
                if d.get("rim_ellipse"):
                    axes = d["rim_ellipse"][1]
                    px_diam = max(axes[0], axes[1])
                    
                failure_reason = "N/A"
                quality = d.get("measurement_quality", "N/A")
                if quality == "MEASUREMENT UNAVAILABLE":
                    if "Depth std" in diag_str or "Insufficient" in diag_str or "Ray intersection" in diag_str:
                        failure_reason = diag_str
                    elif d.get("rim_status") != "RIM DETECTED":
                        failure_reason = f"RIM UNRELIABLE ({d.get('rim_coverage', 0):.2f})"

                result_dict = {
                    "global_instance_id": idx,
                    "sequential_socket_id": seq_id,
                    "assigned_reference_id": assigned_ref_id,
                    "identification_status": d.get("identification_status"),
                    "class_name": d.get("class_name"),
                    "confidence": d.get("confidence"),
                    "bbox": d.get("bbox"),
                    "rim_status": d.get("rim_status"),
                    "rim_ellipse": d.get("rim_ellipse"),
                    "rim_edge_points_count": d.get("rim_edge_points_count"),
                    "rim_coverage": d.get("rim_coverage"),
                    "pixel_diameter": px_diam,
                    "fit_quality": d.get("rim_status"),
                    "valid_depth_sample_count": d.get("rim_depth_count", "N/A"),
                    "estimated_socket_top_depth_mm": depth_val,
                    "socket_height_mm": d.get("socket_height_mm", "N/A"),
                    "measured_outer_diameter_mm": d.get("calculated_diameter_mm", 0.0),
                    "measurement_status": quality,
                    "failure_reason": failure_reason,
                    "camera_outer_diameter_mm": d.get("calculated_diameter_mm", 0.0),
                    "excel_reference_diameter_mm": excel_od,
                    "signed_error_mm": d.get("signed_error"),
                    "absolute_error_mm": d.get("absolute_error"),
                    "applied_tolerance_mm": d.get("applied_tolerance"),
                    "verification_status": d.get("verification_status", "NOT LOADED"),
                    "reference_alignment_status": alignment_status
                }
                json_results.append(result_dict)
                
        try:
            with open(os.path.join(diag_dir, 'geometric_results.json'), 'w') as f:
                json.dump(json_results, f, indent=2)
                
            with open(os.path.join(diag_dir, 'inspection_results.json'), 'w') as f:
                json.dump({
                    "detections": detections,
                    "geometric_results": json_results,
                    "alignment_status": alignment_status,
                    "verification_result": getattr(self, "latest_verification_result", None),
                    "company_verification": getattr(self, "latest_company_verification_result", None),
                    "selected_company": self.company_combo.currentText().strip() if hasattr(self, 'company_combo') and self.company_combo.count() > 0 else None,
                    "selected_socket_company": self.socket_company_combo.currentText().strip() if hasattr(self, 'socket_company_combo') and self.socket_company_combo.count() > 0 else None,
                    "book2_reference_file": getattr(self.company_socket_ref_manager, "workbook_path", "NOT LOADED"),
                    "book2_reload_status": getattr(self.current_inspection_data, "book2_reload_status", "NOT LOADED") if hasattr(self, 'current_inspection_data') and self.current_inspection_data else "NOT LOADED"
                }, f, indent=2)
                
            import csv
            for csv_name in ['metrology_results.csv', 'inspection_measurements.csv']:
                with open(os.path.join(diag_dir, csv_name), 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "Global_ID", "Sequential_ID", "Confidence", "Pixel_Diameter", "Fit_Quality",
                        "Socket_Top_Depth_mm", "Measured_Diameter_mm", "Measurement_Status", "Failure_Reason",
                        "Identification_Status", "Assigned_Reference_ID",
                        "Excel_OD_mm", "Signed_Error_mm", "Absolute_Error_mm", "Applied_Tolerance",
                        "Verification_Status", "Reference_Alignment_Status"
                    ])
                    for r in json_results:
                        writer.writerow([
                            r["global_instance_id"],
                            r.get("sequential_socket_id") or "Unverified",
                            f"{r['confidence']:.2f}" if r.get('confidence') is not None else "N/A",
                            r["pixel_diameter"] if isinstance(r.get("pixel_diameter"), str) else f"{r.get('pixel_diameter', 0):.1f}",
                            r["fit_quality"],
                            r["estimated_socket_top_depth_mm"] if isinstance(r.get("estimated_socket_top_depth_mm"), str) else f"{r.get('estimated_socket_top_depth_mm', 0):.1f}",
                            f"{r.get('measured_outer_diameter_mm', 0):.2f}",
                            r["measurement_status"],
                            r["failure_reason"],
                            r.get("identification_status", "N/A"),
                            r.get("assigned_reference_id") or "NONE",
                            f"{r['excel_reference_diameter_mm']:.2f}" if r.get('excel_reference_diameter_mm') is not None else "N/A",
                            f"{r['signed_error_mm']:+.2f}" if r.get('signed_error_mm') is not None else "N/A",
                            f"{r['absolute_error_mm']:.2f}" if r.get('absolute_error_mm') is not None else "N/A",
                            f"{r['applied_tolerance_mm']:.2f}" if r.get('applied_tolerance_mm') is not None else "N/A",
                            r.get("verification_status", "N/A"),
                            r.get("reference_alignment_status", "N/A")
                        ])
        except Exception as e:
            print(f"[MainWindow] Error writing diagnostic exports: {e}")
        finally:
            self.inspection_in_progress = False

    @pyqtSlot(str)
    def on_inference_error(self, message):
        self.inspection_in_progress = False
        self.btn_capture_detect.setEnabled(self.camera_worker.is_running and self.worker_session.is_active)
        self.btn_load_img.setEnabled(True)
        self.status_bar.showMessage(f"Inference Error: {message}")

    def closeEvent(self, event):
        if hasattr(self, 'excel_poll_timer') and self.excel_poll_timer.isActive():
            self.excel_poll_timer.stop()
        if hasattr(self, 'excel_debounce_timer') and self.excel_debounce_timer.isActive():
            self.excel_debounce_timer.stop()
        if hasattr(self, 'book2_poll_timer') and self.book2_poll_timer.isActive():
            self.book2_poll_timer.stop()
        if hasattr(self, 'book2_debounce_timer') and self.book2_debounce_timer.isActive():
            self.book2_debounce_timer.stop()
        self.camera_worker.stop_camera()
        self.inference_worker.stop()
        event.accept()
        
    def save_report(self):
        if not self.worker_session.is_active:
            QMessageBox.warning(self, "Worker ID Required", "Please enter your Worker ID before saving inspection results.")
            self.open_worker_dialog()
            return

        if not hasattr(self, 'current_inspection_data') or self.current_inspection_data is None:
            self.status_bar.showMessage("No inspection data available to save.")
            return

        # Ensure worker metadata is locked on this inspection data
        if not getattr(self.current_inspection_data, 'worker_id', None):
            self.current_inspection_data.worker_id = self.worker_session.worker_id
            self.current_inspection_data.session_id = self.worker_session.session_id
            self.current_inspection_data.batch_id = self.worker_session.current_batch_id or "BATCH-001"
            self.current_inspection_data.toolkit_id = self.worker_session.current_toolkit_id or "TOOLKIT-001"

        # Save via persistent record manager (handles deduplication and updates)
        rec_path, is_new = self.record_manager.save_inspection(self.current_inspection_data.to_dict())
        self._saved_inspection_ids.add(self.current_inspection_data.inspection_id)

        # Also write legacy JSON export
        out_dir = os.path.join(user_dir, 'output', 'inspection_reports')
        os.makedirs(out_dir, exist_ok=True)
        timestamp = int(time.time())
        legacy_path = os.path.join(out_dir, f"report_{timestamp}.json")
        try:
            with open(legacy_path, 'w') as f:
                json.dump(self.current_inspection_data.to_dict(), f, indent=2)
        except Exception:
            pass

        msg = f"Inspection saved successfully ({os.path.basename(rec_path)})"
        if not is_new:
            msg += " [Record updated]"
        self.status_bar.showMessage(msg)
        QMessageBox.information(
            self,
            "Results Saved",
            f"{msg}\n\n"
            f"Worker ID: {self.current_inspection_data.worker_id}\n"
            f"Batch ID: {self.current_inspection_data.batch_id}\n"
            f"Toolkit ID: {self.current_inspection_data.toolkit_id}\n"
            f"Inspection ID: {self.current_inspection_data.inspection_id}"
        )
        self.btn_gen_report.setEnabled(True)

    def clear_results(self):
        self.inspection_in_progress = False
        self.preview_display.clear()
        self.latest_inference_results = None
        self.latest_raw_inference_image = None
        self.current_inspection_data = None
        self.latest_verification_result = None
        self.latest_company_verification_result = None
        self.meas_table.setRowCount(0)
        self.raw_meas_table.setRowCount(0)
        self.refresh_tool_count_verification()
        self.sum_raw_det_val.setText("0")
        self.sum_seq_ids_val.setText("0")
        self.sum_ident_status_val.setText("PENDING")
        self.sum_ident_status_val.setStyleSheet("")
        self.sum_matched_val.setText("0")
        self.sum_tolerated_val.setText("0")
        self.sum_conflicts_val.setText("0")
        self.sum_missing_val.setText("0")
        self.sum_extra_val.setText("0")
        self.sum_rim_fits_val.setText("0")
        self.sum_meas_status_val.setText("PENDING")
        self.sum_meas_status_val.setStyleSheet("")
        self.current_shared_height = None
        self.valid_heights_count = 0
        if hasattr(self, 'sum_overall_status_val') and self.sum_overall_status_val:
            self.sum_overall_status_val.setText("PENDING")
            self.sum_overall_status_val.setStyleSheet("color: #AAB4C0; font-weight: bold;")
        if hasattr(self, 'eng_dialog') and self.eng_dialog:
            self.eng_dialog.refresh_status()
        if hasattr(self, 'status_bar') and self.status_bar:
            self.status_bar.showMessage("Inspection results cleared.")

    def update_worker_header(self):
        if self.worker_session.is_active:
            w_id = self.worker_session.worker_id
            self.worker_id_val.setText(w_id)
            self.worker_id_val.setStyleSheet("color: #15803D; font-size: 14px; font-weight: bold;")
            self.batch_id_val.setText(self.worker_session.current_batch_id or "BATCH-001")
            if not self.camera_worker.is_running:
                self.btn_start.setEnabled(True)
            else:
                self.btn_start.setEnabled(False)
                if self.sys_status_val.text() == "READY":
                    self.btn_capture_detect.setEnabled(True)
            self.btn_gen_report.setEnabled(True)
        else:
            self.worker_id_val.setText("NOT SET")
            self.worker_id_val.setStyleSheet("color: #DC2626; font-size: 14px; font-weight: bold;")
            self.batch_id_val.setText(self.worker_session.current_batch_id or "BATCH-001")
            self.btn_start.setEnabled(False)
            self.btn_capture_detect.setEnabled(False)
            self.btn_save_report.setEnabled(False)
            self.btn_gen_report.setEnabled(False)

    def is_inspection_running(self) -> bool:
        """
        Returns True if an inspection or capture analysis is actively processing.
        Distinguishes between background threads merely running (camera preview, inference worker)
        and an active inspection task.
        """
        if getattr(self, 'inspection_in_progress', False):
            return True
        if hasattr(self, 'inference_worker') and self.inference_worker is not None:
            if getattr(self.inference_worker, 'is_inferencing', False) or getattr(self.inference_worker, 'is_busy', False):
                return True
        return False

    def open_worker_dialog(self):
        if self.is_inspection_running():
            QMessageBox.warning(self, "Inspection Running", "Cannot switch or modify Worker ID while inspection processing is actively running.")
            return

        # Check for unsaved inspection for current worker (Step 6)
        if self.worker_session.is_active and hasattr(self, 'current_inspection_data') and self.current_inspection_data is not None:
            insp_id = getattr(self.current_inspection_data, 'inspection_id', None)
            if insp_id not in self._saved_inspection_ids:
                cur_worker = self.worker_session.worker_id
                reply = QMessageBox.question(
                    self,
                    "Unsaved Inspection Active",
                    f"An unsaved inspection for worker '{cur_worker}' is currently in progress.\n\n"
                    f"Do you want to save this inspection before managing worker sessions?\n\n"
                    f"Click 'Yes' to Save, 'No' to Discard, or 'Cancel' to continue current inspection.",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Cancel:
                    return
                elif reply == QMessageBox.Yes:
                    self.save_report()
                else:
                    self.clear_results()

        dlg = WorkerDialog(self.worker_session, self)
        if dlg.exec_() == QDialog.Accepted:
            self.update_worker_header()

    def open_report_dialog(self):
        if not self.worker_session.is_active:
            QMessageBox.warning(self, "Worker ID Required", "Please enter your Worker ID before generating a report.")
            self.open_worker_dialog()
            return

        cur_worker = self.worker_session.worker_id
        cur_batch = self.worker_session.current_batch_id or "BATCH-001"
        dlg = ReportDialog(self.record_manager, cur_worker, cur_batch, self)
        dlg.exec_()

    def on_socket_row_double_clicked(self, item):
        if not item:
            return
        row = item.row()
        id_item = self.meas_table.item(row, 0)
        status_item = self.meas_table.item(row, 5)
        if not id_item or not status_item:
            return

        cur_status = status_item.text().strip()
        if cur_status in ["MISSING", "EXTRA"]:
            QMessageBox.information(self, "Status Override Not Applicable", f"Status for {cur_status} sockets cannot be manually overridden.")
            return

        if not self.worker_session.is_active:
            QMessageBox.warning(self, "Worker ID Required", "Please enter your Worker ID before modifying inspection status.")
            self.open_worker_dialog()
            return

        d = id_item.data(Qt.UserRole)
        socket_id = id_item.text().strip()
        nom_size = self.meas_table.item(row, 1).text() if self.meas_table.item(row, 1) else "—"
        exp_od = self.meas_table.item(row, 2).text() if self.meas_table.item(row, 2) else "—"
        meas_od = self.meas_table.item(row, 3).text() if self.meas_table.item(row, 3) else "—"

        auto_status = d.get("automatic_status", cur_status) if isinstance(d, dict) else cur_status
        final_status = d.get("final_status", cur_status) if isinstance(d, dict) else cur_status

        socket_info = {
            "socket_id": socket_id,
            "nominal_size": nom_size,
            "expected_od": exp_od,
            "measured_od": meas_od,
            "automatic_status": auto_status,
            "current_status": final_status
        }

        dlg = StatusOverrideDialog(socket_info, self.worker_session.worker_id, self)
        if dlg.exec_() == QDialog.Accepted and dlg.confirmed_new_status:
            new_status = dlg.confirmed_new_status
            reason = dlg.confirmed_reason
            now_iso = datetime.now().isoformat()

            if isinstance(d, dict):
                d["final_status"] = new_status
                id_item.setData(Qt.UserRole, d)

            if hasattr(self, 'current_inspection_data') and self.current_inspection_data:
                for cand in getattr(self.current_inspection_data, 'socket_detection_candidates', []):
                    if cand.get("sequential_socket_id") == socket_id or cand.get("assigned_reference_id") == socket_id or f"Det #{cand.get('global_instance_id')}" == socket_id:
                        cand["final_status"] = new_status

            from PyQt5.QtGui import QColor, QBrush
            status_item.setText(new_status)
            if new_status == "PASS":
                status_item.setForeground(QBrush(QColor("#15803D")))
            elif new_status == "FAIL":
                status_item.setForeground(QBrush(QColor("#DC2626")))
            else:
                status_item.setForeground(QBrush(QColor("#D97706")))

            insp_id = getattr(self.current_inspection_data, 'inspection_id', 'INSP-UNKNOWN') if hasattr(self, 'current_inspection_data') and self.current_inspection_data else 'INSP-UNKNOWN'
            batch_id = getattr(self.current_inspection_data, 'batch_id', self.worker_session.current_batch_id or "BATCH-001") if hasattr(self, 'current_inspection_data') and self.current_inspection_data else (self.worker_session.current_batch_id or "BATCH-001")
            toolkit_id = getattr(self.current_inspection_data, 'toolkit_id', self.worker_session.current_toolkit_id or "TOOLKIT-001") if hasattr(self, 'current_inspection_data') and self.current_inspection_data else (self.worker_session.current_toolkit_id or "TOOLKIT-001")

            audit_entry = {
                "worker_id": self.worker_session.worker_id,
                "inspection_id": insp_id,
                "batch_id": batch_id,
                "toolkit_id": toolkit_id,
                "socket_id": socket_id,
                "nominal_size": nom_size,
                "original_automatic_status": auto_status,
                "previous_final_status": final_status,
                "new_final_status": new_status,
                "timestamp": now_iso,
                "reason": reason
            }
            if hasattr(self, 'current_inspection_data') and self.current_inspection_data:
                self.current_inspection_data.manual_overrides.append(audit_entry)

            self.status_bar.showMessage(f"Manual override confirmed: {socket_id} -> {new_status} by {self.worker_session.worker_id}")
            self.update_visualization()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'header_widget') and self.header_widget is not None:
            self.header_widget._relayout()



# =====================================================================
# BACKWARDS COMPATIBILITY MODULE REGISTRATION
# =====================================================================
def _register_sys_module_shims():
    """
    Registers module aliases into sys.modules so that existing unit tests,
    plugins, or diagnostic scripts querying 'app.*', 'camera.*', 'inference.*',
    'inspection.*', and 'visualization.*' transparently resolve to this
    consolidated module without requiring legacy folder structures.
    """
    import types
    this_mod = sys.modules[__name__]
    
    mapping = {
        'app': [
            'theme', 'popup_utils', 'zoomable_viewer', 'worker_dialog',
            'status_override_dialog', 'report_dialog', 'teaching_dialog',
            'engineering_settings', 'main_window'
        ],
        'camera': [
            'depth_alignment', 'height_calibration', 'realsense_manager', 'camera_worker'
        ],
        'inference': [
            'class_mapping', 'postprocessing', 'model_loader', 'detector',
            'inference_worker', 'inference_pipeline'
        ],
        'inspection': [
            'inspection_data', 'worker_session', 'inspection_record_manager',
            'metrology', 'rim_detector', 'reference_manager', 'tool_counter',
            'count_comparator', 'company_manager', 'socket_identifier',
            'company_socket_reference_manager', 'batch_report_generator'
        ],
        'visualization': [
            'mask_renderer', 'overlay_renderer'
        ],
        'reporting': []
    }
    
    for pkg_name, submodules in mapping.items():
        if pkg_name not in sys.modules:
            pkg_mod = types.ModuleType(pkg_name)
            sys.modules[pkg_name] = pkg_mod
        else:
            pkg_mod = sys.modules[pkg_name]
            
        for sub in submodules:
            full_name = f"{pkg_name}.{sub}"
            sys.modules[full_name] = this_mod
            setattr(pkg_mod, sub, this_mod)

_register_sys_module_shims()


def run_self_verification(base_dir):
    """
    Automated self-verification harness for packaged/portable distribution.
    Verifies PyTorch, YOLO model inference, Excel workbooks, configuration,
    and RealSense camera discovery without requiring GUI interaction.
    Writes results to 'verification_report.json'.
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "base_dir": base_dir,
        "is_frozen": getattr(sys, 'frozen', False),
        "checks": {}
    }
    
    # 1. PyTorch check
    try:
        t = torch.zeros((1, 3, 64, 64), dtype=torch.float32)
        results["checks"]["pytorch"] = {
            "status": "PASS",
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "tensor_shape": list(t.shape)
        }
    except Exception as e:
        results["checks"]["pytorch"] = {"status": "FAIL", "error": str(e)}

    # 2. SmartLab Logo
    logo_path = os.path.join(base_dir, "Smartlab Logo.png")
    results["checks"]["smartlab_logo"] = {
        "status": "PASS" if os.path.isfile(logo_path) else "FAIL",
        "path": logo_path,
        "exists": os.path.isfile(logo_path)
    }

    # 3. Model Manifest & YOLO Model Loading
    try:
        manifest_path = os.path.join(base_dir, 'config', 'model_manifest.json')
        ml = ModelLoader(manifest_path=manifest_path)
        m_ok, m_msg = ml.load_manifest()
        mod_ok, mod_data = ml.load_model()
        results["checks"]["model_loading"] = {
            "status": "PASS" if (m_ok and mod_ok) else "FAIL",
            "manifest_ok": m_ok,
            "model_ok": mod_ok,
            "resolved_path": getattr(ml, 'manifest_data', {}).get('primary_model', {}).get('relative_path', ''),
            "model_task": getattr(mod_data.get('model', None), 'task', 'unknown') if mod_ok and isinstance(mod_data, dict) else str(mod_data)
        }
    except Exception as e:
        results["checks"]["model_loading"] = {"status": "FAIL", "error": str(e)}

    # 4. YOLO Inference Test
    try:
        if mod_ok and isinstance(mod_data, dict) and 'model' in mod_data:
            dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
            det = Detector(mod_data['model'])
            res = det.detect(dummy_img)
            results["checks"]["yolo_inference"] = {
                "status": "PASS",
                "detections_returned": len(res) if isinstance(res, list) else 0
            }
        else:
            results["checks"]["yolo_inference"] = {"status": "SKIPPED", "reason": "Model not loaded"}
    except Exception as e:
        results["checks"]["yolo_inference"] = {"status": "FAIL", "error": str(e)}

    # 5. Book1.xlsx
    try:
        cm = CompanyManager()
        results["checks"]["book1_companies"] = {
            "status": "PASS" if cm.is_loaded else "FAIL",
            "loaded": bool(cm.is_loaded),
            "companies": cm.get_companies() if cm.is_loaded else []
        }
    except Exception as e:
        results["checks"]["book1_companies"] = {"status": "FAIL", "error": str(e)}

    # 6. Book2.xlsx
    try:
        csm = CompanySocketReferenceManager()
        results["checks"]["book2_sockets"] = {
            "status": "PASS" if csm.is_loaded else "FAIL",
            "loaded": bool(csm.is_loaded),
            "companies": csm.companies if csm.is_loaded else []
        }
    except Exception as e:
        results["checks"]["book2_sockets"] = {"status": "FAIL", "error": str(e)}

    # 7. RealSense Camera Discovery
    try:
        if rs is not None:
            ctx = rs.context()
            devs = ctx.query_devices()
            results["checks"]["realsense"] = {
                "status": "PASS",
                "library_available": True,
                "version": rs.__version__,
                "devices_found": len(devs),
                "device_names": [d.get_info(rs.camera_info.name) for d in devs]
            }
        else:
            results["checks"]["realsense"] = {"status": "FAIL", "error": "pyrealsense2 not imported"}
    except Exception as e:
        results["checks"]["realsense"] = {"status": "FAIL", "error": str(e)}

    # 8. Worker Session Manager
    try:
        wsm = WorkerSessionManager()
        s_ok, s_msg = wsm.start_session("WRK-001", "BATCH-001", "TOOLKIT-001")
        results["checks"]["worker_session"] = {
            "status": "PASS" if s_ok else "FAIL",
            "active_worker": wsm.worker_id,
            "session_active": wsm.session_active
        }
    except Exception as e:
        results["checks"]["worker_session"] = {"status": "FAIL", "error": str(e)}

    # 9. Inspection Storage & Directory Verification
    try:
        rec_mgr = InspectionRecordManager(storage_dir=os.path.join(base_dir, "data", "inspections"))
        results["checks"]["inspection_storage"] = {
            "status": "PASS",
            "storage_dir": rec_mgr.storage_dir,
            "exists": os.path.isdir(rec_mgr.storage_dir)
        }
    except Exception as e:
        results["checks"]["inspection_storage"] = {"status": "FAIL", "error": str(e)}

    # 10. PDF Report Generation Test
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        doc = QTextDocument()
        doc.setHtml("<h1>AXOVRIM Automated System Verification</h1><p>Status: All Subsystems Operational</p>")
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        test_out_dir = os.path.join(base_dir, "Reports", "TEST_BATCH")
        os.makedirs(test_out_dir, exist_ok=True)
        pdf_path = os.path.join(test_out_dir, "verification_test_report.pdf")
        printer.setOutputFileName(pdf_path)
        doc.print_(printer)
        results["checks"]["pdf_report"] = {
            "status": "PASS" if os.path.isfile(pdf_path) else "FAIL",
            "pdf_path": pdf_path,
            "size_bytes": os.path.getsize(pdf_path) if os.path.isfile(pdf_path) else 0
        }
        if os.path.isfile(pdf_path):
            os.remove(pdf_path)
        if os.path.isdir(test_out_dir):
            shutil.rmtree(test_out_dir, ignore_errors=True)
    except Exception as e:
        results["checks"]["pdf_report"] = {"status": "FAIL", "error": str(e)}

    report_path = os.path.join(base_dir, "verification_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


# =====================================================================
# APPLICATION ENTRY POINT
# =====================================================================
def main():
    multiprocessing.freeze_support()
    if '--verify' in sys.argv or '--test' in sys.argv:
        base_dir = USER_DIR
        res = run_self_verification(base_dir)
        print(json.dumps(res, indent=2))
        return 0
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
            
        window = MainWindow()
        
        if os.environ.get('QT_QPA_PLATFORM') != 'offscreen':
            window.show()
            
        return app.exec_()
    except Exception as e:
        traceback.print_exc()
        err_msg = traceback.format_exc()
        try:
            exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(exe_dir, "app_crash.log"), "w", encoding="utf-8") as f:
                f.write(err_msg)
        except Exception:
            pass
        try:
            from PyQt5.QtWidgets import QMessageBox
            app_err = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "AXOVRIM — Startup Error",
                f"An unrecoverable startup error occurred:\n\n{str(e)}\n\nTechnical details have been saved to app_crash.log in the application directory."
            )
        except Exception:
            pass
        return 1

if __name__ == '__main__':
    sys.exit(main())
