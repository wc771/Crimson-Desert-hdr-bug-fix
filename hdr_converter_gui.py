#!/usr/bin/env python3
"""
Crimson Desert HDR Screenshot Converter — GUI
Drag a folder or pick individual files to fix BGR-swapped PQ-encoded HDR screenshots.

Requirements: pip install pillow numpy
(tkinter is included with standard Python on Windows/Mac/Linux)
"""

import threading
import tkinter as tk
from tkinter import filedialog, ttk
from pathlib import Path

import numpy as np
from PIL import Image, ImageTk


# ── Conversion pipeline ─────────────────────────────────────────────────────────

def pq_eotf(v):
    v = np.clip(v, 0.0, 1.0)
    m1, m2 = 0.1593017578125, 78.84375
    c1, c2, c3 = 0.8359375, 18.8515625, 18.6875
    num = np.maximum(v ** (1.0 / m2) - c1, 0.0)
    den = c2 - c3 * v ** (1.0 / m2)
    return 10000.0 * (num / den) ** (1.0 / m1)

def srgb_oetf(v):
    v = np.clip(v, 0.0, 1.0)
    return np.where(v <= 0.0031308, v * 12.92, 1.055 * v ** (1.0 / 2.4) - 0.055)

def tonemap_aces(nits, peak):
    x = nits / peak
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0)

def tonemap_hable(nits, peak):
    def f(x):
        A, B, C, D, E, F = 0.22, 0.30, 0.10, 0.20, 0.01, 0.30
        return ((x*(A*x+C*B)+D*E) / (x*(A*x+B)+D*F)) - E/F
    x = nits / peak * 2.0
    return np.clip(f(x) / f(11.2 / peak * 2.0), 0.0, 1.0)

def tonemap_reinhard(nits, peak):
    x = nits / peak
    return x / (1.0 + x)

TONE_MAPS = {"ACES": tonemap_aces, "Hable": tonemap_hable, "Reinhard": tonemap_reinhard}

def convert_image(src: Path, dst: Path, tone_map: str, brightness: float):
    img = Image.open(src)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    arr = np.array(img, dtype=np.float32)
    has_alpha = arr.shape[2] == 4
    alpha = arr[:, :, 3].astype(np.uint8) if has_alpha else None
    raw = arr[:, :, :3]
    rgb = raw.copy()
    rgb[:, :, 0] = raw[:, :, 2]   # BGR → RGB swap
    rgb[:, :, 2] = raw[:, :, 0]
    nits = pq_eotf(rgb / 255.0)
    linear = TONE_MAPS[tone_map](nits, float(nits.max()))
    if brightness != 1.0:
        linear = np.clip(linear * brightness, 0.0, 1.0)
    out8 = (srgb_oetf(linear) * 255.0 + 0.5).astype(np.uint8)
    result = Image.fromarray(out8, "RGB")
    if has_alpha and alpha is not None:
        result.putalpha(Image.fromarray(alpha))
    result.save(dst, icc_profile=None)


# ── GUI ─────────────────────────────────────────────────────────────────────────

BG       = "#0e0e12"
SURFACE  = "#17171f"
PANEL    = "#1e1e2a"
BORDER   = "#2a2a3a"
ACCENT   = "#c8a96e"       # warm gold
ACCENT2  = "#6e9ec8"       # cool blue
TEXT     = "#e8e4dc"
SUBTEXT  = "#7a7a8a"
SUCCESS  = "#6ec88a"
ERROR    = "#c86e6e"
FONT     = ("Georgia", 11)
FONT_SM  = ("Georgia", 9)
FONT_LG  = ("Georgia", 15, "bold")
MONO     = ("Courier New", 9)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Crimson Desert · HDR Fix")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(680, 520)

        self.files: list[Path] = []
        self.tone_var   = tk.StringVar(value="ACES")
        self.bright_var = tk.DoubleVar(value=1.0)
        self.suffix_var = tk.StringVar(value="_fixed")
        self.same_dir   = tk.BooleanVar(value=True)
        self.out_dir    = tk.StringVar(value="")
        self.running    = False

        self._build()
        self._center()

    # ── layout ──────────────────────────────────────────────────────────────────

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(20, 0))
        tk.Label(hdr, text="HDR FIX", font=("Georgia", 22, "bold"),
                 bg=BG, fg=ACCENT).pack(side="left")
        tk.Label(hdr, text="  ·  Crimson Desert screenshot converter",
                 font=FONT, bg=BG, fg=SUBTEXT).pack(side="left", pady=6)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, pady=12)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_left(body)
        self._build_right(body)

        # Footer log
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(8,0))
        log_frame = tk.Frame(self, bg=SURFACE)
        log_frame.pack(fill="x", padx=24, pady=(0, 16))

        self.log = tk.Text(log_frame, height=6, bg=SURFACE, fg=SUBTEXT,
                           font=MONO, relief="flat", bd=0,
                           state="disabled", wrap="word")
        self.log.pack(fill="x", padx=8, pady=6)

        self._log("Ready. Add files or a folder to begin.")

    def _build_left(self, parent):
        left = tk.Frame(parent, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        left.rowconfigure(1, weight=1)

        # Drop zone / buttons
        drop_row = tk.Frame(left, bg=BG)
        drop_row.pack(fill="x", pady=(0, 8))

        self._btn(drop_row, "＋ Add Files", self._pick_files).pack(side="left", padx=(0,8))
        self._btn(drop_row, "📁 Add Folder", self._pick_folder).pack(side="left", padx=(0,8))
        self._btn(drop_row, "✕ Clear", self._clear_files,
                  fg=SUBTEXT).pack(side="right")

        # File list
        list_frame = tk.Frame(left, bg=PANEL, bd=0,
                               highlightbackground=BORDER, highlightthickness=1)
        list_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, bg=PANEL, troughcolor=PANEL,
                                  relief="flat", bd=0)
        scrollbar.pack(side="right", fill="y")

        self.file_list = tk.Listbox(
            list_frame, bg=PANEL, fg=TEXT, font=FONT_SM,
            selectbackground=ACCENT, selectforeground=BG,
            relief="flat", bd=0, activestyle="none",
            yscrollcommand=scrollbar.set,
            highlightthickness=0,
        )
        self.file_list.pack(fill="both", expand=True, padx=4, pady=4)
        scrollbar.config(command=self.file_list.yview)

        self.count_label = tk.Label(left, text="No files added",
                                    bg=BG, fg=SUBTEXT, font=FONT_SM)
        self.count_label.pack(anchor="w", pady=(4, 0))

    def _build_right(self, parent):
        right = tk.Frame(parent, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")

        # Tone map
        self._section(right, "Tone Map")
        for name in TONE_MAPS:
            rb = tk.Radiobutton(right, text=name, variable=self.tone_var,
                                value=name, bg=BG, fg=TEXT,
                                selectcolor=BG, activebackground=BG,
                                activeforeground=ACCENT, font=FONT,
                                indicatoron=True)
            rb.pack(anchor="w", padx=8)

        tk.Frame(right, bg=BORDER, height=1).pack(fill="x", pady=12)

        # Brightness
        self._section(right, "Brightness")
        bright_row = tk.Frame(right, bg=BG)
        bright_row.pack(fill="x", padx=8)

        self.bright_label = tk.Label(bright_row, text="1.00×",
                                      bg=BG, fg=ACCENT, font=FONT, width=5)
        self.bright_label.pack(side="right")

        slider = tk.Scale(bright_row, from_=0.5, to=2.0, resolution=0.05,
                           orient="horizontal", variable=self.bright_var,
                           bg=BG, fg=TEXT, troughcolor=PANEL,
                           highlightthickness=0, relief="flat",
                           showvalue=False, length=120,
                           command=self._on_bright_change)
        slider.pack(side="left", fill="x", expand=True)

        tk.Frame(right, bg=BORDER, height=1).pack(fill="x", pady=12)

        # Output
        self._section(right, "Output")
        tk.Radiobutton(right, text="Same folder as source", variable=self.same_dir,
                       value=True, bg=BG, fg=TEXT, selectcolor=BG,
                       activebackground=BG, activeforeground=ACCENT,
                       font=FONT_SM).pack(anchor="w", padx=8)

        out_row = tk.Frame(right, bg=BG)
        out_row.pack(fill="x", padx=8, pady=(2,0))
        tk.Radiobutton(out_row, text="Custom:", variable=self.same_dir,
                       value=False, bg=BG, fg=TEXT, selectcolor=BG,
                       activebackground=BG, activeforeground=ACCENT,
                       font=FONT_SM).pack(side="left")
        self._btn(out_row, "…", self._pick_out_dir,
                  padx=4, pady=1).pack(side="left", padx=4)

        self.out_label = tk.Label(right, textvariable=self.out_dir,
                                   bg=BG, fg=SUBTEXT, font=FONT_SM,
                                   wraplength=160, justify="left")
        self.out_label.pack(anchor="w", padx=8)

        suffix_row = tk.Frame(right, bg=BG)
        suffix_row.pack(fill="x", padx=8, pady=(8, 0))
        tk.Label(suffix_row, text="Suffix:", bg=BG, fg=SUBTEXT, font=FONT_SM).pack(side="left")
        tk.Entry(suffix_row, textvariable=self.suffix_var,
                 bg=PANEL, fg=TEXT, font=FONT_SM, relief="flat",
                 insertbackground=TEXT, width=10,
                 highlightbackground=BORDER, highlightthickness=1).pack(side="left", padx=6)

        tk.Frame(right, bg=BORDER, height=1).pack(fill="x", pady=12)

        # Convert button
        self.go_btn = self._btn(right, "Convert All", self._start_conversion,
                                 bg=ACCENT, fg=BG, font=("Georgia", 12, "bold"),
                                 padx=12, pady=8)
        self.go_btn.pack(fill="x", padx=8)

        # Progress
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("HDR.Horizontal.TProgressbar",
                         troughcolor=PANEL, background=ACCENT,
                         darkcolor=ACCENT, lightcolor=ACCENT,
                         bordercolor=BORDER)
        self.progress = ttk.Progressbar(right, style="HDR.Horizontal.TProgressbar",
                                         mode="determinate", length=160)
        self.progress.pack(fill="x", padx=8, pady=(8,0))

        self.status_label = tk.Label(right, text="", bg=BG, fg=SUBTEXT, font=FONT_SM)
        self.status_label.pack(anchor="w", padx=8)

    # ── helpers ─────────────────────────────────────────────────────────────────

    def _btn(self, parent, text, cmd, bg=PANEL, fg=TEXT,
             font=FONT, padx=10, pady=4, **kw):
        b = tk.Button(parent, text=text, command=cmd,
                      bg=bg, fg=fg, font=font,
                      relief="flat", bd=0, cursor="hand2",
                      activebackground=ACCENT, activeforeground=BG,
                      padx=padx, pady=pady, **kw)
        b.bind("<Enter>", lambda e: b.config(bg=ACCENT if bg==PANEL else ACCENT2, fg=BG))
        b.bind("<Leave>", lambda e: b.config(bg=bg, fg=fg))
        return b

    def _section(self, parent, text):
        tk.Label(parent, text=text.upper(), bg=BG, fg=ACCENT,
                 font=("Georgia", 9, "bold")).pack(anchor="w", padx=8, pady=(4,2))

    def _log(self, msg, color=None):
        self.log.config(state="normal")
        tag = f"c{id(msg)}"
        self.log.insert("end", msg + "\n", tag)
        if color:
            self.log.tag_config(tag, foreground=color)
        self.log.see("end")
        self.log.config(state="disabled")

    def _center(self):
        self.update_idletasks()
        w, h = 720, 560
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _on_bright_change(self, val):
        self.bright_label.config(text=f"{float(val):.2f}×")

    # ── file management ─────────────────────────────────────────────────────────

    def _add_files(self, paths):
        added = 0
        for p in paths:
            p = Path(p)
            if p.suffix.lower() in (".png", ".jpg", ".jpeg") and p not in self.files:
                self.files.append(p)
                self.file_list.insert("end", p.name)
                added += 1
        n = len(self.files)
        self.count_label.config(text=f"{n} file{'s' if n != 1 else ''} queued")
        if added:
            self._log(f"Added {added} file(s).")

    def _pick_files(self):
        paths = filedialog.askopenfilenames(
            title="Select screenshots",
            filetypes=[("Images", "*.png *.jpg *.jpeg"), ("All", "*.*")])
        if paths:
            self._add_files(paths)

    def _pick_folder(self):
        folder = filedialog.askdirectory(title="Select screenshot folder")
        if folder:
            folder = Path(folder)
            imgs = list(folder.glob("*.png")) + list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg"))
            if imgs:
                self._add_files(imgs)
                self._log(f"Scanned folder: {folder.name} — found {len(imgs)} image(s).")
            else:
                self._log(f"No PNG/JPG images found in {folder.name}.", color=ERROR)

    def _pick_out_dir(self):
        folder = filedialog.askdirectory(title="Choose output folder")
        if folder:
            self.out_dir.set(folder)
            self.same_dir.set(False)

    def _clear_files(self):
        self.files.clear()
        self.file_list.delete(0, "end")
        self.count_label.config(text="No files added")
        self.progress["value"] = 0
        self.status_label.config(text="")
        self._log("File list cleared.")

    # ── conversion ──────────────────────────────────────────────────────────────

    def _start_conversion(self):
        if self.running:
            return
        if not self.files:
            self._log("No files queued.", color=ERROR)
            return
        if not self.same_dir.get() and not self.out_dir.get():
            self._log("Please choose an output folder.", color=ERROR)
            return

        self.running = True
        self.go_btn.config(state="disabled", text="Converting…")
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.files)

        threading.Thread(target=self._run_conversion, daemon=True).start()

    def _run_conversion(self):
        tone    = self.tone_var.get()
        bright  = self.bright_var.get()
        suffix  = self.suffix_var.get() or "_fixed"
        ok = err = 0

        for i, src in enumerate(self.files):
            try:
                if self.same_dir.get():
                    dst = src.with_name(src.stem + suffix + src.suffix)
                else:
                    dst = Path(self.out_dir.get()) / (src.stem + suffix + src.suffix)

                convert_image(src, dst, tone, bright)
                self._log(f"✓  {src.name}", color=SUCCESS)
                ok += 1
            except Exception as ex:
                self._log(f"✗  {src.name}: {ex}", color=ERROR)
                err += 1

            self.progress["value"] = i + 1
            self.status_label.config(text=f"{i+1} / {len(self.files)}")

        summary = f"Done — {ok} converted"
        if err:
            summary += f", {err} failed"
        self._log(summary, color=SUCCESS if not err else ACCENT)
        self.status_label.config(text=summary)
        self.go_btn.config(state="normal", text="Convert All")
        self.running = False


if __name__ == "__main__":
    app = App()
    app.mainloop()
