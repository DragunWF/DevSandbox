import json
import math
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


# =========================================================================
# 1. BACKGROUND WORKER THREAD (NON-BLOCKING UI)
# =========================================================================

class ProcessingWorker(QThread):
    """Executes the OpenCV & Pillow pipeline off the main GUI thread."""

    finished_success = Signal(object, str)  # (PIL.Image, status_text)
    finished_error = Signal(str, str)       # (status_text, error_message)

    def __init__(self, source_img: Image.Image, params: Dict, input_file_path: str) -> None:
        super().__init__()
        self.source_img = source_img
        self.params = params
        self.input_file_path = input_file_path

    def run(self) -> None:
        try:
            strip_img, metadata = SpritePipeline.process_sprite_sheet(
                source_img=self.source_img,
                target_rgb=self.params["target_rgb"],
                tolerance=self.params["tolerance"],
                cell_w=self.params["cell_w"],
                cell_h=self.params["cell_h"],
                num_colors=self.params["num_colors"],
                scale_factor=self.params["scale_factor"],
                hard_alpha=self.params["hard_alpha"],
            )

            export_msg = ""
            if self.params["export_files"]:
                out_dir = self.params["output_dir"]
                os.makedirs(out_dir, exist_ok=True)
                base_name = os.path.splitext(os.path.basename(self.input_file_path or "sprite"))[0]
                sheet_path = os.path.join(out_dir, f"{base_name}_sheet.png")
                meta_path = os.path.join(out_dir, f"{base_name}_meta.json")

                strip_img.save(sheet_path, format="PNG")
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2)

                export_msg = f" | Exported successfully to {out_dir}"

            frame_count = metadata["frame_count"]
            status_text = f"Detected {frame_count} frame{'s' if frame_count != 1 else ''}{export_msg}"
            self.finished_success.emit(strip_img, status_text)

        except ValueError as ve:
            self.finished_error.emit("Processing aborted: No frames detected.", str(ve))
        except Exception as exc:
            self.finished_error.emit("Error occurred during processing.", str(exc))


# =========================================================================
# 2. PURE COMPUTER VISION & IMAGE PROCESSING PIPELINE
# =========================================================================

class SpritePipeline:
    """Pure OpenCV + Pillow processing logic decoupled from the GUI."""

    @classmethod
    def process_sprite_sheet(
        cls,
        source_img: Image.Image,
        target_rgb: Tuple[int, int, int],
        tolerance: int,
        cell_w: int,
        cell_h: int,
        num_colors: int,
        scale_factor: float,
        hard_alpha: bool,
    ) -> Tuple[Image.Image, Dict]:
        # --- Step 1: Chroma-Keying & Edge Cleanup ---
        rgba_img = source_img.convert("RGBA")
        rgba_np = np.array(rgba_img, dtype=np.uint8)

        rgb_float = rgba_np[:, :, :3].astype(np.float32)
        alpha_channel = rgba_np[:, :, 3].copy()

        target_vec = np.array(target_rgb, dtype=np.float32).reshape((1, 1, 3))
        euclidean_dist = np.linalg.norm(rgb_float - target_vec, axis=2)

        alpha_channel[euclidean_dist <= float(tolerance)] = 0

        kernel = np.ones((2, 2), dtype=np.uint8)
        cleaned_alpha = cv2.morphologyEx(alpha_channel, cv2.MORPH_OPEN, kernel)

        if hard_alpha:
            cleaned_alpha = np.where(cleaned_alpha > 128, 255, 0).astype(np.uint8)
            binary_mask = cleaned_alpha.copy()
        else:
            binary_mask = np.where(cleaned_alpha > 16, 255, 0).astype(np.uint8)

        # --- Step 2: Contour & Frame Detection ---
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_area_threshold = 16
        raw_boxes: List[Tuple[int, int, int, int]] = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if (w * h) >= min_area_threshold:
                raw_boxes.append((x, y, w, h))

        if not raw_boxes:
            raise ValueError(
                "No discrete sprite frames were detected. Try lowering the Chroma Tolerance "
                "or verifying the Key Color."
            )

        sorted_boxes = cls._sort_bounding_boxes_grid(raw_boxes)

        # --- Step 3: Quantization & Crisp Edge Snapping ---
        rgba_np[:, :, 3] = cleaned_alpha
        rgba_np[cleaned_alpha == 0, :3] = 0

        if num_colors > 0:
            rgb_pil = Image.fromarray(rgba_np[:, :, :3], mode="RGB")
            quantized_rgb = rgb_pil.quantize(
                colors=num_colors,
                method=Image.Quantize.MEDIANCUT,
            ).convert("RGB")
            working_img = quantized_rgb.convert("RGBA")
            working_img.putalpha(Image.fromarray(cleaned_alpha, mode="L"))
        else:
            working_img = Image.fromarray(rgba_np, mode="RGBA")

        # --- Step 4: Uniform Frame Normalization & Bottom-Center Ground Alignment ---
        num_frames = len(sorted_boxes)
        strip_width = cell_w * num_frames
        strip_height = cell_h
        destination_strip = Image.new("RGBA", (strip_width, strip_height), (0, 0, 0, 0))

        floor_padding = 2
        max_avail_w = cell_w
        max_avail_h = max(1, cell_h - floor_padding)

        frames_metadata: List[Dict] = []

        for idx, (bx, by, bw, bh) in enumerate(sorted_boxes):
            cropped_frame = working_img.crop((bx, by, bx + bw, by + bh))

            if not math.isclose(scale_factor, 1.0, abs_tol=1e-3):
                scaled_w = max(1, int(round(cropped_frame.width * scale_factor)))
                scaled_h = max(1, int(round(cropped_frame.height * scale_factor)))
                cropped_frame = cropped_frame.resize((scaled_w, scaled_h), Image.Resampling.NEAREST)

            if cropped_frame.width > max_avail_w or cropped_frame.height > max_avail_h:
                fit_ratio = min(max_avail_w / cropped_frame.width, max_avail_h / cropped_frame.height)
                fit_w = max(1, int(math.floor(cropped_frame.width * fit_ratio)))
                fit_h = max(1, int(math.floor(cropped_frame.height * fit_ratio)))
                cropped_frame = cropped_frame.resize((fit_w, fit_h), Image.Resampling.NEAREST)

            cell_origin_x = idx * cell_w
            paste_x = cell_origin_x + (cell_w - cropped_frame.width) // 2
            paste_y = max(0, cell_h - cropped_frame.height - floor_padding)

            destination_strip.paste(cropped_frame, (paste_x, paste_y), cropped_frame)

            frames_metadata.append(
                {
                    "index": idx,
                    "rect": [cell_origin_x, 0, cell_w, cell_h],
                    "pivot": {"x": 0.5, "y": 1.0},
                }
            )

        metadata = {
            "frame_width": cell_w,
            "frame_height": cell_h,
            "frame_count": num_frames,
            "frames": frames_metadata,
        }

        return destination_strip, metadata

    @staticmethod
    def _sort_bounding_boxes_grid(boxes: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        if not boxes:
            return []

        heights = sorted(b[3] for b in boxes)
        median_h = heights[len(heights) // 2]
        row_tolerance = max(8.0, median_h * 0.5)

        boxes_by_y = sorted(boxes, key=lambda b: b[1] + b[3] * 0.5)

        rows: List[List[Tuple[int, int, int, int]]] = []
        row_centers: List[float] = []

        for box in boxes_by_y:
            cy = box[1] + b_h_half if (b_h_half := box[3] * 0.5) else box[1]
            placed = False
            for idx, r_center in enumerate(row_centers):
                if abs(cy - r_center) <= row_tolerance:
                    rows[idx].append(box)
                    row_centers[idx] = sum(b[1] + b[3] * 0.5 for b in rows[idx]) / len(rows[idx])
                    placed = True
                    break
            if not placed:
                rows.append([box])
                row_centers.append(cy)

        sorted_boxes: List[Tuple[int, int, int, int]] = []
        for row in rows:
            row.sort(key=lambda b: b[0])
            sorted_boxes.extend(row)

        return sorted_boxes


# =========================================================================
# 3. PYSIDE6 MODERN DARK GUI
# =========================================================================

class SpriteConverterApp(QMainWindow):
    """Main Desktop Window using PySide6 (Qt6)."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PixelForge — AI Sprite Sheet Cleaner & Normalizer")
        self.resize(1280, 820)
        self.setMinimumSize(1024, 680)

        self.input_file_path: Optional[str] = None
        self.output_dir_path: str = os.path.abspath("./output")
        self.raw_pil_image: Optional[Image.Image] = None
        self.processed_pil_image: Optional[Image.Image] = None
        self.worker: Optional[ProcessingWorker] = None

        self._apply_dark_stylesheet()
        self._build_ui()

    def _apply_dark_stylesheet(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget#MainRoot {
                background-color: #181825;
                color: #cdd6f4;
                font-family: -apple-system, "Segoe UI", sans-serif;
                font-size: 13px;
            }
            QFrame#Sidebar {
                background-color: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 8px;
            }
            QGroupBox {
                background-color: #1e1e2e;
                border: 1px solid #45475a;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                font-weight: bold;
                color: #89b4fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QLabel {
                color: #cdd6f4;
            }
            QLabel#MutedLabel {
                color: #a6adc8;
                font-size: 12px;
            }
            QLabel#StatusLabel {
                color: #a6e3a1;
                font-weight: bold;
                font-size: 13px;
            }
            QLabel#PreviewHeader {
                background-color: #313244;
                color: #cdd6f4;
                font-weight: bold;
                padding: 8px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QLabel#CanvasView {
                background-color: #11111b;
                border: 1px solid #45475a;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
                color: #6c7086;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 5px;
                padding: 7px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
            QPushButton:disabled {
                background-color: #181825;
                color: #585b70;
            }
            QPushButton#AccentButton {
                background-color: #89b4fa;
                color: #11111b;
                border: none;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton#AccentButton:hover {
                background-color: #74c7ec;
            }
            QLineEdit, QSpinBox {
                background-color: #11111b;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 4px 6px;
            }
            """
        )

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("MainRoot")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(12, 12, 12, 8)
        root_layout.setSpacing(8)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)
        root_layout.addLayout(content_layout, stretch=1)

        # --- Left Sidebar ---
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(350)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(10)

        sidebar_layout.addWidget(self._create_file_group())
        sidebar_layout.addWidget(self._create_bg_group())
        sidebar_layout.addWidget(self._create_size_group())
        sidebar_layout.addWidget(self._create_cleaning_group())
        sidebar_layout.addStretch(1)

        self.btn_preview = QPushButton("Update Preview")
        self.btn_preview.clicked.connect(lambda: self._start_processing(export_files=False))
        sidebar_layout.addWidget(self.btn_preview)

        self.btn_export = QPushButton("Process & Export")
        self.btn_export.setObjectName("AccentButton")
        self.btn_export.clicked.connect(lambda: self._start_processing(export_files=True))
        sidebar_layout.addWidget(self.btn_export)

        content_layout.addWidget(sidebar)

        # --- Right Preview Area ---
        preview_layout = QHBoxLayout()
        preview_layout.setSpacing(10)

        # Raw Panel
        raw_col = QVBoxLayout()
        raw_col.setSpacing(0)
        lbl_raw_hdr = QLabel("Original Raw Image")
        lbl_raw_hdr.setObjectName("PreviewHeader")
        self.lbl_raw_canvas = QLabel("Load an input image to preview")
        self.lbl_raw_canvas.setObjectName("CanvasView")
        self.lbl_raw_canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        raw_col.addWidget(lbl_raw_hdr)
        raw_col.addWidget(self.lbl_raw_canvas, stretch=1)

        # Processed Panel
        proc_col = QVBoxLayout()
        proc_col.setSpacing(0)
        lbl_proc_hdr = QLabel("Processed Uniform Sprite Sheet (Alpha Checkerboard)")
        lbl_proc_hdr.setObjectName("PreviewHeader")
        self.lbl_proc_canvas = QLabel("Processed sprite strip will appear here")
        self.lbl_proc_canvas.setObjectName("CanvasView")
        self.lbl_proc_canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        proc_col.addWidget(lbl_proc_hdr)
        proc_col.addWidget(self.lbl_proc_canvas, stretch=1)

        preview_layout.addLayout(raw_col, stretch=1)
        preview_layout.addLayout(proc_col, stretch=1)
        content_layout.addLayout(preview_layout, stretch=1)

        # --- Status Bar ---
        self.lbl_status = QLabel("Ready. Load an input sprite sheet to begin.")
        self.lbl_status.setObjectName("StatusLabel")
        root_layout.addWidget(self.lbl_status)

    def _create_file_group(self) -> QGroupBox:
        group = QGroupBox("1. File Management")
        layout = QVBoxLayout(group)

        btn_in = QPushButton("Browse Input Image...")
        btn_in.clicked.connect(self._on_browse_input)
        self.lbl_input_path = QLabel("No input image selected")
        self.lbl_input_path.setObjectName("MutedLabel")
        self.lbl_input_path.setWordWrap(True)

        btn_out = QPushButton("Browse Output Folder...")
        btn_out.clicked.connect(self._on_browse_output)
        self.lbl_output_path = QLabel(self.output_dir_path)
        self.lbl_output_path.setObjectName("MutedLabel")
        self.lbl_output_path.setWordWrap(True)

        layout.addWidget(btn_in)
        layout.addWidget(self.lbl_input_path)
        layout.addSpacing(4)
        layout.addWidget(btn_out)
        layout.addWidget(self.lbl_output_path)
        return group

    def _create_bg_group(self) -> QGroupBox:
        group = QGroupBox("2. Background Removal")
        layout = QVBoxLayout(group)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Key Color (Hex):"))
        self.edit_hex = QLineEdit("#FF00FF")
        self.edit_hex.setMaxLength(7)
        self.edit_hex.textChanged.connect(self._on_hex_changed)
        color_row.addWidget(self.edit_hex)

        self.btn_swatch = QPushButton()
        self.btn_swatch.setFixedSize(28, 28)
        self.btn_swatch.setStyleSheet("background-color: #FF00FF; border: 1px solid #cdd6f4; border-radius: 4px;")
        self.btn_swatch.clicked.connect(self._on_pick_color)
        color_row.addWidget(self.btn_swatch)

        btn_pick = QPushButton("Pick")
        btn_pick.clicked.connect(self._on_pick_color)
        color_row.addWidget(btn_pick)
        layout.addLayout(color_row)

        tol_hdr = QHBoxLayout()
        tol_hdr.addWidget(QLabel("Chroma Tolerance:"))
        self.lbl_tol_val = QLabel("35")
        self.lbl_tol_val.setObjectName("MutedLabel")
        tol_hdr.addStretch()
        tol_hdr.addWidget(self.lbl_tol_val)
        layout.addLayout(tol_hdr)

        self.slider_tol = QSlider(Qt.Orientation.Horizontal)
        self.slider_tol.setRange(5, 100)
        self.slider_tol.setValue(35)
        self.slider_tol.valueChanged.connect(lambda v: self.lbl_tol_val.setText(str(v)))
        layout.addWidget(self.slider_tol)
        return group

    def _create_size_group(self) -> QGroupBox:
        group = QGroupBox("3. Target Frame Size (px)")
        grid = QGridLayout(group)

        grid.addWidget(QLabel("Cell Width:"), 0, 0)
        self.spin_w = QSpinBox()
        self.spin_w.setRange(8, 512)
        self.spin_w.setValue(48)
        grid.addWidget(self.spin_w, 0, 1)

        grid.addWidget(QLabel("Cell Height:"), 0, 2)
        self.spin_h = QSpinBox()
        self.spin_h.setRange(8, 512)
        self.spin_h.setValue(48)
        grid.addWidget(self.spin_h, 0, 3)
        return group

    def _create_cleaning_group(self) -> QGroupBox:
        group = QGroupBox("4. Pixel Cleaning & Crispness")
        layout = QVBoxLayout(group)

        # Quantization
        q_hdr = QHBoxLayout()
        q_hdr.addWidget(QLabel("Palette Colors (0 = Off):"))
        self.lbl_quant_val = QLabel("24")
        self.lbl_quant_val.setObjectName("MutedLabel")
        q_hdr.addStretch()
        q_hdr.addWidget(self.lbl_quant_val)
        layout.addLayout(q_hdr)

        self.slider_quant = QSlider(Qt.Orientation.Horizontal)
        self.slider_quant.setRange(0, 64)
        self.slider_quant.setValue(24)
        self.slider_quant.valueChanged.connect(lambda v: self.lbl_quant_val.setText(str(v)))
        layout.addWidget(self.slider_quant)

        # Downsample Scale (2 to 20 -> 0.10 to 1.00 in steps of 0.05)
        s_hdr = QHBoxLayout()
        s_hdr.addWidget(QLabel("Downsample Scale:"))
        self.lbl_scale_val = QLabel("1.00x")
        self.lbl_scale_val.setObjectName("MutedLabel")
        s_hdr.addStretch()
        s_hdr.addWidget(self.lbl_scale_val)
        layout.addLayout(s_hdr)

        self.slider_scale = QSlider(Qt.Orientation.Horizontal)
        self.slider_scale.setRange(2, 20)
        self.slider_scale.setSingleStep(1)
        self.slider_scale.setValue(20)
        self.slider_scale.valueChanged.connect(lambda v: self.lbl_scale_val.setText(f"{v * 0.05:.2f}x"))
        layout.addWidget(self.slider_scale)

        # Hard Alpha
        self.chk_hard_alpha = QCheckBox("Hard Alpha Threshold (Strip Fringe)")
        self.chk_hard_alpha.setChecked(True)
        layout.addWidget(self.chk_hard_alpha)
        return group

    # =========================================================================
    # 4. EVENT HANDLERS & CANVAS RENDERING
    # =========================================================================

    def _on_hex_changed(self, text: str) -> None:
        clean = text.strip()
        if re.fullmatch(r"^#[0-9A-Fa-f]{6}$", clean):
            self.btn_swatch.setStyleSheet(
                f"background-color: {clean}; border: 1px solid #cdd6f4; border-radius: 4px;"
            )

    def _on_pick_color(self) -> None:
        initial = QColor(self.edit_hex.text().strip())
        if not initial.isValid():
            initial = QColor("#FF00FF")
        color = QColorDialog.getColor(initial, self, "Select Background Key Color")
        if color.isValid():
            self.edit_hex.setText(color.name().upper())

    def _on_browse_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Input Sprite Sheet",
            "",
            "Images (*.png *.jpg *.jpeg *.webp)",
        )
        if not path:
            return
        try:
            img = Image.open(path)
            img.load()
            self.input_file_path = path
            self.raw_pil_image = img.convert("RGBA")
            self.lbl_input_path.setText(path)
            self._render_canvases()
            self.lbl_status.setText(f"Loaded '{os.path.basename(path)}' ({img.width}x{img.height} px).")
            self._start_processing(export_files=False)
        except Exception as exc:
            QMessageBox.critical(self, "Image Load Error", f"Could not open image file:\n{exc}")

    def _on_browse_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", self.output_dir_path)
        if folder:
            self.output_dir_path = os.path.abspath(folder)
            self.lbl_output_path.setText(self.output_dir_path)

    def _start_processing(self, export_files: bool) -> None:
        if self.worker is not None and self.worker.isRunning():
            return

        if not self.input_file_path or self.raw_pil_image is None:
            QMessageBox.warning(self, "Missing Input Image", "Please select a valid input image first.")
            return

        hex_val = self.edit_hex.text().strip()
        if not re.fullmatch(r"^#[0-9A-Fa-f]{6}$", hex_val):
            QMessageBox.critical(self, "Invalid Color", f"'{hex_val}' is not a valid hex color (e.g., #FF00FF).")
            return

        target_rgb = (int(hex_val[1:3], 16), int(hex_val[3:5], 16), int(hex_val[5:7], 16))
        params = {
            "target_rgb": target_rgb,
            "tolerance": int(self.slider_tol.value()),
            "cell_w": int(self.spin_w.value()),
            "cell_h": int(self.spin_h.value()),
            "num_colors": int(self.slider_quant.value()),
            "scale_factor": round(self.slider_scale.value() * 0.05, 2),
            "hard_alpha": bool(self.chk_hard_alpha.isChecked()),
            "output_dir": self.output_dir_path,
            "export_files": export_files,
        }

        self.btn_export.setEnabled(False)
        self.btn_preview.setEnabled(False)
        self.lbl_status.setText("Processing sprite sheet...")

        self.worker = ProcessingWorker(self.raw_pil_image.copy(), params, self.input_file_path)
        self.worker.finished_success.connect(self._on_worker_success)
        self.worker.finished_error.connect(self._on_worker_error)
        self.worker.start()

    def _on_worker_success(self, result_img: Image.Image, status_text: str) -> None:
        self.btn_export.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.processed_pil_image = result_img
        self.lbl_status.setText(status_text)
        self._render_canvases()

    def _on_worker_error(self, status_text: str, error_msg: str) -> None:
        self.btn_export.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.lbl_status.setText(status_text)
        QMessageBox.warning(self, "Processing Notice", error_msg)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._render_canvases()

    def _render_canvases(self) -> None:
        if self.raw_pil_image is not None:
            cw = max(20, self.lbl_raw_canvas.width() - 16)
            ch = max(20, self.lbl_raw_canvas.height() - 16)
            scaled_raw = self._scale_image_to_fit(self.raw_pil_image, cw, ch)
            self.lbl_raw_canvas.setPixmap(self._pil_to_qpixmap(scaled_raw))

        if self.processed_pil_image is not None:
            cw = max(20, self.lbl_proc_canvas.width() - 16)
            ch = max(20, self.lbl_proc_canvas.height() - 16)
            scaled_fg = self._scale_image_to_fit(self.processed_pil_image, cw, ch)
            checker = self._create_checkerboard(scaled_fg.width, scaled_fg.height, tile_size=12)
            composited = Image.alpha_composite(checker, scaled_fg)
            self.lbl_proc_canvas.setPixmap(self._pil_to_qpixmap(composited))

    @staticmethod
    def _pil_to_qpixmap(pil_img: Image.Image) -> QPixmap:
        rgba = pil_img.convert("RGBA")
        data = rgba.tobytes("raw", "RGBA")
        qimg = QImage(data, rgba.width, rgba.height, rgba.width * 4, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qimg.copy())

    @staticmethod
    def _scale_image_to_fit(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
        if img.width <= 0 or img.height <= 0:
            return img
        scale = min(max_w / img.width, max_h / img.height, 8.0)
        new_w = max(1, int(round(img.width * scale)))
        new_h = max(1, int(round(img.height * scale)))
        return img.resize((new_w, new_h), Image.Resampling.NEAREST)

    @staticmethod
    def _create_checkerboard(width: int, height: int, tile_size: int = 12) -> Image.Image:
        color_a = np.array([30, 30, 46, 255], dtype=np.uint8)
        color_b = np.array([49, 50, 68, 255], dtype=np.uint8)
        y_idx = np.arange(height) // tile_size
        x_idx = np.arange(width) // tile_size
        grid = (y_idx[:, None] + x_idx[None, :]) % 2
        checker = np.where(grid[:, :, None] == 0, color_a, color_b)
        return Image.fromarray(checker, mode="RGBA")


def main() -> None:
    app = QApplication(sys.argv)
    window = SpriteConverterApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()