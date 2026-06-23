# 派单任务索引 — furniture_cutout

> 配合 `项目架构.md`（接口契约）+ `可行性_与_优化方案.md` 使用。
> 每个任务文件 `T##_*.md` 是**自包含派单指令**，直接 `dispatch.sh --tag T## --repo . --file dispatch/T##_*.md`。
> worker 无跨次记忆，每个文件重述锚点/范围/决策规则/门槛。

## 编排者（你，昂贵模型）自己做的，不派单

- **T00a** `git init` + 初始提交（提交现有 3 份 md + 本 dispatch 目录）。verify.sh/snapshot.sh 需要 git。
- **T00b** 核实 BiRefNet_HR-matting 官方预处理：读 HuggingFace 模型卡 + 仓库 `inference.py`，确认输入尺寸 / mean·std / 是否 sigmoid / 输出形状，填入 `项目架构.md` §2.2 占位区。**T05 派单前必须完成**。

## 通用派单参数

- model: `deepseek-v4-flash`
- tools: `read,bash,edit,write,grep,find,ls`
- repo: `/home/projects/furnimatte`
- 全局禁令（每文件已含）：禁 `git commit`；禁改白名单外文件；禁 `except: pass`/`type: ignore` 吞错；禁 fp16/cuda；禁改原始 RGB；禁 Alpha 二值化。

## verify.sh 调用模板（Python 栈）

```bash
verify.sh --repo /home/projects/furnimatte \
  --whitelist "<本任务白名单，逗号分隔 glob>" \
  --build "" --typecheck "<按进度 import 检查>" --test "pytest -q" --lint "ruff check" \
  --lint-baseline 0 \
  --suppress "type: ignore|except\s*(Exception|BaseException)?\s*:\s*pass|except\s*:\s*pass"
```

## 任务表

| ID | 名称 | 白名单（仅可改） | 依赖 | 门 typecheck |
|---|---|---|---|---|
| T01 | 项目脚手架 | `pyproject.toml,requirements.txt,config.json,.gitignore,furniture_cutout/__init__.py,tests/__init__.py,assets/.gitkeep,logs/.gitkeep` | T00a | `python -c "import furniture_cutout"` |
| T02 | 日志 | `furniture_cutout/logging_config.py` | T01 | `python -c "from furniture_cutout import logging_config"` |
| T03 | 图像处理 | `furniture_cutout/image_processing.py` | T01 | `python -c "from furniture_cutout import image_processing"` |
| T04 | 导出器 | `furniture_cutout/exporter.py` | T01 | `python -c "from furniture_cutout import exporter"` |
| T05 | BiRefNet 引擎 | `furniture_cutout/birefnet_engine.py` | T00b,T03 | `python -c "from furniture_cutout import birefnet_engine"` |
| T06 | 推理 worker | `furniture_cutout/inference_worker.py` | T05,T03 | `python -c "from furniture_cutout import inference_worker"` |
| T07 | 设置 | `furniture_cutout/settings.py` | T01 | `python -c "from furniture_cutout import settings"` |
| T08 | 图像视图 | `furniture_cutout/image_view.py` | T03 | `python -c "from furniture_cutout import image_view"` |
| T09 | 框选器 | `furniture_cutout/box_selector.py` | T08 | `python -c "from furniture_cutout import box_selector"` |
| T10 | 主窗口 | `furniture_cutout/main_window.py` | T02..T09 | `python -c "from furniture_cutout import main_window"` |
| T11 | 入口 | `app.py` | T10 | `python -c "import app"` (仅语法/import) |
| T12 | 安装启动脚本 | `install.bat,start.bat` | T01 | (无 python 门) |
| T13 | 测试 | `tests/test_image_mapping.py,tests/test_box_coordinates.py,tests/test_export_size.py,tests/test_alpha_composite.py,tests/test_engine_smoke.py,conftest.py` | T03,T04 | `pytest -q`（逻辑单测全绿；smoke 默认 skip） |
| T14 | README | `README.md` | 全部 | (无门) |

## 推荐执行编排（节省 token）

1. T00a（你）→ T01（worker，串行，必先）
2. **并行 fan-out**：T02 / T03 / T04 / T07 / T08 / T12（白名单互斥，无写冲突）
3. T00b（你）→ T05（worker，串行，最高风险，≥3 轮则你接管）
4. T06（依赖 T05+T03）→ T09（依赖 T08）
5. T10（集成，依赖 T02..T09）
6. T11 → T13 → T14
7. 每步 verify.sh 绿 + 你做对抗性抽检 → 才提交（一任务一提交）。

## 破局规则

- 同一任务 ≥3 轮 worker 仍未过门 → 停止派单，你亲自写。
- T05 官方预处理与占位冲突 → 以官方为准，更新 `项目架构.md` §2.2 后再派/再派。
- 任何 worker 试图改白名单外文件 → 视为越界，引用 verify.sh FAIL 输出重派或接管。
