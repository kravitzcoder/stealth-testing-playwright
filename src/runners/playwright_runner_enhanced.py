"""
PLAYWRIGHT RUNNER - Enhanced with BrowserForge

WebRTC Strategy + BrowserForge Enhancement:
- Force WebRTC to use relay-only mode (uses proxy interface)
- Browser flags to enforce proxy usage
- JavaScript to force iceTransportPolicy='relay'
- BrowserForge intelligent fingerprints (NEW!)
"""

import logging
import time
from typing import Dict, Any

from ..core.test_result import TestResult
from .base_runner_enhanced import BaseRunner

logger = logging.getLogger(__name__)


class PlaywrightRunnerEnhanced(BaseRunner):
    """Vanilla Playwright runner with WebRTC relay mode + BrowserForge"""
    
    def __init__(self, screenshot_engine=None):
        super().__init__(screenshot_engine)
        logger.info("Playwright runner initialized (WebRTC relay + BrowserForge)")
    
    async def run_test(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 15
    ) -> TestResult:
        """Run test with Playwright + WebRTC relay mode + BrowserForge"""
        start_time = time.time()
        logger.info(f"🎭 Testing Playwright (BrowserForge) on {url_name}: {url}")
        
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
                
                # Get enhanced mobile config with BrowserForge (NEW!)
                enhanced_config = self.get_enhanced_mobile_config(
                    mobile_config=mobile_config,
                    device_type="iphone_x",  # or extract from mobile_config
                    use_browserforge=True
                )
                
                # Log enhancement status
                if enhanced_config.get('_browserforge_enhanced'):
                    logger.info(f"🎭 Using BrowserForge fingerprint: {enhanced_config.get('device_name')}")
                    logger.info(f"   User-Agent: {enhanced_config['user_agent'][:60]}...")
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
                
                # Apply stealth + WebRTC relay mode with BrowserForge data
                await self._apply_stealth_with_browserforge(context, enhanced_config)
                
                page = await context.new_page()
                
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
                
                await browser.close()
                
                execution_time = time.time() - start_time
                logger.info(f"✅ Playwright (BrowserForge) test completed in {execution_time:.2f}s")
                
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
                        'device_name': enhanced_config.get('device_name')
                    }
                )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)[:500]
            logger.error(f"❌ Playwright (BrowserForge) test failed: {error_msg}")
            
            return TestResult(
                library="playwright_browserforge",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
    
    async def _apply_stealth_with_browserforge(self, context, enhanced_config: Dict[str, Any]):
        """
        Enhanced stealth + WebRTC relay mode with BrowserForge data
        
        Injects BrowserForge fingerprint values into the page
        """
        platform = enhanced_config.get('platform', 'iPhone')
        hardware_concurrency = enhanced_config.get('hardware_concurrency', 4)
        device_memory = enhanced_config.get('device_memory', 4)
        webgl_vendor = enhanced_config.get('webgl_vendor', 'Apple Inc.')
        webgl_renderer = enhanced_config.get('webgl_renderer', 'Apple GPU')
        language = enhanced_config.get('language', 'en-US')
        languages = enhanced_config.get('languages', ['en-US', 'en'])
        
        # Convert languages list to JavaScript array string
        languages_str = str(languages).replace("'", '"')
        
        script = f"""
(function() {{
    'use strict';
    
    console.log('[Playwright + BrowserForge] Enhanced stealth active');
    
    // Hide webdriver
    Object.defineProperty(navigator, 'webdriver', {{
        get: () => undefined,
        configurable: true
    }});
    
    // BrowserForge: Platform override
    Object.defineProperty(navigator, 'platform', {{
        get: () => '{platform}',
        configurable: true
    }});
    
    // BrowserForge: Hardware concurrency
    Object.defineProperty(navigator, 'hardwareConcurrency', {{
        get: () => {hardware_concurrency},
        configurable: true
    }});
    
    // BrowserForge: Device memory
    Object.defineProperty(navigator, 'deviceMemory', {{
        get: () => {device_memory},
        configurable: true
    }});
    
    // BrowserForge: Languages
    Object.defineProperty(navigator, 'language', {{
        get: () => '{language}',
        configurable: true
    }});
    
    Object.defineProperty(navigator, 'languages', {{
        get: () => {languages_str},
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
    
    // BrowserForge: WebGL fingerprint
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
    
    // WebRTC: Force relay-only mode (uses proxy)
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
            
            console.log('[Playwright WebRTC] Relay mode enforced (proxy)');
            return new OriginalRTCPeerConnection(config);
        }};
        
        window.RTCPeerConnection.prototype = OriginalRTCPeerConnection.prototype;
    }}
    
    console.log('[Playwright + BrowserForge] ✅ Enhanced stealth + WebRTC relay active');
}})();
        """
        
        await context.add_init_script(script)
        logger.info("✅ Playwright: BrowserForge stealth + WebRTC relay mode applied")
