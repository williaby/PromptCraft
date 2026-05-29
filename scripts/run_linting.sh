#!/bin/bash
cd /home/byron/dev/PromptCraft
echo "Running Black formatting..."
uv run black src/core/hyde_processor.py
echo "Running Ruff linting..."
uv run ruff check src/core/hyde_processor.py
echo "Done!"
