# 🎭 Playwright Stealth Testing Framework

**Comprehensive testing framework for Playwright-based stealth browser automation libraries.**

[![Test Single Library](https://github.com/kravitzcoder/stealth-testing-playwright/actions/workflows/test-single.yml/badge.svg)](https://github.com/kravitzcoder/stealth-testing-playwright/actions/workflows/test-single.yml)
[![Test All Libraries](https://github.com/kravitzcoder/stealth-testing-playwright/actions/workflows/test-all-playwright.yml/badge.svg)](https://github.com/kravitzcoder/stealth-testing-playwright/actions/workflows/test-all-playwright.yml)

---

## 🎯 Overview

This repository focuses exclusively on testing **Playwright-based** stealth browser automation libraries against advanced fingerprinting and bot detection systems.

### 🔬 Libraries Tested (4)

| Library | Status | Description |
|---------|--------|-------------|
| **playwright** | ✅ Working | Native Playwright with manual stealth techniques |
| **playwright-stealth** | ✅ Working | Playwright + stealth plugin for enhanced anti-detection |
| **patchright** | ⚠️ Testing | Patched Playwright fork with built-in stealth |
| **camoufox** | ✅ Working | Firefox-based stealth browser with Playwright API |

### 📊 What Gets Tested

- **IP Masking**: Proxy effectiveness and leak detection
- **Browser Fingerprinting**: Canvas, WebGL, audio fingerprints
- **Bot Detection**: Automation signature detection
- **User Agent**: Mobile device emulation accuracy
- **Worker Fingerprinting**: WebWorker/ServiceWorker analysis
- **Behavioral Analysis**: CreepJS comprehensive testing

---

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/kravitzcoder/stealth-testing-playwright.git
cd stealth-testing-playwright
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium firefox
```

### 3. Configure Proxy (GitHub Secrets)
Go to **Settings → Secrets and variables → Actions**, add:
```
PROXY_HOST = your.proxy.host
PROXY_PORT = 8080
PROXY_USERNAME = your_username
PROXY_PASSWORD = your_password
```

### 4. Run Your First Test
```bash
# Set proxy environment variables
export PROXY_HOST="your.proxy.host"
export PROXY_PORT="8080"
export PROXY_USERNAME="your_username"
export PROXY_PASSWORD="your_password"

# Test playwright-stealth
python main.py --proxy env: --library playwright_stealth
```

---

## 🎯 Testing Workflows

### **1. Single Library Test**
Test individual Playwright libraries systematically.

**GitHub Actions:**
1. Go to **Actions** tab
2. Select **"🎯 Single Library Test"**
3. Choose library: `playwright_stealth`
4. Click **"Run workflow"**

**Local:**
```bash
python main.py --proxy env: --library playwright_stealth
```

### **2. Test All Playwright Libraries**
Compare all 4 Playwright libraries at once.

**GitHub Actions:**
1. Go to **Actions** tab
2. Select **"🎭 Test All Playwright Libraries"**
3. Click **"Run workflow"**

**Local:**
```bash
python main.py --proxy env: --all
```

### **3. Test by Status**
Test only working libraries:
```bash
python main.py --proxy env: --status working
```

---

## 📸 Target Websites

| Site | Purpose | Detection Methods |
|------|---------|------------------|
| `pixelscan.net/fingerprint-check` | Browser fingerprinting | Canvas, WebGL, Fonts |
| `pixelscan.net/ip` | IP address detection | Proxy effectiveness |
| `pixelscan.net/bot-check` | Bot detection | Automation signatures |
| `abrahamjuliot.github.io/creepjs/tests/workers.html` | Worker fingerprinting | WebWorker analysis |
| `abrahamjuliot.github.io/creepjs` | Comprehensive analysis | 100+ detection vectors |

---

## 📋 Command Options

```bash
python main.py [OPTIONS]

Required:
  --proxy env:                    # Load proxy from environment variables
  --proxy http://user:pass@host:port  # Or specify directly

Library Selection (choose one):
  --library LIBRARY              # Test specific library
  --status {working,testing}     # Test by status
  --all                          # Test all Playwright libraries

Optional:
  --device {iphone_x,iphone_12,samsung_galaxy}  # Mobile device
  --mode {sequential,parallel}   # Execution mode
  --output-prefix PREFIX         # Output file prefix
  --verify-deps                  # Check dependencies first
  --verbose, -v                  # Detailed logging
```

### Examples

```bash
# Test specific library
python main.py --proxy env: --library playwright_stealth

# Test all working libraries
python main.py --proxy env: --status working

# Test all in parallel with iPad emulation
python main.py --proxy env: --all --mode parallel --device iphone_12

# With dependency verification
python main.py --proxy env: --all --verify-deps
```

---

## 🎯 Systematic Testing Strategy

### Phase 1: Baseline
```
1. playwright_stealth  ← Start here (most reliable)
2. playwright          ← Baseline comparison
3. camoufox            ← Firefox-based alternative
```

### Phase 2: Advanced
```
4. patchright          ← Patched fork testing
```

### Phase 3: Analysis
Run full comparison:
```bash
python main.py --proxy env: --all --mode sequential
```

Compare results to identify:
- Which library passes which detection tests
- Proxy effectiveness per library
- Mobile UA accuracy
- Overall stealth ratings

---

## 📊 Results & Artifacts

Each test generates:
- **Screenshots**: Full-page captures from all target URLs
- **JSON Reports**: Detailed technical analysis
- **Markdown Summaries**: Human-readable results
- **Success Metrics**: Pass/fail rates and stealth effectiveness

### Viewing Results

**GitHub Actions:**
- Scroll to bottom of workflow run
- Download artifacts:
  - `screenshots-{library}-{run_number}`
  - `reports-{library}-{run_number}`

**Local:**
```bash
test_results/
├── screenshots/
│   ├── playwright_stealth_fingerprint_check_20250105_143025.png
│   ├── playwright_stealth_ip_check_20250105_143055.png
│   └── ...
└── reports/
    ├── playwright_test_20250105_143200.json
    └── playwright_test_20250105_143200_summary.md
```

---

## 🏗️ Architecture

```
stealth-testing-playwright/
├── .github/workflows/         # GitHub Actions workflows
│   ├── test-single.yml
│   └── test-all-playwright.yml
├── src/
│   ├── core/                  # Core framework
│   │   ├── test_orchestrator.py
│   │   ├── screenshot_engine.py
│   │   ├── test_result.py
│   │   └── dependency_checker.py
│   ├── runners/
│   │   └── playwright_runner.py   # Playwright-specific runner
│   ├── config/                # Configuration files
│   │   ├── library_matrix.json
│   │   ├── test_targets.json
│   │   └── proxy_config.json
│   └── utils/                 # Utilities
│       ├── device_profile_loader.py
│       ├── fingerprint_injector.py
│       └── logger.py
├── profiles/                  # Device fingerprint profiles
│   ├── iphone-device-profiles.csv
│   └── android-device-profiles.csv
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
└── README.md
```

---

## 🔧 Troubleshooting

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

### ❌ Empty screenshots
- Increase wait time in `test_targets.json`
- Check browser console logs with `--verbose`
- Verify page loads completely

### ❌ Proxy not working
```bash
# Test proxy connection
curl --proxy http://user:pass@host:port https://httpbin.org/ip
```

---

## 🆚 Comparison with Other Categories

This is part of a larger stealth testing framework:

- **[Playwright Category](https://github.com/kravitzcoder/stealth-testing-playwright)** ← You are here
- **[Selenium Category](https://github.com/kravitzcoder/stealth-testing-selenium)** - Selenium-based libraries
- **[Specialized Category](https://github.com/kravitzcoder/stealth-testing-specialized)** - Advanced frameworks
- **[Puppeteer Category](https://github.com/kravitzcoder/stealth-testing-puppeteer)** - Node.js libraries

**Overview:** [Stealth Testing Framework](https://github.com/kravitzcoder/stealth-testing-framework)

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/enhancement`
3. Test your changes: `python main.py --proxy env: --all`
4. Commit: `git commit -m "Add enhancement"`
5. Push: `git push origin feature/enhancement`
6. Submit pull request

---

## 📄 License

MIT License - Feel free to use and modify for your stealth testing needs.

---

## 🙏 Acknowledgments

- **kravitzcoder**: Project lead
- **MiniMax Agent**: Framework development
- **Playwright Team**: Excellent automation framework
- **Open Source Community**: Library maintainers

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/kravitzcoder/stealth-testing-playwright/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kravitzcoder/stealth-testing-playwright/discussions)
- **Documentation**: [Framework Docs](https://github.com/kravitzcoder/stealth-testing-framework)

---

**🎭 Ready to test Playwright stealth capabilities? Start with `playwright_stealth` and build your comparison database!**
