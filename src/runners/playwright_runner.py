"""
PLAYWRIGHT CATEGORY RUNNER - Enhanced Worker Context Spoofing
Handles all Playwright-based stealth libraries with worker fingerprint spoofing

Authors: kravitzcoder & MiniMax Agent
"""
import asyncio
import json
import time
import os
from typing import Dict, Any, Optional
import logging
from pathlib import Path

from ..core.test_result import TestResult

logger = logging.getLogger(__name__)


class PlaywrightRunner:
    """Runner for Playwright-based stealth libraries with worker spoofing"""
    
    def __init__(self, screenshot_engine):
        self.screenshot_engine = screenshot_engine
        logger.info("Playwright runner initialized with worker spoofing")
        self.stealth_available = self._verify_stealth_plugin()
    
    def _verify_stealth_plugin(self) -> bool:
        """Verify playwright-stealth is properly installed"""
        try:
            import playwright_stealth
            logger.info(f"playwright-stealth available")
            return True
        except ImportError:
            logger.warning("playwright-stealth NOT available")
            return False
    
    def _get_worker_spoofing_script(self, mobile_config: Dict[str, Any]) -> str:
        """
        Generate comprehensive worker spoofing script
        This intercepts ALL worker types and spoofs their navigator properties
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
        
        # Determine timezone from config or default to UTC
        timezone = 'Europe/Paris'  # Matching your screenshots
        language = 'en-US'
        languages = ['en-US', 'en']
        
        script = f"""
        // ===== COMPREHENSIVE WORKER SPOOFING =====
        // This script intercepts Worker, SharedWorker, and ServiceWorker creation
        
        const SPOOFED_CONFIG = {{
            userAgent: '{user_agent}',
            platform: '{platform}',
            hardwareConcurrency: {hardware},
            timezone: '{timezone}',
            language: '{language}',
            languages: {json.dumps(languages)}
        }};
        
        // Generate worker injection code
        function generateWorkerInjectionCode() {{
            return `
                // Worker context spoofing - injected before worker script
                (function() {{
                    'use strict';
                    
                    const config = ${{JSON.stringify(SPOOFED_CONFIG)}};
                    
                    // Spoof navigator properties with proper descriptors
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
                    
                    // Timezone spoofing via Date methods
                    const OriginalDate = Date;
                    const tzOffset = -120; // Europe/Paris offset in minutes (UTC+2)
                    
                    Date = class extends OriginalDate {{
                        constructor(...args) {{
                            super(...args);
                        }}
                        
                        getTimezoneOffset() {{
                            return tzOffset;
                        }}
                        
                        toLocaleString(...args) {{
                            return super.toLocaleString(...args).replace(/GMT[+-]\\d{{4}}/, 'GMT+0200');
                        }}
                    }};
                    
                    Date.prototype = OriginalDate.prototype;
                    Date.now = OriginalDate.now;
                    Date.parse = OriginalDate.parse;
                    Date.UTC = OriginalDate.UTC;
                    
                    // Intl.DateTimeFormat timezone spoofing
                    if (typeof Intl !== 'undefined' && Intl.DateTimeFormat) {{
                        const OriginalDateTimeFormat = Intl.DateTimeFormat;
                        Intl.DateTimeFormat = function(...args) {{
                            if (!args[1]) args[1] = {{}};
                            if (!args[1].timeZone) args[1].timeZone = config.timezone;
                            return new OriginalDateTimeFormat(...args);
                        }};
                        Intl.DateTimeFormat.prototype = OriginalDateTimeFormat.prototype;
                    }}
                    
                    console.log('[Worker Spoof] Navigator properties spoofed:', {{
                        userAgent: self.navigator.userAgent,
                        platform: self.navigator.platform,
                        hardwareConcurrency: self.navigator.hardwareConcurrency,
                        language: self.navigator.language,
                        languages: self.navigator.languages
                    }});
                }})();
            `;
        }}
        
        // ===== DEDICATED WORKER INTERCEPTION =====
        if (typeof Worker !== 'undefined') {{
            const OriginalWorker = Worker;
            
            window.Worker = class extends OriginalWorker {{
                constructor(scriptURL, options) {{
                    const injectionCode = generateWorkerInjectionCode();
                    
                    // Create blob with injection code + original script
                    const blob = new Blob([
                        injectionCode,
                        `\\nimportScripts("${{scriptURL}}");`
                    ], {{ type: 'application/javascript' }});
                    
                    const blobURL = URL.createObjectURL(blob);
                    super(blobURL, options);
                    
                    console.log('[Main] Dedicated Worker intercepted:', scriptURL);
                }}
            }};
            
            // Preserve prototype
            window.Worker.prototype = OriginalWorker.prototype;
        }}
        
        // ===== SHARED WORKER INTERCEPTION =====
        if (typeof SharedWorker !== 'undefined') {{
            const OriginalSharedWorker = SharedWorker;
            
            window.SharedWorker = class extends OriginalSharedWorker {{
                constructor(scriptURL, options) {{
                    const injectionCode = generateWorkerInjectionCode();
                    
                    const blob = new Blob([
                        injectionCode,
                        `\\nimportScripts("${{scriptURL}}");`
                    ], {{ type: 'application/javascript' }});
                    
                    const blobURL = URL.createObjectURL(blob);
                    super(blobURL, options);
                    
                    console.log('[Main] Shared Worker intercepted:', scriptURL);
                }}
            }};
            
            window.SharedWorker.prototype = OriginalSharedWorker.prototype;
        }}
        
        // ===== SERVICE WORKER INTERCEPTION =====
        // Service workers are more challenging - intercept registration
        if (navigator.serviceWorker) {{
            const originalRegister = navigator.serviceWorker.register;
            
            navigator.serviceWorker.register = function(scriptURL, options) {{
                console.log('[Main] Service Worker registration intercepted:', scriptURL);
                
                // Fetch original worker script
                return fetch(scriptURL)
                    .then(response => response.text())
                    .then(scriptContent => {{
                        const injectionCode = generateWorkerInjectionCode();
                        const modifiedScript = injectionCode + '\\n' + scriptContent;
                        
                        const blob = new Blob([modifiedScript], {{ type: 'application/javascript' }});
                        const blobURL = URL.createObjectURL(blob);
                        
                        return originalRegister.call(this, blobURL, options);
                    }})
                    .catch(err => {{
                        console.warn('[Main] Service Worker interception failed:', err);
                        return originalRegister.call(this, scriptURL, options);
                    }});
            }};
        }}
        
        console.log('[Main] Worker spoofing initialized');
        """
        
        return script
    
    async def _apply_enhanced_stealth(self, page, context, mobile_config: Dict[str, Any]):
        """Apply enhanced stealth including worker spoofing"""
        
        # Determine platform from user agent
        user_agent = mobile_config.get('user_agent', '')
        if 'iPhone' in user_agent or 'iPad' in user_agent:
            platform = 'iPhone'
        elif 'Android' in user_agent:
            platform = 'Linux armv8l'
        else:
            platform = 'iPhone'
        
        hardware = mobile_config.get('hardware_concurrency', 8)
        
        # 1. CRITICAL: Main window navigator spoofing FIRST
        main_window_spoof = f"""
            // MAIN WINDOW NAVIGATOR SPOOFING - Must run before everything
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
                get: () => 8,
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
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({{ state: Notification.permission }}) :
                    originalQuery(parameters)
            );
            
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
            
            // Language consistency
            Object.defineProperty(navigator, 'language', {{
                get: () => 'en-US',
                enumerable: true
            }});
            
            Object.defineProperty(navigator, 'languages', {{
                get: () => ['en-US', 'en'],
                enumerable: true
            }});
            
            console.log('[Main Window] Navigator spoofed:', {{
                platform: navigator.platform,
                hardwareConcurrency: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory
            }});
        """
        
        await context.add_init_script(main_window_spoof)
        logger.info("Main window navigator spoofing applied")
        
        # 2. Add worker spoofing script
        worker_script = self._get_worker_spoofing_script(mobile_config)
        await context.add_init_script(worker_script)
        logger.info("Worker spoofing script injected")
        
        # 3. Apply playwright-stealth if available (after our spoofing)
        if self.stealth_available:
            try:
                from playwright_stealth import stealth_async
                await stealth_async(context)
                logger.info("Playwright-stealth applied")
            except Exception as e:
                logger.warning(f"Playwright-stealth failed: {e}")
        
        logger.info("Enhanced stealth fully applied")
    
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
        """Test Playwright with enhanced worker spoofing"""
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
            
            logger.info(f"Testing Playwright-Stealth (Enhanced) on {url_name}")
            
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
                
                context = await browser.new_context(
                    viewport=mobile_config.get('viewport', {'width': 375, 'height': 812}),
                    user_agent=mobile_config.get('user_agent'),
                    device_scale_factor=mobile_config.get('device_scale_factor', 2.0),
                    is_mobile=mobile_config.get('is_mobile', True),
                    has_touch=mobile_config.get('has_touch', True),
                    locale='en-US',
                    timezone_id='Europe/Paris'
                )
                
                page = await context.new_page()
                
                # Apply enhanced stealth with worker spoofing
                await self._apply_enhanced_stealth(page, context, mobile_config)
                
                try:
                    await page.goto(url, timeout=30000, wait_until='networkidle')
                except:
                    await page.goto(url, timeout=30000, wait_until='domcontentloaded')
                
                # Wait for workers to initialize
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
                    additional_data={'worker_spoofing': 'enabled'}
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
        """Test native Playwright with worker spoofing"""
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
            
            logger.info(f"Testing Playwright (Enhanced) on {url_name}")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    proxy=proxy_setup,
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
                )
                
                context = await browser.new_context(
                    viewport=mobile_config.get('viewport', {'width': 375, 'height': 812}),
                    user_agent=mobile_config.get('user_agent'),
                    device_scale_factor=mobile_config.get('device_scale_factor', 2.0),
                    is_mobile=mobile_config.get('is_mobile', True),
                    has_touch=mobile_config.get('has_touch', True),
                    locale='en-US',
                    timezone_id='Europe/Paris'
                )
                
                page = await context.new_page()
                
                # Apply enhanced stealth (CRITICAL - was missing)
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
                    additional_data={'worker_spoofing': 'enabled'}
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
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    proxy=proxy_setup,
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                context = await browser.new_context(
                    viewport=mobile_config.get('viewport', {'width': 375, 'height': 812}),
                    user_agent=mobile_config.get('user_agent'),
                    device_scale_factor=mobile_config.get('device_scale_factor', 2.0),
                    is_mobile=mobile_config.get('is_mobile', True),
                    has_touch=mobile_config.get('has_touch', True),
                    locale='en-US',
                    timezone_id='Europe/Paris'
                )
                
                page = await context.new_page()
                
                # Apply worker spoofing
                worker_script = self._get_worker_spoofing_script(mobile_config)
                await context.add_init_script(worker_script)
                
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
                    additional_data={'worker_spoofing': 'enabled'}
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
        """Test Camoufox - Firefox-based, different worker handling"""
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
            
            try:
                async with AsyncCamoufox(
                    headless=True,
                    proxy=proxy,
                    geoip=False,
                    block_images=False
                ) as browser:
                    context = await browser.new_context(
                        viewport={'width': mobile_config['viewport']['width'], 
                                 'height': mobile_config['viewport']['height']},
                        user_agent=mobile_config.get('user_agent'),
                        locale='en-US',
                        timezone_id='Europe/Paris'
                    )
                    
                    # Firefox worker spoofing (slightly different syntax)
                    firefox_worker_script = self._get_worker_spoofing_script(mobile_config)
                    await context.add_init_script(firefox_worker_script)
                    
                    page = await context.new_page()
                    await page.goto(url, timeout=30000)
                    await asyncio.sleep(wait_time + 3)  # Extra time for workers
                    
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"camoufox_{url_name}_{timestamp}.png"
                    filepath = Path("test_results/screenshots") / filename
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    
                    await page.screenshot(path=str(filepath), full_page=True)
                    
                    user_agent = await page.evaluate('navigator.userAgent')
                    detected_ip = None
                    
                    if "pixelscan.net/ip" in url:
                        try:
                            await asyncio.sleep(2)
                            page_content = await page.content()
                            import re
                            ip_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', page_content)
                            if ip_match:
                                detected_ip = ip_match.group(0)
                        except:
                            pass
                    
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
                        additional_data={'worker_spoofing': 'enabled', 'engine': 'firefox'}
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
        """Firefox fallback for Camoufox"""
        from playwright.async_api import async_playwright
        
        proxy_setup = {
            "server": f"http://{proxy_config['host']}:{proxy_config['port']}"
        }
        
        if proxy_config.get('username') and proxy_config.get('password'):
            proxy_setup["username"] = proxy_config['username']
            proxy_setup["password"] = proxy_config['password']
        
        async with async_playwright() as p:
            browser = await p.firefox.launch(proxy=proxy_setup, headless=True)
            context = await browser.new_context(
                viewport=mobile_config.get('viewport'),
                user_agent=mobile_config.get('user_agent')
            )
            
            # Apply worker spoofing
            worker_script = self._get_worker_spoofing_script(mobile_config)
            await context.add_init_script(worker_script)
            
            page = await context.new_page()
            await page.goto(url, timeout=30000)
            await asyncio.sleep(wait_time)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"camoufox_fallback_{url_name}_{timestamp}.png"
            filepath = Path("test_results/screenshots") / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            await page.screenshot(path=str(filepath), full_page=True)
            user_agent = await page.evaluate('navigator.userAgent')
            
            await browser.close()
            
            return TestResult(
                library="camoufox",
                category="playwright",
                test_name=url_name,
                url=url,
                success=True,
                user_agent=user_agent,
                is_mobile_ua=self._check_mobile_ua(user_agent or ''),
                screenshot_path=str(filepath),
                execution_time=time.time() - time.time(),
                additional_data={'fallback': 'firefox', 'worker_spoofing': 'enabled'}
            )
    
    async def _extract_detection_data(self, page, url: str):
        """Extract IP and user agent detection data"""
        detected_ip = None
        user_agent = None
        
        try:
            user_agent = await page.evaluate('navigator.userAgent')
            
            if "pixelscan.net/ip" in url:
                try:
                    await asyncio.sleep(3)
                    page_content = await page.content()
                    import re
                    ip_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', page_content)
                    if ip_match:
                        detected_ip = ip_match.group(0)
                except:
                    pass
                
        except Exception as e:
            logger.warning(f"Could not extract detection data: {str(e)}")
            
        return detected_ip, user_agent
    
    def _check_proxy_working(self, detected_ip: str, proxy_config: Dict[str, str]) -> bool:
        """Check if proxy is working"""
        if not detected_ip:
            return False
        proxy_ip = proxy_config.get('host')
        return proxy_ip in detected_ip if proxy_ip else False
    
    def _check_mobile_ua(self, user_agent: str) -> bool:
        """Check if user agent indicates mobile"""
        mobile_indicators = ['Mobile', 'Android', 'iPhone', 'iPad', 'iPod']
        return any(indicator in user_agent for indicator in mobile_indicators)
