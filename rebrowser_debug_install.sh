#!/bin/bash

# Rebrowser Playwright Installation Debug Script
# This script tries multiple installation methods and provides detailed debugging

echo "========================================"
echo "🔍 Rebrowser Playwright Installation Debug"
echo "========================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if rebrowser_playwright is installed
echo "1. Checking rebrowser_playwright installation..."
if python -c "import rebrowser_playwright; print(f'Version: {rebrowser_playwright.__version__ if hasattr(rebrowser_playwright, \"__version__\") else \"unknown\"}')" 2>/dev/null; then
    echo "✅ rebrowser_playwright Python package is installed"
else
    echo "❌ rebrowser_playwright not found - installing..."
    pip install rebrowser-playwright
fi

echo ""
echo "2. Checking available commands..."
if command_exists "rebrowser-playwright"; then
    echo "✅ rebrowser-playwright CLI command available"
    rebrowser-playwright --version || echo "⚠️ Version command failed"
else
    echo "❌ rebrowser-playwright CLI command not found"
fi

echo ""
echo "3. Checking Python module capabilities..."
python -c "
import sys
try:
    import rebrowser_playwright
    print('✅ Module imported successfully')
    
    # Check if it has install capability
    if hasattr(rebrowser_playwright, 'install'):
        print('✅ Module has install method')
    else:
        print('❌ Module does not have install method')
        
    # Check browser discovery
    from rebrowser_playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    print('✅ sync_playwright started')
    
    # Try to get browser executable path
    try:
        browser_type = p.chromium
        print(f'✅ Chromium browser type available')
        
        # Check executable path without launching
        import os
        # Common paths where playwright browsers are installed
        possible_paths = [
            os.path.expanduser('~/.cache/ms-playwright'),
            '/home/runner/.cache/ms-playwright',
            os.path.join(os.path.dirname(rebrowser_playwright.__file__), 'driver'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f'📁 Found browser cache directory: {path}')
                if os.path.isdir(path):
                    contents = os.listdir(path)
                    print(f'   Contents: {contents[:5]}...' if len(contents) > 5 else f'   Contents: {contents}')
            else:
                print(f'📂 Browser cache not found: {path}')
                
    except Exception as e:
        print(f'⚠️ Browser path check failed: {e}')
    
    p.stop()
    print('✅ sync_playwright stopped cleanly')
    
except Exception as e:
    print(f'❌ Module test failed: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "4. Attempting browser installation methods..."

# Method 1: Standard playwright install (shares cache)
echo "Method 1: Standard playwright install..."
if playwright install chromium; then
    echo "✅ Method 1 succeeded"
    method1_success=true
else
    echo "❌ Method 1 failed"
    method1_success=false
fi

# Method 2: Python module install
echo "Method 2: Python module install..."
if python -c "
import rebrowser_playwright
import subprocess
import sys

try:
    # Try using subprocess to call the install
    result = subprocess.run([sys.executable, '-m', 'rebrowser_playwright', 'install', 'chromium'], 
                          capture_output=True, text=True, timeout=120)
    if result.returncode == 0:
        print('✅ Module install succeeded')
        print(result.stdout)
    else:
        print('❌ Module install failed')
        print('STDOUT:', result.stdout)
        print('STDERR:', result.stderr)
        sys.exit(1)
except Exception as e:
    print(f'❌ Module install exception: {e}')
    sys.exit(1)
"; then
    echo "✅ Method 2 succeeded"
    method2_success=true
else
    echo "❌ Method 2 failed"
    method2_success=false
fi

# Method 3: Direct browser download (fallback)
echo "Method 3: Direct browser verification..."
python -c "
from rebrowser_playwright.sync_api import sync_playwright
import sys

try:
    p = sync_playwright().start()
    print('Starting browser launch test...')
    
    # This might trigger auto-download
    browser = p.chromium.launch(headless=True)
    print('✅ Browser launched successfully!')
    
    # Quick test
    page = browser.new_page()
    page.goto('https://example.com')
    title = page.title()
    print(f'✅ Page loaded: {title}')
    
    browser.close()
    p.stop()
    print('✅ Method 3 complete - browser working')
    
except Exception as e:
    print(f'❌ Method 3 failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ Method 3 succeeded - browser is functional"
    method3_success=true
else
    echo "❌ Method 3 failed"
    method3_success=false
fi

echo ""
echo "========================================"
echo "📊 INSTALLATION SUMMARY"
echo "========================================"
echo "Method 1 (playwright install): $($method1_success && echo "✅ SUCCESS" || echo "❌ FAILED")"
echo "Method 2 (python module): $($method2_success && echo "✅ SUCCESS" || echo "❌ FAILED")"  
echo "Method 3 (direct test): $($method3_success && echo "✅ SUCCESS" || echo "❌ FAILED")"

if $method1_success || $method2_success || $method3_success; then
    echo ""
    echo "🎉 At least one method succeeded!"
    echo "✅ rebrowser_playwright should now be functional"
    exit 0
else
    echo ""
    echo "❌ All installation methods failed"
    echo "This may indicate a compatibility issue or missing dependencies"
    exit 1
fi