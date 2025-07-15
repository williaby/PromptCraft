#!/bin/bash
cd /home/byron/dev/PromptCraft
echo "Running Black formatting..."
poetry run black src/core/hyde_processor.py
echo "Running Ruff linting..."
poetry run ruff check src/core/hyde_processor.py
echo "Done!"
