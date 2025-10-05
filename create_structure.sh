#!/bin/bash
# Script to create complete directory structure for Playwright Stealth Testing Framework
# Usage: bash create_structure.sh

echo "Creating Playwright Stealth Testing Framework directory structure..."

# Create main directories
mkdir -p .github/workflows
mkdir -p src/core
mkdir -p src/runners
mkdir -p src/config
mkdir -p src/utils
mkdir -p profiles
mkdir -p test_results/screenshots
mkdir -p test_results/reports

# Create __init__.py files for Python packages
touch src/__init__.py
touch src/core/__init__.py
touch src/runners/__init__.py
touch src/config/__init__.py
touch src/utils/__init__.py

echo "✅ Directory structure created successfully!"
echo ""
echo "Next steps:"
echo "1. Copy all files from artifacts into their respective directories"
echo "2. Install dependencies: pip install -r requirements.txt"
echo "3. Install Playwright browsers: playwright install chromium"
echo "4. Configure proxy secrets in GitHub"
echo "5. Run first test: python main.py --proxy env: --library playwright_stealth"
echo ""
echo "Directory tree:"
tree -L 3 -I '__pycache__|*.pyc'
