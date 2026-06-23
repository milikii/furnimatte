【锚点】你在 /home/projects/furnimatte 工作。`项目架构.md` §2.3、§3、§6 是契约。动手前读：`项目架构.md` §2.3（信号/方法）、§3（线程模型）、§6（错误 kind）。前置 T05（birefnet_engine.BiRefNetEngine/EngineError 已存在）+ T03（image_processing 已存在）。本任务 **T06 推理 worker**。

【范围 + 文件白名单】仅建 `furniture_cutout/inference_worker.py`。不改其它文件。

【任务】实现 `furniture_cutout/inference_worker.py`：
1. `from PySide6.QtCore import QThread, Signal`（顶层）。
2. `from furniture_cutout.birefnet_engine import BiRefNetEngine, EngineError`
3. `from furniture_cutout import image_processing as ip`
4. `class InferenceWorker(QThread)`：
   - 信号：
     - `status = Signal(str)`
     - `progress = Signal(str)`
     - `finished = Signal(object)` — object = dict{"rgba":PIL.Image, "alpha":np.ndarray, "elapsed":float, "mode":str}
     - `failed = Signal(str, str, str)` — (kind, message, traceback_str)
   - `__init__(self, settings, parent=None)`：settings 是 settings.Settings 实例（T07 产物）；先不依赖其具体字段存在与否，用 getattr 防御。建 `self._engine = None`，`self._task = None`（待执行任务 dict）。
   - `request_load(self)`：把 `{"op":"load"}` 放入 `self._task` 并 `start()`（若未运行）。
   - `request_infer_full(self, rgb_pil)`：`self._task={"op":"full","rgb":rgb_pil}`；`start()`。
   - `request_infer_box(self, rgb_pil, box)`：`self._task={"op":"box","rgb":rgb_pil,"box":box}`；`start()`。
   - `run(self)`（QThread 入口，后台线程）：
     - 取 `self._task`；若空 return。
     - op=="load"：发 status("正在加载模型…")；try 建 `BiRefNetEngine(...)` → `engine.load()` → `self._engine=engine` → `status("模型就绪")`；except EngineError as e → `failed.emit(e.kind, str(e), traceback.format_exc())`；except Exception → `failed.emit("model_load", "模型加载失败", traceback.format_exc())`。
     - op=="full"：要求 `self._engine` 已加载，否则 `failed.emit("model_load","模型未加载","")`。try：`t0=time.time(); alpha=engine.infer(rgb); rgba=ip.compose_rgba(rgb, alpha); finished.emit({"rgba":rgba,"alpha":alpha,"elapsed":time.time()-t0,"mode":"full"})`；except EngineError → failed(kind,...)；except MemoryError → failed("oom","内存不足，请尝试较小图片或关闭其他程序",tb)；except Exception → failed("inference","推理失败，详情见日志",tb)。
     - op=="box"：try：`box=ip.expand_box(box, pad_ratio, img_size); roi=ip.crop_roi(rgb, box); roi_alpha=engine.infer(roi); full_alpha=ip.map_roi_alpha_to_full(roi_alpha, box, img_size); rgba=ip.compose_rgba(rgb, full_alpha); finished.emit({...,"mode":"box"})`。img_size=(rgb.width, rgb.height)。pad_ratio 来自 settings（getattr(settings,"box_pad_ratio",0.05)）。<50px 小框保护由 main_window 判定，本处不重复。
     - 结束清 `self._task=None`。
   - 同一时刻只跑一个：用 `self.isRunning()` 判定，已在跑则忽略新请求（主线程侧也会禁用按钮）。可在 request_* 里 `if self.isRunning(): return` 防御。
5. 顶层 `import time, traceback`。

【决策规则】
- worker 线程**绝不**直接操作 widget，只 `emit` 信号。
- 不得在主线程加载/推理（run 内才做）。
- 错误 kind 严格用 §6 集合：model_load / download / image_read / oom / inference / save。
- MemoryError 单独捕获 → kind="oom"。
- 不得 `except: pass`；每个 except 都要 emit failed 或 re-raise。
- settings 可能尚未实现（T07），用 `getattr` 防御，不要 import settings 模块强依赖（可 `try: from furniture_cutout import settings` 但运行期用 getattr 取字段）。
- 不 `git commit`。

【完成门槛——逐条亲自跑】
- `python -c "from furniture_cutout import inference_worker as w; print('InferenceWorker' in dir(w))"` 成功
- `python -c "from furniture_cutout.inference_worker import InferenceWorker; import inspect; print(all(hasattr(InferenceWorker,s) for s in ['status','progress','finished','failed','request_load','request_infer_full','request_infer_box','run']))"` 输出 True
- `ruff check furniture_cutout/inference_worker.py` 退出 0
- grep 自检：`grep -nE "type: ignore|except\s*:\s*pass|except\s+Exception\s*:\s*pass|torch\.cuda|\.half\(\)" furniture_cutout/inference_worker.py` 为空
- grep 自检：`grep -n "failed.emit" furniture_cutout/inference_worker.py` 至少 3 处（load/full/box 各类失败）
- `git status`：仅 `furniture_cutout/inference_worker.py`

【铁律】需要改白名单外文件则停下报告。禁止 `git commit`。

【报告格式】文件改了什么 + 每条门槛实际结果。
