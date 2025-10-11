"""
PLAYWRIGHT RUNNER - BrowserForge Native WebRTC Implementation

Uses BrowserForge's intelligent WebRTC handling instead of custom blocking
"""

import logging
import time
from typing import Dict, Any

from ..core.test_result import TestResult
from .base_runner_enhanced import BaseRunner

logger = logging.getLogger(__name__)


class PlaywrightRunnerEnhanced(BaseRunner):
    """Playwright runner with BrowserForge native WebRTC"""
    
    def __init__(self, screenshot_engine=None):
        super().__init__(screenshot_engine)
        logger.info("Playwright runner initialized (BrowserForge WebRTC)")
    
    async def run_test(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 15
    ) -> TestResult:
        """Run test with Playwright + BrowserForge WebRTC"""
        start_time = time.time()
        logger.info(f"🎭 Testing Playwright (BrowserForge WebRTC) on {url_name}: {url}")
        
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
            async with async_playwright() as p:
                proxy = self._build_proxy(proxy_config)
                
                # Extract proxy IP for WebRTC masking
                proxy_ip = proxy_config.get("host") if proxy_config.get("host") else None
                
                # Launch with minimal args (no custom WebRTC flags)
                browser = await p.chromium.launch(
                    headless=True,
                    proxy=proxy,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                    ]
                )
                
                # Get enhanced mobile config with BrowserForge + proxy IP
                enhanced_config = self.get_enhanced_mobile_config(
                    mobile_config=mobile_config,
                    device_type="iphone_x",
                    use_browserforge=True,
                    proxy_ip=proxy_ip
                )
                
                # Log enhancement status
                if enhanced_config.get('_browserforge_enhanced'):
                    logger.info(f"🎭 BrowserForge fingerprint: {enhanced_config.get('device_name')}")
                    if enhanced_config.get('_browserforge_webrtc_enabled'):
                        logger.info(f"🔒 BrowserForge WebRTC protection enabled for proxy: {proxy_ip}")
                else:
                    logger.info(f"📱 Using standard profile: {enhanced_config.get('device_name')}")
                
                # Create context with enhanced config
                context = await browser.new_context(
                    user_agent=enhanced_config.get("user_agent"),
                    viewport=enhanced_config.get("viewport"),
                    device_scale_factor=enhanced_config.get("device_scale_factor", 2),
                    is_mobile=True,
                    has_touch=True,
                    locale=enhanced_config.get("language", "en-US").replace("_", "-"),
                    timezone_id=enhanced_config.get("timezone", "America/New_York"),
                    permissions=['geolocation'],
                    geolocation={"latitude": 37.7749, "longitude": -122.4194}
                )
                
                # Apply BrowserForge stealth with proper WebRTC injection
                await self._apply_browserforge_stealth(context, enhanced_config)
                
                page = await context.new_page()
                
                # Additional page-level injection if needed
                await self.browserforge.inject_fingerprint_to_page(page, enhanced_config)
                
                logger.info(f"Navigating to {url}")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Extra wait for dynamic pages
                await self._extra_wait_for_dynamic_pages(url, url_name)
                
                # Capture screenshot
                screenshot_path = await self.screenshot_engine.capture_with_wait(
                    page, "playwright_browserforge", url_name, wait_time, page=page
                )
                
                # Check results
                proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
                is_mobile = await self._check_mobile_ua(page, enhanced_config)
                
                # Debug: Check WebRTC status
                try:
                    webrtc_ips = await page.evaluate("""
                        () => {
                            // Try to detect WebRTC leak
                            if (typeof RTCPeerConnection !== 'undefined') {
                                return 'RTCPeerConnection exists';
                            }
                            return 'No RTCPeerConnection';
                        }
                    """)
                    logger.debug(f"WebRTC check: {webrtc_ips}")
                except:
                    pass
                
                await browser.close()
                
                execution_time = time.time() - start_time
                logger.info(f"✅ Playwright (BrowserForge WebRTC) test completed in {execution_time:.2f}s")
                
                return TestResult(
                    library="playwright_browserforge",
                    category="playwright",
                    test_name=url_name,
                    url=url,
                    success=True,
                    detected_ip=detected_ip,
                    user_agent=enhanced_config.get("user_agent"),
                    proxy_working=proxy_working,
                    is_mobile_ua=is_mobile,
                    screenshot_path=screenshot_path,
                    execution_time=execution_time,
                    additional_data={
                        'browserforge_enhanced': enhanced_config.get('_browserforge_enhanced', False),
                        'browserforge_webrtc': enhanced_config.get('_browserforge_webrtc_enabled', False),
                        'device_name': enhanced_config.get('device_name'),
                        'proxy_ip': proxy_ip
                    }
                )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)[:500]
            logger.error(f"❌ Playwright (BrowserForge WebRTC) test failed: {error_msg}")
            
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
        """
        Apply BrowserForge stealth with native WebRTC protection
        
        This combines BrowserForge's fingerprint injection with additional stealth
        """
        
        # Get BrowserForge injection script if available
        browserforge_script = self.browserforge.get_browserforge_injection_script(enhanced_config)
        
        # Prepare additional stealth overrides
        platform = enhanced_config.get('platform', 'iPhone')
        hardware_concurrency = enhanced_config.get('hardware_concurrency', 4)
        device_memory = enhanced_config.get('device_memory', 4)
        webgl_vendor = enhanced_config.get('webgl_vendor', 'Apple Inc.')
        webgl_renderer = enhanced_config.get('webgl_renderer', 'Apple GPU')
        language = enhanced_config.get('language', 'en-US')
        languages = enhanced_config.get('languages', ['en-US', 'en'])
        
        # Convert languages list to JavaScript array string
        languages_str = str(languages).replace("'", '"')
        
        # Combine BrowserForge injection with additional stealth
        combined_script = f"""
// BrowserForge Injection (includes WebRTC mocking)
{browserforge_script}

// Additional stealth overrides
(function() {{
    'use strict';
    
    console.log('[Enhanced Stealth] Applying additional overrides');
    
    // Hide webdriver (if not already done by BrowserForge)
    if (navigator.webdriver) {{
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined,
            configurable: true
        }});
    }}
    
    // Chrome runtime (for compatibility)
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
    
    console.log('[Enhanced Stealth] ✅ All overrides applied');
}})();
"""
        
        # Apply the combined script to the context
        await context.add_init_script(combined_script)
        logger.info("✅ BrowserForge stealth + WebRTC protection applied to context")
