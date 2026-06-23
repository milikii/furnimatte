"""Application entry point."""

import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox

from furniture_cutout.logging_config import setup_logging, log_exception


def main() -> int:
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("家具自动抠图")
    app.setOrganizationName("furnimatte")

    # Load icon if available
    try:
        from PySide6.QtGui import QIcon
        icon = QIcon("assets/app_icon.ico")
        if not icon.isNull():
            app.setWindowIcon(icon)
    except Exception:
        pass

    # Late import: main_window depends on everything
    from furniture_cutout.main_window import MainWindow  # noqa: PLC0415

    w = MainWindow()
    w.show()

    # Global exception hook
    def excepthook(typ, val, tb):
        log_exception(val, context="Unhandled exception")
        msg = "".join(traceback.format_exception(typ, val, tb))
        msg_short = msg[:200]
        QMessageBox.critical(
            None,
            "未处理的异常",
            f"程序遇到意外错误，详情见 logs/app.log。\n{msg_short}",
        )

    sys.excepthook = excepthook

    return app.exec()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log_exception(e, context="Fatal startup error")
        msg_e = str(e)[:200]
        QMessageBox.critical(None, "启动失败", f"启动失败，详情见logs/app.log。\n{msg_e}")
        sys.exit(1)
