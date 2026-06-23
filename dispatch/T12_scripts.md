【锚点】你在 /home/projects/furnimatte 工作。`项目架构.md` §7、规范第 15 节是契约。动手前读：`项目架构.md` §7 依赖矩阵、`requirements.txt`（T01 已建）。本任务 **T12 安装与启动脚本**。

【范围 + 文件白名单】仅建 `install.bat`、`start.bat`（项目根）。不改其它文件。

【任务】
1. `install.bat`：
   - `@echo off` + `chcp 65001 >nul`（UTF-8 输出）。
   - 检查 Python：`python --version` 是否含 3.11（或 3.1x 64-bit）；缺失/版本不符 → `echo 请安装 Python 3.11 64-bit` + `exit /b 1`。
   - 检查 64-bit：`python -c "import platform; assert platform.architecture()[0]=='64bit'"` 失败 → 提示并退出。
   - `python -m venv .venv`（已存在则跳过）。
   - `call .venv\Scripts\activate.bat`
   - 升级 pip：`python -m pip install --upgrade pip`
   - **CPU 版 torch**：`pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu`（**不装 CUDA**）。
   - `pip install -r requirements.txt`（torch 已装，requirements 含 torch==2.3.1 会确认版本一致）。
   - 若设了 `HF_ENDPOINT` 镜像提示（README 说明，脚本不强设）。
   - 成功：`echo 安装完成，运行 start.bat 启动`；失败：`echo 安装失败，请检查上方错误` + `exit /b 1`。
   - 每步用 `if errorlevel 1` 检查失败并提示。
2. `start.bat`：
   - `@echo off` + `chcp 65001 >nul`。
   - 检查 `.venv` 是否存在，不存在 → 提示先运行 install.bat + `exit /b 1`。
   - `call .venv\Scripts\activate.bat`
   - 设 `HF_HUB_DISABLE_PROGRESS_BARS=0`（确保下载有进度，可选）。
   - `python app.py`
   - 结尾 `if errorlevel 1` → `echo 程序异常退出，详见 logs\app.log` + `pause`（保持窗口查看错误）。
   - 正常退出也 `pause`（可选，便于看输出）——但 GUI 程序正常关闭不需要 pause；改为仅异常时 pause。

【决策规则】
- **不安装 CUDA 版 PyTorch**；torch 用 `--index-url https://download.pytorch.org/whl/cpu`。
- 不写死 12 线程（线程由程序运行期按 cpu_count 决定）。
- UTF-8 输出（chcp 65001）防中文乱码。
- 不 `git commit`。

【完成门槛——逐条亲自跑】
- `bash -c "grep -q 'pytorch.org/whl/cpu' install.bat && echo OK"` 输出 OK（CPU 版）
- `bash -c "grep -qi 'cuda' install.bat && echo FOUND_CUDA || echo NO_CUDA"` 输出 NO_CUDA（install.bat 不应强制 CUDA；若有 "不安装 CUDA" 注释行需排除——确保没有 `pip install torch+CUDA`）
- `bash -c "grep -q 'python app.py' start.bat && echo OK"` 输出 OK
- `bash -c "grep -q 'pause' start.bat && echo OK"` 输出 OK（异常保持窗口）
- `bash -c "grep -q 'chcp 65001' install.bat && grep -q 'chcp 65001' start.bat && echo OK"` 输出 OK
- `git status`：仅 `install.bat`, `start.bat`

【铁律】需要改白名单外文件则停下报告。禁止 `git commit`。禁止 CUDA 版 torch。

【报告格式】文件改了什么 + 每条门槛实际结果。
