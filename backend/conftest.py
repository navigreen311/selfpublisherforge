"""Root conftest: ensures project root is on sys.path for shared imports."""
import sys
from pathlib import Path

# Add the project root (parent of backend/) to sys.path
# so that 'shared' package imports work correctly
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
