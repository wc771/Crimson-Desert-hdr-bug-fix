# Crimson-Desert-hdr-bug-fix
For fixing the bgr screenshot bug in crimson desert


# ⚠️ Disclaimer
# I vibe coded this. 
I have a CISSP, which means I can tell you exactly how this could be weaponized in a threat model — but I cannot promise the code is pretty, optimal, or won't do something unexpected on your machine. It worked on mine. Claude wrote most of it. I pointed at the problem and said "fix this."
Use at your own risk, don't run it on anything you haven't backed up, and if you're a real developer and something in here makes you physically recoil, feel free to open a PR. Idk what the hell a PR is, but the AI that I poked and prodded added that bit.
This is a community tool for a game bug that shouldn't exist. It is not affiliated with Pearl Abyss in any way.
Dont be evil and add nasty stuff to the script and then self distribute it either.
___________________________________________________________________________________________________________________________________________________________________________________________________



# Crimson Desert HDR Screenshot Fix
Crimson Desert has a bug in its screenshot tool when HDR is enabled: screenshots are saved as PNGs with the red and blue channels swapped (BGR instead of RGB), because the game dumps the DirectX BGRA surface to disk directly without reordering the channels. The files also use PQ (ST.2084) transfer function encoding with no embedded ICC profile, so they appear washed out, dark, or color-shifted when opened in any standard image viewer.
This repo provides two tools to fix affected screenshots:

hdr_to_sdr.py — command-line script for single files or batch processing
hdr_converter_gui.py — GUI version with drag-and-drop folder support, live settings, and a progress log

# What the tools do
Swap R and B channels back to correct RGB order
Decode PQ (ST.2084) EOTF to linear light (nits)
Apply a tone mapping operator to fit HDR luminance into SDR range
Apply sRGB gamma (OETF) and save as a standard 8-bit PNG

# Requirements
pip install pillow numpy
tkinter is required for the GUI and is included with standard Python on Windows. On Linux you may need sudo apt install python3-tk.
# CLI usage
bash# Single file, default settings (ACES tone map)
python hdr_to_sdr.py screenshot.png

# Specify output path
python hdr_to_sdr.py screenshot.png -o screenshot_fixed.png

# Batch — saves each as *_fixed.png
python hdr_to_sdr.py *.png

# Choose a different tone map or adjust brightness
python hdr_to_sdr.py screenshot.png --tone-map hable --brightness 1.1
#GUI usage
bashpython hdr_converter_gui.py
Add individual files with ＋ Add Files or scan a whole folder with 📁 Add Folder, adjust tone map and brightness, then click Convert All. Output goes alongside the originals with a _fixed suffix by default; a custom output directory can be specified.
#Tone map options
OptionCharacterBest forACES (default)Filmic, contrasty S-curve, compressed highlightsMost screenshots; cinematic lookHableFilmic but gentler highlight rolloffWell-lit scenes where ACES feels too punchyReinhardSimple, smooth, low-contrast rolloffAlready well-exposed images; preserves original color character

# Notes
Output files have no embedded ICC profile (same as source); they will display correctly in any sRGB viewer.
Alpha channels are preserved if present.
The tools do not modify the original files; originals are left untouched.



# Before
<img width="3440" height="1440" alt="screenshot_2026-04-02_003919" src="https://github.com/user-attachments/assets/2591412a-5618-4ff7-b65f-26b3dd882b73" />
<img width="3440" height="1440" alt="screenshot_2026-04-02_003930" src="https://github.com/user-attachments/assets/395f1465-813f-4831-b819-505a78100cca" />
<img width="3440" height="1440" alt="screenshot_2026-04-07_210350" src="https://github.com/user-attachments/assets/5f43d586-3c40-45f9-b778-ef5fd1784ce5" />
<img width="3440" height="1440" alt="screenshot_2026-04-07_210146" src="https://github.com/user-attachments/assets/58eefc6a-5296-4f74-a535-3bd6cbc4f953" />
<img width="3440" height="1440" alt="screenshot_2026-04-07_210440" src="https://github.com/user-attachments/assets/2e9892c6-9e3d-4a69-851d-5bee2bbe63d1" />


# After - Options Selected -> Tone Map Reinhard + Brightness 2.0
<img width="3440" height="1440" alt="screenshot_2026-04-02_003919_fixed" src="https://github.com/user-attachments/assets/3412010e-52d1-4a8a-9f53-6f4b2227a932" />
<img width="3440" height="1440" alt="screenshot_2026-04-02_003930_fixed" src="https://github.com/user-attachments/assets/0fdabbe9-97ff-48c6-a8d8-febde14e26f1" />
<img width="3440" height="1440" alt="screenshot_2026-04-07_210350_fixed" src="https://github.com/user-attachments/assets/116dfec8-f1d6-49f0-b8f4-e56e6a8c684c" />
<img width="3440" height="1440" alt="screenshot_2026-04-07_210146_fixed" src="https://github.com/user-attachments/assets/8e611dfd-6e01-40b1-9cf4-490f0e5bb8a1" />
<img width="3440" height="1440" alt="screenshot_2026-04-07_210440_fixed" src="https://github.com/user-attachments/assets/86231821-71df-428a-81b8-e070d70c7e3f" />





















