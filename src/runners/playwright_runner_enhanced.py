"""
PLAYWRIGHT RUNNER - BrowserForge Native mock_webrtc Implementation

Uses BrowserForge's native mock_webrtc feature for intelligent WebRTC handling
"""

import logging
import time
from typing import Dict, Any

from ..core.test_result import TestResult
from .base_runner_enhanced import BaseRunner

logger = logging.getLogger(__name__)


class PlaywrightRunnerEnhanced(BaseRunner):
    """Playwright runner with BrowserForge native mock_webrtc"""
    
    def __init__(self, screenshot_engine=None):
        super().__init__(screenshot_engine)
        logger.info("Playwright runner initialized (BrowserForge mock_webrtc)")
    
    async def run_test(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 15
    ) -> TestResult:
        """Run test with Playwright + BrowserForge native mock_webrtc"""
        start_time = time.time()
        logger.info(f"🎭 Testing Playwright (BrowserForge mock_webrtc) on {url_name}: {url}")
        
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
                
                # Launch browser with minimal flags
                browser = await p.chromium.launch(
                    headless=True,
                    proxy=proxy,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                    ]
                )
                
                # Get enhanced mobile config with BrowserForge mock_webrtc enabled
                enhanced_config = self.get_enhanced_mobile_config(
                    mobile_config=mobile_config,
                    device_type="iphone_x",
                    use_browserforge=True,
                    proxy_ip=proxy_ip,
                    mock_webrtc=True  # Enable BrowserForge's native WebRTC mocking
                )
                
                # Log enhancement status
                if enhanced_config.get('_browserforge_enhanced'):
                    logger.info(f"🎭 BrowserForge fingerprint: {enhanced_config.get('device_name')}")
                    if enhanced_config.get('_browserforge_webrtc_mock'):
                        logger.info(f"🔒 BrowserForge mock_webrtc ENABLED for proxy: {proxy_ip}")
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
                
                # Apply BrowserForge stealth (basic)
                await self._apply_browserforge_basic_stealth(context, enhanced_config)
                
                page = await context.new_page()
                
                # Inject BrowserForge fingerprint (includes WebRTC mocking)
                if enhanced_config.get('_browserforge_fingerprint'):
                    self.browserforge.inject_fingerprint_to_page(page, enhanced_config)
                    logger.info("✅ BrowserForge fingerprint injected (with mock_webrtc)")
                
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
                logger.info(f"✅ Playwright (BrowserForge mock_webrtc) test completed in {execution_time:.2f}s")
                
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
                        'browserforge_webrtc_mock': enhanced_config.get('_browserforge_webrtc_mock', False),
                        'device_name': enhanced_config.get('device_name'),
                        'proxy_ip': proxy_ip
                    }
                )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)[:500]
            logger.error(f"❌ Playwright (BrowserForge mock_webrtc) test failed: {error_msg}")
            
            return TestResult(
                library="playwright_browserforge",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
    
    async def _apply_browserforge_basic_stealth(self, context, enhanced_config: Dict[str, Any]):
        """
        Apply basic BrowserForge stealth (WebRTC handled by fingerprint injection)
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
    
    console.log('[BrowserForge] Applying basic stealth overrides');
    
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
    
    console.log('[BrowserForge] ✅ Basic stealth applied (WebRTC via fingerprint injection)');
}})();
        """
        
        await context.add_init_script(script)
        logger.info("✅ BrowserForge basic stealth applied")
config = self.get_enhanced_mobile_config(
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
                
                # Apply BrowserForge stealth + native WebRTC
                await self._apply_browserforge_stealth(context, enhanced_config)
                
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
        Apply BrowserForge stealth + native WebRTC protection
        
        This uses ONLY BrowserForge's approach - no custom blocking
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
        
        # Get BrowserForge WebRTC script if enabled
        webrtc_script = ""
        if enhanced_config.get('_browserforge_webrtc_enabled'):
            webrtc_script = self.browserforge.get_browserforge_webrtc_script(enhanced_config)
        
        script = f"""
(function() {{
    'use strict';
    
    console.log('[BrowserForge Stealth] Applying fingerprint overrides');
    
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
    
    console.log('[BrowserForge Stealth] ✅ Fingerprint overrides applied');
}})();

{webrtc_script}
        """
        
        await context.add_init_script(script)
        logger.info("✅ BrowserForge stealth + WebRTC protection applied")
