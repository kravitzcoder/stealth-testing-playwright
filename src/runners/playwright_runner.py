"""
STEALTH BROWSER TESTING FRAMEWORK - Playwright Runner (COMPLETE)
Handles all 4 Playwright-based libraries with enhanced worker spoofing

Authors: kravitzcoder & MiniMax Agent
Repository: https://github.com/kravitzcoder/stealth-testing-playwright

Libraries supported:
- playwright (manual stealth)
- patchright (patched fork)
- camoufox (Firefox-based)
- rebrowser_playwright (commercial-grade)
"""

import logging
import asyncio
import time
import re
import json
from typing import Dict, Any, Optional
from pathlib import Path

from ..core.test_result import TestResult
from ..core.screenshot_engine import ScreenshotEngine
from ..utils.device_profile_loader import DeviceProfileLoader
from ..utils.fingerprint_injector import generate_fingerprint_script

logger = logging.getLogger(__name__)


class PlaywrightRunner:
    """Runner for Playwright-based stealth browser libraries"""
    
    def __init__(self, screenshot_engine: Optional[ScreenshotEngine] = None):
        """
        Initialize Playwright runner
        
        Args:
            screenshot_engine: Screenshot engine instance (optional)
        """
        self.screenshot_engine = screenshot_engine or ScreenshotEngine()
        self.profile_loader = DeviceProfileLoader()
        
        # Optional GeoIP support (graceful degradation if not available)
        self.geoip = None
        try:
            import pygeoip
            geoip_path = Path(__file__).parent.parent.parent / "profiles" / "GeoLiteCity.dat"
            if geoip_path.exists():
                self.geoip = pygeoip.GeoIP(str(geoip_path))
                logger.info("✅ GeoIP database loaded for location spoofing")
            else:
                logger.info("ℹ️ GeoIP database not found (optional feature)")
        except ImportError:
            logger.info("ℹ️ pygeoip not installed (optional feature)")
        except Exception as e:
            logger.warning(f"⚠️ Could not load GeoIP database: {e}")
        
        logger.info("Playwright runner initialized with ENHANCED worker spoofing")
        logger.info("🎭 Supported libraries: playwright, patchright, camoufox, rebrowser_playwright")
    
    async def run_test(
        self,
        library_name: str,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 30
    ) -> TestResult:
        """
        Run test for a Playwright library
        
        Args:
            library_name: Name of library (playwright, patchright, camoufox, rebrowser_playwright)
            url: Target URL to test
            url_name: Name of the test
            proxy_config: Proxy configuration dict
            mobile_config: Mobile device configuration
            wait_time: Wait time before screenshot
        
        Returns:
            TestResult object with test results
        """
        start_time = time.time()
        logger.info(f"🎭 Testing {library_name} on {url_name}: {url}")
        
        try:
            # Route to appropriate library handler
            if library_name == "playwright":
                result = await self._run_playwright(
                    url, url_name, proxy_config, mobile_config, wait_time
                )
            elif library_name == "patchright":
                result = await self._run_patchright(
                    url, url_name, proxy_config, mobile_config, wait_time
                )
            elif library_name == "camoufox":
                result = await self._run_camoufox(
                    url, url_name, proxy_config, mobile_config, wait_time
                )
            elif library_name == "rebrowser_playwright":
                result = await self._run_rebrowser(
                    url, url_name, proxy_config, mobile_config, wait_time
                )
            else:
                raise ValueError(f"Unknown library: {library_name}")
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            logger.info(f"✅ Test completed for {library_name}/{url_name} in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)[:500]
            logger.error(f"❌ Test failed for {library_name}/{url_name}: {error_msg}")
            
            return TestResult(
                library=library_name,
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
    
    async def _run_playwright(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int
    ) -> TestResult:
        """Run test using native Playwright with manual stealth"""
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            proxy_url = self._build_proxy_url(proxy_config)
            
            browser = await p.chromium.launch(
                headless=True,
                proxy={"server": proxy_url} if proxy_url else None
            )
            
            context = await browser.new_context(
                user_agent=mobile_config.get("user_agent"),
                viewport=mobile_config.get("viewport"),
                device_scale_factor=mobile_config.get("device_scale_factor", 2),
                is_mobile=mobile_config.get("is_mobile", True),
                has_touch=mobile_config.get("has_touch", True),
                locale=mobile_config.get("language", "en-US").replace("_", "-"),
                timezone_id=mobile_config.get("timezone", "America/New_York")
            )
            
            # Apply enhanced stealth
            await context.route("**/*", lambda route: self._enhanced_worker_interceptor(
                route, mobile_config
            ))
            
            await self._apply_enhanced_stealth(context, mobile_config)
            
            page = await context.new_page()
            
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Extra wait for worker-heavy pages
            if "creepjs" in url.lower() or "worker" in url_name.lower():
                logger.info("⏳ Extra 15s wait for worker analysis pages")
                await asyncio.sleep(15)
            
            # Capture screenshot (may skip if timeout)
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "playwright", url_name, wait_time, page=page
            )
            
            # Analyze results
            proxy_working, detected_ip = await self._check_proxy_status(page, proxy_config)
            is_mobile = await self._check_mobile_ua(page, mobile_config)
            
            await browser.close()
            
            return TestResult(
                library="playwright",
                category="playwright",
                test_name=url_name,
                url=url,
                success=True,
                detected_ip=detected_ip,
                user_agent=mobile_config.get("user_agent"),
                proxy_working=proxy_working,
                is_mobile_ua=is_mobile,
                screenshot_path=screenshot_path,
                execution_time=0
            )
    
    async def _run_patchright(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int
    ) -> TestResult:
        """Run test using Patchright (patched Playwright fork)"""
        try:
            from patchright.async_api import async_playwright
        except ImportError:
            raise ImportError("patchright not installed. Run: pip install patchright")
        
        async with async_playwright() as p:
            proxy_url = self._build_proxy_url(proxy_config)
            
            browser = await p.chromium.launch(
                headless=True,
                proxy={"server": proxy_url} if proxy_url else None
            )
            
            context = await browser.new_context(
                user_agent=mobile_config.get("user_agent"),
                viewport=mobile_config.get("viewport"),
                device_scale_factor=mobile_config.get("device_scale_factor", 2),
                is_mobile=mobile_config.get("is_mobile", True),
                has_touch=mobile_config.get("has_touch", True),
                locale=mobile_config.get("language", "en-US").replace("_", "-"),
                timezone_id=mobile_config.get("timezone", "America/New_York")
            )
            
            await context.route("**/*", lambda route: self._enhanced_worker_interceptor(
                route, mobile_config
            ))
            
            await self._apply_enhanced_stealth(context, mobile_config)
            
            page = await context.new_page()
            
            logger.info(f"Navigating to {url} with Patchright")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            if "creepjs" in url.lower() or "worker" in url_name.lower():
                logger.info("⏳ Extra 15s wait for worker analysis pages")
                await asyncio.sleep(15)
            
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "patchright", url_name, wait_time, page=page
            )
            
            proxy_working, detected_ip = await self._check_proxy_status(page, proxy_config)
            is_mobile = await self._check_mobile_ua(page, mobile_config)
            
            await browser.close()
            
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
                execution_time=0
            )
    
    async def _run_camoufox(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int
    ) -> TestResult:
        """Run test using Camoufox (Firefox-based stealth browser)"""
        try:
            from camoufox.async_api import AsyncCamoufox
        except ImportError:
            raise ImportError("camoufox not installed. Run: pip install 'camoufox[geoip]'")
        
        # Build proxy configuration for Camoufox
        proxy_dict = None
        if proxy_config.get("host"):
            proxy_dict = {
                "server": f"http://{proxy_config['host']}:{proxy_config['port']}"
            }
            if proxy_config.get("username"):
                proxy_dict["username"] = proxy_config["username"]
                proxy_dict["password"] = proxy_config["password"]
        
        # Firefox mobile UA
        user_agent = "Mozilla/5.0 (Android 11; Mobile; rv:109.0) Gecko/109.0 Firefox/115.0"
        
        async with AsyncCamoufox(
            headless=True,
            proxy=proxy_dict,
            humanize=True,
            geoip=True if self.geoip else False
        ) as browser:
            
            page = await browser.new_page()
            
            await page.set_viewport_size(mobile_config.get("viewport", {"width": 375, "height": 812}))
            await page.evaluate(f"Object.defineProperty(navigator, 'userAgent', {{get: () => '{user_agent}'}})")
            
            logger.info(f"Navigating to {url} with Camoufox (Firefox)")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            if "creepjs" in url.lower() or "worker" in url_name.lower():
                logger.info("⏳ Extra 15s wait for worker analysis pages")
                await asyncio.sleep(15)
            
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "camoufox", url_name, wait_time, page=page
            )
            
            proxy_working, detected_ip = await self._check_proxy_status(page, proxy_config)
            is_mobile = await self._check_mobile_ua(page, mobile_config)
            
            await browser.close()
            
            return TestResult(
                library="camoufox",
                category="playwright",
                test_name=url_name,
                url=url,
                success=True,
                detected_ip=detected_ip,
                user_agent=user_agent,
                proxy_working=proxy_working,
                is_mobile_ua=is_mobile,
                screenshot_path=screenshot_path,
                execution_time=0
            )
    
    async def _run_rebrowser(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int
    ) -> TestResult:
        """Run test using Rebrowser Playwright (commercial-grade stealth)"""
        try:
            from rebrowser_playwright.async_api import async_playwright
        except ImportError:
            raise ImportError("rebrowser-playwright not installed. Run: pip install rebrowser-playwright")
        
        async with async_playwright() as p:
            proxy_url = self._build_proxy_url(proxy_config)
            
            # Rebrowser has built-in stealth, but we still apply manual techniques
            browser = await p.chromium.launch(
                headless=True,
                proxy={"server": proxy_url} if proxy_url else None
            )
            
            context = await browser.new_context(
                user_agent=mobile_config.get("user_agent"),
                viewport=mobile_config.get("viewport"),
                device_scale_factor=mobile_config.get("device_scale_factor", 2),
                is_mobile=mobile_config.get("is_mobile", True),
                has_touch=mobile_config.get("has_touch", True),
                locale=mobile_config.get("language", "en-US").replace("_", "-"),
                timezone_id=mobile_config.get("timezone", "America/New_York")
            )
            
            # Apply enhanced worker interception (on top of Rebrowser's built-in stealth)
            await context.route("**/*", lambda route: self._enhanced_worker_interceptor(
                route, mobile_config
            ))
            
            await self._apply_enhanced_stealth(context, mobile_config)
            
            page = await context.new_page()
            
            logger.info(f"Navigating to {url} with Rebrowser Playwright")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            if "creepjs" in url.lower() or "worker" in url_name.lower():
                logger.info("⏳ Extra 15s wait for worker analysis pages")
                await asyncio.sleep(15)
            
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "rebrowser_playwright", url_name, wait_time, page=page
            )
            
            proxy_working, detected_ip = await self._check_proxy_status(page, proxy_config)
            is_mobile = await self._check_mobile_ua(page, mobile_config)
            
            await browser.close()
            
            return TestResult(
                library="rebrowser_playwright",
                category="playwright",
                test_name=url_name,
                url=url,
                success=True,
                detected_ip=detected_ip,
                user_agent=mobile_config.get("user_agent"),
                proxy_working=proxy_working,
                is_mobile_ua=is_mobile,
                screenshot_path=screenshot_path,
                execution_time=0
            )
    
    async def _apply_enhanced_stealth(self, context, mobile_config: Dict[str, Any]) -> None:
        """Apply comprehensive stealth techniques"""
        
        # Generate enhanced init script with proper worker handling
        enhanced_script = self._generate_enhanced_init_script(mobile_config)
        
        await context.add_init_script(enhanced_script)
        
        logger.info("✅ Enhanced stealth applied (main context + workers)")
    
    def _generate_enhanced_init_script(self, mobile_config: Dict[str, Any]) -> str:
        """Generate enhanced initialization script that properly handles workers"""
        
        user_agent = mobile_config.get("user_agent", "")
        platform = mobile_config.get("platform", "iPhone")
        hardware_concurrency = mobile_config.get("hardware_concurrency", 8)
        device_memory = mobile_config.get("device_memory", 4)
        max_touch_points = mobile_config.get("max_touch_points", 5)
        
        # Escape for safe JavaScript injection
        user_agent_escaped = json.dumps(user_agent)
        
        return f"""
(function() {{
    'use strict';
    
    // Determine if we're in a Worker context
    const isWorker = typeof WorkerGlobalScope !== 'undefined' && self instanceof WorkerGlobalScope;
    const isServiceWorker = typeof ServiceWorkerGlobalScope !== 'undefined' && self instanceof ServiceWorkerGlobalScope;
    const isSharedWorker = typeof SharedWorkerGlobalScope !== 'undefined' && self instanceof SharedWorkerGlobalScope;
    
    console.log('[Stealth] Context:', isWorker ? 'Worker' : isServiceWorker ? 'ServiceWorker' : isSharedWorker ? 'SharedWorker' : 'Window');
    
    // Define properties that work in ALL contexts
    const spoofedProperties = {{
        userAgent: {user_agent_escaped},
        platform: '{platform}',
        hardwareConcurrency: {hardware_concurrency},
        deviceMemory: {device_memory},
        maxTouchPoints: {max_touch_points}
    }};
    
    // Apply navigator spoofing
    if (typeof navigator !== 'undefined') {{
        try {{
            Object.defineProperty(navigator, 'userAgent', {{
                get: () => spoofedProperties.userAgent,
                configurable: true
            }});
            
            Object.defineProperty(navigator, 'platform', {{
                get: () => spoofedProperties.platform,
                configurable: true
            }});
            
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => spoofedProperties.hardwareConcurrency,
                configurable: true
            }});
            
            if ('deviceMemory' in navigator) {{
                Object.defineProperty(navigator, 'deviceMemory', {{
                    get: () => spoofedProperties.deviceMemory,
                    configurable: true
                }});
            }}
            
            if ('maxTouchPoints' in navigator) {{
                Object.defineProperty(navigator, 'maxTouchPoints', {{
                    get: () => spoofedProperties.maxTouchPoints,
                    configurable: true
                }});
            }}
            
            // Remove webdriver property
            if ('webdriver' in navigator) {{
                delete navigator.__proto__.webdriver;
                Object.defineProperty(navigator, 'webdriver', {{
                    get: () => undefined,
                    configurable: true
                }});
            }}
            
            console.log('[Stealth] Navigator properties spoofed successfully');
        }} catch (e) {{
            console.warn('[Stealth] Some navigator properties could not be spoofed:', e.message);
        }}
    }}
    
    // Spoof canvas fingerprint consistency
    if (typeof CanvasRenderingContext2D !== 'undefined') {{
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        CanvasRenderingContext2D.prototype.getImageData = function() {{
            const imageData = originalGetImageData.apply(this, arguments);
            // Add subtle noise to make it look more natural
            for (let i = 0; i < imageData.data.length; i += 4) {{
                imageData.data[i] = imageData.data[i] ^ 1;
            }}
            return imageData;
        }};
    }}
    
    console.log('[Stealth] Enhanced stealth injection complete');
}})();
        """
    
    async def _enhanced_worker_interceptor(self, route, mobile_config: Dict[str, Any]) -> None:
        """ENHANCED worker script interceptor - properly modifies ALL worker types"""
        try:
            request = route.request
            
            # Broader detection for worker scripts
            is_worker_script = (
                request.resource_type == "script" and (
                    "worker" in request.url.lower() or
                    request.header_value("sec-fetch-dest") in ["worker", "sharedworker", "serviceworker"] or
                    request.url.endswith(".worker.js") or
                    "creepjs" in request.url.lower()
                )
            )
            
            if is_worker_script:
                logger.info(f"🔧 Intercepting worker: {request.url[-60:]}")
                
                # Fetch original response
                response = await route.fetch()
                original_body = await response.text()
                
                # Generate worker-compatible spoofing script
                worker_spoof_script = self._generate_enhanced_init_script(mobile_config)
                
                # Prepend spoofing to original script
                modified_body = worker_spoof_script + "\n\n// === Original Worker Script ===\n\n" + original_body
                
                # Remove encoding headers
                headers = {k: v for k, v in response.headers.items() 
                          if k.lower() not in ['content-encoding', 'content-length']}
                
                await route.fulfill(
                    status=response.status,
                    headers=headers,
                    body=modified_body
                )
                
                logger.info("✅ Worker script modified successfully")
                return
        
        except Exception as e:
            if "Target closed" not in str(e):
                logger.debug(f"Worker interception warning: {e}")
        
        # Continue with original request
        await route.continue_()
    
    async def _check_proxy_status(self, page, proxy_config: Dict[str, str]) -> tuple[bool, Optional[str]]:
        """Check if proxy is working"""
        try:
            content = await page.content()
            ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
            found_ips = re.findall(ip_pattern, content)
            
            if not found_ips:
                logger.warning("No IP found on page")
                return False, None
            
            detected_ip = found_ips[0]
            proxy_ip = proxy_config.get("host")
            
            if proxy_ip and detected_ip == proxy_ip:
                logger.info(f"✅ Proxy working: {detected_ip}")
                return True, detected_ip
            else:
                logger.warning(f"⚠️ IP mismatch: detected={detected_ip}, proxy={proxy_ip}")
                return False, detected_ip
        
        except Exception as e:
            logger.error(f"Error checking proxy: {e}")
            return False, None
    
    async def _check_mobile_ua(self, page, mobile_config: Dict[str, Any]) -> bool:
        """Check if mobile user agent is detected"""
        try:
            ua = await page.evaluate("navigator.userAgent")
            is_mobile = any(kw in ua.lower() for kw in ["mobile", "iphone", "android"])
            
            if is_mobile:
                logger.info(f"✅ Mobile UA: {ua[:50]}...")
            else:
                logger.warning(f"⚠️ Desktop UA: {ua[:50]}...")
            
            return is_mobile
        except Exception as e:
            logger.error(f"Error checking UA: {e}")
            return False
    
    def _build_proxy_url(self, proxy_config: Dict[str, str]) -> Optional[str]:
        """Build proxy URL from configuration"""
        if not proxy_config.get("host"):
            return None
        
        host = proxy_config["host"]
        port = proxy_config["port"]
        username = proxy_config.get("username", "")
        password = proxy_config.get("password", "")
        
        if username and password:
            return f"http://{username}:{password}@{host}:{port}"
        else:
            return f"http://{host}:{port}"
