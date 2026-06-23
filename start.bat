@echo off
chcp 65001 >nul

echo ========================================
echo  Furniture Cutout — 启动
echo ========================================

if not exist .venv\ (
    echo [错误] 未检测到虚拟环境，请先运行 install.bat
    exit /b 1
)

call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 激活虚拟环境失败
    pause
    exit /b 1
)

set HF_HUB_DISABLE_PROGRESS_BARS=0

python app.py
if errorlevel 1 (
    echo [错误] 程序异常退出，详见 logs\app.log
    pause
)
