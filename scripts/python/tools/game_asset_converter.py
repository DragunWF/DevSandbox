import json
import math
import os
import re
import threading
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageTk


class SpriteConverterApp:
    """
    Standalone Desktop Application for converting raw AI-generated sprite sheets
    into crisp, game-ready 2D pixel art strips with animation metadata.
    """

    # Color Palette (Modern Dark Theme)
    BG_DARK = "#181825"
    BG_PANEL = "#1e1e2e"
    BG_SURFACE = "#313244"
    FG_PRIMARY = "#cdd6f4"
    FG_MUTED = "#a6adc8"
    ACCENT_PRIMARY = "#89b4fa"
    ACCENT_ACTIVE = "#74c7ec"
    SUCCESS_COLOR = "#a6e3a1"
    BORDER_COLOR = "#45475a"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("PixelForge — AI Sprite Sheet Cleaner & Normalizer")
        self.root.geometry("1280x820")
        self.root.minsize(1024, 680)
        self.root.configure(bg=self.BG_DARK)

        # State Variables
        self.input_path_var = tk.StringVar(value="No input image selected")
        self.output_dir_var = tk.StringVar(value=os.path.abspath("./output"))
        self.bg_color_var = tk.StringVar(value="#FF00FF")
        self.tolerance_var = tk.IntVar(value=35)
        self.cell_width_var = tk.IntVar(value=48)
        self.cell_height_var = tk.IntVar(value=48)
        self.quantize_colors_var = tk.IntVar(value=24)
        self.scale_factor_var = tk.DoubleVar(value=1.0)
        self.hard_alpha_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Ready. Load an input sprite sheet to begin.")

        # Internal Image References
        self.input_file_path: Optional[str] = None
        self.raw_pil_image: Optional[Image.Image] = None
        self.processed_pil_image: Optional[Image.Image] = None
        self.raw_tk_image: Optional[ImageTk.PhotoImage] = None
        self.processed_tk_image: Optional[ImageTk.PhotoImage] = None
        self.is_processing: bool = False

        # Initialize UI
        self._configure_styles()
        self._build_ui()

    # =========================================================================
    # 1. GUI CONSTRUCTION & STYLING
    # =========================================================================

    def _configure_styles(self) -> None:
        """Configures custom dark-mode ttk styles without external libraries."""
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(".", background=self.BG_PANEL, foreground=self.FG_PRIMARY, font=("Segoe UI", 10))
        style.configure("TFrame", background=self.BG_PANEL)
        style.configure("Dark.TFrame", background=self.BG_DARK)

        style.configure(
            "TLabelframe",
            background=self.BG_PANEL,
            foreground=self.ACCENT_PRIMARY,
            bordercolor=self.BORDER_COLOR,
            relief="solid",
            borderwidth=1,
        )
        style.configure(
            "TLabelframe.Label",
            background=self.BG_PANEL,
            foreground=self.ACCENT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
        )

        style.configure("TLabel", background=self.BG_PANEL, foreground=self.FG_PRIMARY)
        style.configure("Muted.TLabel", background=self.BG_PANEL, foreground=self.FG_MUTED, font=("Segoe UI", 9))
        style.configure("Status.TLabel", background=self.BG_DARK, foreground=self.SUCCESS_COLOR, font=("Segoe UI", 10, "bold"))
        style.configure("Header.TLabel", background=self.BG_SURFACE, foreground=self.FG_PRIMARY, font=("Segoe UI", 10, "bold"))

        style.configure(
            "TButton",
            background=self.BG_SURFACE,
            foreground=self.FG_PRIMARY,
            bordercolor=self.BORDER_COLOR,
            focuscolor=self.BG_SURFACE,
            padding=(10, 6),
            font=("Segoe UI", 9, "bold"),
        )
        style.map(
            "TButton",
            background=[("active", self.BORDER_COLOR), ("disabled", self.BG_DARK)],
            foreground=[("disabled", self.FG_MUTED)],
        )

        style.configure(
            "Accent.TButton",
            background=self.ACCENT_PRIMARY,
            foreground="#11111b",
            bordercolor=self.ACCENT_PRIMARY,
            padding=(12, 8),
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Accent.TButton",
            background=[("active", self.ACCENT_ACTIVE), ("disabled", self.BG_SURFACE)],
            foreground=[("disabled", self.FG_MUTED)],
        )

        style.configure(
            "TEntry",
            fieldbackground=self.BG_DARK,
            foreground=self.FG_PRIMARY,
            insertcolor=self.FG_PRIMARY,
            bordercolor=self.BORDER_COLOR,
            lightcolor=self.BORDER_COLOR,
            darkcolor=self.BORDER_COLOR,
            padding=4,
        )

        style.configure(
            "TSpinbox",
            fieldbackground=self.BG_DARK,
            foreground=self.FG_PRIMARY,
            insertcolor=self.FG_PRIMARY,
            background=self.BG_SURFACE,
            bordercolor=self.BORDER_COLOR,
            arrowcolor=self.FG_PRIMARY,
            padding=4,
        )

        style.configure(
            "TCheckbutton",
            background=self.BG_PANEL,
            foreground=self.FG_PRIMARY,
            indicatorbackground=self.BG_DARK,
            indicatorforeground=self.ACCENT_PRIMARY,
            focuscolor=self.BG_PANEL,
        )
        style.map("TCheckbutton", background=[("active", self.BG_PANEL)])

        style.configure(
            "Horizontal.TScale",
            background=self.BG_PANEL,
            troughcolor=self.BG_DARK,
            bordercolor=self.BORDER_COLOR,
            lightcolor=self.ACCENT_PRIMARY,
            darkcolor=self.ACCENT_PRIMARY,
        )

    def _build_ui(self) -> None:
        """Builds the sidebar controls, preview canvases, and status bar."""
        # Top-level container
        main_container = ttk.Frame(self.root, style="Dark.TFrame", padding=10)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Left Sidebar (Controls & File Management)
        sidebar = ttk.Frame(main_container, width=350, padding=12)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        sidebar.pack_propagate(False)

        self._build_file_section(sidebar)
        self._build_bg_removal_section(sidebar)
        self._build_frame_size_section(sidebar)
        self._build_pixel_cleaning_section(sidebar)
        self._build_action_buttons(sidebar)

        # Right Main Area (Interactive Side-by-Side Preview)
        preview_area = ttk.Frame(main_container, style="Dark.TFrame")
        preview_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_preview_canvases(preview_area)

        # Bottom Status Bar
        status_bar = ttk.Frame(self.root, style="Dark.TFrame", padding=(12, 6))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        status_lbl = ttk.Label(status_bar, textvariable=self.status_var, style="Status.TLabel")
        status_lbl.pack(side=tk.LEFT)

    def _build_file_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text=" 1. File Management ", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))

        btn_in = ttk.Button(frame, text="Browse Input Image...", command=self._on_browse_input)
        btn_in.pack(fill=tk.X, pady=(0, 4))

        lbl_in = ttk.Label(frame, textvariable=self.input_path_var, style="Muted.TLabel", wraplength=300)
        lbl_in.pack(fill=tk.X, pady=(0, 8))

        btn_out = ttk.Button(frame, text="Browse Output Folder...", command=self._on_browse_output)
        btn_out.pack(fill=tk.X, pady=(0, 4))

        lbl_out = ttk.Label(frame, textvariable=self.output_dir_var, style="Muted.TLabel", wraplength=300)
        lbl_out.pack(fill=tk.X)

    def _build_bg_removal_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text=" 2. Background Removal ", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))

        # Hex Color Row
        color_row = ttk.Frame(frame)
        color_row.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(color_row, text="Key Color (Hex):").pack(side=tk.LEFT)

        self.color_swatch = tk.Label(
            color_row,
            bg=self.bg_color_var.get(),
            width=3,
            relief="solid",
            bd=1,
            cursor="hand2",
        )
        self.color_swatch.pack(side=tk.RIGHT, padx=(4, 0))
        self.color_swatch.bind("<Button-1>", lambda _: self._on_pick_color())

        btn_pick = ttk.Button(color_row, text="Pick", width=6, command=self._on_pick_color)
        btn_pick.pack(side=tk.RIGHT, padx=(4, 0))

        entry_hex = ttk.Entry(color_row, textvariable=self.bg_color_var, width=9)
        entry_hex.pack(side=tk.RIGHT)
        self.bg_color_var.trace_add("write", self._on_hex_entry_change)

        # Tolerance Slider
        tol_header = ttk.Frame(frame)
        tol_header.pack(fill=tk.X)
        ttk.Label(tol_header, text="Chroma Tolerance:").pack(side=tk.LEFT)
        self.tol_val_label = ttk.Label(tol_header, text="35", style="Muted.TLabel")
        self.tol_val_label.pack(side=tk.RIGHT)

        tol_slider = ttk.Scale(
            frame,
            from_=5,
            to=100,
            orient=tk.HORIZONTAL,
            command=lambda val: self._update_int_slider(val, self.tolerance_var, self.tol_val_label),
        )
        tol_slider.set(self.tolerance_var.get())
        tol_slider.pack(fill=tk.X, pady=(4, 0))

    def _build_frame_size_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text=" 3. Target Frame Size (px) ", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))

        grid_frame = ttk.Frame(frame)
        grid_frame.pack(fill=tk.X)
        grid_frame.columnconfigure(1, weight=1)
        grid_frame.columnconfigure(3, weight=1)

        ttk.Label(grid_frame, text="Cell Width:").grid(row=0, column=0, sticky=tk.W, padx=(0, 6))
        sp_width = ttk.Spinbox(grid_frame, from_=8, to=512, textvariable=self.cell_width_var, width=7)
        sp_width.grid(row=0, column=1, sticky=tk.EW, padx=(0, 10))

        ttk.Label(grid_frame, text="Cell Height:").grid(row=0, column=2, sticky=tk.W, padx=(0, 6))
        sp_height = ttk.Spinbox(grid_frame, from_=8, to=512, textvariable=self.cell_height_var, width=7)
        sp_height.grid(row=0, column=3, sticky=tk.EW)

    def _build_pixel_cleaning_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text=" 4. Pixel Cleaning & Crispness ", padding=10)
        frame.pack(fill=tk.X, pady=(0, 12))

        # Palette Quantization Slider
        quant_header = ttk.Frame(frame)
        quant_header.pack(fill=tk.X)
        ttk.Label(quant_header, text="Palette Colors (0 = Off):").pack(side=tk.LEFT)
        self.quant_val_label = ttk.Label(quant_header, text="24", style="Muted.TLabel")
        self.quant_val_label.pack(side=tk.RIGHT)

        quant_slider = ttk.Scale(
            frame,
            from_=0,
            to=64,
            orient=tk.HORIZONTAL,
            command=lambda val: self._update_int_slider(val, self.quantize_colors_var, self.quant_val_label),
        )
        quant_slider.set(self.quantize_colors_var.get())
        quant_slider.pack(fill=tk.X, pady=(4, 10))

        # Scale / Downsample Slider (step 0.05)
        scale_header = ttk.Frame(frame)
        scale_header.pack(fill=tk.X)
        ttk.Label(scale_header, text="Downsample Scale:").pack(side=tk.LEFT)
        self.scale_val_label = ttk.Label(scale_header, text="1.00x", style="Muted.TLabel")
        self.scale_val_label.pack(side=tk.RIGHT)

        self.scale_slider = ttk.Scale(
            frame,
            from_=0.1,
            to=1.0,
            orient=tk.HORIZONTAL,
            command=self._on_scale_slider_move,
        )
        self.scale_slider.set(self.scale_factor_var.get())
        self.scale_slider.pack(fill=tk.X, pady=(4, 10))

        # Hard Alpha Checkbox
        chk_alpha = ttk.Checkbutton(
            frame,
            text="Hard Alpha Threshold (Strip Fringe)",
            variable=self.hard_alpha_var,
        )
        chk_alpha.pack(fill=tk.X, pady=(2, 0))

    def _build_action_buttons(self, parent: ttk.Frame) -> None:
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.btn_preview = ttk.Button(
            btn_frame,
            text="Update Preview",
            command=lambda: self._start_processing(export_files=False),
        )
        self.btn_preview.pack(fill=tk.X, pady=(0, 6))

        self.btn_process_export = ttk.Button(
            btn_frame,
            text="Process & Export",
            style="Accent.TButton",
            command=lambda: self._start_processing(export_files=True),
        )
        self.btn_process_export.pack(fill=tk.X)

    def _build_preview_canvases(self, parent: ttk.Frame) -> None:
        """Creates side-by-side interactive preview panels."""
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        # Left Panel: Original Raw Image
        raw_panel = ttk.Frame(parent, padding=2)
        raw_panel.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 5))

        raw_header = ttk.Label(raw_panel, text="  Original Raw Image", style="Header.TLabel", padding=6)
        raw_header.pack(fill=tk.X)

        self.canvas_raw = tk.Canvas(raw_panel, bg=self.BG_DARK, highlightthickness=1, highlightbackground=self.BORDER_COLOR)
        self.canvas_raw.pack(fill=tk.BOTH, expand=True)
        self.canvas_raw.bind("<Configure>", lambda _: self._render_raw_canvas())

        # Right Panel: Processed Uniform Sprite Sheet
        proc_panel = ttk.Frame(parent, padding=2)
        proc_panel.grid(row=0, column=1, sticky=tk.NSEW, padx=(5, 0))

        proc_header = ttk.Label(
            proc_panel,
            text="  Processed Uniform Sprite Sheet (Alpha Checkerboard)",
            style="Header.TLabel",
            padding=6,
        )
        proc_header.pack(fill=tk.X)

        self.canvas_proc = tk.Canvas(proc_panel, bg=self.BG_DARK, highlightthickness=1, highlightbackground=self.BORDER_COLOR)
        self.canvas_proc.pack(fill=tk.BOTH, expand=True)
        self.canvas_proc.bind("<Configure>", lambda _: self._render_processed_canvas())

    # =========================================================================
    # 2. UI EVENT HANDLERS & VALIDATION
    # =========================================================================

    def _update_int_slider(self, val: str, var: tk.IntVar, label: ttk.Label) -> None:
        int_val = int(round(float(val)))
        var.set(int_val)
        label.configure(text=str(int_val))

    def _on_scale_slider_move(self, val: str) -> None:
        raw_val = float(val)
        # Snap to nearest 0.05 increment
        snapped = round(round(raw_val / 0.05) * 0.05, 2)
        snapped = max(0.10, min(1.00, snapped))
        self.scale_factor_var.set(snapped)
        self.scale_val_label.configure(text=f"{snapped:.2f}x")

    def _on_hex_entry_change(self, *args) -> None:
        hex_str = self.bg_color_var.get().strip()
        if re.fullmatch(r"^#[0-9A-Fa-f]{6}$", hex_str):
            self.color_swatch.configure(bg=hex_str)

    def _on_pick_color(self) -> None:
        current_hex = self.bg_color_var.get().strip()
        if not re.fullmatch(r"^#[0-9A-Fa-f]{6}$", current_hex):
            current_hex = "#FF00FF"
        color = colorchooser.askcolor(color=current_hex, title="Select Background Key Color")
        if color and color[1]:
            self.bg_color_var.set(color[1].upper())

    def _on_browse_input(self) -> None:
        filetypes = [
            ("Supported Images", "*.png *.jpg *.jpeg *.webp"),
            ("PNG Files", "*.png"),
            ("JPEG Files", "*.jpg *.jpeg"),
            ("WebP Files", "*.webp"),
        ]
        path = filedialog.askopenfilename(title="Select Input Sprite Sheet", filetypes=filetypes)
        if not path:
            return

        try:
            img = Image.open(path)
            img.load()
            self.input_file_path = path
            self.raw_pil_image = img.convert("RGBA")
            self.input_path_var.set(path)
            self._render_raw_canvas()
            self.status_var.set(f"Loaded '{os.path.basename(path)}' ({img.width}x{img.height} px).")
            # Automatically run a preview on load
            self._start_processing(export_files=False)
        except Exception as exc:
            messagebox.showerror("Image Load Error", f"Could not open image file:\n{exc}")

    def _on_browse_output(self) -> None:
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_dir_var.set(os.path.abspath(folder))

    def _validate_parameters(self, export_files: bool) -> Optional[Dict]:
        """Validates user inputs before launching the processing thread."""
        if not self.input_file_path or not os.path.isfile(self.input_file_path) or self.raw_pil_image is None:
            messagebox.showwarning("Missing Input Image", "Please select a valid input image first.")
            return None

        hex_val = self.bg_color_var.get().strip()
        if not re.fullmatch(r"^#[0-9A-Fa-f]{6}$", hex_val):
            messagebox.showerror(
                "Invalid Hex Color",
                f"'{hex_val}' is not a valid 6-digit hex color (e.g., #FF00FF).",
            )
            return None

        try:
            cell_w = int(self.cell_width_var.get())
            cell_h = int(self.cell_height_var.get())
            if cell_w < 4 or cell_h < 4:
                raise ValueError("Cell dimensions must be at least 4x4 pixels.")
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror("Invalid Frame Size", f"Please enter valid integer frame dimensions:\n{exc}")
            return None

        out_dir = self.output_dir_var.get().strip()
        if export_files and not out_dir:
            messagebox.showwarning("Missing Output Directory", "Please select an output directory for exporting.")
            return None

        target_rgb = (
            int(hex_val[1:3], 16),
            int(hex_val[3:5], 16),
            int(hex_val[5:7], 16),
        )

        return {
            "target_rgb": target_rgb,
            "tolerance": int(self.tolerance_var.get()),
            "cell_w": cell_w,
            "cell_h": cell_h,
            "num_colors": int(self.quantize_colors_var.get()),
            "scale_factor": float(self.scale_factor_var.get()),
            "hard_alpha": bool(self.hard_alpha_var.get()),
            "output_dir": out_dir,
            "export_files": export_files,
        }

    # =========================================================================
    # 3. THREAD DISPATCH & CANVAS RENDERING
    # =========================================================================

    def _start_processing(self, export_files: bool) -> None:
        if self.is_processing:
            return

        params = self._validate_parameters(export_files)
        if not params:
            return

        self.is_processing = True
        self.btn_process_export.configure(state=tk.DISABLED)
        self.btn_preview.configure(state=tk.DISABLED)
        self.status_var.set("Processing sprite sheet...")

        worker = threading.Thread(
            target=self._processing_worker,
            args=(self.raw_pil_image.copy(), params),
            daemon=True,
        )
        worker.start()

    def _processing_worker(self, source_img: Image.Image, params: Dict) -> None:
        """Runs the OpenCV/Pillow image pipeline on a background thread."""
        try:
            strip_img, metadata = self.process_sprite_sheet(
                source_img=source_img,
                target_rgb=params["target_rgb"],
                tolerance=params["tolerance"],
                cell_w=params["cell_w"],
                cell_h=params["cell_h"],
                num_colors=params["num_colors"],
                scale_factor=params["scale_factor"],
                hard_alpha=params["hard_alpha"],
            )

            export_msg = ""
            if params["export_files"]:
                out_dir = params["output_dir"]
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

            self.root.after(0, self._on_processing_complete, strip_img, status_text, None)

        except ValueError as ve:
            self.root.after(0, self._on_processing_complete, None, "Processing aborted: No frames detected.", str(ve))
        except Exception as exc:
            self.root.after(0, self._on_processing_complete, None, "Error occurred during processing.", str(exc))

    def _on_processing_complete(
        self,
        result_img: Optional[Image.Image],
        status_text: str,
        error_msg: Optional[str],
    ) -> None:
        self.is_processing = False
        self.btn_process_export.configure(state=tk.NORMAL)
        self.btn_preview.configure(state=tk.NORMAL)
        self.status_var.set(status_text)

        if error_msg:
            messagebox.showwarning("Processing Notice", error_msg)
            return

        if result_img is not None:
            self.processed_pil_image = result_img
            self._render_processed_canvas()

    def _render_raw_canvas(self) -> None:
        self.canvas_raw.delete("all")
        if self.raw_pil_image is None:
            self._draw_canvas_placeholder(self.canvas_raw, "Load an input image to preview")
            return

        cw = max(10, self.canvas_raw.winfo_width() - 20)
        ch = max(10, self.canvas_raw.winfo_height() - 20)

        scaled = self._scale_image_to_fit(self.raw_pil_image, cw, ch)
        self.raw_tk_image = ImageTk.PhotoImage(scaled)
        self.canvas_raw.create_image(
            self.canvas_raw.winfo_width() // 2,
            self.canvas_raw.winfo_height() // 2,
            image=self.raw_tk_image,
            anchor=tk.CENTER,
        )

    def _render_processed_canvas(self) -> None:
        self.canvas_proc.delete("all")
        if self.processed_pil_image is None:
            self._draw_canvas_placeholder(self.canvas_proc, "Processed sprite strip will appear here")
            return

        cw = max(10, self.canvas_proc.winfo_width() - 20)
        ch = max(10, self.canvas_proc.winfo_height() - 20)

        scaled_fg = self._scale_image_to_fit(self.processed_pil_image, cw, ch)
        checker_bg = self._create_checkerboard(scaled_fg.width, scaled_fg.height, tile_size=12)
        composited = Image.alpha_composite(checker_bg, scaled_fg)

        self.processed_tk_image = ImageTk.PhotoImage(composited)
        self.canvas_proc.create_image(
            self.canvas_proc.winfo_width() // 2,
            self.canvas_proc.winfo_height() // 2,
            image=self.processed_tk_image,
            anchor=tk.CENTER,
        )

    def _draw_canvas_placeholder(self, canvas: tk.Canvas, text: str) -> None:
        w = max(100, canvas.winfo_width())
        h = max(100, canvas.winfo_height())
        canvas.create_text(w // 2, h // 2, text=text, fill=self.FG_MUTED, font=("Segoe UI", 11))

    @staticmethod
    def _scale_image_to_fit(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
        """Scales an image to fit within (max_w, max_h) using NEAREST resampling to preserve crisp pixels."""
        if img.width <= 0 or img.height <= 0:
            return img
        scale = min(max_w / img.width, max_h / img.height)
        # Cap upscale at 8x so tiny strips remain crisp without overflowing memory
        scale = min(scale, 8.0)
        new_w = max(1, int(round(img.width * scale)))
        new_h = max(1, int(round(img.height * scale)))
        return img.resize((new_w, new_h), Image.Resampling.NEAREST)

    @staticmethod
    def _create_checkerboard(width: int, height: int, tile_size: int = 12) -> Image.Image:
        """Generates a dark-themed RGBA checkerboard image to visualize transparency."""
        color_a = np.array([30, 30, 46, 255], dtype=np.uint8)
        color_b = np.array([49, 50, 68, 255], dtype=np.uint8)

        y_idx = np.arange(height) // tile_size
        x_idx = np.arange(width) // tile_size
        grid = (y_idx[:, None] + x_idx[None, :]) % 2

        checker = np.where(grid[:, :, None] == 0, color_a, color_b)
        return Image.fromarray(checker, mode="RGBA")

    # =========================================================================
    # 4. PURE COMPUTER VISION & IMAGE PROCESSING PIPELINE
    # =========================================================================

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
        """
        Executes the complete sprite cleaning, contour detection, quantization,
        and ground-aligned normalization pipeline.
        """
        # --- Step 1: Chroma-Keying & Edge Cleanup ---
        rgba_img = source_img.convert("RGBA")
        rgba_np = np.array(rgba_img, dtype=np.uint8)

        rgb_float = rgba_np[:, :, :3].astype(np.float32)
        alpha_channel = rgba_np[:, :, 3].copy()

        target_vec = np.array(target_rgb, dtype=np.float32).reshape((1, 1, 3))
        euclidean_dist = np.linalg.norm(rgb_float - target_vec, axis=2)

        # Zero out pixels matching background color within tolerance
        alpha_channel[euclidean_dist <= float(tolerance)] = 0

        # Morphological opening (2x2 kernel) to eliminate stray 1-pixel background artifacts
        kernel = np.ones((2, 2), dtype=np.uint8)
        cleaned_alpha = cv2.morphologyEx(alpha_channel, cv2.MORPH_OPEN, kernel)

        # Snap alpha channel: > 128 -> 255, <= 128 -> 0
        if hard_alpha:
            cleaned_alpha = np.where(cleaned_alpha > 128, 255, 0).astype(np.uint8)
            binary_mask = cleaned_alpha.copy()
        else:
            binary_mask = np.where(cleaned_alpha > 16, 255, 0).astype(np.uint8)

        # --- Step 2: Contour & Frame Detection ---
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_area_threshold = 16  # Filter out tiny noise specks (< 4x4 area)
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
        # Zero out RGB values on completely transparent pixels to prevent color bleed during quantization
        transparent_mask = cleaned_alpha == 0
        rgba_np[transparent_mask, :3] = 0

        if num_colors > 0:
            rgb_pil = Image.fromarray(rgba_np[:, :, :3], mode="RGB")
            quantized_rgb = rgb_pil.quantize(
                colors=num_colors,
                method=Image.Quantize.MEDIANCUT,
            ).convert("RGB")
            working_img = quantized_rgb.convert("RGBA")
            # Reapply the exact alpha mask after quantization
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
            cropped_frame = working_img.crop((bx, by, bx + bw, bh + by))

            # Apply user nearest-neighbor downsampling scale factor
            if not math.isclose(scale_factor, 1.0, abs_tol=1e-3):
                scaled_w = max(1, int(round(cropped_frame.width * scale_factor)))
                scaled_h = max(1, int(round(cropped_frame.height * scale_factor)))
                cropped_frame = cropped_frame.resize((scaled_w, scaled_h), Image.Resampling.NEAREST)

            # Fit-check: preserve aspect ratio if sprite exceeds target cell boundaries
            if cropped_frame.width > max_avail_w or cropped_frame.height > max_avail_h:
                fit_ratio = min(max_avail_w / cropped_frame.width, max_avail_h / cropped_frame.height)
                fit_w = max(1, int(math.floor(cropped_frame.width * fit_ratio)))
                fit_h = max(1, int(math.floor(cropped_frame.height * fit_ratio)))
                cropped_frame = cropped_frame.resize((fit_w, fit_h), Image.Resampling.NEAREST)

            # Bottom-Center Ground Alignment (2px floor padding)
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
        """
        Sorts bounding boxes in reading order: primary by row (Y-bucketed)
        and secondary by column (left-to-right X).
        """
        if not boxes:
            return []

        # Calculate median height to determine row bucketing tolerance
        heights = sorted(b[3] for b in boxes)
        median_h = heights[len(heights) // 2]
        row_tolerance = max(8.0, median_h * 0.5)

        # Sort initially by vertical center (y + h/2)
        boxes_by_y = sorted(boxes, key=lambda b: b[1] + b[3] * 0.5)

        rows: List[List[Tuple[int, int, int, int]]] = []
        row_centers: List[float] = []

        for box in boxes_by_y:
            cy = box[1] + box[3] * 0.5
            placed = False
            for idx, r_center in enumerate(row_centers):
                if abs(cy - r_center) <= row_tolerance:
                    rows[idx].append(box)
                    # Update running mean vertical center of the row
                    row_centers[idx] = sum(b[1] + b[3] * 0.5 for b in rows[idx]) / len(rows[idx])
                    placed = True
                    break
            if not placed:
                rows.append([box])
                row_centers.append(cy)

        # Sort each row left-to-right by x coordinate and flatten
        sorted_boxes: List[Tuple[int, int, int, int]] = []
        for row in rows:
            row.sort(key=lambda b: b[0])
            sorted_boxes.extend(row)

        return sorted_boxes


def main() -> None:
    root = tk.Tk()
    SpriteConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()