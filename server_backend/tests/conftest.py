import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture(autouse=True)
def set_test_mode(monkeypatch):
    """Ensure TEST_MODE is enabled for all tests."""
    monkeypatch.setenv('TEST_MODE', 'true')
    monkeypatch.setenv('SKIP_VERIFICATION', 'true')
