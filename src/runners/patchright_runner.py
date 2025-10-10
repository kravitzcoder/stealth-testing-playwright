"""
PATCHRIGHT RUNNER - With WebRTC Relay Mode

WebRTC Strategy:
- Leverage Patchright's browser patches
- Add WebRTC relay-only mode
- Browser flags + JavaScript masking
"""

import logging
import time
from typing import Dict, Any

from ..core.test_result import TestResult
from .base_runner import BaseRunner

logger = logging.getLogger(__name__)


class PatchrightRunner(BaseRunner):
    """Patchright runner with browser patches + WebRTC relay mode"""
    
    def __init__(self, screenshot_engine=None):
        super().__init__(screenshot_engine)
        logger.info("Patchright runner initialized (patches + WebRTC relay)")
    
    async def run_test(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 15
    ) -> TestResult:
        """Run test with Patchright's patches + WebRTC relay mode"""
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
                
                # Patchright launch args + WebRTC flags
                browser = await p.chromium.launch(
                    headless=True,
                    proxy=proxy,
                    args=[
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
                
                # Apply Patchright stealth + WebRTC relay
                await self._apply_patchright_stealth_with_webrtc(context, mobile_config)
                
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
    
    async def _apply_patchright_stealth_with_webrtc(self, context, mobile_config: Dict[str, Any]):
        """
        Patchright stealth + WebRTC relay mode
        
        Patchright has browser-level patches, we add JS stealth + WebRTC relay
        """
        platform = mobile_config.get("platform", "iPhone")
        
        script = f"""
(function() {{
    'use strict';
    
    console.log('[Patchright] Browser patches + stealth + WebRTC relay');
    
    // Hide webdriver
    Object.defineProperty(navigator, 'webdriver', {{
        get: () => undefined,
        configurable: true
    }});
    
    // Platform override
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
    
    // WebRTC: Force relay-only mode (uses proxy)
    if (typeof RTCPeerConnection !== 'undefined') {{
        const OriginalRTCPeerConnection = RTCPeerConnection;
        
        window.RTCPeerConnection = function(config) {{
            // Force relay mode
            if (config) {{
                config.iceServers = config.iceServers || [];
                config.iceTransportPolicy = 'relay';
            }} else {{
                config = {{ iceTransportPolicy: 'relay' }};
            }}
            
            console.log('[Patchright WebRTC] Relay mode enforced (proxy)');
            return new OriginalRTCPeerConnection(config);
        }};
        
        window.RTCPeerConnection.prototype = OriginalRTCPeerConnection.prototype;
    }}
    
    console.log('[Patchright] ✅ Patches + stealth + WebRTC relay active');
}})();
        """
        
        await context.add_init_script(script)
        logger.info("✅ Patchright: Browser patches + stealth + WebRTC relay applied")
