【锚点】你在 /home/projects/furnimatte 工作。`项目架构.md` §2.8 是契约。动手前读：`项目架构.md` §2.8、§6（错误模型）、§3（线程）。前置 T01 已完成（`furniture_cutout/__init__.py` 已存在）。本任务 **T02 日志配置**。

【范围 + 文件白名单】仅建 `furniture_cutout/logging_config.py`。不改其它文件。结尾 `git status` 自查。

【任务（逐条）】实现 `furniture_cutout/logging_config.py`：
1. `setup_logging(log_dir: str = "logs") -> logging.Logger`：
   - 创建 `logs/` 目录（`os.makedirs(exist_ok=True)`）。
   - 根 logger 级别 INFO。
   - `RotatingFileHandler`：`logs/app.log`，`maxBytes=2*1024*1024`，`backupCount=3`，UTF-8，格式 `%(asctime)s %(levelname)s %(name)s %(message)s`。
   - `StreamHandler` 到 stdout（控制台镜像），同格式。
   - 避免重复添加 handler（重复调用 setup_logging 不重复加 handler）。
   - 返回 root logger。
2. `log_exception(exc: BaseException, context: str = "") -> None`：
   - 用 `logging.exception` 或 `logger.error("%s\n%s", context, traceback.format_exc())` 写**完整 traceback** 到 app.log。
3. 模块级不产生副作用（不在 import 时自动配置）。

【决策规则】
- 只用标准库 `logging`、`os`、`sys`、`traceback`。不引入第三方。
- 不吞异常（本模块就是用来记录异常的，禁止 `except: pass`）。
- 不要 `git commit`。

【完成门槛——逐条亲自跑】
- `python -c "from furniture_cutout import logging_config; logging_config.setup_logging(); logging_config.log_exception(ValueError('x'))"` 成功且 `logs/app.log` 出现含 traceback 的记录
- `ruff check furniture_cutout/logging_config.py` 退出 0
- grep 自检：`grep -nE "type: ignore|except\s*(Exception|BaseException)?\s*:\s*pass|except\s*:\s*pass" furniture_cutout/logging_config.py` 为空
- `git status`：仅 `furniture_cutout/logging_config.py`（及临时产生的 app.log，不应提交，确认 .gitignore 生效后忽略它）

【铁律】需要改白名单外文件则停下报告，不要扩大范围。禁止 `git commit`。

【报告格式】文件改了什么 + 每条门槛实际结果。
