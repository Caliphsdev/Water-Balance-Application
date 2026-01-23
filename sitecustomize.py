"""Site customization to add src/ to Python path before pytest runs.

This executes automatically when Python starts if in the current directory.
"""

import sys
from pathlib import Path

# Add src to path FIRST (before any imports)
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
