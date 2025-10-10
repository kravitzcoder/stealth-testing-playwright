"""
CAMOUFOX RUNNER ENHANCED - JavaScript Relay Mode + BrowserForge

WebRTC Strategy + BrowserForge:
- NO Firefox preferences (they cause errors!)
- ONLY JavaScript to force relay mode
- Works in Firefox just like Chromium
- BrowserForge intelligent fingerprints (NEW!)
"""

import logging
import time
from typing import Dict, Any

from ..core.test_result import TestResult
from .base_runner_enhanced import BaseRunner

logger = logging.getLogger(__name__)


class CamoufoxRunnerEnhanced(BaseRunner):
    """Camoufox runner with JavaScript relay mode + BrowserForge"""
    
    def __init__(self, screenshot_engine=None):
        super().__init__(screenshot_engine)
        logger.info("Camoufox runner initialized (JS relay + BrowserForge)")
    
    async def run_test(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 15
    ) -> TestResult:
        """Run test with Camoufox + JavaScript relay mode + BrowserForge"""
        start_time = time.time()
        logger.info(f"🎭 Testing Camoufox (BrowserForge) on {url_name}: {url}")
        
        try:
            from camoufox.async_api import AsyncCamoufox
        except ImportError:
            error_msg = "camoufox not installed. Run: pip install 'camoufox[geoip]'"
            logger.error(error_msg)
            return TestResult(
                library="camoufox",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=error_msg,
                execution_time=time.time() - start_time
            )
        
        try:
            # Build proxy dict
            proxy_dict = None
            if proxy_config.get("host"):
                proxy_dict = {
                    "server": f"http://{proxy_config['host']}:{proxy_config['port']}"
                }
                if proxy_config.get("username") and proxy_config.get("password"):
                    proxy_dict["username"] = proxy_config["username"]
                    proxy_dict["password"] = proxy_config["password"]
                logger.info(f"Proxy: {proxy_dict['server']}")
            
            # Get enhanced mobile config with BrowserForge (NEW!)
            enhanced_config = self.get_enhanced_mobile_config(
                mobile_config=mobile_config,
                device_type="iphone_x",  # or extract from mobile_config
                use_browserforge=True
            )
            
            # Log enhancement status
            if enhanced_config.get('_browserforge_enhanced'):
                logger.info(f"🎭 Using BrowserForge fingerprint: {enhanced_config.get('device_name')}")
            else:
                logger.info(f"📱 Using standard profile: {enhanced_config.get('device_name')}")
            
            # Camoufox WITHOUT any config (no Firefox prefs!)
            async with AsyncCamoufox(
                headless=True,
                proxy=proxy_dict,
                humanize=True,
                geoip=True if self.geoip else False
            ) as browser:
                
                page = await browser.new_page()
                
                # Set mobile viewport from enhanced config
                viewport = enhanced_config.get("viewport", {"width": 375, "height": 812})
                await page.set_viewport_size(viewport)
                
                # Apply JavaScript relay mode + BrowserForge stealth
                await self._apply_webrtc_relay_mode_with_browserforge(page, enhanced_config)
                
                logger.info(f"Navigating to {url} with Camoufox (BrowserForge)")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Extra wait for dynamic pages
                await self._extra_wait_for_dynamic_pages(url, url_name)
                
                # Capture screenshot
                screenshot_path = await self.screenshot_engine.capture_with_wait(
                    page, "camoufox_browserforge", url_name, wait_time, page=page
                )
                
                # Check results
                proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
                is_mobile = await self._check_mobile_ua(page, enhanced_config)
                
                await browser.close()
                
                execution_time = time.time() - start_time
                logger.info(f"✅ Camoufox (BrowserForge) test completed in {execution_time:.2f}s")
                
                return TestResult(
                    library="camoufox_browserforge",
                    category="playwright",
                    test_name=url_name,
                    url=url,
                    success=True,
                    detected_ip=detected_ip,
                    user_agent=enhanced_config.get("user_agent", "Firefox Mobile"),
                    proxy_working=proxy_working,
                    is_mobile_ua=is_mobile,
                    screenshot_path=screenshot_path,
                    execution_time=execution_time,
                    additional_data={
                        'browserforge_enhanced': enhanced_config.get('_browserforge_enhanced', False),
                        'device_name': enhanced_config.get('device_name')
                    }
                )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)[:500]
            logger.error(f"❌ Camoufox (BrowserForge) test failed: {error_msg}")
            
            return TestResult(
                library="camoufox_browserforge",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
    
    async def _apply_webrtc_relay_mode_with_browserforge(self, page, enhanced_config: Dict[str, Any]):
        """
        JavaScript WebRTC relay mode + BrowserForge stealth (works in Firefox!)
        
        This combines:
        - WebRTC relay-only mode
        - BrowserForge fingerprint injection
        """
        platform = enhanced_config.get('platform', 'iPhone')
        hardware_concurrency = enhanced_config.get('hardware_concurrency', 4)
        device_memory = enhanced_config.get('device_memory', 4)
        webgl_vendor = enhanced_config.get('webgl_vendor', 'Apple Inc.')
        webgl_renderer = enhanced_config.get('webgl_renderer', 'Apple GPU')
        language = enhanced_config.get('language', 'en-US')
        languages = enhanced_config.get('languages', ['en-US', 'en'])
        
        # Convert languages list to JavaScript array
        languages_str = str(languages).replace("'", '"')
        
        script = f"""
(function() {{
    'use strict';
    
    console.log('[Camoufox + BrowserForge] Enhanced stealth active');
    
    // Hide webdriver
    try {{
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined,
            configurable: true
        }});
    }} catch(e) {{}}
    
    // BrowserForge: Platform override
    try {{
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{platform}',
            configurable: true
        }});
    }} catch(e) {{}}
    
    // BrowserForge: Hardware concurrency
    try {{
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {hardware_concurrency},
            configurable: true
        }});
    }} catch(e) {{}}
    
    // BrowserForge: Device memory
    try {{
        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => {device_memory},
            configurable: true
        }});
    }} catch(e) {{}}
    
    // BrowserForge: Languages
    try {{
        Object.defineProperty(navigator, 'language', {{
            get: () => '{language}',
            configurable: true
        }});
        
        Object.defineProperty(navigator, 'languages', {{
            get: () => {languages_str},
            configurable: true
        }});
    }} catch(e) {{}}
    
    // BrowserForge: WebGL fingerprint
    try {{
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return '{webgl_vendor}';
            if (parameter === 37446) return '{webgl_renderer}';
            return getParameter.call(this, parameter);
        }};
        
        if (typeof WebGL2RenderingContext !== 'undefined') {{
            const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{webgl_vendor}';
                if (parameter === 37446) return '{webgl_renderer}';
                return getParameter2.call(this, parameter);
            }};
        }}
    }} catch(e) {{}}
    
    // WebRTC: Force relay-only mode (uses proxy)
    // This works in BOTH Firefox AND Chromium!
    if (typeof RTCPeerConnection !== 'undefined') {{
        const OriginalRTCPeerConnection = RTCPeerConnection;
        
        window.RTCPeerConnection = function(config) {{
            // Force relay mode - uses proxy interface
            if (config) {{
                config.iceServers = config.iceServers || [];
                config.iceTransportPolicy = 'relay';
            }} else {{
                config = {{ iceTransportPolicy: 'relay' }};
            }}
            
            console.log('[Camoufox WebRTC] Relay mode enforced (proxy)');
            return new OriginalRTCPeerConnection(config);
        }};
        
        window.RTCPeerConnection.prototype = OriginalRTCPeerConnection.prototype;
    }}
    
    console.log('[Camoufox + BrowserForge] ✅ Enhanced stealth + WebRTC relay active');
}})();
        """
        
        await page.evaluate(script)
        logger.info("✅ Camoufox: BrowserForge stealth + WebRTC relay mode applied")
