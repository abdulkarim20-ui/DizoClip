"""
Test isolation. Runs BEFORE any `app.*` import, because app/config/paths.py
resolves its file paths at import time.
"""
import os
import shutil
import tempfile
from pathlib import Path

_TEST_DATA = Path(tempfile.mkdtemp(prefix="dizoclip_tests_"))
os.environ["DIZOCLIP_DATA_DIR"] = str(_TEST_DATA)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # no real windows during tests

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_test_data_dir():
    """Every test starts with an empty data folder."""
    for child in _TEST_DATA.iterdir():
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink(missing_ok=True)
    yield


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(_TEST_DATA, ignore_errors=True)
