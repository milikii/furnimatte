【锚点】你在 /home/projects/furnimatte 工作。`项目架构.md` §2.2、§5 是契约。动手前**完整读**：`项目架构.md` §2.2、§5、§9。前置 T00b（编排者已核实官方预处理并填入 §2.2 占位区）+ T03（image_processing.letterbox/unletterbox 已存在）。本任务 **T05 BiRefNet 引擎（最高风险）**。

> ⚠️ **官方预处理参数以 `项目架构.md` §2.2 "官方预处理参数"小节为准**。编排者已在该节填入：输入尺寸 / mean·std / 是否 sigmoid / 输出形状。你**必须**使用该节给的值，**不要凭空编造**，也不要沿用占位的默认。若该节仍为占位文本（含"待官方核实"），**立刻停下报告**，不要实现。

【范围 + 文件白名单】仅建 `furniture_cutout/birefnet_engine.py`。不改其它文件。

【任务】实现 `furniture_cutout/birefnet_engine.py`：
1. 常量 `MODEL_INPUT_SIZE`：取 §2.2 给定值（默认 1024）。
2. `class BiRefNetEngine`：
   - `__init__(self, model_id="ZhengPeng7/BiRefNet_HR-matting", cache_dir=None, num_threads=None, progress_cb=None)`：仅存参数，**不加载**。`num_threads=None` → 调用方算好后传入整数。
   - `load(self) -> None`：
     - `from transformers import AutoModelForImageSegmentation`（函数内导入，避免模块 import 时强依赖）。
     - `model = AutoModelForImageSegmentation.from_pretrained(model_id, trust_remote_code=True, cache_dir=cache_dir)`
     - `import torch; torch.set_num_threads(num_threads); torch.set_num_interop_threads(1)`
     - `model.to(torch.device("cpu")); model.eval()`
     - 存为 `self.model`。
     - 失败（网络/文件/权重大小）→ 抛 `EngineError(kind="model_load"或"download", message=...)`，由调用方转 worker 信号。**不要** `except: pass`。
   - `infer(self, rgb_pil: PIL.Image.Image) -> np.ndarray`：返回 float [0,1] (H×W)，H×W == 输入原图 H×W。流程：
     1. `from furniture_cutout.image_processing import letterbox, unletterbox_mask`
     2. `padded, scale, pad_l, pad_t = letterbox(rgb_pil, MODEL_INPUT_SIZE, pad_value=§2.2给定或(114,114,114))`
     3. 按 §2.2 归一化：`to_tensor` → 减 mean 除 std → `(1,3,S,S)` float32。（若 §2.2 指明其它方式，照办）
     4. `torch.inference_mode()`：`preds = model(x)`；取输出（按 §2.2 指明 logits 还是 sigmoid 后）→ `alpha = torch.sigmoid(...)` 或直接取，→ `[0,0]` → numpy (S,S) float32 [0,1]。
     5. `alpha_full = unletterbox_mask(alpha, (H,W), scale, (pad_l,pad_t))`
     6. `np.nan_to_num(alpha_full, nan=0.0, posinf=1.0, neginf=0.0); np.clip(alpha_full,0,1,out=alpha_full)`
     7. `del` 中间张量；返回 alpha_full。
   - `is_loaded` property：`self.model is not None`。
3. `class EngineError(Exception)`：`__init__(self, kind, message)`，存 `self.kind` ∈ {"model_load","download","inference"}。
4. 顶层 `import torch`、`numpy`、`PIL`；transformers/torch 在函数内或模块顶按需（torch 顶层 import OK，transformers 建议函数内 import 以降 import 成本）。

【决策规则（铁律）】
- `device = torch.device("cpu")`，**禁止** `torch.cuda`、禁止 fp16、禁止 `.half()`、禁止检测 CUDA 失败报错。
- **float32 全程**。
- 模型只加载一次（load 后常驻 self.model）；infer 不得重建模型。
- `infer` 输出尺寸必须 == 输入原图尺寸（letterbox→推理→unletterbox 保证）。
- Alpha **不得二值化**（不得 `>0.5`），保持连续 [0,1]。
- 不得修改原始 RGB（infer 不返回 RGB，只返回 alpha）。
- 失败必须抛 `EngineError`，不得静默吞错。
- 不 `git commit`。

【完成门槛——逐条亲自跑】
- `python -c "from furniture_cutout import birefnet_engine as e; print(hasattr(e,'BiRefNetEngine'), hasattr(e,'EngineError'))"` 输出 True True
- `python -c "from furniture_cutout import birefnet_engine as e; eng=e.BiRefNetEngine(); print(eng.is_loaded)"` 输出 False（未加载，且未触发下载/import transformers）
- `ruff check furniture_cutout/birefnet_engine.py` 退出 0
- grep 自检：`grep -nE "type: ignore|except\s*:\s*pass|except\s+Exception\s*:\s*pass|torch\.cuda|\.half\(\)|float16|fp16|> 0\.5" furniture_cutout/birefnet_engine.py` 为空
- grep 自检：`grep -n "from furniture_cutout.image_processing import" furniture_cutout/birefnet_engine.py` 存在（复用 letterbox）
- `git status`：仅 `furniture_cutout/birefnet_engine.py`
- （模型冒烟测试在 T13 的 test_engine_smoke.py，需联网/模型，本任务不要求跑）

【铁律】若 §2.2 官方预处理参数仍为占位（含"待官方核实"），**立刻停下报告阻塞点**，不要实现。若达成门槛需改白名单外文件，停下报告。禁止 `git commit`。

【报告格式】文件改了什么 + §2.2 实际使用的参数值（输入尺寸/mean/std/sigmoid）+ 每条门槛实际结果。
