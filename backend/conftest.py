"""Root conftest — ensures ``app`` and ``shared`` packages are importable."""
import sys
from pathlib import Path

# backend/ directory
backend_dir = Path(__file__).resolve().parent
# project root (parent of backend/)
project_root = backend_dir.parent

# Add both to sys.path so `import app.…` and `import shared.…` work
for p in (str(backend_dir), str(project_root)):
    if p not in sys.path:
        sys.path.insert(0, p)
