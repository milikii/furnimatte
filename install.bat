@echo off
chcp 65001 >nul

echo ========================================
echo  Furniture Cutout — 安装依赖
echo ========================================

REM ---- 检查 Python 3.11 ----
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请安装 Python 3.11 64-bit
    exit /b 1
)

python --version 2>&1 | findstr /R "3\.11" >nul
if errorlevel 1 (
    echo [错误] 需要 Python 3.11，请安装 Python 3.11 64-bit
    exit /b 1
)

REM ---- 检查 64-bit ----
python -c "import platform; assert platform.architecture()[0]=='64bit'" 2>nul
if errorlevel 1 (
    echo [错误] 需要 64-bit Python，当前为 32-bit
    echo 请卸载当前版本后安装 Python 3.11 64-bit
    exit /b 1
)

echo [通过] Python 3.11 64-bit

REM ---- 创建虚拟环境 ----
if exist .venv\ (
    echo [跳过] .venv 已存在
) else (
    echo [步骤] 创建虚拟环境 .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        exit /b 1
    )
    echo [完成] 虚拟环境创建成功
)

call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 激活虚拟环境失败
    exit /b 1
)

echo [步骤] 升级 pip ...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [警告] pip 升级失败，继续安装 ...
)

REM ---- 安装 CPU 版 PyTorch（不装 CUDA）----
echo [步骤] 安装 PyTorch 2.3.1 CPU 版 ...
pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 (
    echo [错误] PyTorch 安装失败
    exit /b 1
)

REM ---- 安装其余依赖 ----
echo [步骤] 安装 requirements.txt ...
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查 requirements.txt
    exit /b 1
)

echo ========================================
echo  安装完成，运行 start.bat 启动
echo ========================================
