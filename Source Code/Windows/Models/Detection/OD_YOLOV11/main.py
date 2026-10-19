import sys
import os
from pathlib import Path
from datetime import datetime

from PyQt5 import QtCore, QtGui, QtWidgets

import cv2
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None


class DetectionApp(QtWidgets.QWidget):
    def __init__(self, weights_path: str):
        super().__init__()
        self.setWindowTitle("Object Detection - YOLOv11")
        self.weights_path = weights_path
        self._check_weights()

        self.model = None
        self.detected_image = None

        self.left_img_lbl = QtWidgets.QLabel("Upload\nImage", alignment=QtCore.Qt.AlignCenter)
        self.right_img_lbl = QtWidgets.QLabel("Detection\nResult", alignment=QtCore.Qt.AlignCenter)

        for lbl in (self.left_img_lbl, self.right_img_lbl):
            lbl.setMinimumSize(400, 400)
            lbl.setFrameShape(QtWidgets.QFrame.Box)
            lbl.setLineWidth(2)
            lbl.setScaledContents(True)

        img_layout = QtWidgets.QHBoxLayout()
        img_layout.addWidget(self.left_img_lbl)
        img_layout.addWidget(self.right_img_lbl)

        upload_btn = QtWidgets.QPushButton("Upload Image")
        upload_btn.clicked.connect(self.choose_image)

        detect_btn = QtWidgets.QPushButton("Run Detection")
        detect_btn.clicked.connect(self.run_detection)

        save_btn = QtWidgets.QPushButton("Save Result")
        save_btn.clicked.connect(self.save_result)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(upload_btn)
        btn_layout.addWidget(detect_btn)
        btn_layout.addWidget(save_btn)
        btn_layout.addStretch(1)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(img_layout)
        main_layout.addLayout(btn_layout)

        self.image_path: str | None = None

    def _check_weights(self):
        if not Path(self.weights_path).is_file():
            QtWidgets.QMessageBox.critical(
                self,
                "Weights not found",
                f"Could not find weights file:\n{self.weights_path}",
            )

    def choose_image(self):
        file_dialog = QtWidgets.QFileDialog(self, "Select image")
        file_dialog.setNameFilters([
            "Images (*.png *.jpg *.jpeg *.bmp)",
            "All files (*.*)",
        ])
        if file_dialog.exec_():
            selected = file_dialog.selectedFiles()
            if selected:
                self.image_path = selected[0]
                self.display_image(self.image_path, self.left_img_lbl)
                self.right_img_lbl.clear()
                self.right_img_lbl.setText("Detection\nResult")
                self.detected_image = None

    def run_detection(self):
        if self.image_path is None:
            QtWidgets.QMessageBox.warning(self, "No image", "Please upload an image before running detection.")
            return

        if YOLO is None:
            QtWidgets.QMessageBox.critical(self, "Ultralytics missing", "Install it via\n    pip install ultralytics")
            return

        if self.model is None:
            try:
                self.model = YOLO(self.weights_path)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Model error", f"Failed to load model:\n{e}")
                return

        try:
            results = self.model(self.image_path)[0]
            det_img = results.plot()
            self.detected_image = det_img.copy()
            self.display_np_image(det_img, self.right_img_lbl)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Detection error", f"Detection failed:\n{e}")

    def save_result(self):
        if self.detected_image is None:
            QtWidgets.QMessageBox.warning(self, "No result", "No detection result to save.")
            return

        try:
            save_path = r"C:\Devansh Work\CCU\CCU - Research Paper\Devansh\Results\Datection\OD_YOLOV11\Downloads"
            os.makedirs(save_path, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"detection_result_{timestamp}.png"
            filepath = os.path.join(save_path, filename)
            cv2.imwrite(filepath, self.detected_image)
            QtWidgets.QMessageBox.information(self, "Saved", f"Result saved to:\n{filepath}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Save error", f"Failed to save image:\n{e}")

    @staticmethod
    def display_image(path: str, label: QtWidgets.QLabel):
        pix = QtGui.QPixmap(path)
        if pix.isNull():
            label.setText("Failed to load image")
        else:
            label.setPixmap(pix.scaled(label.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

    @staticmethod
    def display_np_image(img: np.ndarray, label: QtWidgets.QLabel):
        if img is None:
            label.setText("Invalid image data")
            return
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img.shape
        bytes_per_line = ch * w
        qimg = QtGui.QImage(img.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap.fromImage(qimg)
        label.setPixmap(pix.scaled(label.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))


def main():
    weights_path = r"C:\Devansh Work\CCU\CCU - Research Paper\Devansh\Results\Datection\OD_YOLOV11\best (2).pt"
    app = QtWidgets.QApplication(sys.argv)
    win = DetectionApp(weights_path)
    win.resize(1000, 600)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

