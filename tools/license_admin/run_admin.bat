@echo off
echo Starting License Admin Tool...
cd /d "%~dp0"
cd ..\..
.venv\Scripts\python tools\license_admin\main.py
pause
