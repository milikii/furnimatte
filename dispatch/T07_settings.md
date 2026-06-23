【锚点】你在 /home/projects/furnimatte 工作。`项目架构.md` §2.6 是契约。动手前读：`项目架构.md` §2.6、`config.json`（T01 已建，默认值见此）。前置 T01。本任务 **T07 设置**。

【范围 + 文件白名单】仅建 `furniture_cutout/settings.py`。不改 config.json（只读它）。

【任务】实现 `furniture_cutout/settings.py`：
1. `from dataclasses import dataclass, field, asdict`；`import json, os`；`from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, QFileDialog, QHBoxLayout`。
2. `@dataclass class Settings`：
   - `model_id: str = "ZhengPeng7/BiRefNet_HR-matting"`
   - `model_cache_dir: str = ""`
   - `box_pad_ratio: float = 0.05`
   - `cpu_threads: int = 0` — 0 表示 auto（运行期由 engine 算 max(1,cpu-2)）
   - `output_dir: str = ""`
   - `save_alpha: bool = False`
   - `auto_cutout_on_open: bool = False`
   - `hf_mirror: bool = True`
3. `CONFIG_PATH = "config.json"`（项目根，相对运行目录）。
4. `load() -> Settings`：读 config.json（若不存在或损坏 → 返回默认 Settings，不抛、不崩溃）。字段缺失用默认补。
5. `save(settings: Settings) -> None`：写 config.json（`json.dump(asdict(settings), indent=2, ensure_ascii=False)`）。失败 → 抛 `SettingsError`（不吞错）。
6. `class SettingsError(Exception)`。
7. `class SettingsDialog(QDialog)`：
   - 表单：模型缓存目录（QLineEdit + 浏览按钮）、框选扩展比例（QDoubleSpinBox 0.00–0.15 step 0.01）、CPU 线程数（QSpinBox 0–32，0=auto）、默认输出目录（QLineEdit + 浏览）、同时保存 Alpha（QCheckBox）、打开后自动抠图（QCheckBox）。
   - "清除极小背景杂点"**不实现**（第一版隐藏，不要加控件）。
   - `get_settings() -> Settings`：从表单收集。
   - 接受/取消按钮；接受时 `save()`。
8. `resolve_cpu_threads(s: Settings) -> int`：`if s.cpu_threads and s.cpu_threads>0: return s.cpu_threads; return max(1, (os.cpu_count() or 6) - 2)`。

【决策规则】
- config.json 的 `cpu_threads` 在文件里是字符串 `"auto"`（T01 设的默认）；`load()` 需把 `"auto"`/缺省 → 0，数字 → int。**不要**把 dataclass 字段改成 str，内部统一 int(0=auto)。
- `box_pad_ratio` 在文件里是 0.05（float）。
- 不要把模型参数暴露给用户。
- 不 `git commit`。

【完成门槛——逐条亲自跑】
- `python -c "from furniture_cutout import settings as s; st=s.load(); print(st.model_id, st.box_pad_ratio, st.cpu_threads, st.save_alpha)"` 输出 `ZhengPeng7/BiRefNet_HR-matting 0.05 0 False`
- `python -c "from furniture_cutout import settings as s; print(s.resolve_cpu_threads(s.Settings()))"` 输出正整数
- `python -c "from furniture_cutout import settings as s; st=s.Settings(); st.cpu_threads=4; assert s.resolve_cpu_threads(st)==4"` 成功
- `ruff check furniture_cutout/settings.py` 退出 0
- grep 自检：`grep -nE "type: ignore|except\s*:\s*pass" furniture_cutout/settings.py` 为空
- `git status`：仅 `furniture_cutout/settings.py`（config.json 不应被改）

【铁律】需要改白名单外文件（含 config.json）则停下报告。禁止 `git commit`。

【报告格式】文件改了什么 + 每条门槛实际结果。
