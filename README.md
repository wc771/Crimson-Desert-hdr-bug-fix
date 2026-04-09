# Crimson-Desert-hdr-bug-fix
For fixing the bgr screenshot bug in crimson desert


⚠️ Disclaimer
I vibe coded this. I have a CISSP, which means I can tell you exactly how this could be weaponized in a threat model — but I cannot promise the code is pretty, optimal, or won't do something unexpected on your machine. It worked on mine. Claude wrote most of it. I pointed at the problem and said "fix this."
Use at your own risk, don't run it on anything you haven't backed up, and if you're a real developer and something in here makes you physically recoil, feel free to open a PR. I will merge it and feel no shame.
This is a community tool for a game bug that shouldn't exist. It is not affiliated with Pearl Abyss in any way.
___________________________________________________________________________________________________________________________________________________________________________________________________



Crimson Desert HDR Screenshot Fix
Crimson Desert has a bug in its screenshot tool when HDR is enabled: screenshots are saved as PNGs with the red and blue channels swapped (BGR instead of RGB), because the game dumps the DirectX BGRA surface to disk directly without reordering the channels. The files also use PQ (ST.2084) transfer function encoding with no embedded ICC profile, so they appear washed out, dark, or color-shifted when opened in any standard image viewer.
This repo provides two tools to fix affected screenshots:

hdr_to_sdr.py — command-line script for single files or batch processing
hdr_converter_gui.py — GUI version with drag-and-drop folder support, live settings, and a progress log

What the tools do

Swap R and B channels back to correct RGB order
Decode PQ (ST.2084) EOTF to linear light (nits)
Apply a tone mapping operator to fit HDR luminance into SDR range
Apply sRGB gamma (OETF) and save as a standard 8-bit PNG

Requirements
pip install pillow numpy
tkinter is required for the GUI and is included with standard Python on Windows. On Linux you may need sudo apt install python3-tk.
CLI usage
bash# Single file, default settings (ACES tone map)
python hdr_to_sdr.py screenshot.png

# Specify output path
python hdr_to_sdr.py screenshot.png -o screenshot_fixed.png

# Batch — saves each as *_fixed.png
python hdr_to_sdr.py *.png

# Choose a different tone map or adjust brightness
python hdr_to_sdr.py screenshot.png --tone-map hable --brightness 1.1
GUI usage
bashpython hdr_converter_gui.py
Add individual files with ＋ Add Files or scan a whole folder with 📁 Add Folder, adjust tone map and brightness, then click Convert All. Output goes alongside the originals with a _fixed suffix by default; a custom output directory can be specified.
Tone map options
OptionCharacterBest forACES (default)Filmic, contrasty S-curve, compressed highlightsMost screenshots; cinematic lookHableFilmic but gentler highlight rolloffWell-lit scenes where ACES feels too punchyReinhardSimple, smooth, low-contrast rolloffAlready well-exposed images; preserves original color character
Notes

Output files have no embedded ICC profile (same as source); they will display correctly in any sRGB viewer.
Alpha channels are preserved if present.
The tools do not modify the original files; originals are left untouched.
