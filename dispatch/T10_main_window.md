【锚点】你在 /home/projects/furnimatte 工作。`项目架构.md` §2.3（worker 信号）、§2.4–2.7、§4、§6 是契约。动手前**完整读**：`项目架构.md` §2 全部、§3、§4、§6、§9。前置 T02..T09 全部完成。本任务 **T10 主窗口（集成，最大）**。

【范围 + 文件白名单】仅建 `furniture_cutout/main_window.py`。不改其它文件。

【任务】实现 `furniture_cutout/main_window.py`：`class MainWindow(QMainWindow)`。
1. 依赖导入：`from furniture_cutout import image_processing as ip, exporter, logging_config, settings as settings_mod`；`from furniture_cutout.inference_worker import InferenceWorker`；`from furniture_cutout.image_view import ImageView`；`from furniture_cutout.box_selector import BoxSelector`；`from furniture_cutout.settings import SettingsDialog, Settings, load as load_settings, save as save_settings, resolve_cpu_threads`。
2. 顶部工具栏 7 按钮：打开图片 / 自动抠图 / 框选重算 / 取消框选 / 保存 PNG / 重置 / 设置。状态管理仅：`self.original_rgb`(PIL), `self.preview`, `self.current_alpha`, `self.current_rgba`, `self.selected_box`, `self.current_file_path`, `self.output_file_path`（§2.3/规范第 10 节，不要图层/历史/多蒙版）。
3. **打开图片**：文件对话框（jpg/jpeg/png/webp 过滤）+ 窗口拖放（`setAcceptDrops(True)` + `dragEnterEvent`/`dropEvent` 接受图片文件 URL）。打开 → `ip.load_image` → 存 original_rgb、建 preview → 左 view set_original(preview) → 清 current_alpha/rgba/selected_box → 状态栏显示尺寸。打开后**默认不自动推理**，除非 settings.auto_cutout_on_open。
4. **自动抠图**：禁用按钮 → 发 worker.request_load()（首次）→ request_infer_full(original_rgb)。处理中状态栏 + 不确定进度条（QProgressBar.setRange(0,0)）。
5. **框选重算**：进入框选模式 → 左 view 安装/启用 BoxSelector → box_drawn 信号 → 判定 w<50 or h<50 → QMessageBox 提示"框选区域太小，请重新框选家具主体"并 return（不推理）→ 否则 worker.request_infer_box(original_rgb, box)。
6. **取消框选**：BoxSelector.clear()；退出框选模式；恢复按钮。
7. **保存 PNG**：若 current_rgba 为空 → 提示先抠图。否则 `exporter.save(current_rgba, current_file_path, settings.output_dir or None, also_alpha=settings.save_alpha)` → 成功状态栏显示路径；失败捕获 ExporterError → QMessageBox。
8. **重置**：清 current_alpha/current_rgba/selected_box；左 view 复位；右 view 清空；回到刚打开原图状态（不丢弃 original_rgb）。
9. **设置**：开 SettingsDialog；接受后 reload settings；若改了模型/线程，提示下次生效（不强制重载模型，简单处理即可）。
10. worker 信号接线：
    - `status` → 状态栏。
    - `progress` → 状态栏 + 进度条可见。
    - `finished` → 存 current_alpha/current_rgba；右 view set_result(rgba)；状态栏显示耗时与输出尺寸；恢复按钮；进度条隐藏。
    - `failed` → QMessageBox（按 §6 kind 给中文提示）+ `logging_config.log_exception`（用 message+traceback 构造）；恢复按钮；**不退出**，可继续打开下一张。
11. 底部状态栏：状态 / 模型加载状态 / 当前图片尺寸 / 输出尺寸 / 推理耗时。处理中显示不确定进度条或旋转动画（QProgressBar range(0,0) 即可）。
12. 按钮启停：推理/加载期间禁用"自动抠图""框选重算""保存""重置"；保留窗口移动/最小化/刷新。
13. 全局异常兜底：关键槽用 try/except 包，except → log_exception + QMessageBox，不得 `except: pass`。

【决策规则】
- 模型只加载一次：首次自动抠图时 request_load；后续直接 infer。worker 内部已保证只建一次。
- 框选重算不复用整图蒙版（worker 内部已用原图 ROI 重算）。
- 失败一律 QMessageBox（非控制台）+ 日志 traceback；不崩溃退出。
- 状态管理只用上述 7 个字段，不引入图层/历史/撤销。
- 拖放打开图片与按钮等价。
- 打开图片后默认不自动推理。
- 不 `git commit`。

【完成门槛——逐条亲自跑】
- `python -c "from furniture_cutout import main_window as m; print('MainWindow' in dir(m))"` 成功（需 QApplication 实例：`from PySide6.QtWidgets import QApplication; import sys; app=QApplication.instance() or QApplication(sys.argv)`）
- `python -c "from furniture_cutout.main_window import MainWindow; from PySide6.QtWidgets import QApplication; import sys; app=QApplication.instance() or QApplication(sys.argv); w=MainWindow(); print(all(hasattr(w,b) for b in ['open_image','auto_cutout','box_recompute','cancel_box','save_png','reset','open_settings']) or True)"` 不崩（方法名可微调，但 7 按钮功能齐全）
- `ruff check furniture_cutout/main_window.py` 退出 0
- grep 自检：`grep -nE "type: ignore|except\s*:\s*pass|except\s+Exception\s*:\s*pass" furniture_cutout/main_window.py` 为空
- grep 自检：`grep -n "QMessageBox" furniture_cutout/main_window.py` ≥3 处（错误弹窗）
- grep 自检：`grep -n "dropEvent" furniture_cutout/main_window.py` 存在（拖放）
- grep 自检：`grep -n "50" furniture_cutout/main_window.py` 存在（小框保护）
- `git status`：仅 `furniture_cutout/main_window.py`

【铁律】需要改白名单外文件则停下报告。禁止 `git commit`。

【报告格式】文件改了什么 + 每条门槛实际结果 + 7 按钮与方法名清单。
