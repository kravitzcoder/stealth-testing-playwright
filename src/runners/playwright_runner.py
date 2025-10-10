"""
PLAYWRIGHT RUNNER - With WebRTC Masking

WebRTC Strategy:
- Force WebRTC to use proxy interface (not block it)
- Use browser flags to enforce proxy usage
- More natural than blocking (less detectable)
"""

import logging
import time
from typing import Dict, Any

from ..core.test_result import TestResult
from .base_runner import BaseRunner

logger = logging.getLogger(__name__)


class PlaywrightRunner(BaseRunner):
    """Vanilla Playwright runner with WebRTC masking"""
    
    def __init__(self, screenshot_engine=None):
        super().__init__(screenshot_engine)
        logger.info("Playwright runner initialized (WebRTC masking enabled)")
    
    async def run_test(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 15
    ) -> TestResult:
        """Run test with vanilla Playwright + WebRTC masking"""
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
                
                # CRITICAL: WebRTC masking via browser flags
                browser = await p.chromium.launch(
                    headless=True,
                    proxy=proxy,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        
                        # WebRTC IP masking (force proxy interface)
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
                
                # Apply WebRTC IP masking script
                await self._apply_webrtc_masking(context, proxy_config)
                
                # Apply minimal stealth (only hide webdriver)
                await self._apply_minimal_stealth(context)
                
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
    
    async def _apply_webrtc_masking(self, context, proxy_config: Dict[str, str]):
        """
        WebRTC IP masking (not blocking)
        
        Strategy: Force WebRTC to use proxy IP instead of real IP
        This is more natural than blocking (less detectable)
        """
        proxy_ip = proxy_config.get("host", "")
        
        script = f"""
(function() {{
    'use strict';
    
    console.log('[WebRTC] Masking enabled - forcing proxy interface');
    
    // Override RTCPeerConnection to use proxy interface only
    if (typeof RTCPeerConnection !== 'undefined') {{
        const OriginalRTCPeerConnection = RTCPeerConnection;
        
        window.RTCPeerConnection = function(config) {{
            // Force proxy interface usage
            if (config) {{
                config.iceServers = config.iceServers || [];
                config.iceTransportPolicy = 'relay'; // Force TURN relay
            }} else {{
                config = {{ iceTransportPolicy: 'relay' }};
            }}
            
            console.log('[WebRTC] Using relay-only mode (proxy interface)');
            return new OriginalRTCPeerConnection(config);
        }};
        
        // Preserve prototype
        window.RTCPeerConnection.prototype = OriginalRTCPeerConnection.prototype;
    }}
    
    console.log('[WebRTC] ✅ Masking applied (proxy IP will be used)');
}})();
        """
        
        await context.add_init_script(script)
        logger.info("✅ WebRTC masking applied (will use proxy IP)")
    
    async def _apply_minimal_stealth(self, context):
        """
        Minimal stealth - only hide navigator.webdriver
        """
        script = """
(function() {
    'use strict';
    
    // Only hide webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });
    
    console.log('[Playwright] Minimal stealth: webdriver hidden');
})();
        """
        
        await context.add_init_script(script)
        logger.info("✅ Minimal stealth applied (webdriver hidden)")
