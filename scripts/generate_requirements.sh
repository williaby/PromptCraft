#!/bin/bash

##: name = generate_requirements.sh
##: description = Generates requirements.txt and requirements-dev.txt from poetry.lock with hash verification for security.
##: usage = ./scripts/generate_requirements.sh [--without-hashes]
##: behavior = Uses poetry export to regenerate requirements files with cryptographic hashes by default.

set -e

# Parse command line arguments
WITHOUT_HASHES=""
if [[ "$1" == "--without-hashes" ]]; then
    WITHOUT_HASHES="--without-hashes"
    echo "🔓 Generating requirements files WITHOUT hashes (compatibility mode)"
else
    echo "🔐 Generating requirements files WITH hashes (secure mode)"
fi

# Backup existing files for rollback capability
if [[ -f requirements.txt ]]; then
    cp requirements.txt requirements.txt.backup
fi
if [[ -f requirements-dev.txt ]]; then
    cp requirements-dev.txt requirements-dev.txt.backup
fi

# Function to validate generated requirements file
validate_requirements() {
    local file="$1"
    local description="$2"

    echo "🔍 Validating $description..."

    # Check file exists and is not empty
    if [[ ! -f "$file" ]] || [[ ! -s "$file" ]]; then
        echo "❌ ERROR: $file is missing or empty"
        return 1
    fi

    # Validate hash integrity if hashes are enabled
    if [[ "$WITHOUT_HASHES" == "" ]]; then
        # Check that hashes are present
        if ! grep -q "sha256:" "$file"; then
            echo "❌ ERROR: No SHA256 hashes found in $file"
            return 1
        fi

        # Validate hash format (basic sanity check)
        if grep -E "sha256:[^a-f0-9]" "$file"; then
            echo "❌ ERROR: Invalid hash format found in $file"
            return 1
        fi

        echo "✅ Hash validation passed for $file"
    fi

    # Check for dependency conflicts (basic)
    if python -c "
import pkg_resources
try:
    with open('$file', 'r') as f:
        reqs = [line.split('==')[0].split(' ')[0] for line in f if '==' in line and not line.startswith('#')]
    pkg_resources.require(reqs[:5])  # Sample check first 5 deps
    print('✅ Basic dependency compatibility check passed')
except Exception as e:
    print(f'⚠️  Warning: Potential dependency conflict: {e}')
" 2>/dev/null || echo "⚠️  Could not perform dependency conflict check"; then
        :
    fi
}

# Function to rollback on failure
rollback_on_failure() {
    echo "❌ Generation failed, rolling back..."
    if [[ -f requirements.txt.backup ]]; then
        mv requirements.txt.backup requirements.txt
        echo "✅ Restored requirements.txt backup"
    fi
    if [[ -f requirements-dev.txt.backup ]]; then
        mv requirements-dev.txt.backup requirements-dev.txt
        echo "✅ Restored requirements-dev.txt backup"
    fi
    exit 1
}

# Trap to handle failures
trap rollback_on_failure ERR

echo "📦 Exporting requirements.txt using poetry export..."
poetry export \
    --format=requirements.txt \
    --output=requirements.txt \
    $WITHOUT_HASHES

# Validate the generated file
validate_requirements "requirements.txt" "main requirements"

echo "✅ requirements.txt updated and validated."

echo "📦 Exporting requirements-dev.txt using poetry export..."
poetry export \
    --format=requirements.txt \
    --output=requirements-dev.txt \
    --with=dev \
    $WITHOUT_HASHES

# Validate the generated file
validate_requirements "requirements-dev.txt" "dev requirements"

echo "✅ requirements-dev.txt updated and validated."

# Generate Docker requirements (minimal, always with hashes for security)
echo "📦 Generating requirements-docker.txt (production only)..."
poetry export \
    --format=requirements.txt \
    --output=requirements-docker.txt \
    --only=main

# Validate the Docker requirements file
validate_requirements "requirements-docker.txt" "Docker requirements"

echo "✅ requirements-docker.txt updated and validated."

# Lockfile consistency check
echo "🔍 Verifying lockfile consistency..."
LOCK_DEPS=$(poetry show --without=dev | wc -l)
REQ_DEPS=$(grep -c "==" requirements.txt || echo "0")

if [[ $((LOCK_DEPS - REQ_DEPS)) -gt 5 ]] || [[ $((REQ_DEPS - LOCK_DEPS)) -gt 5 ]]; then
    echo "⚠️  Warning: Significant difference between poetry.lock ($LOCK_DEPS) and requirements.txt ($REQ_DEPS) dependencies"
    echo "   This might indicate a synchronization issue"
else
    echo "✅ Lockfile and requirements.txt are reasonably consistent"
fi

# Clean up backup files on success
rm -f requirements.txt.backup requirements-dev.txt.backup

echo ""
echo "📋 Summary:"
echo "  - requirements.txt (main dependencies: $REQ_DEPS packages)"
echo "  - requirements-dev.txt (main + dev dependencies)"
echo "  - requirements-docker.txt (production only, always with hashes)"
echo ""

if [[ "$WITHOUT_HASHES" == "" ]]; then
    echo "🔐 Hash verification enabled. Install with:"
    echo "   pip install --require-hashes -r requirements.txt"
    echo ""
    echo "⚠️  Note: Hash verification requires all dependencies to be from trusted sources"
    echo "   AssuredOSS packages included in hash verification"
else
    echo "🔓 Hash verification disabled. Install with:"
    echo "   pip install -r requirements.txt"
fi
