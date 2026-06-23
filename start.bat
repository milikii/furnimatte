@echo off
chcp 65001 >nul

echo ========================================
echo  Furniture Cutout — 启动
echo ========================================
echo.

if not exist .venv\ (
    echo [错误] 未检测到虚拟环境 .venv
    echo 请先双击运行 install.bat 安装依赖。
    goto :end
)

call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 激活虚拟环境失败
    goto :end
)

set HF_HUB_DISABLE_PROGRESS_BARS=0

python app.py
if errorlevel 1 (
    echo.
    echo [错误] 程序异常退出，详见 logs\app.log
)

:end
echo.
pause
