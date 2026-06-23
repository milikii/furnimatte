@echo off
chcp 65001 >nul
REM furniture_cutout 安装脚本
REM 要求：Python 3.11 64-bit，CPU-only（不安装 CUDA）

echo === 家具自动抠图工具 — 安装 ===
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python。请安装 Python 3.11 64-bit。
    pause
    exit /b 1
)

python -c "import platform; assert platform.architecture()[0]=='64bit'" >nul 2>&1
if errorlevel 1 (
    echo [错误] 请使用 Python 3.11 64-bit 版本，当前不是 64-bit。
    pause
    exit /b 1
)

REM 创建虚拟环境
if not exist .venv (
    echo [1/4] 创建虚拟环境...
    python -m venv .venv
) else (
    echo [1/4] 虚拟环境已存在，跳过。
)

call .venv\Scripts\activate.bat

if errorlevel 1 (
    echo [错误] 激活虚拟环境失败。
    pause
    exit /b 1
)

REM 升级 pip
echo [2/4] 升级 pip...
python -m pip install --upgrade pip >nul 2>&1

REM 安装 CPU 版 PyTorch
echo [3/4] 安装 CPU 版 PyTorch（不安装 CUDA）...
pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 (
    echo [错误] PyTorch 安装失败。请检查网络连接。
    pause
    exit /b 1
)

REM 安装其他依赖
echo [4/4] 安装其他依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败。请检查网络连接和 requirements.txt。
    pause
    exit /b 1
)

echo.
echo === 安装完成！运行 start.bat 启动程序 ===
pause
