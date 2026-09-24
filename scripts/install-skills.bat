@echo off
chcp 65001 >nul
REM Codeteam skills 安装器：双击即可在任何电脑安装
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-skills.ps1"
pause
