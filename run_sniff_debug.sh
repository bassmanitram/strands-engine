#!/bin/bash

# Shell script to run strands_agent_factory sniff tests with debug logging
# This script enables comprehensive debug logging to help diagnose issues

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Running strands_agent_factory sniff test with debug logging${NC}"
echo "=================================================================="

# Set the working directory to the script's location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}Working directory:${NC} $PWD"

# Check if we're in a virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo -e "${GREEN}✓ Virtual environment active:${NC} $VIRTUAL_ENV"
else
    echo -e "${YELLOW}⚠ No virtual environment detected${NC}"
fi

# Check for required dependencies
echo -e "\n${BLUE}Checking dependencies...${NC}"
python -c "import strands" 2>/dev/null && echo -e "${GREEN}✓ strands-agents installed${NC}" || echo -e "${RED}✗ strands-agents not found${NC}"
python -c "import loguru" 2>/dev/null && echo -e "${GREEN}✓ loguru installed${NC}" || echo -e "${RED}✗ loguru not found${NC}"

# Check for API credentials
echo -e "\n${BLUE}Checking API credentials...${NC}"
if [[ -n "$GOOGLE_API_KEY" ]]; then
    echo -e "${GREEN}✓ GOOGLE_API_KEY is set${NC}"
elif [[ -n "$GEMINI_API_KEY" ]]; then
    echo -e "${GREEN}✓ GEMINI_API_KEY is set${NC}"
elif [[ -n "$OPENAI_API_KEY" ]]; then
    echo -e "${YELLOW}⚠ OPENAI_API_KEY is set (but test uses Gemini)${NC}"
else
    echo -e "${RED}✗ No API credentials found${NC}"
    echo -e "${YELLOW}Set GOOGLE_API_KEY or GEMINI_API_KEY for full testing${NC}"
fi

# Choose which test to run
echo -e "\n${BLUE}Available tests:${NC}"
echo "1. Basic sniff test (no credentials required)"
echo "2. Enhanced sniff test with Gemini (requires API key)"
echo "3. Both tests"
echo ""

# Default to enhanced test if credentials are available
if [[ -n "$GOOGLE_API_KEY" || -n "$GEMINI_API_KEY" ]]; then
    DEFAULT_CHOICE="2"
    echo -e "${GREEN}API credentials detected - defaulting to enhanced test${NC}"
else
    DEFAULT_CHOICE="1"
    echo -e "${YELLOW}No API credentials - defaulting to basic test${NC}"
fi

read -p "Choose test to run [1-3] (default: $DEFAULT_CHOICE): " CHOICE
CHOICE=${CHOICE:-$DEFAULT_CHOICE}

# Set up logging environment
export LOGURU_LEVEL="DEBUG"
export PYTHONPATH="$PWD:$PYTHONPATH"

echo -e "\n${BLUE}Debug logging enabled - LOGURU_LEVEL=DEBUG${NC}"
echo "=================================================================="

run_basic_test() {
    echo -e "\n${BLUE}🔍 Running basic sniff test...${NC}"
    echo "=================================================================="
    
    if python test_sniff.py; then
        echo -e "\n${GREEN}✅ Basic sniff test completed${NC}"
        return 0
    else
        echo -e "\n${RED}❌ Basic sniff test failed${NC}"
        return 1
    fi
}

run_enhanced_test() {
    echo -e "\n${BLUE}🚀 Running enhanced sniff test with credentials...${NC}"
    echo "=================================================================="
    
    if [[ -z "$GOOGLE_API_KEY" && -z "$GEMINI_API_KEY" ]]; then
        echo -e "${RED}❌ Enhanced test requires GOOGLE_API_KEY or GEMINI_API_KEY${NC}"
        return 1
    fi
    
    if python test_sniff_with_credentials.py; then
        echo -e "\n${GREEN}✅ Enhanced sniff test completed${NC}"
        return 0
    else
        echo -e "\n${RED}❌ Enhanced sniff test failed${NC}"
        return 1
    fi
}

# Run the selected test(s)
case $CHOICE in
    1)
        run_basic_test
        exit_code=$?
        ;;
    2)
        run_enhanced_test
        exit_code=$?
        ;;
    3)
        echo -e "\n${BLUE}Running both tests...${NC}"
        run_basic_test
        basic_result=$?
        
        run_enhanced_test
        enhanced_result=$?
        
        if [[ $basic_result -eq 0 && $enhanced_result -eq 0 ]]; then
            exit_code=0
        else
            exit_code=1
        fi
        ;;
    *)
        echo -e "${RED}Invalid choice: $CHOICE${NC}"
        exit 1
        ;;
esac

# Summary
echo ""
echo "=================================================================="
if [[ $exit_code -eq 0 ]]; then
    echo -e "${GREEN}🎉 All selected tests completed successfully!${NC}"
    echo -e "${GREEN}strands_agent_factory is working correctly${NC}"
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo -e "${YELLOW}Check the debug output above for details${NC}"
fi
echo "=================================================================="

# Additional debug information
echo -e "\n${BLUE}Debug Information:${NC}"
echo "Python version: $(python --version)"
echo "Working directory: $PWD"
echo "PYTHONPATH: $PYTHONPATH"
echo "Loguru level: $LOGURU_LEVEL"

if [[ -n "$GOOGLE_API_KEY" ]]; then
    echo "GOOGLE_API_KEY: [SET - ${#GOOGLE_API_KEY} characters]"
fi

if [[ -n "$GEMINI_API_KEY" ]]; then
    echo "GEMINI_API_KEY: [SET - ${#GEMINI_API_KEY} characters]"
fi

# Show available test files
echo -e "\n${BLUE}Available test files:${NC}"
ls -la test_*.py 2>/dev/null || echo "No test files found"

echo -e "\n${BLUE}For more detailed debugging, you can also run:${NC}"
echo "  LOGURU_LEVEL=TRACE python test_sniff_with_credentials.py"
echo "  python -c 'from strands_agent_factory import EngineConfig, AgentFactory; print(\"Import test passed\")'"

exit $exit_code