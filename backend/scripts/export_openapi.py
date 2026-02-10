"""Export the OpenAPI schema from the FastAPI application to a JSON file.

Usage:
    python -m scripts.export_openapi

The generated file is written to ``docs/openapi.json`` (relative to the
repository root / working directory).
"""

import json
import os
from pathlib import Path

from app.main import app

def main() -> None:
    schema = app.openapi()

    output_dir = Path("docs")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "openapi.json"
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)

    endpoint_count = len(schema.get("paths", {}))
    print(f"OpenAPI spec exported: {endpoint_count} endpoints")
    print(f"Written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
