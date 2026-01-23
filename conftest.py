"""Root conftest for pytest - sets up Python path for all tests.

This must run BEFORE pytest imports test modules.
"""

import sys
from pathlib import Path


def pytest_configure(config):
    """Pytest hook that runs before test collection.
    
    This adds src/ to sys.path so test modules can import app code.
    """
    src_path = Path(__file__).parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


