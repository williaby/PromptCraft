#!/bin/bash
# Generate separate HTML coverage reports for each test type
# This allows detailed analysis of coverage by unit, integration, performance, etc.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Generating coverage reports by test type${NC}"
echo "=============================================="

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Create coverage output directory
mkdir -p htmlcov-by-type

# Function to run tests and generate coverage for a specific test type
generate_coverage_for_test_type() {
    local test_type=$1
    local test_path=$2
    local marker=$3
    local description=$4
    
    echo -e "\n${YELLOW}📊 Generating coverage for ${description}${NC}"
    
    # Run tests with coverage for this specific type
    poetry run pytest \
        --cov=src \
        --cov-report=html:htmlcov-by-type/${test_type} \
        --cov-report=xml:coverage-${test_type}.xml \
        --cov-report=term-missing \
        --tb=short \
        -m "${marker}" \
        ${test_path} || {
        echo -e "${RED}⚠️  Some ${description} failed, but coverage was generated${NC}"
    }
    
    # Add test type info to the HTML report
    if [ -f "htmlcov-by-type/${test_type}/index.html" ]; then
        # Insert custom header with test type info
        sed -i "s/<h1>Coverage report<\/h1>/<h1>Coverage report: ${description}<\/h1><p style=\"background: #e6f3ff; padding: 10px; border-radius: 5px; margin: 10px 0;\"><strong>Test Type:<\/strong> ${description} | <strong>Marker:<\/strong> ${marker} | <strong>Path:<\/strong> ${test_path}<\/p>/" \
            "htmlcov-by-type/${test_type}/index.html"
        
        echo -e "${GREEN}✅ ${description} coverage report: htmlcov-by-type/${test_type}/index.html${NC}"
    else
        echo -e "${RED}❌ Failed to generate ${description} coverage report${NC}"
    fi
}

# Generate coverage for each test type
generate_coverage_for_test_type "unit" "tests/unit/" "unit" "Unit Tests"
generate_coverage_for_test_type "integration" "tests/integration/" "integration" "Integration Tests"
generate_coverage_for_test_type "auth" "tests/auth/" "auth" "Authentication Tests"
generate_coverage_for_test_type "performance" "tests/performance/" "performance" "Performance Tests"
generate_coverage_for_test_type "stress" "tests/performance/" "stress" "Stress Tests"

# Generate combined coverage for comparison
echo -e "\n${YELLOW}📊 Generating combined coverage report${NC}"
poetry run pytest \
    --cov=src \
    --cov-report=html:htmlcov-by-type/combined \
    --cov-report=xml:coverage-combined.xml \
    --cov-report=term-missing \
    --tb=short \
    tests/ || {
    echo -e "${RED}⚠️  Some tests failed, but combined coverage was generated${NC}"
}

# Add combined report info
if [ -f "htmlcov-by-type/combined/index.html" ]; then
    sed -i "s/<h1>Coverage report<\/h1>/<h1>Coverage report: All Tests Combined<\/h1><p style=\"background: #f0f8e6; padding: 10px; border-radius: 5px; margin: 10px 0;\"><strong>Test Type:<\/strong> All Tests Combined | <strong>Includes:<\/strong> Unit, Integration, Auth, Performance, Stress<\/p>/" \
        "htmlcov-by-type/combined/index.html"
    echo -e "${GREEN}✅ Combined coverage report: htmlcov-by-type/combined/index.html${NC}"
fi

# Generate summary comparison
echo -e "\n${BLUE}📈 Coverage Summary by Test Type${NC}"
echo "=================================="

# Extract coverage percentages from each XML report
for report in coverage-unit.xml coverage-integration.xml coverage-auth.xml coverage-performance.xml coverage-stress.xml coverage-combined.xml; do
    if [ -f "$report" ]; then
        test_type=$(echo "$report" | sed 's/coverage-\(.*\)\.xml/\1/')
        coverage=$(grep -oP 'line-rate="\K[^"]*' "$report" | head -1 | awk '{printf "%.2f%%", $1*100}')
        lines_covered=$(grep -oP 'lines-covered="\K[^"]*' "$report" | head -1)
        lines_valid=$(grep -oP 'lines-valid="\K[^"]*' "$report" | head -1)
        
        printf "%-15s %8s (%s/%s lines)\n" "$test_type:" "$coverage" "$lines_covered" "$lines_valid"
    fi
done

echo -e "\n${GREEN}🎉 Coverage reports generated successfully!${NC}"
echo -e "${BLUE}📁 Reports location: htmlcov-by-type/${NC}"
echo -e "${BLUE}🌐 Start server: cd htmlcov-by-type && python -m http.server 8081${NC}"

# Start a simple HTTP server for viewing reports
echo -e "\n${YELLOW}🚀 Starting HTTP server for coverage reports...${NC}"
cd htmlcov-by-type
nohup python -m http.server 8081 > /dev/null 2>&1 & 
SERVER_PID=$!
echo -e "${GREEN}📡 Coverage reports server started at http://localhost:8081${NC}"
echo -e "${BLUE}Available reports:${NC}"
echo "  • Unit Tests: http://localhost:8081/unit/"
echo "  • Integration Tests: http://localhost:8081/integration/"
echo "  • Auth Tests: http://localhost:8081/auth/"
echo "  • Performance Tests: http://localhost:8081/performance/"
echo "  • Stress Tests: http://localhost:8081/stress/"
echo "  • Combined: http://localhost:8081/combined/"
echo -e "${YELLOW}💡 Use VS Code Simple Browser (Ctrl+Shift+P) to view these URLs${NC}"