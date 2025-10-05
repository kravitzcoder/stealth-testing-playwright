# Quick Start - Playwright Stealth Testing

Get testing in 15 minutes!

## Step 1: Clone & Install (5 minutes)

```bash
git clone https://github.com/kravitzcoder/stealth-testing-playwright.git
cd stealth-testing-playwright
pip install -r requirements.txt
playwright install chromium
```

## Step 2: Configure Proxy (2 minutes)

```bash
export PROXY_HOST="84.200.91.70"
export PROXY_PORT="8083"
export PROXY_USERNAME="deola"
export PROXY_PASSWORD="deola"
```

## Step 3: Run Test (3 minutes)

```bash
python main.py --proxy env: --library playwright_stealth
```

## Step 4: View Results (2 minutes)

```bash
ls test_results/screenshots/    # Screenshots
ls test_results/reports/        # Reports
```

## That's It!

Results in `test_results/` directory.

**Next:** Test all libraries:
```bash
python main.py --proxy env: --all
```

Full docs: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
