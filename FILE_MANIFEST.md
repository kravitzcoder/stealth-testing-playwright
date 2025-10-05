# 📦 Playwright Repository - Complete File Manifest

This document lists all files needed for the Playwright repository and where to place them.

---

## 📁 Root Directory Files

| File | Source | Notes |
|------|--------|-------|
| `main.py` | Artifact #3 | Playwright-specific CLI |
| `requirements.txt` | Artifact #2 | Playwright-only dependencies |
| `README.md` | Artifact #8 | Playwright-specific docs |
| `DEPLOYMENT_GUIDE.md` | Artifact #9 | Complete setup guide |
| `QUICK_START.md` | Artifact #10 | Fast setup (15 min) |
| `.gitignore` | Artifact #7 | Python/Playwright exclusions |
| `create_structure.sh` | Artifact #11 | Directory creation script |

---

## 📁 .github/workflows/

| File | Source | Purpose |
|------|--------|---------|
| `test-single.yml` | Artifact #4 | Single library testing |
| `test-all-playwright.yml` | Artifact #5 | Test all 4 libraries |

---

## 📁 src/config/

| File | Source | Notes |
|------|--------|-------|
| `__init__.py` | Document #19 | Config loader |
| `library_matrix.json` | Artifact #1 | **FILTERED: Playwright only** |
| `test_targets.json` | Document #22 | Same as original |
| `proxy_config.json` | Document #21 | Same as original |

---

## 📁 src/core/

| File | Source | Notes |
|------|--------|-------|
| `__init__.py` | Document #23 | Core exports |
| `test_orchestrator.py` | Document #26 | Same as original |
| `screenshot_engine.py` | Document #25 | Same as original |
| `test_result.py` | Document #27 | Same as original |
| `dependency_checker.py` | Document #24 | Same as original |

---

## 📁 src/runners/

| File | Source | Notes |
|------|--------|-------|
| `__init__.py` | **CREATE NEW** | Only exports PlaywrightRunner |
| `playwright_runner.py` | Document #15 | **ONLY THIS RUNNER** |

**NEW `src/runners/__init__.py`:**
```python
"""Playwright category runner"""
from .playwright_runner import PlaywrightRunner

__all__ = ['PlaywrightRunner']
```

---

## 📁 src/utils/

| File | Source | Notes |
|------|--------|-------|
| `__init__.py` | Document #28 | Empty file |
| `device_profile_loader.py` | Document #29 | Same as original |
| `fingerprint_injector.py` | Document #30 | Same as original |
| `logger.py` | Document #31 | Same as original |

---

## 📁 profiles/

| File | Source | Notes |
|------|--------|-------|
| `iphone-device-profiles.csv` | Document #12 | Same as original |
| `android-device-profiles.csv` | Document #11 | Same as original |

---

## 🔧 Modified Files (From Original Repo)

### 1. library_matrix.json (FILTERED)
**Original:** 13 libraries across 4 categories  
**Playwright Version:** 4 libraries in 1 category only

Only keep:
```json
{
  "library_matrix": {
    "playwright_category": { /* all 4 Playwright libraries */ }
  }
}
```

Remove: selenium_category, specialized_category, puppeteer_category

### 2. src/runners/__init__.py (SIMPLIFIED)
**Original:** Exports all 4 runners  
**Playwright Version:** Only exports PlaywrightRunner

```python
"""Playwright category runner"""
from .playwright_runner import PlaywrightRunner

__all__ = ['PlaywrightRunner']
```

---

## 📋 Files to COPY AS-IS (No Changes)

These files remain identical to the original Enhanced_Testing_Framework:

✅ `src/core/test_orchestrator.py`  
✅ `src/core/screenshot_engine.py`  
✅ `src/core/test_result.py`  
✅ `src/core/dependency_checker.py`  
✅ `src/runners/playwright_runner.py`  
✅ `src/utils/device_profile_loader.py`  
✅ `src/utils/fingerprint_injector.py`  
✅ `src/utils/logger.py`  
✅ `src/config/test_targets.json`  
✅ `src/config/proxy_config.json`  
✅ `profiles/iphone-device-profiles.csv`  
✅ `profiles/android-device-profiles.csv`

---

## 🚫 Files to EXCLUDE (Not Needed)

Do NOT copy these files from original repo:

❌ `src/categories/selenium_runner.py` - Selenium category  
❌ `src/categories/specialized_runner.py` - Specialized category  
❌ `src/categories/puppeteer_runner.py` - Puppeteer category  
❌ `stealth-test-all.yml` - Tests all 13 libraries  
❌ `stealth-test-category.yml` - Multi-category workflow  
❌ `package.json` - Node.js (Puppeteer only)

---

## 📊 Quick Reference: File Counts

| Category | Count | Details |
|----------|-------|---------|
| **Root files** | 7 | Main scripts & docs |
| **Workflows** | 2 | GitHub Actions |
| **Config files** | 4 | Filtered + originals |
| **Core files** | 5 | Framework components |
| **Runner files** | 2 | PlaywrightRunner only |
| **Utility files** | 4 | Helpers |
| **Profile files** | 2 | Device profiles |
| **TOTAL** | 26 | Complete Playwright repo |

---

## ✅ Setup Checklist

- [ ] Create directory structure (`bash create_structure.sh`)
- [ ] Copy all root files
- [ ] Copy workflow files to `.github/workflows/`
- [ ] Copy config files to `src/config/` (use filtered library_matrix.json)
- [ ] Copy core files to `src/core/`
- [ ] Copy playwright_runner.py to `src/runners/`
- [ ] Create new `src/runners/__init__.py` with only PlaywrightRunner
- [ ] Copy utils files to `src/utils/`
- [ ] Copy profile CSVs to `profiles/`
- [ ] Create all `__init__.py` files in subdirectories
- [ ] Initialize git: `git init`
- [ ] Add files: `git add .`
- [ ] Commit: `git commit -m "Initial commit: Playwright stealth testing framework"`
- [ ] Create GitHub repo
- [ ] Push: `git remote add origin <url> && git push -u origin main`
- [ ] Configure secrets in GitHub
- [ ] Run first test

---

## 🎯 Quick Copy Commands

```bash
# After creating structure, copy from original repo:

# Root files (use NEW versions from artifacts)
cp ../Enhanced_Testing_Framework/.gitignore .

# Workflows (use NEW versions)
# (Copy from artifacts)

# Config (filter library_matrix.json, copy others as-is)
cp ../Enhanced_Testing_Framework/src/config/test_targets.json src/config/
cp ../Enhanced_Testing_Framework/src/config/proxy_config.json src/config/
# Use filtered version for library_matrix.json

# Core (copy as-is)
cp ../Enhanced_Testing_Framework/src/core/*.py src/core/

# Runner (only playwright_runner.py)
cp ../Enhanced_Testing_Framework/src/categories/playwright_runner.py src/runners/

# Utils (copy as-is)
cp ../Enhanced_Testing_Framework/src/utils/*.py src/utils/

# Profiles (copy as-is)
cp ../Enhanced_Testing_Framework/profiles/*.csv profiles/
```

---

## 🧪 Verification

After copying all files, verify:

```bash
# Check structure
tree -L 3

# Check Python syntax
python -m py_compile main.py
python -m py_compile src/core/*.py
python -m py_compile src/runners/*.py

# Check imports
python -c "from src.core.test_orchestrator import StealthTestOrchestrator; print('✅')"
python -c "from src.runners.playwright_runner import PlaywrightRunner; print('✅')"

# Check config loads
python -c "import json; json.load(open('src/config/library_matrix.json')); print('✅')"

# Install and test
pip install -r requirements.txt
playwright install chromium
python main.py --help
```

---

**Total Files: 26**  
**Ready to deploy!** 🚀
