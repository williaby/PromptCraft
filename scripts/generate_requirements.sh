#!/bin/bash

##: name = generate_requirements.sh
##: description = Generates requirements.txt and requirements-dev.txt from poetry.lock with hash verification for security.
##: usage = ./scripts/generate_requirements.sh [--without-hashes]
##: behavior = Uses poetry export to regenerate requirements files with cryptographic hashes by default.

set -e

# Debug information for CI environments
echo "🔍 Environment Debug Info:"
echo "  Working directory: $(pwd)"
echo "  Poetry version: $(poetry --version)"
echo "  Python version: $(python --version)"
echo "  Virtual environment: ${VIRTUAL_ENV:-Not activated}"
echo "  Poetry environment: $(poetry env info --path 2>/dev/null || echo 'No poetry env')"
echo "  Lock file exists: $(test -f poetry.lock && echo 'Yes' || echo 'No')"
echo "  Packages count: $(poetry show 2>/dev/null | wc -l || echo '0')"
echo "  Poetry config: $(poetry config --list | head -5)"
echo ""

# Test basic poetry commands before proceeding
echo "🧪 Testing Poetry commands..."
if ! poetry check --lock; then
    echo "❌ Poetry lock check failed!"
    exit 1
fi

if ! poetry show --quiet > /dev/null 2>&1; then
    echo "❌ Poetry show failed - dependencies not properly installed"
    echo "   Running poetry install..."
    poetry install
fi
echo "✅ Poetry environment validated"
echo ""

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

# Function to normalize platform markers for consistent ordering across environments
normalize_platform_markers() {
    local file="$1"
    local description="$2"

    echo "🔧 Normalizing platform markers in $description..."

    # Create a temporary file for processing
    local temp_file="${file}.tmp"

    # Use Python to normalize platform marker ordering
    python3 -c "
import re
import sys

def normalize_markers(content):
    '''Normalize platform marker ordering within parentheses for consistent output'''

    def sort_marker_conditions(match):
        full_match = match.group(0)

        # Extract all conditions within the parentheses
        inner_content = full_match[1:-1]  # Remove outer parentheses

        # Split by ' or ' to get individual conditions
        conditions = [cond.strip() for cond in inner_content.split(' or ')]

        # Sort conditions for deterministic ordering:
        # 1. python_version conditions first
        # 2. platform_python_implementation conditions second
        # 3. platform_machine conditions last (sorted alphabetically)
        def condition_sort_key(condition):
            if 'python_version' in condition:
                return (0, condition)
            elif 'platform_python_implementation' in condition:
                return (1, condition)
            elif 'platform_machine' in condition:
                return (2, condition)
            else:
                return (3, condition)

        sorted_conditions = sorted(conditions, key=condition_sort_key)

        # Reconstruct the parentheses with sorted conditions
        return '(' + ' or '.join(sorted_conditions) + ')'

    # Pattern to match parentheses containing platform/python markers
    marker_pattern = r'\([^)]*(?:platform_|python_version)[^)]*\)'

    # Apply normalization to all marker groups
    normalized_content = re.sub(marker_pattern, sort_marker_conditions, content)

    return normalized_content

try:
    with open('$file', 'r') as f:
        content = f.read()

    normalized = normalize_markers(content)

    with open('$temp_file', 'w') as f:
        f.write(normalized)

    # Atomic replacement
    import os
    os.replace('$temp_file', '$file')

    print('✅ Platform markers normalized successfully')

except Exception as e:
    print(f'❌ Error normalizing platform markers: {e}')
    sys.exit(1)
"

    if [[ $? -ne 0 ]]; then
        echo "❌ Failed to normalize platform markers in $file"
        rm -f "$temp_file"
        return 1
    fi

    echo "✅ Platform markers normalized in $description"
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

# Normalize platform markers for consistent ordering
normalize_platform_markers "requirements.txt" "main requirements"

# Validate the generated file
validate_requirements "requirements.txt" "main requirements"

echo "✅ requirements.txt updated and validated."

echo "📦 Exporting requirements-dev.txt using poetry export..."
poetry export \
    --format=requirements.txt \
    --output=requirements-dev.txt \
    --with=dev \
    $WITHOUT_HASHES

# Normalize platform markers for consistent ordering
normalize_platform_markers "requirements-dev.txt" "dev requirements"

# Validate the generated file
validate_requirements "requirements-dev.txt" "dev requirements"

echo "✅ requirements-dev.txt updated and validated."

# Generate Docker requirements (minimal, always with hashes for security)
echo "📦 Generating requirements-docker.txt (production only)..."
poetry export \
    --format=requirements.txt \
    --output=requirements-docker.txt \
    --without=dev

# Normalize platform markers for consistent ordering
normalize_platform_markers "requirements-docker.txt" "Docker requirements"

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
