@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -u run_updater_1.4.py
pause
