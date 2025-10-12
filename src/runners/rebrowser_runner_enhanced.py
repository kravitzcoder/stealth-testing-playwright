"""
REBROWSER RUNNER ENHANCED - BrowserForge Native WebRTC (CLEANED)

WebRTC Strategy:
- NO custom WebRTC blocking or relay mode
- NO CDP STUN/TURN blocking
- BrowserForge handles ALL WebRTC masking natively
- Uses Rebrowser's stealth patches + BrowserForge fingerprints
"""

import logging
import time
import json
from typing import Dict, Any

from ..core.test_result import TestResult
from .base_runner_enhanced import BaseRunner

logger = logging.getLogger(__name__)


class RebrowserRunnerEnhanced(BaseRunner):
    """Rebrowser runner with BrowserForge native WebRTC"""
    
    def __init__(self, screenshot_engine=None):
        super().__init__(screenshot_engine)
        logger.info("🔥 Rebrowser runner initialized (BrowserForge native)")
    
    async def run_test(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 15
    ) -> TestResult:
        """Run test with Rebrowser + BrowserForge native WebRTC"""
        start_time = time.time()
        logger.info(f"🎭 Testing Rebrowser (BrowserForge) on {url_name}: {url}")
        
        try:
            from rebrowser_playwright.async_api import async_playwright
        except ImportError:
            error_msg = "rebrowser-playwright not installed. Run: pip install rebrowser-playwright"
            logger.error(error_msg)
            return TestResult(
                library="rebrowser_playwright",
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
                    logger.info(f"   User-Agent: {enhanced_config['user_agent'][:60]}...")
                    if enhanced_config.get('_browserforge_webrtc_enabled'):
                        logger.info(f"🔒 BrowserForge WebRTC protection enabled for proxy: {proxy_ip}")
                else:
                    logger.info(f"📱 Using standard profile: {enhanced_config.get('device_name')}")
                
                # CLEANED: Rebrowser launch args WITHOUT WebRTC flags
                browser = await p.chromium.launch(
                    headless=True,
                    proxy=proxy,
                    args=self._get_rebrowser_launch_args_clean()
                )
                
                # Enhanced context with BrowserForge data
                context = await browser.new_context(
                    **self._get_rebrowser_context_config(enhanced_config)
                )
                
                # Apply Rebrowser stealth + BrowserForge (no custom WebRTC)
                await self._apply_rebrowser_stealth_with_browserforge(context, enhanced_config)
                
                page = await context.new_page()
                
                # CLEANED: No CDP WebRTC blocking - let BrowserForge handle it
                # Optionally apply minimal CDP stealth (geolocation, timezone, touch)
                await self._apply_cdp_stealth_minimal(page, enhanced_config)
                
                logger.info(f"Navigating to {url} with Rebrowser (BrowserForge)")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Extra wait for dynamic pages
                await self._extra_wait_for_dynamic_pages(url, url_name)
                
                # Capture screenshot
                screenshot_path = await self.screenshot_engine.capture_with_wait(
                    page, "rebrowser_browserforge", url_name, wait_time, page=page
                )
                
                # Check results
                proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
                is_mobile = await self._check_mobile_ua(page, enhanced_config)
                
                await browser.close()
                
                execution_time = time.time() - start_time
                logger.info(f"✅ Rebrowser (BrowserForge) test completed in {execution_time:.2f}s")
                
                return TestResult(
                    library="rebrowser_browserforge",
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
            logger.error(f"❌ Rebrowser (BrowserForge) test failed: {error_msg}")
            
            return TestResult(
                library="rebrowser_browserforge",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
    
    def _get_rebrowser_launch_args_clean(self) -> list:
        """
        CLEANED: Rebrowser launch args WITHOUT WebRTC blocking
        
        Let BrowserForge handle WebRTC natively
        """
        return [
            # Core anti-detection
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            
            # Environment
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu',
            
            # Automation markers removal
            '--disable-automation',
            '--disable-dev-tools',
            
            # ✅ NO WebRTC-disabling flags - BrowserForge handles it!
        ]
    
    def _get_rebrowser_context_config(self, enhanced_config: Dict[str, Any]) -> dict:
        """Enhanced context configuration with BrowserForge data"""
        return {
            'user_agent': enhanced_config.get("user_agent"),
            'viewport': enhanced_config.get("viewport"),
            'device_scale_factor': enhanced_config.get("device_scale_factor", 2),
            'is_mobile': True,
            'has_touch': True,
            'locale': enhanced_config.get("language", "en-US").replace("_", "-"),
            'timezone_id': enhanced_config.get("timezone", "America/New_York"),
            'bypass_csp': True,
            'extra_http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': f'"{enhanced_config.get("platform", "Android")}"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            },
            'permissions': ['geolocation'],
            'geolocation': {"latitude": 37.7749, "longitude": -122.4194}
        }
    
    async def _apply_rebrowser_stealth_with_browserforge(self, context, enhanced_config: Dict[str, Any]):
        """
        CLEANED: Rebrowser stealth + BrowserForge (NO custom WebRTC)
        
        BrowserForge handles ALL WebRTC masking
        """
        ua = enhanced_config.get("user_agent", "")
        platform = enhanced_config.get("platform", "iPhone")
        hardware_concurrency = enhanced_config.get('hardware_concurrency', 4)
        device_memory = enhanced_config.get('device_memory', 4)
        max_touch_points = enhanced_config.get('max_touch_points', 5)
        language = enhanced_config.get('language', 'en-US')
        languages = enhanced_config.get('languages', ['en-US', 'en'])
        webgl_vendor = enhanced_config.get('webgl_vendor', 'Apple Inc.')
        webgl_renderer = enhanced_config.get('webgl_renderer', 'Apple GPU')
        
        ua_escaped = json.dumps(ua)
        languages_str = str(languages).replace("'", '"')
        
        # Get BrowserForge WebRTC script
        webrtc_script = ""
        if enhanced_config.get('_browserforge_webrtc_enabled'):
            webrtc_script = self.browserforge.get_browserforge_webrtc_script(enhanced_config)
        
        script = f"""
(function() {{
    'use strict';
    
    console.log('[Rebrowser + BrowserForge] Enhanced stealth active');
    
    // Core navigator properties (BrowserForge)
    const props = {{
        userAgent: {ua_escaped},
        platform: '{platform}',
        vendor: 'Google Inc.',
        language: '{language}',
        languages: {languages_str},
        hardwareConcurrency: {hardware_concurrency},
        deviceMemory: {device_memory},
        maxTouchPoints: {max_touch_points}
    }};
    
    Object.keys(props).forEach(prop => {{
        try {{
            if (prop in navigator) {{
                Object.defineProperty(navigator, prop, {{
                    get: () => props[prop],
                    configurable: true
                }});
            }}
        }} catch(e) {{}}
    }});
    
    // Remove webdriver
    delete navigator.__proto__.webdriver;
    Object.defineProperty(navigator, 'webdriver', {{
        get: () => undefined,
        configurable: true
    }});
    
    // BrowserForge: WebGL vendor/renderer spoofing
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
    
    // Chrome runtime
    if (!window.chrome) {{
        window.chrome = {{}};
    }}
    window.chrome.runtime = {{
        connect: () => ({{}}),
        sendMessage: () => ({{}})
    }};
    
    console.log('[Rebrowser + BrowserForge] ✅ Stealth + fingerprints active');
}})();

{webrtc_script}
        """
        
        await context.add_init_script(script)
        logger.info("✅ Rebrowser: Enhanced stealth + BrowserForge + WebRTC protection applied")
    
    async def _apply_cdp_stealth_minimal(self, page, enhanced_config: Dict[str, Any]):
        """
        CLEANED: Minimal CDP commands (NO WebRTC blocking)
        
        Only applies geolocation, timezone, and touch emulation
        BrowserForge handles WebRTC
        """
        try:
            client = await page.context.new_cdp_session(page)
            
            # Geolocation override
            await client.send('Emulation.setGeolocationOverride', {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'accuracy': 100
            })
            
            # Timezone override
            await client.send('Emulation.setTimezoneOverride', {
                'timezoneId': enhanced_config.get("timezone", "America/New_York")
            })
            
            # Touch emulation
            await client.send('Emulation.setTouchEmulationEnabled', {
                'enabled': True,
                'maxTouchPoints': enhanced_config.get("max_touch_points", 5)
            })
            
            logger.info("✅ CDP: Geolocation, timezone, touch emulation applied (BrowserForge handles WebRTC)")
            
        except Exception as e:
            logger.warning(f"⚠️ CDP stealth partial: {str(e)[:80]}")
