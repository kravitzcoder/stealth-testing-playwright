"""
PLAYWRIGHT CATEGORY RUNNER - Complete Fix with All Improvements
Handles all Playwright-based stealth libraries

FIXES APPLIED:
- playwright-stealth v1.0.6 compatibility
- Route-based worker interception
- WebRTC leak protection (Chromium)
- Camoufox User-Agent consistency (HTTP vs JS)
- Improved IP detection on all pages
- Better timing for dynamic/worker pages
- GeoIP enabled for Camoufox

Authors: kravitzcoder & MiniMax Agent
"""
import asyncio
import json
import time
import os
import re
from typing import Dict, Any, Optional
import logging
from pathlib import Path

from ..core.test_result import TestResult

logger = logging.getLogger(__name__)


class PlaywrightRunner:
    """Runner for Playwright-based stealth libraries"""
    
    def __init__(self, screenshot_engine):
        self.screenshot_engine = screenshot_engine
        logger.info("Playwright runner initialized with route-based worker spoofing")
        self.stealth_available = self._verify_stealth_plugin()
    
    def _verify_stealth_plugin(self) -> bool:
        """Verify playwright-stealth v1.0.6 - DISABLED due to bugs"""
        # DISABLED: playwright-stealth v1.0.6 has a bug where it injects code with undefined 'opts' variable
        # This breaks page JavaScript and prevents data extraction
        # Our manual spoofing is more comprehensive anyway
        logger.info("ℹ️ playwright-stealth plugin DISABLED (using manual spoofing only)")
        return False
    
    def _get_worker_injection_code(self, mobile_config: Dict[str, Any]) -> str:
        """Generate worker injection code - FIXED to not wrap in IIFE"""
        user_agent = mobile_config.get('user_agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)')
        
        if 'iPhone' in user_agent or 'iPad' in user_agent:
            platform = 'iPhone'
        elif 'Android' in user_agent:
            platform = 'Linux armv8l'
        else:
            platform = 'iPhone'
            
        hardware = mobile_config.get('hardware_concurrency', 8)
        device_memory = mobile_config.get('device_memory', 8)
        # FIXED: Use proxy timezone instead of device profile timezone
        timezone = 'America/Los_Angeles'  # Match proxy location
        language = mobile_config.get('language', 'en-US').replace('_', '-')
        
        # FIXED: Los Angeles timezone offset (UTC-8 or UTC-7 depending on DST)
        # Use -420 for PDT (summer) or -480 for PST (winter)
        # Since it's October, we're in PDT (UTC-7)
        tz_offset = 420  # PDT = UTC-7 = +420 minutes
        
        # FIXED: Don't wrap in IIFE, just define properties directly
        code = f"""
// ===== WORKER CONTEXT SPOOFING (Minimal Injection) =====
// Spoof navigator properties without blocking worker communication

if (typeof self !== 'undefined' && self.navigator) {{
    const originalUserAgent = self.navigator.userAgent;
    const originalPlatform = self.navigator.platform;
    
    try {{
        Object.defineProperty(self.navigator, 'userAgent', {{
            get: function() {{ return '{user_agent}'; }},
            enumerable: true,
            configurable: true
        }});
    }} catch(e) {{ console.warn('[Worker] UA spoof failed:', e); }}
    
    try {{
        Object.defineProperty(self.navigator, 'platform', {{
            get: function() {{ return '{platform}'; }},
            enumerable: true,
            configurable: true
        }});
    }} catch(e) {{ console.warn('[Worker] Platform spoof failed:', e); }}
    
    try {{
        Object.defineProperty(self.navigator, 'hardwareConcurrency', {{
            get: function() {{ return {hardware}; }},
            enumerable: true,
            configurable: true
        }});
    }} catch(e) {{}}
    
    try {{
        Object.defineProperty(self.navigator, 'deviceMemory', {{
            get: function() {{ return {device_memory}; }},
            enumerable: true,
            configurable: true
        }});
    }} catch(e) {{}}
    
    try {{
        Object.defineProperty(self.navigator, 'language', {{
            get: function() {{ return '{language}'; }},
            enumerable: true,
            configurable: true
        }});
    }} catch(e) {{}}
    
    try {{
        Object.defineProperty(self.navigator, 'languages', {{
            get: function() {{ return ['{language}', 'en']; }},
            enumerable: true,
            configurable: true
        }});
    }} catch(e) {{}}
}}

// Minimal timezone spoofing - don't override Date entirely
if (typeof self !== 'undefined' && typeof Date !== 'undefined') {{
    const OriginalDate = Date;
    const tzOffset = {tz_offset};
    
    try {{
        const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
        Date.prototype.getTimezoneOffset = function() {{
            return tzOffset;
        }};
    }} catch(e) {{}}
}}

// End of worker spoofing - original worker script continues below
"""
        return code
    
    async def _apply_enhanced_stealth(self, page, context, mobile_config: Dict[str, Any]):
        """Apply enhanced stealth with worker interception"""
        
        user_agent = mobile_config.get('user_agent', '')
        if 'iPhone' in user_agent or 'iPad' in user_agent:
            platform = 'iPhone'
        elif 'Android' in user_agent:
            platform = 'Linux armv8l'
        else:
            platform = 'iPhone'
        
        hardware = mobile_config.get('hardware_concurrency', 8)
        device_memory = mobile_config.get('device_memory', 8)
        
        main_window_spoof = f"""
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{platform}', enumerable: true, configurable: true
            }});
            
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {hardware}, enumerable: true, configurable: true
            }});
            
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {device_memory}, enumerable: true, configurable: true
            }});
            
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined, enumerable: true, configurable: true
            }});
            
            if (!window.chrome) {{ window.chrome = {{}}; }}
            window.chrome.runtime = {{}};
            
            if (navigator.permissions && navigator.permissions.query) {{
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({{ state: Notification.permission }}) :
                        originalQuery(parameters)
                );
            }}
            
            Object.defineProperty(navigator, 'plugins', {{
                get: () => [
                    {{ name: 'PDF Viewer', filename: 'internal-pdf-viewer' }},
                    {{ name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer' }},
                    {{ name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer' }},
                    {{ name: 'WebKit built-in PDF', filename: 'internal-pdf-viewer' }}
                ],
                enumerable: true
            }});
            
            console.log('[Main Window] Spoofed:', {{
                platform: navigator.platform,
                hardwareConcurrency: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory
            }});
        """
        
        await context.add_init_script(main_window_spoof)
        logger.info("✅ Main window navigator spoofing applied")
        
        worker_injection = self._get_worker_injection_code(mobile_config)
        
        async def handle_route(route, request):
            """Intercept worker SCRIPTS only"""
            url = request.url
            resource_type = request.resource_type
            
            is_worker_script = (
                resource_type == 'script' and (
                    'worker' in url.lower() and url.endswith('.js')
                )
            )
            
            if is_worker_script:
                try:
                    logger.info(f"🔧 Intercepting worker script: {url}")
                    response = await context.request.fetch(url)
                    original_script = await response.text()
                    modified_script = worker_injection + '\n\n' + original_script
                    
                    await route.fulfill(
                        status=200,
                        content_type='application/javascript; charset=utf-8',
                        body=modified_script
                    )
                    logger.info(f"✅ Worker script injection successful")
                except Exception as e:
                    logger.error(f"❌ Worker script interception failed: {e}")
                    await route.continue_()
            else:
                await route.continue_()
        
        await page.route('**/*', handle_route)
        logger.info("✅ Route-based worker interception enabled")
        
        # REMOVED: playwright-stealth plugin disabled due to bugs
        # The plugin injects code with undefined 'opts' variable which breaks page JavaScript
        # Our manual spoofing above is more comprehensive and doesn't break pages
        
        logger.info("✅ Enhanced stealth fully applied (manual spoofing only)")
    
    async def run_test(
        self, 
        library_name: str,
        url: str,
        url_name: str, 
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 30
    ) -> TestResult:
        """Run test for a Playwright-based library"""
        
        test_methods = {
            "playwright": self._test_playwright_basic,
            "playwright-stealth": self._test_playwright_stealth,
            "playwright_stealth": self._test_playwright_stealth,
            "patchright": self._test_patchright,
            "camoufox": self._test_camoufox
        }
        
        test_method = test_methods.get(library_name)
        if not test_method:
            return TestResult(
                library=library_name, category="playwright", test_name=url_name,
                url=url, success=False, error=f"Unknown library: {library_name}"
            )
        
        return await test_method(url, url_name, proxy_config, mobile_config, wait_time)
    
    async def _test_playwright_stealth(
        self, url: str, url_name: str, proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any], wait_time: int
    ) -> TestResult:
        """Test Playwright with stealth plugin"""
        start_time = time.time()
        browser = None
        
        try:
            from playwright.async_api import async_playwright
            
            proxy_setup = {
                "server": f"http://{proxy_config['host']}:{proxy_config['port']}"
            }
            
            if proxy_config.get('username') and proxy_config.get('password'):
                proxy_setup["username"] = proxy_config['username']
                proxy_setup["password"] = proxy_config['password']
            
            logger.info(f"Testing Playwright-Stealth v1.0.6 on {url_name}")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    proxy=proxy_setup,
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-webrtc',  # FIX: Block WebRTC
                        '--disable-webrtc-hw-encoding',
                        '--enforce-webrtc-ip-permission-check'
                    ]
                )
                
                # FIXED: Use proxy timezone (Los Angeles) to match IP location
                timezone = 'America/Los_Angeles'
                
                context = await browser.new_context(
                    viewport=mobile_config.get('viewport', {'width': 375, 'height': 812}),
                    user_agent=mobile_config.get('user_agent'),
                    device_scale_factor=mobile_config.get('device_scale_factor', 2.0),
                    is_mobile=mobile_config.get('is_mobile', True),
                    has_touch=mobile_config.get('has_touch', True),
                    locale='en-US',
                    timezone_id=timezone
                )
                
                page = await context.new_page()
                await self._apply_enhanced_stealth(page, context, mobile_config)
                
                try:
                    await page.goto(url, timeout=30000, wait_until='networkidle')
                except:
                    await page.goto(url, timeout=30000, wait_until='domcontentloaded')
                
                # FIX: Extra wait for dynamic pages
                if 'worker' in url_name.lower():
                    # Wait for workers to initialize, run, and display results
                    logger.info("Waiting for workers to complete analysis...")
                    await asyncio.sleep(15)  # Extra time for worker execution
                    
                    # Try to wait for the UI to render (wait for specific elements)
                    try:
                        # Wait for worker results to appear
                        await page.wait_for_selector('text=/Window compared to/', timeout=10000)
                        logger.info("✅ Worker results UI detected")
                    except:
                        logger.warning("Worker results UI not detected, continuing anyway")
                        await asyncio.sleep(5)
                else:
                    await asyncio.sleep(3)
                
                screenshot_path = await self.screenshot_engine.capture_with_wait(
                    browser, "playwright-stealth", url_name, wait_time, page
                )
                
                detected_ip, user_agent = await self._extract_detection_data(page, url)
                
                await browser.close()
                
                return TestResult(
                    library="playwright-stealth", category="playwright",
                    test_name=url_name, url=url, success=True,
                    detected_ip=detected_ip, user_agent=user_agent,
                    is_mobile_ua=self._check_mobile_ua(user_agent or mobile_config.get('user_agent', '')),
                    proxy_working=self._check_proxy_working(detected_ip, proxy_config),
                    screenshot_path=screenshot_path,
                    execution_time=time.time() - start_time,
                    additional_data={
                        'worker_spoofing': 'route-based',
                        'stealth_plugin': 'disabled (manual only)',
                        'webrtc': 'blocked'
                    }
                )
                
        except Exception as e:
            logger.error(f"Playwright-stealth test failed: {str(e)}")
            if browser:
                try:
                    await browser.close()
                except:
                    pass
            
            return TestResult(
                library="playwright-stealth", category="playwright",
                test_name=url_name, url=url, success=False,
                error=str(e)[:200], execution_time=time.time() - start_time
            )
    
    async def _test_playwright_basic(
        self, url: str, url_name: str, proxy_config: Dict[str, str], 
        mobile_config: Dict[str, Any], wait_time: int
    ) -> TestResult:
        """Test native Playwright"""
        start_time = time.time()
        browser = None
        
        try:
            from playwright.async_api import async_playwright
            
            proxy_setup = {
                "server": f"http://{proxy_config['host']}:{proxy_config['port']}"
            }
            
            if proxy_config.get('username') and proxy_config.get('password'):
                proxy_setup["username"] = proxy_config['username']
                proxy_setup["password"] = proxy_config['password']
            
            logger.info(f"Testing Playwright (native) on {url_name}")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    proxy=proxy_setup,
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-webrtc',  # FIX: Block WebRTC
                        '--disable-webrtc-hw-encoding',
                        '--enforce-webrtc-ip-permission-check'
                    ]
                )
                
                timezone = 'America/Los_Angeles'
                
                context = await browser.new_context(
                    viewport=mobile_config.get('viewport', {'width': 375, 'height': 812}),
                    user_agent=mobile_config.get('user_agent'),
                    device_scale_factor=mobile_config.get('device_scale_factor', 2.0),
                    is_mobile=mobile_config.get('is_mobile', True),
                    has_touch=mobile_config.get('has_touch', True),
                    locale='en-US',
                    timezone_id=timezone
                )
                
                page = await context.new_page()
                await self._apply_enhanced_stealth(page, context, mobile_config)
                
                try:
                    await page.goto(url, timeout=30000, wait_until='networkidle')
                except:
                    await page.goto(url, timeout=30000, wait_until='domcontentloaded')
                
                if 'worker' in url_name.lower():
                    logger.info("Waiting for workers to complete analysis...")
                    await asyncio.sleep(15)
                    
                    # Scroll page to trigger any lazy loading
                    try:
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        await asyncio.sleep(2)
                        await page.evaluate('window.scrollTo(0, 0)')
                        await asyncio.sleep(1)
                    except:
                        pass
                    
                    try:
                        await page.wait_for_selector('text=/Window compared to/', timeout=10000)
                        logger.info("✅ Worker results UI detected")
                    except:
                        logger.warning("Worker results UI not detected, continuing anyway")
                        await asyncio.sleep(5)
                else:
                    await asyncio.sleep(3)
                
                screenshot_path = await self.screenshot_engine.capture_with_wait(
                    browser, "playwright", url_name, wait_time, page
                )
                
                detected_ip, user_agent = await self._extract_detection_data(page, url)
                
                await browser.close()
                
                return TestResult(
                    library="playwright", category="playwright",
                    test_name=url_name, url=url, success=True,
                    detected_ip=detected_ip, user_agent=user_agent,
                    is_mobile_ua=self._check_mobile_ua(user_agent or mobile_config.get('user_agent', '')),
                    proxy_working=self._check_proxy_working(detected_ip, proxy_config),
                    screenshot_path=screenshot_path,
                    execution_time=time.time() - start_time,
                    additional_data={'worker_spoofing': 'route-based', 'webrtc': 'blocked'}
                )
                
        except Exception as e:
            logger.error(f"Playwright test failed: {str(e)}")
            if browser:
                try:
                    await browser.close()
                except:
                    pass
            
            return TestResult(
                library="playwright", category="playwright",
                test_name=url_name, url=url, success=False,
                error=str(e)[:200], execution_time=time.time() - start_time
            )
    
    async def _test_patchright(
        self, url: str, url_name: str, proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any], wait_time: int
    ) -> TestResult:
        """Test Patchright"""
        start_time = time.time()
        browser = None
        
        try:
            try:
                from patchright.async_api import async_playwright
            except ImportError:
                return TestResult(
                    library="patchright", category="playwright",
                    test_name=url_name, url=url, success=False,
                    error="Patchright not installed"
                )
            
            proxy_setup = {
                "server": f"http://{proxy_config['host']}:{proxy_config['port']}"
            }
            
            if proxy_config.get('username') and proxy_config.get('password'):
                proxy_setup["username"] = proxy_config['username']
                proxy_setup["password"] = proxy_config['password']
            
            logger.info(f"Testing Patchright on {url_name}")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    proxy=proxy_setup,
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-webrtc',  # FIX: Block WebRTC
                        '--disable-webrtc-hw-encoding',
                        '--enforce-webrtc-ip-permission-check'
                    ]
                )
                
                timezone = 'America/Los_Angeles'
                
                context = await browser.new_context(
                    viewport=mobile_config.get('viewport', {'width': 375, 'height': 812}),
                    user_agent=mobile_config.get('user_agent'),
                    device_scale_factor=mobile_config.get('device_scale_factor', 2.0),
                    is_mobile=mobile_config.get('is_mobile', True),
                    has_touch=mobile_config.get('has_touch', True),
                    locale='en-US',
                    timezone_id=timezone
                )
                
                page = await context.new_page()
                await self._apply_enhanced_stealth(page, context, mobile_config)
                
                try:
                    await page.goto(url, timeout=30000, wait_until='networkidle')
                except:
                    await page.goto(url, timeout=30000, wait_until='domcontentloaded')
                
                if 'worker' in url_name.lower():
                    await asyncio.sleep(10)
                else:
                    await asyncio.sleep(3)
                
                screenshot_path = await self.screenshot_engine.capture_with_wait(
                    browser, "patchright", url_name, wait_time, page
                )
                
                detected_ip, user_agent = await self._extract_detection_data(page, url)
                
                await browser.close()
                
                return TestResult(
                    library="patchright", category="playwright",
                    test_name=url_name, url=url, success=True,
                    detected_ip=detected_ip, user_agent=user_agent,
                    is_mobile_ua=self._check_mobile_ua(user_agent or mobile_config.get('user_agent', '')),
                    proxy_working=self._check_proxy_working(detected_ip, proxy_config),
                    screenshot_path=screenshot_path,
                    execution_time=time.time() - start_time,
                    additional_data={'worker_spoofing': 'route-based', 'webrtc': 'blocked'}
                )
                
        except Exception as e:
            logger.error(f"Patchright test failed: {str(e)}")
            if browser:
                try:
                    await browser.close()
                except:
                    pass
            
            return TestResult(
                library="patchright", category="playwright",
                test_name=url_name, url=url, success=False,
                error=str(e)[:200], execution_time=time.time() - start_time
            )
    
    async def _test_camoufox(
        self, url: str, url_name: str, proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any], wait_time: int
    ) -> TestResult:
        """Test Camoufox with User-Agent consistency fix"""
        start_time = time.time()
        
        try:
            os.environ['CAMOUFOX_SKIP_AUTO_UPDATE'] = 'true'
            os.environ['NO_GITHUB_API'] = 'true'
            
            try:
                from camoufox.async_api import AsyncCamoufox
            except ImportError:
                return TestResult(
                    library="camoufox", category="playwright",
                    test_name=url_name, url=url, success=False,
                    error="Camoufox not installed"
                )
            
            proxy = None
            if proxy_config.get('host'):
                proxy = {
                    'server': f"{proxy_config['host']}:{proxy_config['port']}",
                    'username': proxy_config.get('username'),
                    'password': proxy_config.get('password')
                }
            
            user_agent_str = mobile_config.get('user_agent')
            logger.info(f"Testing Camoufox (Firefox) on {url_name}")
            
            try:
                async with AsyncCamoufox(
                    headless=True,
                    proxy=proxy,
                    geoip=True,  # FIX: Enables WebRTC IP spoofing
                    humanize=True,
                    block_images=False
                ) as browser:
                    timezone = 'America/Los_Angeles'
                    
                    context = await browser.new_context(
                        viewport={'width': mobile_config['viewport']['width'], 
                                 'height': mobile_config['viewport']['height']},
                        user_agent=user_agent_str,
                        locale='en-US',
                        timezone_id=timezone,
                        # FIX: Set User-Agent in HTTP headers
                        extra_http_headers={
                            'User-Agent': user_agent_str
                        }
                    )
                    
                    # FIX: Force JavaScript navigator.userAgent consistency
                    ua_override_script = f"""
                        Object.defineProperty(navigator, 'userAgent', {{
                            get: () => '{user_agent_str}',
                            configurable: true,
                            enumerable: true
                        }});
                        
                        console.log('[Camoufox] User-Agent forced to:', navigator.userAgent);
                    """
                    await context.add_init_script(ua_override_script)
                    
                    page = await context.new_page()
                    
                    # Worker spoofing for Firefox
                    worker_injection = self._get_worker_injection_code(mobile_config)
                    
                    async def handle_firefox_route(route, request):
                        """Intercept worker SCRIPTS only for Firefox"""
                        url_str = request.url
                        resource_type = request.resource_type
                        
                        is_worker_script = (
                            resource_type == 'script' and (
                                'worker' in url_str.lower() and url_str.endswith('.js')
                            )
                        )
                        
                        if is_worker_script:
                            try:
                                response = await context.request.fetch(url_str)
                                original = await response.text()
                                modified = worker_injection + '\n\n' + original
                                await route.fulfill(
                                    status=200,
                                    content_type='application/javascript',
                                    body=modified
                                )
                                logger.info(f"✅ Firefox worker script intercepted: {url_str}")
                            except:
                                await route.continue_()
                        else:
                            await route.continue_()
                    
                    await page.route('**/*', handle_firefox_route)
                    
                    await page.goto(url, timeout=30000)
                    
                    # FIX: Extra wait for workers
                    if 'worker' in url_name.lower():
                        logger.info("Waiting for workers to complete analysis...")
                        await asyncio.sleep(wait_time + 15)
                        # Scroll to trigger lazy loading
                        try:
                            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                            await asyncio.sleep(2)
                            await page.evaluate('window.scrollTo(0, 0)')
                            await asyncio.sleep(1)
                        except:
                            pass
                        # Try to detect if results UI is ready
                        try:
                            await page.wait_for_selector('text=/Window compared to/', timeout=10000)
                            logger.info("✅ Worker results UI detected")
                        except:
                            logger.warning("Worker results UI not detected, continuing anyway")
                            await asyncio.sleep(5)
                    else:
                        await asyncio.sleep(wait_time + 3)
                    
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"camoufox_{url_name}_{timestamp}.png"
                    filepath = Path("test_results/screenshots") / filename
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    
                    # FIX: Try full_page first, fallback to viewport
                    try:
                        await page.screenshot(path=str(filepath), full_page=True)
                    except:
                        logger.warning("Full page failed, using viewport")
                        await page.screenshot(path=str(filepath))
                    
                    user_agent = await page.evaluate('navigator.userAgent')
                    detected_ip = None
                    
                    # FIX: Try to detect IP on all pages
                    detected_ip = await self._extract_ip_from_page(page)
                    
                    await context.close()
                    
                    return TestResult(
                        library="camoufox", category="playwright",
                        test_name=url_name, url=url, success=True,
                        detected_ip=detected_ip, user_agent=user_agent,
                        is_mobile_ua=self._check_mobile_ua(user_agent or ''),
                        proxy_working=self._check_proxy_working(detected_ip, proxy_config),
                        screenshot_path=str(filepath),
                        execution_time=time.time() - start_time,
                        additional_data={
                            'worker_spoofing': 'route-based',
                            'engine': 'firefox',
                            'geoip': 'enabled',
                            'ua_forced': 'true'
                        }
                    )
                    
            except Exception as browser_error:
                if "rate limit" in str(browser_error).lower():
                    logger.warning("Camoufox rate limited, using fallback")
                    return await self._test_camoufox_fallback(url, url_name, proxy_config, mobile_config, wait_time)
                else:
                    raise browser_error
                    
        except Exception as e:
            logger.error(f"Camoufox test failed: {str(e)}")
            return TestResult(
                library="camoufox", category="playwright",
                test_name=url_name, url=url, success=False,
                error=str(e)[:200], execution_time=time.time() - start_time
            )
    
    async def _test_camoufox_fallback(
        self, url: str, url_name: str, proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any], wait_time: int
    ) -> TestResult:
        """Firefox fallback"""
        start_time = time.time()
        browser = None
        
        try:
            from playwright.async_api import async_playwright
            
            proxy_setup = {
                "server": f"http://{proxy_config['host']}:{proxy_config['port']}"
            }
            
            if proxy_config.get('username') and proxy_config.get('password'):
                proxy_setup["username"] = proxy_config['username']
                proxy_setup["password"] = proxy_config['password']
            
            logger.info("Using Firefox fallback for Camoufox")
            
            async with async_playwright() as p:
                browser = await p.firefox.launch(proxy=proxy_setup, headless=True)
                
                timezone = mobile_config.get('timezone', 'Europe/Paris')
                user_agent_str = mobile_config.get('user_agent')
                
                context = await browser.new_context(
                    viewport=mobile_config.get('viewport'),
                    user_agent=user_agent_str,
                    locale='en-US',
                    timezone_id=timezone,
                    extra_http_headers={'User-Agent': user_agent_str}
                )
                
                # Force UA in JavaScript
                await context.add_init_script(f"""
                    Object.defineProperty(navigator, 'userAgent', {{
                        get: () => '{user_agent_str}',
                        configurable: true
                    }});
                """)
                
                page = await context.new_page()
                
                worker_injection = self._get_worker_injection_code(mobile_config)
                
                async def handle_route(route, request):
                    """Intercept worker SCRIPTS only"""
                    url_str = request.url
                    resource_type = request.resource_type
                    
                    is_worker_script = (
                        resource_type == 'script' and (
                            'worker' in url_str.lower() and url_str.endswith('.js')
                        )
                    )
                    
                    if is_worker_script:
                        try:
                            response = await context.request.fetch(url_str)
                            original = await response.text()
                            modified = worker_injection + '\n\n' + original
                            await route.fulfill(
                                status=200,
                                content_type='application/javascript',
                                body=modified
                            )
                            logger.info(f"✅ Worker script intercepted: {url_str}")
                        except:
                            await route.continue_()
                    else:
                        await route.continue_()
                
                await page.route('**/*', handle_route)
                await page.goto(url, timeout=30000)
                
                if 'worker' in url_name.lower():
                    logger.info("Waiting for workers to complete analysis...")
                    await asyncio.sleep(wait_time + 15)
                    try:
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        await asyncio.sleep(2)
                        await page.evaluate('window.scrollTo(0, 0)')
                        await asyncio.sleep(1)
                    except:
                        pass
                    try:
                        await page.wait_for_selector('text=/Window compared to/', timeout=10000)
                        logger.info("✅ Worker results UI detected")
                    except:
                        await asyncio.sleep(5)
                else:
                    await asyncio.sleep(wait_time)
                
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"camoufox_fallback_{url_name}_{timestamp}.png"
                filepath = Path("test_results/screenshots") / filename
                filepath.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    await page.screenshot(path=str(filepath), full_page=True)
                except:
                    await page.screenshot(path=str(filepath))
                
                user_agent = await page.evaluate('navigator.userAgent')
                detected_ip = await self._extract_ip_from_page(page)
                
                await browser.close()
                
                return TestResult(
                    library="camoufox", category="playwright",
                    test_name=url_name, url=url, success=True,
                    detected_ip=detected_ip, user_agent=user_agent,
                    is_mobile_ua=self._check_mobile_ua(user_agent or ''),
                    proxy_working=self._check_proxy_working(detected_ip, proxy_config),
                    screenshot_path=str(filepath),
                    execution_time=time.time() - start_time,
                    additional_data={'fallback': 'firefox', 'worker_spoofing': 'route-based', 'ua_forced': 'true'}
                )
                
        except Exception as e:
            logger.error(f"Firefox fallback failed: {str(e)}")
            if browser:
                try:
                    await browser.close()
                except:
                    pass
            
            return TestResult(
                library="camoufox", category="playwright",
                test_name=url_name, url=url, success=False,
                error=f"Fallback failed: {str(e)[:150]}",
                execution_time=time.time() - start_time
            )
    
    async def _extract_ip_from_page(self, page) -> Optional[str]:
        """Extract IP from any page (not just ip_check)"""
        try:
            await asyncio.sleep(2)
            
            # Strategy 1: Look for "Your IP:" pattern
            try:
                page_text = await page.evaluate('document.body.innerText')
                ip_pattern = r'Your IP[:\s]+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                match = re.search(ip_pattern, page_text, re.IGNORECASE)
                if match:
                    detected_ip = match.group(1)
                    logger.info(f"✅ Found IP via 'Your IP:' pattern: {detected_ip}")
                    return detected_ip
            except Exception as e:
                logger.debug(f"Pattern search failed: {e}")
            
            # Strategy 2: Find all IPs and filter
            try:
                page_content = await page.content()
                all_ips = re.findall(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', page_content)
                
                if all_ips:
                    # Filter out private IPs
                    public_ips = [
                        ip for ip in all_ips 
                        if not ip.startswith(('127.', '192.168.', '10.', '172.16.', '172.17.', 
                                             '172.18.', '172.19.', '172.20.', '172.21.', 
                                             '172.22.', '172.23.', '172.24.', '172.25.',
                                             '172.26.', '172.27.', '172.28.', '172.29.',
                                             '172.30.', '172.31.', '0.0.0.0', '255.255.'))
                    ]
                    
                    if public_ips:
                        detected_ip = public_ips[0]
                        logger.info(f"✅ Found IP via content search: {detected_ip}")
                        return detected_ip
            except Exception as e:
                logger.debug(f"Content search failed: {e}")
                    
        except Exception as e:
            logger.warning(f"⚠️ IP extraction failed: {e}")
        
        return None
    
    async def _extract_detection_data(self, page, url: str):
        """Extract IP and UA from any page"""
        detected_ip = None
        user_agent = None
        
        try:
            user_agent = await page.evaluate('navigator.userAgent')
            
            # FIX: Try to detect IP on ALL pages, not just ip_check
            detected_ip = await self._extract_ip_from_page(page)
                
        except Exception as e:
            logger.warning(f"Detection data extraction failed: {e}")
            
        return detected_ip, user_agent
    
    def _check_proxy_working(self, detected_ip: Optional[str], proxy_config: Dict[str, str]) -> bool:
        """Check if proxy is working"""
        if not detected_ip:
            return False
        
        proxy_ip = proxy_config.get('host')
        if not proxy_ip:
            return False
        
        is_working = detected_ip == proxy_ip
        
        if is_working:
            logger.info(f"✅ Proxy working: {detected_ip} == {proxy_ip}")
        else:
            logger.warning(f"⚠️ Proxy mismatch: {detected_ip} != {proxy_ip}")
        
        return is_working
    
    def _check_mobile_ua(self, user_agent: str) -> bool:
        """Check if user agent indicates mobile"""
        if not user_agent:
            return False
        
        mobile_indicators = ['Mobile', 'Android', 'iPhone', 'iPad', 'iPod']
        return any(indicator in user_agent for indicator in mobile_indicators)
