"""
CAMOUFOX RUNNER ENHANCED - BrowserForge Integration (CLEANED)

WebRTC Strategy + BrowserForge:
- NO custom WebRTC blocking or relay mode
- BrowserForge handles ALL WebRTC masking
- Works in Firefox with BrowserForge's native approach
"""

import logging
import time
from typing import Dict, Any

from ..core.test_result import TestResult
from .base_runner_enhanced import BaseRunner

logger = logging.getLogger(__name__)


class CamoufoxRunnerEnhanced(BaseRunner):
    """Camoufox runner with BrowserForge native WebRTC"""
    
    def __init__(self, screenshot_engine=None):
        super().__init__(screenshot_engine)
        logger.info("Camoufox runner initialized (BrowserForge native)")
    
    async def run_test(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 15
    ) -> TestResult:
        """Run test with Camoufox + BrowserForge native WebRTC"""
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
            
            # Extract proxy IP for WebRTC masking
            proxy_ip = proxy_config.get("host") if proxy_config.get("host") else None
            
            # Get enhanced mobile config with BrowserForge
            enhanced_config = self.get_enhanced_mobile_config(
                mobile_config=mobile_config,
                device_type="iphone_x",
                use_browserforge=True,
                proxy_ip=proxy_ip
            )
            
            # Log enhancement status
            if enhanced_config.get('_browserforge_enhanced'):
                logger.info(f"🎭 Using BrowserForge fingerprint: {enhanced_config.get('device_name')}")
                if enhanced_config.get('_browserforge_webrtc_enabled'):
                    logger.info(f"🔒 BrowserForge WebRTC protection enabled for proxy: {proxy_ip}")
            else:
                logger.info(f"📱 Using standard profile: {enhanced_config.get('device_name')}")
            
            # CLEANED: Camoufox WITHOUT any custom WebRTC configuration
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
                
                # Apply BrowserForge stealth (includes WebRTC)
                await self._apply_browserforge_stealth(page, enhanced_config)
                
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
                        'browserforge_webrtc': enhanced_config.get('_browserforge_webrtc_enabled', False),
                        'device_name': enhanced_config.get('device_name'),
                        'proxy_ip': proxy_ip
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
    
    async def _apply_browserforge_stealth(self, page, enhanced_config: Dict[str, Any]):
        """
        Apply BrowserForge stealth (CLEANED - no custom WebRTC code)
        
        BrowserForge handles ALL WebRTC masking natively
        """
        platform = enhanced_config.get('platform', 'iPhone')
        hardware_concurrency = enhanced_config.get('hardware_concurrency', 4)
        device_memory = enhanced_config.get('device_memory', 4)
        webgl_vendor = enhanced_config.get('webgl_vendor', 'Apple Inc.')
        webgl_renderer = enhanced_config.get('webgl_renderer', 'Apple GPU')
        language = enhanced_config.get('language', 'en-US')
        languages = enhanced_config.get('languages', ['en-US', 'en'])
        max_touch_points = enhanced_config.get('max_touch_points', 5)
        
        # Convert languages list to JavaScript array
        languages_str = str(languages).replace("'", '"')
        
        # Get BrowserForge WebRTC script
        webrtc_script = ""
        if enhanced_config.get('_browserforge_webrtc_enabled'):
            webrtc_script = self.browserforge.get_browserforge_webrtc_script(enhanced_config)
        
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
    
    // BrowserForge: Max touch points
    try {{
        Object.defineProperty(navigator, 'maxTouchPoints', {{
            get: () => {max_touch_points},
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
    
    console.log('[Camoufox + BrowserForge] ✅ Enhanced stealth applied');
}})();

{webrtc_script}
        """
        
        await page.evaluate(script)
        logger.info("✅ Camoufox: BrowserForge stealth + WebRTC protection applied")
