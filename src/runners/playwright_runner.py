"""
PLAYWRIGHT RUNNER - With WebRTC Relay Mode

WebRTC Strategy:
- Force WebRTC to use relay-only mode (uses proxy interface)
- Browser flags to enforce proxy usage
- JavaScript to force iceTransportPolicy='relay'
"""

import logging
import time
from typing import Dict, Any

from ..core.test_result import TestResult
from .base_runner import BaseRunner

logger = logging.getLogger(__name__)


class PlaywrightRunner(BaseRunner):
    """Vanilla Playwright runner with WebRTC relay mode"""
    
    def __init__(self, screenshot_engine=None):
        super().__init__(screenshot_engine)
        logger.info("Playwright runner initialized (WebRTC relay mode)")
    
    async def run_test(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 15
    ) -> TestResult:
        """Run test with Playwright + WebRTC relay mode"""
        start_time = time.time()
        logger.info(f"🎭 Testing Playwright on {url_name}: {url}")
        
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
                
                # Launch args with WebRTC flags
                browser = await p.chromium.launch(
                    headless=True,
                    proxy=proxy,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        
                        # WebRTC flags
                        '--force-webrtc-ip-handling-policy=default_public_interface_only',
                        '--enforce-webrtc-ip-permission-check',
                    ]
                )
                
                # Standard mobile context
                context = await browser.new_context(
                    user_agent=mobile_config.get("user_agent"),
                    viewport=mobile_config.get("viewport"),
                    device_scale_factor=mobile_config.get("device_scale_factor", 2),
                    is_mobile=True,
                    has_touch=True,
                    locale=mobile_config.get("language", "en-US").replace("_", "-"),
                    timezone_id=mobile_config.get("timezone", "America/New_York"),
                    permissions=['geolocation'],
                    geolocation={"latitude": 37.7749, "longitude": -122.4194}
                )
                
                # Apply stealth + WebRTC relay mode
                await self._apply_stealth_with_webrtc(context)
                
                page = await context.new_page()
                
                logger.info(f"Navigating to {url}")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Extra wait for dynamic pages
                await self._extra_wait_for_dynamic_pages(url, url_name)
                
                # Capture screenshot
                screenshot_path = await self.screenshot_engine.capture_with_wait(
                    page, "playwright", url_name, wait_time, page=page
                )
                
                # Check results
                proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
                is_mobile = await self._check_mobile_ua(page, mobile_config)
                
                await browser.close()
                
                execution_time = time.time() - start_time
                logger.info(f"✅ Playwright test completed in {execution_time:.2f}s")
                
                return TestResult(
                    library="playwright",
                    category="playwright",
                    test_name=url_name,
                    url=url,
                    success=True,
                    detected_ip=detected_ip,
                    user_agent=mobile_config.get("user_agent"),
                    proxy_working=proxy_working,
                    is_mobile_ua=is_mobile,
                    screenshot_path=screenshot_path,
                    execution_time=execution_time
                )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)[:500]
            logger.error(f"❌ Playwright test failed: {error_msg}")
            
            return TestResult(
                library="playwright",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
    
    async def _apply_stealth_with_webrtc(self, context):
        """
        Minimal stealth + WebRTC relay mode
        
        Forces WebRTC to use relay-only (proxy interface)
        """
        script = """
(function() {
    'use strict';
    
    console.log('[Playwright] Stealth + WebRTC relay mode');
    
    // Hide webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });
    
    // WebRTC: Force relay-only mode (uses proxy)
    if (typeof RTCPeerConnection !== 'undefined') {
        const OriginalRTCPeerConnection = RTCPeerConnection;
        
        window.RTCPeerConnection = function(config) {
            // Force relay mode - uses proxy interface
            if (config) {
                config.iceServers = config.iceServers || [];
                config.iceTransportPolicy = 'relay';
            } else {
                config = { iceTransportPolicy: 'relay' };
            }
            
            console.log('[Playwright WebRTC] Relay mode enforced (proxy)');
            return new OriginalRTCPeerConnection(config);
        };
        
        window.RTCPeerConnection.prototype = OriginalRTCPeerConnection.prototype;
    }
    
    console.log('[Playwright] ✅ Stealth + WebRTC relay active');
})();
        """
        
        await context.add_init_script(script)
        logger.info("✅ Playwright: Stealth + WebRTC relay mode applied")
