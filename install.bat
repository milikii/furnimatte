@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ========================================
echo  Furniture Cutout — 安装依赖
echo ========================================
echo.

REM ---- 检查 Python ----
where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 python 命令。
    echo 请安装 Python 3.11 64-bit，并勾选 "Add Python to PATH"。
    echo 下载: https://www.python.org/downloads/release/python-3119/
    goto :error
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo 检测到: !PYVER!

echo !PYVER! | findstr /R "3\.11" >nul
if errorlevel 1 (
    echo [错误] 需要 Python 3.11，当前为 !PYVER!。
    echo 请安装 Python 3.11 64-bit。
    goto :error
)

python -c "import platform; assert platform.architecture()[0]=='64bit'" >nul 2>&1
if errorlevel 1 (
    echo [错误] 需要 64-bit Python，当前为 32-bit。
    echo 请卸载后安装 Python 3.11 64-bit。
    goto :error
)

echo [通过] Python 3.11 64-bit
echo.

REM ---- 创建虚拟环境 ----
if exist .venv\ (
    echo [跳过] .venv 已存在
) else (
    echo [步骤] 创建虚拟环境 .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        goto :error
    )
    echo [完成] 虚拟环境创建成功
)
echo.

REM ---- 激活虚拟环境 ----
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 激活虚拟环境失败
    goto :error
)

echo [步骤] 升级 pip ...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [警告] pip 升级失败，继续安装 ...
)
echo.

REM ---- 安装 CPU 版 PyTorch（不装 CUDA）----
echo [步骤] 安装 PyTorch 2.3.1 CPU 版 ...
echo （约 200MB，请耐心等待）
pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 (
    echo [错误] PyTorch 安装失败
    echo 可能是网络问题，可尝试配置镜像或代理后重试。
    goto :error
)
echo.

REM ---- 安装其余依赖 ----
echo [步骤] 安装 requirements.txt ...
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查 requirements.txt
    goto :error
)
echo.

echo ========================================
echo  安装完成！运行 start.bat 启动程序
echo ========================================
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo  安装失败，请查看上方错误信息
echo ========================================
echo.
pause
exit /b 1
