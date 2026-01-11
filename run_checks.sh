#!/bin/bash
# Run code quality checks (ruff and mypy)

set -e  # Exit on error

echo "Running code quality checks..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if any checks failed
FAILED=0

# Run ruff format check
echo -e "${YELLOW}Running ruff format check...${NC}"
if uv run ruff format --check .; then
    echo -e "${GREEN}✓ Ruff format check passed${NC}"
else
    echo -e "${RED}✗ Ruff format check failed${NC}"
    FAILED=1
fi
echo ""

# Run ruff lint
echo -e "${YELLOW}Running ruff lint...${NC}"
if uv run ruff check .; then
    echo -e "${GREEN}✓ Ruff lint passed${NC}"
else
    echo -e "${RED}✗ Ruff lint failed${NC}"
    FAILED=1
fi
echo ""

# Run mypy
echo -e "${YELLOW}Running mypy type checking...${NC}"
if uv run mypy src scripts; then
    echo -e "${GREEN}✓ Mypy type checking passed${NC}"
else
    echo -e "${RED}✗ Mypy type checking failed${NC}"
    FAILED=1
fi
echo ""

# Final result
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All checks passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some checks failed. Please fix the issues above.${NC}"
    exit 1
fi
