【锚点】你在 /home/projects/furnimatte 工作。`项目架构.md`、`实现计划.md`、`可行性_与_优化方案.md`、规范全文是依据。动手前读：`项目架构.md` §7、§9；`install.bat`/`start.bat`（T12 已建）；`requirements.txt`。本任务 **T14 README**（最后）。

【范围 + 文件白名单】仅建 `README.md`。不改其它文件。

【任务】写 `README.md`（中文，面向非开发者 Windows 用户 + 可重装的维护者），包含：
1. **简介**：极简家具自动抠图工具，本地 CPU 运行，输出透明 PNG。基于 BiRefNet_HR-matting。
2. **环境要求**：Windows 10/11，Python 3.11 64-bit，i5 级 CPU，32GB 内存（说明 16GB 可能 4K 吃紧），无显卡要求。
3. **安装**：双击 `install.bat`（检查 Python→建 .venv→装 CPU torch→装依赖→成功/失败提示）。说明 torch 用 CPU 源，不装 CUDA。
4. **启动**：双击 `start.bat`。异常时窗口停留，看 `logs/app.log`。
5. **使用流程**：
   - 打开图片（或拖入）→ 点"自动抠图"→ 看右侧透明结果（棋盘/白/黑背景切换）→ 点"保存 PNG"。
   - 自动结果错主体 → 点"框选重算"→ 在左图框住家具→ 等待→ 保存。
   - 输出 `<原名>_cutout.png`，存原图目录。
6. **模型下载**：首次自动抠图会下载 ~800MB BiRefNet_HR-matting。国内网络慢/失败 → 设置里开启 HF 镜像，或手动选已下载的本地模型目录。下载后可完全离线。
7. **依赖版本**：列出 requirements.txt 锁定版本表（torch 2.3.1 CPU / transformers 4.45.2 / PySide6 6.7.3 等）。说明重装：删 .venv 重跑 install.bat；transformers 若与 trust_remote_code 不兼容可回退 4.42.4。
8. **设置说明**：模型缓存目录 / 框选扩展比例（0/5/10/15%）/ CPU 线程（auto=cpu-2）/ 输出目录 / 同时保存 Alpha / 打开后自动抠图。
9. **手动验证 checklist**（规范第 17 节 18 项，逐条列出供人工勾选）。
10. **常见问题**：CPU 慢属正常（质量优先）；模型下载失败→镜像/本地目录；内存不足→关其他程序/小图；日志在 logs/app.log。
11. **项目结构**简述（指向 `项目架构.md` 详单）。
12. **测试**：`pytest -q`（逻辑单测）；`FURNIMATTE_MODEL=1 pytest -q`（含模型冒烟）。

【决策规则】
- README 面向非开发者，步骤明确可照做。
- 不夸大速度（CPU 推理 30s–2min 正常）。
- 强调纯本地、不联网（除首次下载）、不上传。
- 不 `git commit`。

【完成门槛——逐条亲自跑】
- `bash -c "test -s README.md && echo OK"` 输出 OK
- `bash -c "grep -qi 'install.bat' README.md && grep -qi 'start.bat' README.md && grep -qi 'BiRefNet' README.md && echo OK"` 输出 OK
- `bash -c "grep -qi 'CPU' README.md && grep -qi 'logs/app.log' README.md && echo OK"` 输出 OK
- `git status`：仅 `README.md`

【铁律】需要改白名单外文件则停下报告。禁止 `git commit`。

【报告格式】README 结构清单 + 每条门槛结果。
