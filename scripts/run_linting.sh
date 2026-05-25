#!/bin/bash
set -euo pipefail
# Resolve repo root from git so the script works for any developer and on CI.
cd "$(git rev-parse --show-toplevel)"
echo "Running Ruff format..."
uv run --frozen ruff format src/core/hyde_processor.py
echo "Running Ruff lint..."
uv run --frozen ruff check src/core/hyde_processor.py
echo "Done!"
