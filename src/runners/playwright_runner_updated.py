"""
PLAYWRIGHT RUNNER - With IP Pre-Resolution (FIXED)

Now resolves proxy IP and timezone BEFORE browser launch
"""

import logging
import time
from typing import Dict, Any

from ..core.test_result import TestResult
from .base_runner_enhanced import BaseRunner

logger = logging.getLogger(__name__)


class PlaywrightRunnerEnhanced(BaseRunner):
    """Playwright runner with IP pre-resolution + BrowserForge"""
    
    def __init__(self, screenshot_engine=None):
        super().__init__(screenshot_engine)
        logger.info("Playwright runner initialized (with IP pre-resolution)")
    
    async def run_test(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 15
    ) -> TestResult:
        """Run test with Playwright + IP pre-resolution + BrowserForge"""
        start_time = time.time()
        logger.info(f"🎭 Testing Playwright (IP Pre-Resolved) on {url_name}: {url}")
        
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            error_msg = "playwright not installed. Run: pip install playwright && playwright install chromium"
            logger.error(error_msg)
            return TestResult(
                library="playwright",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=error_msg,
                execution_time=time.time() - start_time
            )
        
        try:
            # 🆕 STEP 1: Resolve proxy IP and timezone BEFORE browser launch
            logger.info("=" * 60)
            logger.info("STEP 1: Resolving proxy IP and timezone...")
            logger.info("=" * 60)
            
            resolved_proxy = await self.resolve_proxy_before_launch(proxy_config)
            
            logger.info(f"✅ Pre-resolution complete:")
            logger.info(f"   Hostname: {resolved_proxy.hostname}")
            logger.info(f"   IP: {resolved_proxy.ip_address}")
            logger.info(f"   Timezone: {resolved_proxy.timezone}")
            if resolved_proxy.city:
                logger.info(f"   Location: {resolved_proxy.city}, {resolved_proxy.country}")
            logger.info(f"   Method: {resolved_proxy.resolution_method}")
            logger.info(f"   Time: {resolved_proxy.resolution_time_ms:.1f}ms")
            
            # 🆕 STEP 2: Get enhanced config with pre-resolved timezone
            logger.info("=" * 60)
            logger.info("STEP 2: Creating browser config with correct timezone...")
            logger.info("=" * 60)
            
            enhanced_config = self.get_enhanced_mobile_config(
                mobile_config=mobile_config,
                device_type="iphone_x",
                use_browserforge=True,
                resolved_proxy=resolved_proxy  # 🆕 Pass resolved proxy
            )
            
            logger.info(f"✅ Config created:")
            logger.info(f"   Device: {enhanced_config.get('device_name')}")
            logger.info(f"   User-Agent: {enhanced_config.get('user_agent', '')[:60]}...")
            logger.info(f"   Timezone: {enhanced_config.get('timezone')} (✅ MATCHES PROXY IP)")
            logger.info(f"   BrowserForge: {enhanced_config.get('_browserforge_enhanced', False)}")
            
            # 🆕 STEP 3: Launch browser with CORRECT timezone from start
            logger.info("=" * 60)
            logger.info("STEP 3: Launching browser with correct timezone...")
            logger.info("=" * 60)
            
            async with async_playwright() as p:
                proxy = self._build_proxy(proxy_config)
                
                browser = await p.chromium.launch(
                    headless=True,
                    proxy=proxy,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                    ]
                )
                
                # Create context with CORRECT timezone (pre-resolved)
                context = await browser.new_context(
                    user_agent=enhanced_config.get("user_agent"),
                    viewport=enhanced_config.get("viewport"),
                    device_scale_factor=enhanced_config.get("device_scale_factor", 2),
                    is_mobile=True,
                    has_touch=True,
                    locale=enhanced_config.get("language", "en-US").replace("_", "-"),
                    timezone_id=enhanced_config.get("timezone"),  # ✅ CORRECT from start!
                    permissions=['geolocation'],
                    geolocation={"latitude": 37.7749, "longitude": -122.4194}
                )
                
                logger.info(f"✅ Browser context created with timezone: {enhanced_config.get('timezone')}")
                
                # Apply BrowserForge stealth
                await self._apply_browserforge_stealth(context, enhanced_config)
                
                page = await context.new_page()
                
                # 🆕 STEP 4: Navigate and verify
                logger.info("=" * 60)
                logger.info(f"STEP 4: Navigating to {url_name}...")
                logger.info("=" * 60)
                
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Check proxy (verify detected IP matches resolved IP)
                proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
                
                if detected_ip:
                    if detected_ip == resolved_proxy.ip_address:
                        logger.info(f"✅ IP MATCH: Detected {detected_ip} = Pre-resolved {resolved_proxy.ip_address}")
                    else:
                        logger.warning(f"⚠️ IP MISMATCH: Detected {detected_ip} ≠ Pre-resolved {resolved_proxy.ip_address}")
                
                # Extra wait for dynamic pages
                await self._extra_wait_for_dynamic_pages(url, url_name)
                
                # Capture screenshot
                screenshot_path = await self.screenshot_engine.capture_with_wait(
                    page, "playwright_browserforge", url_name, wait_time, page=page
                )
                
                # Check results
                is_mobile = await self._check_mobile_ua(page, enhanced_config)
                
                await browser.close()
                
                execution_time = time.time() - start_time
                logger.info("=" * 60)
                logger.info(f"✅ TEST COMPLETE in {execution_time:.2f}s")
                logger.info("=" * 60)
                
                return TestResult(
                    library="playwright_browserforge",
                    category="playwright",
                    test_name=url_name,
                    url=url,
                    success=True,
                    detected_ip=detected_ip or resolved_proxy.ip_address,
                    user_agent=enhanced_config.get("user_agent"),
                    proxy_working=proxy_working,
                    is_mobile_ua=is_mobile,
                    screenshot_path=screenshot_path,
                    execution_time=execution_time,
                    additional_data={
                        'browserforge_enhanced': enhanced_config.get('_browserforge_enhanced', False),
                        'browserforge_webrtc': enhanced_config.get('_browserforge_webrtc_enabled', False),
                        'device_name': enhanced_config.get('device_name'),
                        'timezone': enhanced_config.get('timezone'),
                        'pre_resolved_ip': resolved_proxy.ip_address,
                        'pre_resolved_timezone': resolved_proxy.timezone,
                        'timezone_method': resolved_proxy.resolution_method,
                        'ip_match': (detected_ip == resolved_proxy.ip_address) if detected_ip else None,
                    }
                )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)[:500]
            logger.error(f"❌ Playwright test failed: {error_msg}")
            
            return TestResult(
                library="playwright_browserforge",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
    
    async def _apply_browserforge_stealth(self, context, enhanced_config: Dict[str, Any]):
        """Apply BrowserForge stealth with native WebRTC protection"""
        
        # Get BrowserForge injection script (includes WebRTC masking)
        browserforge_script = self.browserforge.get_browserforge_injection_script(enhanced_config)
        
        # Additional stealth overrides
        additional_script = f"""
(function() {{
    'use strict';
    
    console.log('[Playwright Enhanced] Applying stealth overrides');
    
    // Hide webdriver
    if (navigator.webdriver) {{
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined,
            configurable: true
        }});
    }}
    
    // Chrome runtime
    if (!window.chrome) {{
        window.chrome = {{}};
    }}
    if (!window.chrome.runtime) {{
        window.chrome.runtime = {{
            connect: () => ({{}}),
            sendMessage: () => ({{}}),
            id: undefined,
            onMessage: {{
                addListener: () => {{}}
            }}
        }};
    }}
    
    // Permissions API override
    if (navigator.permissions && navigator.permissions.query) {{
        const originalQuery = navigator.permissions.query;
        navigator.permissions.query = function(parameters) {{
            if (parameters.name === 'notifications') {{
                return Promise.resolve({{ state: 'default' }});
            }}
            return originalQuery.apply(this, arguments);
        }};
    }}
    
    // Battery API (mobile-like behavior)
    if (navigator.getBattery) {{
        navigator.getBattery = async () => ({{
            charging: {str(enhanced_config.get('battery_charging', False)).lower()},
            chargingTime: Infinity,
            dischargingTime: 28800,
            level: {enhanced_config.get('battery_level', 0.75)},
            onchargingchange: null,
            onchargingtimechange: null,
            ondischargingtimechange: null,
            onlevelchange: null
        }});
    }}
    
    console.log('[Playwright Enhanced] ✅ Stealth overrides applied');
}})();
"""
        
        # Combine BrowserForge injection with additional stealth
        combined_script = f"""
// BrowserForge Injection (includes WebRTC masking)
{browserforge_script}

// Additional compatibility overrides
{additional_script}
"""
        
        # Apply the combined script to the context
        await context.add_init_script(combined_script)
        logger.info("✅ Playwright: BrowserForge stealth + WebRTC protection applied")
