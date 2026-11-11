@echo off
setlocal
cd /d "%~dp0"

REM Python 3.15 environment
py -3.15 --version >nul 2>nul
if errorlevel 1 (
  echo Python 3.15 was not found by the Python launcher.
  echo Check that Python 3.15 is installed, then run: py -0p
  pause
  exit /b 1
)

REM Recreate virtual environment if it was created with another Python version.
if exist ".venv\pyvenv.cfg" (
  findstr /c:"version = 3.15." ".venv\pyvenv.cfg" >nul
  if errorlevel 1 (
    echo Removing old virtual environment...
    rmdir /s /q ".venv"
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating Python 3.15 virtual environment...
  py -3.15 -m venv .venv
  if errorlevel 1 goto :failed
)

REM PyYAML has no CPython 3.15 Windows wheel in this release.
REM Disable its optional LibYAML C extension so it installs in pure Python mode.
set PYYAML_FORCE_LIBYAML=0

echo Upgrading pip build tools...
".venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :failed

echo Installing application dependencies for Python 3.15...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :failed

echo.
echo Starting AI Image Check...
echo Open http://127.0.0.1:5000 in your browser.
".venv\Scripts\python.exe" app.py
pause
exit /b 0

:failed
echo.
echo Installation failed. Send a screenshot of the last 20 lines.
pause
exit /b 1
