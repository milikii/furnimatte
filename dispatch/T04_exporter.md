【锚点】你在 /home/projects/furnimatte 工作。`项目架构.md` §2.7、§9 是契约。动手前读：`项目架构.md` §2.7、§9 不变量（1,2,5 输出尺寸==原图/含 Straight Alpha/不覆盖原图）。前置 T01 已完成。本任务 **T04 导出器**。

【范围 + 文件白名单】仅建 `furniture_cutout/exporter.py`。不改其它文件。

【任务】实现 `furniture_cutout/exporter.py`：
1. `class ExporterError(Exception)`：带可读 message。
2. `save(rgba_pil: PIL.Image.Image, src_path: str, out_dir: str | None = None, also_alpha: bool = False) -> str`：
   - 输入须为 RGBA；否则抛 ExporterError。
   - 文件名：`<src_stem>_cutout.png`（src_stem = 原文件名去扩展名）。
   - out_dir 为空 → 默认存原图所在目录。
   - **不覆盖原图**：若目标 == src_path 抛 ExporterError。
   - 重名处理：若 `<stem>_cutout.png` 已存在，用 `<stem>_cutout_1.png`、`_2.png`… 直至不冲突。
   - 保存为 PNG RGBA 8-bit **Straight（非预乘）Alpha**（PIL PNG 默认即 straight，不要做预乘）。
   - `also_alpha=True` → 额外调 `save_alpha`。
   - 返回 out_path。
3. `save_alpha(alpha_np: np.ndarray, src_path: str, out_dir: str | None = None) -> str`：
   - alpha_np float [0,1] (H×W) → uint8 'L' 模式 PNG；文件名 `<src_stem>_alpha.png`；同样重名加序号；返回路径。
4. 保存失败（权限/磁盘）→ 捕获并抛 `ExporterError(可读中文)`，**不要** `except: pass`。

【决策规则】
- 输出尺寸 = rgba_pil 尺寸（即原图尺寸，由调用方保证）；本函数不改尺寸。
- 不要 `git commit`。
- 用 `os.path`/`pathlib`，不引入第三方。

【完成门槛——逐条亲自跑】
- `python -c "from furniture_cutout import exporter; print([f for f in dir(exporter) if not f.startswith('_')])"` 列出 save/save_alpha/ExporterError
- 临时测试：`python -c "from furniture_cutout import exporter; from PIL import Image; import tempfile,os; d=tempfile.mkdtemp(); src=os.path.join(d,'a.jpg'); Image.new('RGB',(100,100)).save(src); r=Image.new('RGBA',(100,100)); p=exporter.save(r,src); assert p.endswith('a_cutout.png') and os.path.exists(p); im=Image.open(p); assert im.mode=='RGBA' and im.size==(100,100)"` 成功
- `python -c "from furniture_cutout import exporter; from PIL import Image; import tempfile,os; d=tempfile.mkdtemp(); src=os.path.join(d,'a.jpg'); Image.new('RGB',(100,100)).save(src); import pytest" ` —— 不覆盖检查：再跑一次保存同名应得 `a_cutout_1.png`
- `ruff check furniture_cutout/exporter.py` 退出 0
- grep 自检：`grep -nE "type: ignore|except\s*:\s*pass|except\s+Exception\s*:\s*pass" furniture_cutout/exporter.py` 为空
- `git status`：仅 `furniture_cutout/exporter.py`

【铁律】需要改白名单外文件则停下报告。禁止 `git commit`。

【报告格式】文件改了什么 + 每条门槛实际结果。
