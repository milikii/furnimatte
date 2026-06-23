【锚点】你在 /home/projects/furnimatte 工作。`项目架构.md` §2.9 是契约。动手前读：`项目架构.md` §2.9、§6。前置 T10。本任务 **T11 入口**。

【范围 + 文件白名单】仅建 `app.py`（项目根）。不改其它文件。

【任务】实现 `app.py`：
1. `import sys`；`from PySide6.QtWidgets import QApplication, QMessageBox`；`from furniture_cutout.logging_config import setup_logging, log_exception`；`from furniture_cutout.main_window import MainWindow`。
2. `def main()`：
   - `setup_logging()`
   - `app = QApplication(sys.argv)`
   - 设应用名/图标（图标 `assets/app_icon.ico` 若存在则 `app.setWindowIcon`，不存在不报错）。
   - `w = MainWindow(); w.show()`
   - `sys.excethook = lambda t,v,tb: log_exception(v)`（全局未捕获异常入日志）
   - `return app.exec()`
3. `if __name__ == "__main__": sys.exit(main())`
4. 在 main 外层 try/except 兜底：若 MainWindow 构造抛 → log_exception + QMessageBox.critical 后退出。

【决策规则】
- 入口保持极简，业务逻辑都在 MainWindow。
- 不 `git commit`。

【完成门槛——逐条亲自跑】
- `python -c "import ast; ast.parse(open('app.py').read()); print('syntax ok')"` 成功
- `python -c "import app; print(hasattr(app,'main'))"` 成功（不执行 main，只 import）
- `ruff check app.py` 退出 0
- grep 自检：`grep -nE "type: ignore|except\s*:\s*pass" app.py` 为空
- `git status`：仅 `app.py`

【铁律】需要改白名单外文件则停下报告。禁止 `git commit`。

【报告格式】文件改了什么 + 每条门槛实际结果。
