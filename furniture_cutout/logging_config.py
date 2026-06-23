"""Logging configuration for furniture_cutout."""

import logging
import os
import sys
import traceback
from logging.handlers import RotatingFileHandler

_configured = False


def setup_logging(log_dir: str = "logs") -> logging.Logger:
    global _configured
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger()
    if _configured:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    fh = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    _configured = True
    return logger


def log_exception(exc: BaseException, context: str = "") -> None:
    """Log a full traceback for *exc* to the app.log file."""
    logger = logging.getLogger()
    tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
    msg = "".join(tb_lines)
    if context:
        msg = context + "\n" + msg
    logger.error(msg)
