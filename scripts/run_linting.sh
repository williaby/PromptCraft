#!/bin/bash
cd /home/byron/dev/PromptCraft
echo "Running Ruff format..."
uv run --frozen ruff format src/core/hyde_processor.py
echo "Running Ruff lint..."
uv run --frozen ruff check src/core/hyde_processor.py
echo "Done!"
