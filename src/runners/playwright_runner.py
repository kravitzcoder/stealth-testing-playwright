"""
PLAYWRIGHT CATEGORY RUNNER - Fixed with Proper Worker Spoofing
Handles all Playwright-based stealth libraries with route-based worker interception

Authors: kravitzcoder & MiniMax Agent
FIXES:
- playwright-stealth v1.0.6 compatibility (stealth_async)
- Route-based worker script interception instead of blob URLs
- Improved proxy IP detection with multiple selectors
- Camoufox geoip support
- Timezone consistency from device profiles
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
    """Runner for Playwright-based stealth libraries with proper worker spoofing"""
    
    def __init__(self, screenshot_engine):
        self.screenshot_engine = screenshot_engine
        logger.info("Playwright runner initialized with route-based worker spoofing")
        self.stealth_available = self._verify_stealth_plugin()
    
    def _verify_stealth_plugin(self) -> bool:
        """Verify playwright-stealth v1.0.6 is properly installed"""
        try:
            from playwright_stealth import stealth_async
            logger.info("✅ playwright-stealth v1.0.6 available (stealth_async)")
            return True
        except ImportError as e:
            logger.warning(f"⚠️ playwright-stealth NOT available: {e}")
            return False
    
    def _get_worker_injection_code(self, mobile_config: Dict[str, Any]) -> str:
        """
        Generate worker injection code (will be prepended to worker scripts)
        This runs INSIDE worker context, so it's plain JavaScript
        """
        user_agent = mobile_config.get('user_agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)')
        
        # Determine platform from user agent
        if 'iPhone' in user_agent or 'iPad' in user_agent:
            platform = 'iPhone'
        elif 'Android' in user_agent:
            platform = 'Linux armv8l'
        else:
            platform = 'iPhone'
            
        hardware = mobile_config.get('hardware_concurrency', 8)
        device_memory = mobile_config.get('device_memory', 8)
        timezone = mobile_config.get('timezone', 'Europe/Paris')
        language = mobile_config.get('language', 'en-US').replace('_', '-')
        
        # Calculate timezone offset (simplified - you might want to use a library)
        tz_offsets = {
            'Europe/Paris': -120,  # UTC+2 in summer, UTC+1 in winter
            'America/New_York': 300,  # UTC-5
            'America/Chicago': 360,  # UTC-6
            'America/Los_Angeles': 420,  # UTC-7
            'America/Denver': 420,  # UTC-7
            'America/Toronto': 300,  # UTC-5
            'Europe/London': -60,  # UTC+1
            'Europe/Berlin': -120,  # UTC+2
        }
        tz_offset = tz_offsets.get(timezone, -120)
        
        code = f"""
// ===== WORKER CONTEXT SPOOFING =====
// This code runs INSIDE the worker before the worker's actual script
(function() {{
    'use strict';
    
    const config = {{
        userAgent: '{user_agent}',
        platform: '{platform}',
        hardwareConcurrency: {hardware},
        deviceMemory: {device_memory},
        timezone: '{timezone}',
        timezoneOffset: {tz_offset},
        language: '{language}',
        languages: ['{language}', 'en']
    }};
    
    // Override navigator properties
    Object.defineProperty(self.navigator, 'userAgent', {{
        get: () => config.userAgent,
        enumerable: true,
        configurable: true
    }});
    
    Object.defineProperty(self.navigator, 'platform', {{
        get: () => config.platform,
        enumerable: true,
        configurable: true
    }});
    
    Object.defineProperty(self.navigator, 'hardwareConcurrency', {{
        get: () => config.hardwareConcurrency,
        enumerable: true,
        configurable: true
    }});
    
    Object.defineProperty(self.navigator, 'deviceMemory', {{
        get: () => config.deviceMemory,
        enumerable: true,
        configurable: true
    }});
    
    Object.defineProperty(self.navigator, 'language', {{
        get: () => config.language,
        enumerable: true,
        configurable: true
    }});
    
    Object.defineProperty(self.navigator, 'languages', {{
        get: () => config.languages,
        enumerable: true,
        configurable: true
    }});
    
    // Timezone spoofing via Date override
    const OriginalDate = Date;
    const tzOffset = config.timezoneOffset;
    
    self.Date = class extends OriginalDate {{
        constructor(...args) {{
            if (args.length === 0) {{
                super();
            }} else {{
                super(...args);
            }}
        }}
        
        getTimezoneOffset() {{
            return tzOffset;
        }}
        
        toString() {{
            return super.toString().replace(/GMT[+-]\\d{{4}}/, 'GMT' + (tzOffset > 0 ? '-' : '+') + String(Math.abs(tzOffset/60)).padStart(2, '0') + '00');
        }}
    }};
    
    // Preserve static methods
    self.Date.now = OriginalDate.now;
    self.Date.parse = OriginalDate.parse;
    self.Date.UTC = OriginalDate.UTC;
    self.Date.prototype = OriginalDate.prototype;
    
    // Intl.DateTimeFormat timezone
    if (typeof Intl !== 'undefined' && Intl.DateTimeFormat) {{
        const OriginalDateTimeFormat = Intl.DateTimeFormat;
        self.Intl.DateTimeFormat = function(...args) {{
            if (!args[1]) args[1] = {{}};
            if (!args[1].timeZone) args[1].timeZone = config.timezone;
            return new OriginalDateTimeFormat(...args);
        }};
        self.Intl.DateTimeFormat.prototype = OriginalDateTimeFormat.prototype;
        self.Intl.DateTimeFormat.supportedLocalesOf = OriginalDateTimeFormat.supportedLocalesOf;
    }}
    
    console.log('[Worker Injected] Properties spoofed:', {{
        type: typeof WorkerGlobalScope !== 'undefined' ? 'Worker' : 'Unknown',
        userAgent: self.navigator.userAgent,
        platform: self.navigator.platform,
        hardwareConcurrency: self.navigator.hardwareConcurrency,
        language: self.navigator.language,
        timezone: config.timezone
    }});
}})();

// Original worker script continues below...
"""
        return code
    
    async def _apply_enhanced_stealth(self, page, context, mobile_config: Dict[str, Any]):
        """Apply enhanced stealth including route-based worker interception"""
        
        # Determine platform from user agent
        user_agent = mobile_config.get('user_agent', '')
        if 'iPhone' in user_agent or 'iPad' in user_agent:
            platform = 'iPhone'
        elif 'Android' in user_agent:
            platform = 'Linux armv8l'
        else:
            platform = 'iPhone'
        
        hardware = mobile_config.get('hardware_concurrency', 8)
        device_memory = mobile_config.get('device_memory', 8)
        timezone = mobile_config.get('timezone', 'Europe/Paris')
        
        # 1. Main window navigator spoofing
        main_window_spoof = f"""
            // MAIN WINDOW NAVIGATOR SPOOFING
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{platform}',
                enumerable: true,
                configurable: true
            }});
            
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {hardware},
                enumerable: true,
                configurable: true
            }});
            
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {device_memory},
                enumerable: true,
                configurable: true
            }});
            
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined,
                enumerable: true,
                configurable: true
            }});
            
            // Chrome runtime
            if (!window.chrome) {{
                window.chrome = {{}};
            }}
            window.chrome.runtime = {{}};
            
            // Permissions API
            if (navigator.permissions && navigator.permissions.query) {{
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({{ state: Notification.permission }}) :
                        originalQuery(parameters)
                );
            }}
            
            // Plugin array spoofing
            Object.defineProperty(navigator, 'plugins', {{
                get: () => [
                    {{ name: 'PDF Viewer', filename: 'internal-pdf-viewer' }},
                    {{ name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer' }},
                    {{ name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer' }},
                    {{ name: 'Microsoft Edge PDF Viewer', filename: 'internal-pdf-viewer' }},
                    {{ name: 'WebKit built-in PDF', filename: 'internal-pdf-viewer' }}
                ],
                enumerable: true
            }});
            
            console.log('[Main Window] Navigator spoofed:', {{
                platform: navigator.platform,
                hardwareConcurrency: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory,
                webdriver: navigator.webdriver
            }});
        """
        
        await context.add_init_script(main_window_spoof)
        logger.info("✅ Main window navigator spoofing applied")
        
        # 2. Route-based worker script interception
        worker_injection = self._get_worker_injection_code(mobile_config)
        
        async def handle_route(route, request):
            """Intercept and modify worker scripts"""
            url = request.url
            resource_type = request.resource_type
            
            # Check if this is a worker script request
            is_worker = (
                resource_type == 'worker' or
                'worker' in url.lower() or
                url.endswith('.worker.js') or
                'creepjs/tests/workers' in url
            )
            
            if is_worker:
                try:
                    logger.info(f"🔧 Intercepting worker script: {url}")
                    
                    # Fetch original script
                    response = await context.request.fetch(url)
                    original_script = await response.text()
                    
                    # Prepend injection code
                    modified_script = worker_injection + '\n\n' + original_script
                    
                    # Return modified script
                    await route.fulfill(
                        status=200,
                        content_type='application/javascript; charset=utf-8',
                        body=modified_script
                    )
                    logger.info(f"✅ Worker injection successful: {url}")
                    
                except Exception as browser_error:
                if "rate limit" in str(browser_error).lower():
                    logger.warning("Camoufox rate limited, using fallback")
                    return await self._test_camoufox_fallback(url, url_name, proxy_config, mobile_config, wait_time)
                else:
                    raise browser_error
                    
        except Exception as e:
            logger.error(f"Camoufox test failed: {str(e)}")
            return TestResult(
                library="camoufox",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=str(e)[:200],
                execution_time=time.time() - start_time
            )
    
    async def _test_camoufox_fallback(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int
    ) -> TestResult:
        """Firefox fallback for Camoufox when main method fails"""
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
                
                context = await browser.new_context(
                    viewport=mobile_config.get('viewport'),
                    user_agent=mobile_config.get('user_agent'),
                    locale='en-US',
                    timezone_id=timezone
                )
                
                page = await context.new_page()
                
                # Apply worker spoofing
                worker_injection = self._get_worker_injection_code(mobile_config)
                
                async def handle_route(route, request):
                    if 'worker' in request.url.lower():
                        try:
                            response = await context.request.fetch(request.url)
                            original = await response.text()
                            modified = worker_injection + '\n\n' + original
                            await route.fulfill(
                                status=200,
                                content_type='application/javascript',
                                body=modified
                            )
                        except:
                            await route.continue_()
                    else:
                        await route.continue_()
                
                await page.route('**/*', handle_route)
                await page.goto(url, timeout=30000)
                await asyncio.sleep(wait_time)
                
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"camoufox_fallback_{url_name}_{timestamp}.png"
                filepath = Path("test_results/screenshots") / filename
                filepath.parent.mkdir(parents=True, exist_ok=True)
                
                await page.screenshot(path=str(filepath), full_page=True)
                user_agent = await page.evaluate('navigator.userAgent')
                
                detected_ip = None
                if "pixelscan.net/ip" in url:
                    detected_ip = await self._extract_ip_from_page(page)
                
                await browser.close()
                
                return TestResult(
                    library="camoufox",
                    category="playwright",
                    test_name=url_name,
                    url=url,
                    success=True,
                    detected_ip=detected_ip,
                    user_agent=user_agent,
                    is_mobile_ua=self._check_mobile_ua(user_agent or ''),
                    proxy_working=self._check_proxy_working(detected_ip, proxy_config),
                    screenshot_path=str(filepath),
                    execution_time=time.time() - start_time,
                    additional_data={'fallback': 'firefox', 'worker_spoofing': 'route-based'}
                )
                
        except Exception as e:
            logger.error(f"Firefox fallback failed: {str(e)}")
            if browser:
                try:
                    await browser.close()
                except:
                    pass
            
            return TestResult(
                library="camoufox",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=f"Fallback failed: {str(e)[:150]}",
                execution_time=time.time() - start_time
            )
    
    async def _extract_ip_from_page(self, page) -> Optional[str]:
        """Extract IP address from page with multiple strategies"""
        try:
            # Wait for IP to appear
            await page.wait_for_selector('text=/\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}/', timeout=5000)
            
            # Try multiple selectors
            selectors = [
                'div.ip-address',
                'span.ip',
                'code',
                'pre',
                'div[class*="ip"]',
                'span[class*="address"]'
            ]
            
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        ip_match = re.search(r'\\b(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})\\b', text)
                        if ip_match:
                            detected_ip = ip_match.group(1)
                            logger.info(f"Found IP via selector '{selector}': {detected_ip}")
                            return detected_ip
                except:
                    continue
            
            # Fallback to page content search
            page_content = await page.content()
            all_ips = re.findall(r'\\b(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})\\b', page_content)
            
            if all_ips:
                # Filter out private/local IPs
                public_ips = [
                    ip for ip in all_ips 
                    if not ip.startswith(('127.', '192.168.', '10.', '172.16.', '172.17.', 
                                         '172.18.', '172.19.', '172.20.', '172.21.', 
                                         '172.22.', '172.23.', '172.24.', '172.25.',
                                         '172.26.', '172.27.', '172.28.', '172.29.',
                                         '172.30.', '172.31.', '0.0.0.0'))
                ]
                
                if public_ips:
                    detected_ip = public_ips[0]
                    logger.info(f"Found IP via content search: {detected_ip}")
                    return detected_ip
                    
        except Exception as e:
            logger.warning(f"IP extraction failed: {e}")
        
        return None
    
    async def _extract_detection_data(self, page, url: str):
        """Extract IP and user agent detection data with improved logic"""
        detected_ip = None
        user_agent = None
        
        try:
            user_agent = await page.evaluate('navigator.userAgent')
            
            if "pixelscan.net/ip" in url:
                detected_ip = await self._extract_ip_from_page(page)
                
        except Exception as e:
            logger.warning(f"Could not extract detection data: {str(e)}")
            
        return detected_ip, user_agent
    
    def _check_proxy_working(self, detected_ip: Optional[str], proxy_config: Dict[str, str]) -> bool:
        """Check if proxy is working with exact match"""
        if not detected_ip:
            return False
        
        proxy_ip = proxy_config.get('host')
        if not proxy_ip:
            return False
        
        # Exact match (not substring)
        is_working = detected_ip == proxy_ip
        
        if is_working:
            logger.info(f"Proxy working: {detected_ip} == {proxy_ip}")
        else:
            logger.warning(f"Proxy mismatch: {detected_ip} != {proxy_ip}")
        
        return is_working
    
    def _check_mobile_ua(self, user_agent: str) -> bool:
        """Check if user agent indicates mobile device"""
        if not user_agent:
            return False
        
        mobile_indicators = ['Mobile', 'Android', 'iPhone', 'iPad', 'iPod']
        return any(indicator in user_agent for indicator in mobile_indicators) e:
                    logger.error(f"❌ Worker interception failed for {url}: {e}")
                    await route.continue_()
            else:
                await route.continue_()
        
        # Register route handler
        await page.route('**/*', handle_route)
        logger.info("✅ Route-based worker interception enabled")
        
        # 3. Apply playwright-stealth v1.0.6
        if self.stealth_available:
            try:
                from playwright_stealth import stealth_async
                await stealth_async(page)  # Apply to page, not context
                logger.info("✅ Playwright-stealth v1.0.6 applied")
            except Exception as e:
                logger.warning(f"⚠️ Playwright-stealth failed: {e}")
        
        logger.info("✅ Enhanced stealth fully applied")
    
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
                library=library_name,
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=f"Unknown Playwright library: {library_name}"
            )
        
        return await test_method(url, url_name, proxy_config, mobile_config, wait_time)
    
    async def _test_playwright_stealth(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int
    ) -> TestResult:
        """Test Playwright with stealth plugin (v1.0.6) and worker spoofing"""
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
                        '--disable-gpu'
                    ]
                )
                
                # Get timezone from device profile
                timezone = mobile_config.get('timezone', 'Europe/Paris')
                
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
                
                # Apply enhanced stealth with worker spoofing
                await self._apply_enhanced_stealth(page, context, mobile_config)
                
                try:
                    await page.goto(url, timeout=30000, wait_until='networkidle')
                except:
                    await page.goto(url, timeout=30000, wait_until='domcontentloaded')
                
                # Extra wait for workers to initialize
                await asyncio.sleep(3)
                
                screenshot_path = await self.screenshot_engine.capture_with_wait(
                    browser, "playwright-stealth", url_name, wait_time, page
                )
                
                detected_ip, user_agent = await self._extract_detection_data(page, url)
                
                await browser.close()
                
                return TestResult(
                    library="playwright-stealth",
                    category="playwright",
                    test_name=url_name,
                    url=url,
                    success=True,
                    detected_ip=detected_ip,
                    user_agent=user_agent,
                    is_mobile_ua=self._check_mobile_ua(user_agent or mobile_config.get('user_agent', '')),
                    proxy_working=self._check_proxy_working(detected_ip, proxy_config),
                    screenshot_path=screenshot_path,
                    execution_time=time.time() - start_time,
                    additional_data={
                        'worker_spoofing': 'route-based',
                        'stealth_plugin': 'v1.0.6'
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
                library="playwright-stealth",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=str(e)[:200],
                execution_time=time.time() - start_time
            )
    
    async def _test_playwright_basic(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str], 
        mobile_config: Dict[str, Any],
        wait_time: int
    ) -> TestResult:
        """Test native Playwright with worker spoofing (no stealth plugin)"""
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
                    args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
                )
                
                timezone = mobile_config.get('timezone', 'Europe/Paris')
                
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
                
                # Apply enhanced stealth
                await self._apply_enhanced_stealth(page, context, mobile_config)
                
                try:
                    await page.goto(url, timeout=30000, wait_until='networkidle')
                except:
                    await page.goto(url, timeout=30000, wait_until='domcontentloaded')
                
                await asyncio.sleep(3)
                
                screenshot_path = await self.screenshot_engine.capture_with_wait(
                    browser, "playwright", url_name, wait_time, page
                )
                
                detected_ip, user_agent = await self._extract_detection_data(page, url)
                
                await browser.close()
                
                return TestResult(
                    library="playwright",
                    category="playwright",
                    test_name=url_name,
                    url=url,
                    success=True,
                    detected_ip=detected_ip,
                    user_agent=user_agent,
                    is_mobile_ua=self._check_mobile_ua(user_agent or mobile_config.get('user_agent', '')),
                    proxy_working=self._check_proxy_working(detected_ip, proxy_config),
                    screenshot_path=screenshot_path,
                    execution_time=time.time() - start_time,
                    additional_data={'worker_spoofing': 'route-based'}
                )
                
        except Exception as e:
            logger.error(f"Playwright test failed: {str(e)}")
            if browser:
                try:
                    await browser.close()
                except:
                    pass
            
            return TestResult(
                library="playwright",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=str(e)[:200],
                execution_time=time.time() - start_time
            )
    
    async def _test_patchright(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int
    ) -> TestResult:
        """Test Patchright with worker spoofing"""
        start_time = time.time()
        browser = None
        
        try:
            try:
                from patchright.async_api import async_playwright
            except ImportError:
                return TestResult(
                    library="patchright",
                    category="playwright",
                    test_name=url_name,
                    url=url,
                    success=False,
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
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                timezone = mobile_config.get('timezone', 'Europe/Paris')
                
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
                
                # Apply worker spoofing
                await self._apply_enhanced_stealth(page, context, mobile_config)
                
                try:
                    await page.goto(url, timeout=30000, wait_until='networkidle')
                except:
                    await page.goto(url, timeout=30000, wait_until='domcontentloaded')
                
                await asyncio.sleep(3)
                
                screenshot_path = await self.screenshot_engine.capture_with_wait(
                    browser, "patchright", url_name, wait_time, page
                )
                
                detected_ip, user_agent = await self._extract_detection_data(page, url)
                
                await browser.close()
                
                return TestResult(
                    library="patchright",
                    category="playwright",
                    test_name=url_name,
                    url=url,
                    success=True,
                    detected_ip=detected_ip,
                    user_agent=user_agent,
                    is_mobile_ua=self._check_mobile_ua(user_agent or mobile_config.get('user_agent', '')),
                    proxy_working=self._check_proxy_working(detected_ip, proxy_config),
                    screenshot_path=screenshot_path,
                    execution_time=time.time() - start_time,
                    additional_data={'worker_spoofing': 'route-based'}
                )
                
        except Exception as e:
            logger.error(f"Patchright test failed: {str(e)}")
            if browser:
                try:
                    await browser.close()
                except:
                    pass
            
            return TestResult(
                library="patchright",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=str(e)[:200],
                execution_time=time.time() - start_time
            )
    
    async def _test_camoufox(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int
    ) -> TestResult:
        """Test Camoufox - Firefox-based with geoip support"""
        start_time = time.time()
        
        try:
            os.environ['CAMOUFOX_SKIP_AUTO_UPDATE'] = 'true'
            os.environ['NO_GITHUB_API'] = 'true'
            
            try:
                from camoufox.async_api import AsyncCamoufox
            except ImportError:
                return TestResult(
                    library="camoufox",
                    category="playwright",
                    test_name=url_name,
                    url=url,
                    success=False,
                    error="Camoufox not installed"
                )
            
            proxy = None
            if proxy_config.get('host'):
                proxy = {
                    'server': f"{proxy_config['host']}:{proxy_config['port']}",
                    'username': proxy_config.get('username'),
                    'password': proxy_config.get('password')
                }
            
            logger.info(f"Testing Camoufox (Firefox) on {url_name}")
            
            try:
                async with AsyncCamoufox(
                    headless=True,
                    proxy=proxy,
                    geoip=True,  # FIXED: Enable GeoIP to prevent leaks
                    humanize=True,
                    block_images=False
                ) as browser:
                    timezone = mobile_config.get('timezone', 'Europe/Paris')
                    
                    context = await browser.new_context(
                        viewport={'width': mobile_config['viewport']['width'], 
                                 'height': mobile_config['viewport']['height']},
                        user_agent=mobile_config.get('user_agent'),
                        locale='en-US',
                        timezone_id=timezone
                    )
                    
                    # Firefox worker spoofing (route-based)
                    page = await context.new_page()
                    
                    # Apply worker interception
                    worker_injection = self._get_worker_injection_code(mobile_config)
                    
                    async def handle_firefox_route(route, request):
                        url_str = request.url
                        if 'worker' in url_str.lower() or request.resource_type == 'worker':
                            try:
                                response = await context.request.fetch(url_str)
                                original = await response.text()
                                modified = worker_injection + '\n\n' + original
                                await route.fulfill(
                                    status=200,
                                    content_type='application/javascript',
                                    body=modified
                                )
                                logger.info(f"✅ Firefox worker intercepted: {url_str}")
                            except:
                                await route.continue_()
                        else:
                            await route.continue_()
                    
                    await page.route('**/*', handle_firefox_route)
                    
                    await page.goto(url, timeout=30000)
                    await asyncio.sleep(wait_time + 3)
                    
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"camoufox_{url_name}_{timestamp}.png"
                    filepath = Path("test_results/screenshots") / filename
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    
                    await page.screenshot(path=str(filepath), full_page=True)
                    
                    user_agent = await page.evaluate('navigator.userAgent')
                    detected_ip = None
                    
                    if "pixelscan.net/ip" in url:
                        detected_ip = await self._extract_ip_from_page(page)
                    
                    await context.close()
                    
                    return TestResult(
                        library="camoufox",
                        category="playwright",
                        test_name=url_name,
                        url=url,
                        success=True,
                        detected_ip=detected_ip,
                        user_agent=user_agent,
                        is_mobile_ua=self._check_mobile_ua(user_agent or ''),
                        proxy_working=self._check_proxy_working(detected_ip, proxy_config),
                        screenshot_path=str(filepath),
                        execution_time=time.time() - start_time,
                        additional_data={
                            'worker_spoofing': 'route-based',
                            'engine': 'firefox',
                            'geoip': 'enabled'
                        }
                    )
                    
            except Exception as
