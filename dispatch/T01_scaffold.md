【锚点】你在 /home/projects/furnimatte 工作。`项目架构.md` 是架构依据，`实现计划.md`/`可行性_与_优化方案.md` 是背景。动手前读：`项目架构.md`（全文，尤其 §2 接口契约、§7 依赖版本）、`dispatch/TASKS.md`。本任务是 **T01 项目脚手架**，后续所有任务依赖它。

【范围 + 文件白名单】只创建项目骨架文件，不写任何业务逻辑。仅以下文件可改/可建：
`pyproject.toml`, `requirements.txt`, `config.json`, `.gitignore`, `furniture_cutout/__init__.py`, `tests/__init__.py`, `assets/.gitkeep`, `logs/.gitkeep`
不要建任何其它 .py。结尾跑 `git status` 自查无越界。

【任务（逐条）】
1. 建 `furniture_cutout/__init__.py`（空文件 + 一行 `__version__ = "0.1.0"`）。
2. 建 `tests/__init__.py`（空）。
3. 建 `assets/.gitkeep`、`logs/.gitkeep`（空）。
4. 建 `requirements.txt`，内容**严格**为以下锁定版本：
   ```
   torch==2.3.1
   transformers==4.45.2
   PySide6==6.7.3
   Pillow==10.4.0
   numpy==1.26.4
   opencv-python-headless==4.10.0.84
   huggingface-hub==0.25.1
   pytest==8.3.2
   ruff==0.6.9
   ```
   并在文件顶部注释：torch 须用 `--index-url https://download.pytorch.org/whl/cpu` 安装（不写进 requirements，由 install.bat 处理）。
5. 建 `pyproject.toml`（最小，目的：让 detect-stack.sh 识别为 python 栈 + 配置 pytest/ruff）。包含：
   - `[build-system]` 可省或 `setuptools`
   - `[tool.pytest.ini_options]`：`testpaths=["tests"]`，`addopts="-q"`
   - `[tool.ruff]`：`line-length=100`，`[tool.ruff.lint]` 选 `E,F,W`（基础）
   - 不要 `[project]` 依赖（用 requirements.txt 管理）
6. 建 `config.json`（默认配置，对应架构 §2.6 Settings）：
   ```json
   {
     "model_id": "ZhengPeng7/BiRefNet_HR-matting",
     "model_cache_dir": "",
     "box_pad_ratio": 0.05,
     "cpu_threads": "auto",
     "output_dir": "",
     "save_alpha": false,
     "auto_cutout_on_open": false,
     "hf_mirror": true
   }
   ```
7. 建 `.gitignore`：忽略 `.venv/`, `__pycache__/`, `*.pyc`, `logs/*.log`, `models/`, `.pytest_cache/`, `.ruff_cache/`。

【决策规则（遇到就照此）】
- 版本号**必须**与上面完全一致，不要"升级到最新"。
- `config.json` 的 `cpu_threads` 是字符串 `"auto"`，不是数字。
- 不要创建 `setup.py`/`setup.cfg`（pyproject.toml 已够）。
- 不要 `git commit`。

【完成门槛——逐条亲自跑，并在报告里给结论】
- `python -c "import furniture_cutout; print(furniture_cutout.__version__)"` 成功输出 0.1.0
- `python -c "import json; json.load(open('config.json'))"` 成功
- `ruff check .` 退出 0（或无 .py 可查时跳过，注明）
- `git status`：改动仅限白名单 8 个文件
- grep 自检：`grep -rn "except.*pass\|type: ignore" .` 为空（目前无 .py 逻辑，应为空）

【铁律】若达成门槛必须改白名单外文件，立刻停下，在报告写明阻塞点和建议，不要自行扩大范围。禁止 `git commit`。

【报告格式】每个文件做了什么 + 上面每条门槛的实际命令输出/结论。
