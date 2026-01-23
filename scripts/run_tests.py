"""Helper script to run pytest with correct PYTHONPATH.

Usage:
    .venv\\Scripts\\python run_tests.py [pytest args]
    
Example:
    .venv\\Scripts\\python run_tests.py tests/licensing/ -v
    .venv\\Scripts\\python run_tests.py tests/licensing/test_grace_period.py::test_grace_period_expired_blocks_access
"""

import sys
from pathlib import Path

# Add src to sys.path BEFORE any imports (including pytest)
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Now import and run pytest
import pytest

pytest_args = sys.argv[1:] if len(sys.argv) > 1 else ['tests/', '-v']
sys.exit(pytest.main(pytest_args))

