@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ========================================
echo  Furniture Cutout - Install Dependencies
echo ========================================
echo.

REM ---- Check Python ----
where python >nul 2>&1
if errorlevel 1 goto :no_python

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo Detected: !PYVER!

echo !PYVER! | findstr /R "3\.11 3\.12" >nul
if errorlevel 1 goto :wrong_version

python -c "import platform; assert platform.architecture()[0]=='64bit'" >nul 2>&1
if errorlevel 1 goto :wrong_arch

echo [OK] Python 3.11/3.12 64-bit
echo.
goto :python_ok

:no_python
echo [ERROR] python not found in PATH.
echo Install Python 3.11 or 3.12 64-bit and check "Add Python to PATH".
echo https://www.python.org/downloads/release/python-3119/
goto :error

:wrong_version
echo [ERROR] Need Python 3.11 or 3.12, got !PYVER!.
echo torch 2.3.1 has no wheel for this version.
echo Install Python 3.11 or 3.12 64-bit:
echo https://www.python.org/downloads/release/python-3119/
goto :error

:wrong_arch
echo [ERROR] Need 64-bit Python, current is 32-bit.
goto :error

:python_ok
REM ---- Create venv ----
if exist .venv\ (
    echo [SKIP] .venv already exists
) else (
    echo [STEP] Creating venv .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] venv creation failed
        goto :error
    )
    echo [DONE] venv created
)
echo.

REM ---- Activate venv ----
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] venv activation failed
    goto :error
)

echo [STEP] Upgrading pip ...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [WARN] pip upgrade failed, continuing ...
)
echo.

REM ---- Install CPU PyTorch (no CUDA) ----
echo [STEP] Installing PyTorch 2.3.1 CPU ...
echo (~200MB, please wait)
echo Trying Tsinghua mirror first (faster in China) ...
pip install torch==2.3.1 -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [WARN] Tsinghua mirror failed, trying official PyTorch CPU index ...
    pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu
    if errorlevel 1 (
        echo [ERROR] PyTorch install failed
        echo Network issue? Try a mirror or proxy.
        goto :error
    )
)
echo.

REM ---- Install requirements ----
echo [STEP] Installing requirements.txt ...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] requirements install failed
    goto :error
)
echo.

echo ========================================
echo  Done. Run start.bat to launch.
echo ========================================
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo  Install failed. See error above.
echo ========================================
echo.
pause
exit /b 1
