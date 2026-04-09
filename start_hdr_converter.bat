@echo off
setlocal

:: ── Crimson Desert HDR Fix — Launcher ───────────────────────────────────────
title Crimson Desert HDR Fix

:: Check for the main script in the same directory
if not exist "%~dp0hdr_converter_gui.py" (
    echo.
    echo  [ERROR] hdr_converter_gui.py not found in this folder.
    echo  Make sure this launcher is in the same folder as the script.
    echo.
    pause
    exit /b 1
)

:: Check Python is installed and on PATH
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Python was not found.
    echo  Download and install Python from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

:: Check Pillow
python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo  [INFO] Pillow not found. Installing...
    pip install pillow
    if errorlevel 1 (
        echo.
        echo  [ERROR] Failed to install Pillow. Try running: pip install pillow
        echo.
        pause
        exit /b 1
    )
    echo  [OK] Pillow installed.
)

:: Check numpy
python -c "import numpy" >nul 2>&1
if errorlevel 1 (
    echo  [INFO] numpy not found. Installing...
    pip install numpy
    if errorlevel 1 (
        echo.
        echo  [ERROR] Failed to install numpy. Try running: pip install numpy
        echo.
        pause
        exit /b 1
    )
    echo  [OK] numpy installed.
)

:: Check tkinter
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] tkinter is not available.
    echo  This is included with standard Python on Windows.
    echo  Try reinstalling Python from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: All good — launch
echo  [OK] All dependencies found. Launching...
echo.
python "%~dp0hdr_converter_gui.py"