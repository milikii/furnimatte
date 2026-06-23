"""Pytest configuration."""

import os

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "model: needs BiRefNet model (skipped without FURNIMATTE_MODEL=1)")


def pytest_collection_modifyitems(config, items):
    if os.environ.get("FURNIMATTE_MODEL") != "1":
        skip = pytest.mark.skip(reason="set FURNIMATTE_MODEL=1 to run model smoke test")
        for item in items:
            if "model" in item.keywords:
                item.add_marker(skip)
