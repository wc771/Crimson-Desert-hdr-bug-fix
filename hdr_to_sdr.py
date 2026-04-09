#!/usr/bin/env python3
"""
Crimson Desert HDR Screenshot Converter
Fixes screenshots saved by the in-game tool when HDR is enabled.

The game saves PNGs with:
  - R and B channels swapped (DirectX BGRA surface dumped directly)
  - PQ (ST.2084) transfer function encoding
  - No ICC profile embedded

This script corrects the channel swap, decodes PQ to linear light,
and tone maps to SDR sRGB.

Usage:
    python hdr_to_sdr.py screenshot.png
    python hdr_to_sdr.py *.png               # batch, saves as *_fixed.png
    python hdr_to_sdr.py shot.png -o out.png
    python hdr_to_sdr.py shot.png --tone-map hable
    python hdr_to_sdr.py shot.png --brightness 1.1
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image


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
        return ((x * (A * x + C * B) + D * E) / (x * (A * x + B) + D * F)) - E / F
    x = nits / peak * 2.0
    return np.clip(f(x) / f(11.2 / peak * 2.0), 0.0, 1.0)


def tonemap_reinhard(nits, peak):
    x = nits / peak
    return x / (1.0 + x)


TONE_MAPS = {"aces": tonemap_aces, "hable": tonemap_hable, "reinhard": tonemap_reinhard}


def convert(src, dst, tone_map="aces", brightness=1.0):
    img = Image.open(src)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")

    arr = np.array(img, dtype=np.float32)
    has_alpha = arr.shape[2] == 4
    alpha = arr[:, :, 3].astype(np.uint8) if has_alpha else None

    raw = arr[:, :, :3]

    # Fix BGR→RGB channel swap (DirectX BGRA surface saved without reordering)
    rgb = raw.copy()
    rgb[:, :, 0] = raw[:, :, 2]
    rgb[:, :, 2] = raw[:, :, 0]

    # PQ EOTF → linear nits
    nits = pq_eotf(rgb / 255.0)

    # Tone map
    linear = TONE_MAPS[tone_map](nits, float(nits.max()))

    if brightness != 1.0:
        linear = np.clip(linear * brightness, 0.0, 1.0)

    out8 = (srgb_oetf(linear) * 255.0 + 0.5).astype(np.uint8)
    result = Image.fromarray(out8, "RGB")
    if has_alpha and alpha is not None:
        result.putalpha(Image.fromarray(alpha))

    result.save(dst, icc_profile=None)
    print(f"  ✓  {Path(src).name}  →  {Path(dst).name}")


def main():
    parser = argparse.ArgumentParser(description="Fix Crimson Desert HDR screenshots.")
    parser.add_argument("inputs", nargs="+", help="PNG screenshot(s)")
    parser.add_argument("-o", "--output", help="Output path (single file only)")
    parser.add_argument("--tone-map", choices=list(TONE_MAPS), default="aces")
    parser.add_argument("--brightness", type=float, default=1.0)
    args = parser.parse_args()

    inputs = [Path(p) for p in args.inputs]
    if args.output and len(inputs) > 1:
        parser.error("--output can only be used with a single input file")

    for src in inputs:
        if not src.exists():
            print(f"  ✗  {src}: not found", file=sys.stderr)
            continue
        dst = Path(args.output) if args.output else src.with_name(src.stem + "_fixed" + src.suffix)
        convert(src, dst, tone_map=args.tone_map, brightness=args.brightness)


if __name__ == "__main__":
    main()
