@echo off
cd /d %~dp0

REM Check if icon exists
if not exist cie256x256.ico (
    echo ERROR: Icon file cie256x256.ico not found!
    pause
    exit /b
)

poetry run pip install pyinstaller

REM Remove previous build/dist folders
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q __pycache__
del /q LedCAL.spec

REM Build the executable with GUI window (no console)
poetry run pyinstaller ^
  --noconsole ^
  --onefile ^
  --icon=cie256x256.ico ^
  --add-data "cie256x256.ico;." ^
  --add-data "Luxshare640.png;." ^
  --add-binary "ch341/CH341DLLA64.DLL;ch341" ^
  --hidden-import ch341.ch341 ^
  --additional-hooks-dir=. ^
  LedCAL.py

copy dist\LedCAL.exe .

echo Build complete.
