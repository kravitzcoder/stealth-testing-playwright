# 🚀 Deployment Guide - Playwright Stealth Testing Framework

**Complete setup guide for testing Playwright-based stealth libraries**

---

## 📋 Prerequisites

- Python 3.11+
- Git
- GitHub account (for Actions)
- Proxy with authentication support

---

## 🔧 Step 1: Repository Setup (5 minutes)

### Clone Repository
```bash
git clone https://github.com/kravitzcoder/stealth-testing-playwright.git
cd stealth-testing-playwright
```

### Verify Structure
```bash
ls -la
# Should see: main.py, requirements.txt, src/, profiles/, .github/
```

---

## 📦 Step 2: Install Dependencies (10 minutes)

### Install Python Packages
```bash
# Upgrade pip first
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

### Install Playwright Browsers
```bash
# Install Chromium (required for most libraries)
playwright install chromium

# Install system dependencies
playwright install-deps chromium

# Optional: Install Firefox for Camoufox
playwright install firefox
playwright install-deps firefox
```

### Install Patchright Browser
```bash
patchright install chromium
```

### Verify Installations
```bash
python -c "import playwright; print('✅ Playwright')"
python -c "from playwright_stealth import StealthConfig; print('✅ Playwright-stealth')"
python -c "import patchright; print('✅ Patchright')"
python -c "import camoufox; print('✅ Camoufox')"
```

---

## 🔐 Step 3: Configure Proxy (3 minutes)

### For GitHub Actions

1. Go to repository: **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Add these 4 secrets:

```
Name: PROXY_HOST
Value: 84.200.91.70

Name: PROXY_PORT
Value: 8083

Name: PROXY_USERNAME
Value: deola

Name: PROXY_PASSWORD
Value: deola
```

**Important:** No trailing spaces, no quotes!

### For Local Testing

**Option A: Environment Variables**
```bash
export PROXY_HOST="84.200.91.70"
export PROXY_PORT="8083"
export PROXY_USERNAME="deola"
export PROXY_PASSWORD="deola"
```

**Option B: Add to `.env` file** (gitignored)
```bash
cat > .env << EOF
PROXY_HOST=84.200.91.70
PROXY_PORT=8083
PROXY_USERNAME=deola
PROXY_PASSWORD=deola
EOF
```

Then load it:
```bash
export $(cat .env | xargs)
```

---

## 🎯 Step 4: Run First Test (3 minutes)

### Test playwright-stealth (Most Reliable)

**Local:**
```bash
python main.py --proxy env: --library playwright_stealth
```

**GitHub Actions:**
1. Go to **Actions** tab
2. Select **"🎯 Single Library Test"**
3. Click **"Run workflow"**
4. Choose: `playwright_stealth`
5. Click **"Run workflow"**

### Expected Timeline:
- **0-2 min:** Setup and installation
- **2-5 min:** Running tests (5 URLs)
- **5-6 min:** Uploading artifacts
- **Total:** ~6-8 minutes

### Success Indicators:
✅ Workflow completes with green checkmark  
✅ 5 screenshots in artifacts  
✅ JSON report generated  
✅ Markdown summary created

---

## 📸 Step 5: Verify Results (2 minutes)

### Check Workflow Summary
Scroll to bottom of workflow run, you should see:
```
## 🎯 Playwright Library Test Results
Library: playwright_stealth
Device: iphone_x
Status: success
```

### Download Artifacts
1. Click **"screenshots-playwright_stealth-XXX"**
2. Download and extract ZIP
3. Open PNG files to verify:
   - `fingerprint_check` - Browser fingerprint analysis
   - `ip_check` - Proxy IP displayed
   - `bot_check` - Bot detection results
   - `creepjs_workers` - Worker fingerprinting
   - `creepjs_main` - Comprehensive analysis

### Check Reports
1. Download **"reports-playwright_stealth-XXX"**
2. Open JSON file for detailed results
3. Check markdown summary for human-readable format

---

## 🧪 Step 6: Baseline Testing (10 minutes)

Run these tests in order:

### Test 1: playwright_stealth ✅
```bash
python main.py --proxy env: --library playwright_stealth
```
**Expected:** High stealth score, proxy working

### Test 2: playwright (basic)
```bash
python main.py --proxy env: --library playwright
```
**Expected:** Lower stealth score (baseline comparison)

### Test 3: camoufox (Firefox)
```bash
python main.py --proxy env: --library camoufox
```
**Expected:** Firefox-based fingerprint, different detection profile

### Test 4: patchright
```bash
python main.py --proxy env: --library patchright
```
**Expected:** Similar to playwright_stealth

---

## 📊 Step 7: Full Comparison (15 minutes)

### Test All Playwright Libraries

**Local:**
```bash
python main.py --proxy env: --all --mode sequential
```

**GitHub Actions:**
1. Go to **Actions** tab
2. Select **"🎭 Test All Playwright Libraries"**
3. Click **"Run workflow"**

### What You'll Get:
- **20 screenshots** (4 libraries × 5 URLs)
- **Comparison matrix** showing:
  - Which libraries pass which tests
  - Proxy effectiveness per library
  - Mobile UA accuracy
  - Execution speeds
  - Overall stealth ratings

---

## 🔍 Understanding Results

### Success Metrics

**Good Start (3+ tests passing):**
- Screenshots captured
- Proxy detected correctly
- Mobile UA detected

**Strong Performance (6+ tests passing):**
- Multiple libraries working
- Clear comparison data
- Consistent results

**Excellent Setup (10+ tests passing):**
- All libraries tested
- Performance rankings established
- Strengths/weaknesses documented

### What Tests Measure

1. **IP Detection** (`pixelscan.net/ip`)
   - Is proxy IP showing?
   - Any IP leaks?

2. **Fingerprinting** (`pixelscan.net/fingerprint-check`)
   - Canvas fingerprint
   - WebGL detection
   - Font enumeration

3. **Bot Detection** (`pixelscan.net/bot-check`)
   - Automation signatures
   - WebDriver detection
   - Behavioral patterns

4. **Worker Analysis** (`creepjs/tests/workers.html`)
   - WebWorker fingerprinting
   - ServiceWorker detection
   - Worker context spoofing

5. **Comprehensive** (`creepjs`)
   - 100+ detection vectors
   - JavaScript engine analysis
   - Complete fingerprint

---

## 🐛 Troubleshooting

### ❌ "playwright-stealth not found"
```bash
pip install playwright-stealth==2.0.0
python -c "from playwright_stealth import StealthConfig; print('✅')"
```

### ❌ "Chromium binary not found"
```bash
playwright install chromium
playwright install-deps chromium
```

### ❌ Empty Screenshots
**Causes:**
- Wait time too short (increase in test_targets.json)
- Page navigation failed (check logs with --verbose)
- Browser crashed (check system resources)

**Fix:**
```bash
# Increase memory for browsers
export NODE_OPTIONS="--max-old-space-size=4096"

# Run with verbose logging
python main.py --proxy env: --library playwright_stealth --verbose
```

### ❌ Proxy Not Working
```bash
# Test proxy connection
curl --proxy http://deola:deola@84.200.91.70:8083 https://httpbin.org/ip

# Check if proxy is online
ping 84.200.91.70
```

### ❌ GitHub Actions Timeout
**Fix:** Reduce concurrent tests or increase timeout in workflow:
```yaml
jobs:
  test-playwright-library:
    timeout-minutes: 30  # Increase from 20
```

---

## 🎛️ Advanced Configuration

### Custom Device Profiles

Edit `profiles/iphone-device-profiles.csv` to add custom devices:
```csv
profile_id,user_agent,platform,viewport_width,viewport_height,...
custom1,"Mozilla/5.0...",iPhone,428,926,...
```

### Custom Test Targets

Edit `src/config/test_targets.json`:
```json
{
  "test_targets": {
    "custom_test": {
      "url": "https://your-site.com",
      "name": "custom_test",
      "expected_load_time": 25
    }
  }
}
```

### Adjust Wait Times

Edit `src/config/test_targets.json`:
```json
{
  "wait_configuration": {
    "default_wait_time": 45,  // Increase for slower sites
    "min_wait_time": 20,
    "max_wait_time": 90
  }
}
```

---

## 📈 Performance Optimization

### Parallel Testing (Faster)
```bash
python main.py --proxy env: --all --mode parallel
```
**Pros:** 2-3x faster  
**Cons:** Higher resource usage

### Sequential Testing (Safer)
```bash
python main.py --proxy env: --all --mode sequential
```
**Pros:** More stable, lower resource usage  
**Cons:** Takes longer

---

## 🔄 Regular Maintenance

### Weekly Tasks
- Run full comparison test
- Update library dependencies
- Review failed tests
- Archive old screenshots

```bash
# Update dependencies
pip install --upgrade -r requirements.txt
playwright install chromium

# Clean old results
find test_results/screenshots -type f -mtime +7 -delete
```

### Monthly Tasks
- Update device profiles
- Add new detection sites
- Review proxy performance
- Compare trends

---

## 📞 Support

**Issues:** [GitHub Issues](https://github.com/kravitzcoder/stealth-testing-playwright/issues)  
**Docs:** [Main Framework](https://github.com/kravitzcoder/stealth-testing-framework)  
**Community:** [Discussions](https://github.com/kravitzcoder/stealth-testing-playwright/discussions)

---

**🎭 Your Playwright Stealth Testing Framework is ready!**

**Next Steps:**
1. ✅ Run your first test
2. ✅ Verify results
3. ✅ Complete baseline testing
4. ✅ Run full comparison
5. ✅ Analyze and document findings
