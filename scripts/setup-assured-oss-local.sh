#!/bin/bash
# Setup script for local Assured-OSS authentication
# This script configures Poetry to use Assured-OSS package repository

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 Setting up Assured-OSS authentication for local development${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud CLI not found${NC}"
    echo "Please install gcloud CLI: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}❌ Poetry not found${NC}"
    echo "Please install Poetry: https://python-poetry.org/docs/#installation"
    exit 1
fi

echo -e "${GREEN}🔐 Using service account authentication${NC}"

# Look for service account file in common locations
SA_LOCATIONS=(
    "$(pwd)/.gcp/service-account.json"
    "$(pwd)/secrets/service-account.json"
    "$HOME/.config/promptcraft/service-account.json"
)

SA_FILE=""
for location in "${SA_LOCATIONS[@]}"; do
    if [[ -f "$location" ]]; then
        SA_FILE="$location"
        break
    fi
done

if [[ -z "$SA_FILE" ]]; then
    echo -e "${YELLOW}📁 Service account file not found in default locations${NC}"
    echo "Default locations checked:"
    for location in "${SA_LOCATIONS[@]}"; do
        echo "  - $location"
    done
    echo ""
    echo -e "${BLUE}💡 To set up the service account file:${NC}"
    echo "1. Create directory: mkdir -p .gcp"
    echo "2. Copy your service account JSON: cp /path/to/your/service-account.json .gcp/service-account.json"
    echo "3. Re-run this script"
    echo ""
    read -p "Enter path to service account JSON file: " SA_FILE
fi

if [[ ! -f "$SA_FILE" ]]; then
    echo -e "${RED}❌ Service account file not found: $SA_FILE${NC}"
    exit 1
fi

# Validate the service account file format
if ! jq empty "$SA_FILE" 2>/dev/null; then
    echo -e "${RED}❌ Invalid JSON format in service account file${NC}"
    exit 1
fi

# Extract project ID from service account file
PROJECT_ID=$(jq -r '.project_id' "$SA_FILE" 2>/dev/null)
if [[ -z "$PROJECT_ID" || "$PROJECT_ID" == "null" ]]; then
    echo -e "${RED}❌ Could not extract project_id from service account file${NC}"
    exit 1
fi

# Set project ID
gcloud config set project "$PROJECT_ID"

# Activate service account
gcloud auth activate-service-account --key-file="$SA_FILE"
echo -e "${GREEN}✅ Service account activated for project: $PROJECT_ID${NC}"

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Configure Poetry repositories
echo -e "${GREEN}🔧 Configuring Poetry repositories...${NC}"
poetry config repositories.assured-oss https://us-python.pkg.dev/assured-oss/python-packages/simple/

# Get access token and configure authentication
echo -e "${GREEN}🔐 Setting up authentication...${NC}"
ACCESS_TOKEN=$(gcloud auth print-access-token)
poetry config http-basic.assured-oss oauth2accesstoken "$ACCESS_TOKEN"

# Verify configuration
echo -e "${GREEN}🔍 Verifying configuration...${NC}"
poetry config --list | grep -E "(assured-oss|http-basic)"

# Test access to Assured-OSS
echo -e "${GREEN}🧪 Testing Assured-OSS access...${NC}"
if curl -H "Authorization: Bearer $ACCESS_TOKEN" \
        "https://us-python.pkg.dev/assured-oss/python-packages/simple/" \
        --fail --silent --show-error > /dev/null; then
    echo -e "${GREEN}✅ Assured-OSS access verified${NC}"
else
    echo -e "${RED}❌ Failed to access Assured-OSS${NC}"
    echo "Please check your Google Cloud permissions"
    exit 1
fi

echo -e "${GREEN}🎉 Assured-OSS setup completed successfully!${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Run 'poetry install' to install dependencies from assured-oss"
echo "2. Access tokens expire after 1 hour - re-run this script if you get auth errors"
echo "3. Keep your service account file secure and never commit it to git"
echo ""
echo -e "${BLUE}📁 Service account file locations (in order of preference):${NC}"
echo "   - .gcp/service-account.json (project-specific, git-ignored)"
echo "   - secrets/service-account.json (project-specific, git-ignored)"
echo "   - ~/.config/promptcraft/service-account.json (user-global)"
