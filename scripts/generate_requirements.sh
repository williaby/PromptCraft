#!/bin/bash
# Generate requirements files with hashes for secure pip installation

set -e

echo "Generating requirements files with hashes..."

# Function to generate requirements for a specific group
generate_requirements() {
    local group=$1
    local output=$2
    
    if [ "$group" == "main" ]; then
        echo "Generating main requirements..."
        poetry export \
            --format=requirements.txt \
            --with-hashes \
            --without-urls \
            --output="$output"
    else
        echo "Generating $group requirements..."
        poetry export \
            --format=requirements.txt \
            --with-hashes \
            --without-urls \
            --with="$group" \
            --output="$output"
    fi
}

# Main requirements
generate_requirements "main" "requirements.txt"

# Development requirements (includes main + dev)
generate_requirements "dev" "requirements-dev.txt"

# Test requirements (if test group exists)
if poetry show --with test &>/dev/null; then
    generate_requirements "test" "requirements-test.txt"
fi

# Create a minimal requirements file for Docker
echo "Creating minimal Docker requirements..."
cat > requirements-docker.txt << 'DOCKER_EOF'
# Minimal requirements for Docker production image
# Generated from pyproject.toml - DO NOT EDIT MANUALLY
# Regenerate with: ./scripts/generate_requirements.sh

# Core dependencies only - no dev/test packages
DOCKER_EOF

# Extract only production dependencies
poetry export \
    --format=requirements.txt \
    --without-hashes \
    --without-urls \
    --output=requirements-temp.txt

# Filter out dev dependencies and add to Docker requirements
grep -E '^(gradio|fastapi|uvicorn|pydantic|qdrant-client|sentence-transformers|anthropic|openai|azure-|redis|prometheus-client|python-dotenv|structlog|pyyaml|httpx|tenacity|aiofiles|cryptography|pyjwt)' requirements-temp.txt >> requirements-docker.txt

rm requirements-temp.txt

echo "Requirements files generated successfully!"
echo ""
echo "Files created:"
echo "  - requirements.txt (with hashes for secure installation)"
echo "  - requirements-dev.txt (includes development dependencies)"
echo "  - requirements-docker.txt (minimal for Docker images)"
if [ -f "requirements-test.txt" ]; then
    echo "  - requirements-test.txt (includes test dependencies)"
fi
echo ""
echo "To install with hash verification:"
echo "  pip install --require-hashes -r requirements.txt"
