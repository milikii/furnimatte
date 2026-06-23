@echo off
chcp 65001 >nul
REM furniture_cutout 启动脚本

if not exist .venv (
    echo 请先运行 install.bat 完成安装
    exit /b 1
)

call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo 请先运行 install.bat 完成安装
    exit /b 1
)

REM 确保下载有进度显示（可选）
set HF_HUB_DISABLE_PROGRESS_BARS=0

python app.py
if errorlevel 1 (
    echo 程序异常退出，详见 logs\app.log
    pause
)
