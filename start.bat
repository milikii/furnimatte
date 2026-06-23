@echo off
chcp 65001 >nul
REM furniture_cutout 启动脚本

if not exist .venv (
    echo [错误] 未找到虚拟环境。请先运行 install.bat 完成安装。
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

if errorlevel 1 (
    echo [错误] 激活虚拟环境失败。
    pause
    exit /b 1
)

python app.py
if errorlevel 1 (
    echo 程序异常退出，详见 logs\app.log
    pause
)
