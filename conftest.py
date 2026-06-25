"""Pytest configuration."""

import os

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "model: needs BiRefNet model (skipped without FURNIMATTE_MODEL=1)",
    )


def pytest_collection_modifyitems(config, items):
    if os.environ.get("FURNIMATTE_MODEL") != "1":
        skip = pytest.mark.skip(reason="set FURNIMATTE_MODEL=1 to run model smoke test")
        for item in items:
            if "model" in item.keywords:
                item.add_marker(skip)


@pytest.fixture(scope="session")
def qapp():
    """A single offscreen QApplication for widget tests (no display needed)."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
