@echo off
REM Curious Mind - Pilot 01 render (Windows 10)
REM   tools\render\render_pilot.bat                -> final render (requires courtyard plates)
REM   tools\render\render_pilot.bat --test-plates  -> pipeline test render with TEST plates
cd /d "%~dp0\..\.."
python tools\render\render.py pilot\PILOT_01_STOP_TIME %*
if errorlevel 1 (
  echo.
  echo Render did not complete. See messages above.
  exit /b %errorlevel%
)
