#!/bin/bash
# Script to move coverage files to reports/coverage directory

echo "Moving coverage files..."

cd /home/byron/dev/PromptCraft

# Move each file and report status
for file in coverage-auth.xml coverage-focused.xml coverage-integration.xml coverage-performance.xml coverage-unit.xml coverage.json coverage.xml; do
    if [ -f "$file" ]; then
        mv "$file" "reports/coverage/"
        echo "✓ Moved $file"
    else
        echo "✗ File not found: $file"
    fi
done

echo "Done."
