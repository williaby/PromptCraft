#!/bin/bash
# Configure GitHub branch protection with required security checks
# This script enforces security gates to make all security scans blocking (not advisory)

set -euo pipefail

# Configuration
REPO_OWNER="${GITHUB_REPOSITORY_OWNER:-williaby}"
REPO_NAME="${GITHUB_REPOSITORY_NAME:-PromptCraft}"
BRANCH="${BRANCH:-main}"
ENFORCE_ADMINS="${ENFORCE_ADMINS:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Required status checks that must pass before merging
# These match the existing CI/CD workflows in the repository
REQUIRED_CHECKS=(
    "CodeQL Analysis"
    "CI / Test"
    "dependency-review"
    "PR Validation"
)

# Function to check if GitHub CLI is installed and authenticated
check_prerequisites() {
    echo "Checking prerequisites..."

    if ! command -v gh &> /dev/null; then
        echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
        echo "Please install it from: https://cli.github.com/"
        exit 1
    fi

    if ! gh auth status &> /dev/null; then
        echo -e "${RED}Error: GitHub CLI is not authenticated${NC}"
        echo "Please run: gh auth login"
        exit 1
    fi

    echo -e "${GREEN}✓ Prerequisites checked${NC}"
}

# Function to get current branch protection settings
get_current_protection() {
    echo "Fetching current branch protection settings..."

    local current_settings
    current_settings=$(gh api repos/${REPO_OWNER}/${REPO_NAME}/branches/${BRANCH}/protection 2>/dev/null || echo "{}")

    if [[ "$current_settings" == "{}" ]]; then
        echo -e "${YELLOW}No existing branch protection found${NC}"
    else
        echo -e "${GREEN}Current branch protection settings retrieved${NC}"
    fi

    echo "$current_settings"
}

# Function to configure branch protection
configure_protection() {
    echo "Configuring branch protection for ${BRANCH}..."

    # Build the required status checks array
    local checks_json=""
    for check in "${REQUIRED_CHECKS[@]}"; do
        checks_json="${checks_json}\"${check}\","
    done
    checks_json="${checks_json%,}" # Remove trailing comma

    # Create the protection rules JSON
    local protection_json=$(cat <<EOF
{
    "required_status_checks": {
        "strict": true,
        "contexts": [${checks_json}]
    },
    "enforce_admins": ${ENFORCE_ADMINS},
    "required_pull_request_reviews": {
        "dismiss_stale_reviews": true,
        "require_code_owner_reviews": true,
        "required_approving_review_count": 1,
        "require_last_push_approval": false
    },
    "restrictions": null,
    "allow_force_pushes": false,
    "allow_deletions": false,
    "block_creations": false,
    "required_conversation_resolution": true,
    "lock_branch": false,
    "allow_fork_syncing": false
}
EOF
)

    # Apply the protection rules
    if gh api repos/${REPO_OWNER}/${REPO_NAME}/branches/${BRANCH}/protection \
        --method PUT \
        --input - <<< "$protection_json"; then
        echo -e "${GREEN}✓ Branch protection configured successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to configure branch protection${NC}"
        return 1
    fi
}

# Function to verify the configuration
verify_configuration() {
    echo "Verifying branch protection configuration..."

    local current_settings
    current_settings=$(gh api repos/${REPO_OWNER}/${REPO_NAME}/branches/${BRANCH}/protection 2>/dev/null)

    # Check if all required status checks are present
    local all_checks_present=true
    for check in "${REQUIRED_CHECKS[@]}"; do
        if ! echo "$current_settings" | jq -e ".required_status_checks.contexts[] | select(. == \"$check\")" > /dev/null; then
            echo -e "${RED}✗ Missing required check: $check${NC}"
            all_checks_present=false
        else
            echo -e "${GREEN}✓ Required check present: $check${NC}"
        fi
    done

    # Check if status checks are strict (blocking)
    local strict_checks
    strict_checks=$(echo "$current_settings" | jq -r '.required_status_checks.strict')
    if [[ "$strict_checks" == "true" ]]; then
        echo -e "${GREEN}✓ Status checks are blocking (strict mode enabled)${NC}"
    else
        echo -e "${RED}✗ Status checks are not blocking${NC}"
        all_checks_present=false
    fi

    if [[ "$all_checks_present" == "true" ]]; then
        echo -e "${GREEN}✓ Branch protection verified successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ Branch protection verification failed${NC}"
        return 1
    fi
}

# Function to display usage information
usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Configure GitHub branch protection with required security checks.

OPTIONS:
    -o, --owner OWNER       Repository owner (default: from GITHUB_REPOSITORY_OWNER or 'promptcraft-hybrid')
    -r, --repo REPO         Repository name (default: from GITHUB_REPOSITORY_NAME or 'PromptCraft')
    -b, --branch BRANCH     Branch to protect (default: main)
    -a, --enforce-admins    Enforce protection for administrators (default: false)
    -h, --help              Display this help message

EXAMPLES:
    # Configure protection for main branch
    $0

    # Configure protection for a test branch
    $0 --branch test/security-gates

    # Configure with admin enforcement
    $0 --enforce-admins

    # Configure for a different repository
    $0 --owner myorg --repo myrepo
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--owner)
            REPO_OWNER="$2"
            shift 2
            ;;
        -r|--repo)
            REPO_NAME="$2"
            shift 2
            ;;
        -b|--branch)
            BRANCH="$2"
            shift 2
            ;;
        -a|--enforce-admins)
            ENFORCE_ADMINS="true"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    echo "GitHub Branch Protection Configuration Script"
    echo "==========================================="
    echo "Repository: ${REPO_OWNER}/${REPO_NAME}"
    echo "Branch: ${BRANCH}"
    echo "Enforce for admins: ${ENFORCE_ADMINS}"
    echo ""

    # Check prerequisites
    check_prerequisites

    # Get current protection settings
    echo ""
    get_current_protection > /dev/null

    # Configure protection
    echo ""
    if configure_protection; then
        # Verify the configuration
        echo ""
        if verify_configuration; then
            echo ""
            echo -e "${GREEN}✓ Branch protection successfully configured!${NC}"
            echo ""
            echo "Security gates are now enforced for the ${BRANCH} branch."
            echo "All PRs must pass the following checks before merging:"
            for check in "${REQUIRED_CHECKS[@]}"; do
                echo "  - $check"
            done
            exit 0
        else
            exit 1
        fi
    else
        exit 1
    fi
}

# Run main function
main
