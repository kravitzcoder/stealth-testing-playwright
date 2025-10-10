"""
PATCHRIGHT RUNNER - With WebRTC Masking

WebRTC Strategy:
- Browser-level patches (Patchright's strength)
- Force WebRTC to use proxy interface
- Light JavaScript masking on top
"""

import logging
import time
from typing import Dict, Any

from ..core.test_result import TestResult
from .base_runner import BaseRunner

logger = logging.getLogger(__name__)


class PatchrightRunner(BaseRunner):
    """Patchright runner with browser-level stealth + WebRTC masking"""
    
    def __init__(self, screenshot_engine=None):
        super().__init__(screenshot_engine)
        logger.info("Patchright runner initialized (browser patches + WebRTC masking)")
    
    async def run_test(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 15
    ) -> TestResult:
        """Run test with Patchright's browser-level patches + WebRTC masking"""
        start_time = time.time()
        logger.info(f"🎭 Testing Patchright on {url_name}: {url}")
        
        try:
            from patchright.async_api import async_playwright
        except ImportError:
            error_msg = "patchright not installed. Run: pip install patchright"
            logger.error(error_msg)
            return TestResult(
                library="patchright",
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
                
                # Patchright has built-in patches, add WebRTC masking flags
                browser = await p.chromium.launch(
                    headless=True,
                    proxy=proxy,
                    args=[
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
                
                # Apply WebRTC masking
                await self._apply_webrtc_masking(context, proxy_config)
                
                # Add light stealth on top of Patchright's patches
                await self._apply_patchright_stealth(context, mobile_config)
                
                page = await context.new_page()
                
                logger.info(f"Navigating to {url}")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Extra wait for dynamic pages
                await self._extra_wait_for_dynamic_pages(url, url_name)
                
                # Capture screenshot
                screenshot_path = await self.screenshot_engine.capture_with_wait(
                    page, "patchright", url_name, wait_time, page=page
                )
                
                # Check results
                proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
                is_mobile = await self._check_mobile_ua(page, mobile_config)
                
                await browser.close()
                
                execution_time = time.time() - start_time
                logger.info(f"✅ Patchright test completed in {execution_time:.2f}s")
                
                return TestResult(
                    library="patchright",
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
            logger.error(f"❌ Patchright test failed: {error_msg}")
            
            return TestResult(
                library="patchright",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
    
    async def _apply_webrtc_masking(self, context, proxy_config: Dict[str, str]):
        """
        WebRTC IP masking for Patchright
        
        Force WebRTC to use proxy interface (not real IP)
        """
        script = """
(function() {
    'use strict';
    
    console.log('[WebRTC] Patchright masking enabled');
    
    // Override RTCPeerConnection to force relay mode
    if (typeof RTCPeerConnection !== 'undefined') {
        const OriginalRTCPeerConnection = RTCPeerConnection;
        
        window.RTCPeerConnection = function(config) {
            // Force relay-only mode (uses proxy)
            if (config) {
                config.iceServers = config.iceServers || [];
                config.iceTransportPolicy = 'relay';
            } else {
                config = { iceTransportPolicy: 'relay' };
            }
            
            console.log('[WebRTC] Using relay mode (proxy interface)');
            return new OriginalRTCPeerConnection(config);
        };
        
        window.RTCPeerConnection.prototype = OriginalRTCPeerConnection.prototype;
    }
    
    console.log('[WebRTC] ✅ Masking applied (Patchright)');
})();
        """
        
        await context.add_init_script(script)
        logger.info("✅ WebRTC masking applied (Patchright)")
    
    async def _apply_patchright_stealth(self, context, mobile_config: Dict[str, Any]):
        """
        Light stealth for Patchright
        
        Patchright already has browser-level patches
        """
        platform = mobile_config.get("platform", "iPhone")
        
        script = f"""
(function() {{
    'use strict';
    
    // Hide webdriver
    Object.defineProperty(navigator, 'webdriver', {{
        get: () => undefined,
        configurable: true
    }});
    
    // Basic platform override
    Object.defineProperty(navigator, 'platform', {{
        get: () => '{platform}',
        configurable: true
    }});
    
    // Chrome runtime
    if (!window.chrome) {{
        window.chrome = {{}};
    }}
    window.chrome.runtime = {{
        connect: () => ({{}}),
        sendMessage: () => ({{}})
    }};
    
    console.log('[Patchright] Browser patches + light JS stealth applied');
}})();
        """
        
        await context.add_init_script(script)
        logger.info("✅ Patchright stealth applied (browser patches + light JS)")
