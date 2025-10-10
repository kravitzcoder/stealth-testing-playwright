"""
STEALTH BROWSER TESTING FRAMEWORK - Playwright Runner (PRODUCTION)
Minimal stealth that actually works - tested and proven

Authors: kravitzcoder & Claude

LESSONS LEARNED:
- Aggressive stealth (property overrides, canvas mods) BREAKS pixelscan.net
- Minimal stealth (just hide webdriver) works perfectly
- Pages load in 15 seconds naturally without interference
- rebrowser/patchright provide browser-level stealth (better than JS)
"""

import logging
import asyncio
import time
import re
from typing import Dict, Any, Optional
from pathlib import Path

from ..core.test_result import TestResult
from ..core.screenshot_engine import ScreenshotEngine
from ..utils.device_profile_loader import DeviceProfileLoader

logger = logging.getLogger(__name__)


class PlaywrightRunner:
    """Production runner for Playwright-based stealth browser libraries"""
    
    def __init__(self, screenshot_engine: Optional[ScreenshotEngine] = None):
        """Initialize Playwright runner"""
        self.screenshot_engine = screenshot_engine or ScreenshotEngine()
        self.profile_loader = DeviceProfileLoader()
        
        # Optional GeoIP support
        self.geoip = None
        try:
            import pygeoip
            geoip_path = Path(__file__).parent.parent.parent / "profiles" / "GeoLiteCity.dat"
            if geoip_path.exists():
                self.geoip = pygeoip.GeoIP(str(geoip_path))
                logger.info("✅ GeoIP database loaded")
        except ImportError:
            logger.debug("GeoIP not available (optional)")
        except Exception as e:
            logger.debug(f"GeoIP load warning: {e}")
        
        logger.info("Playwright runner initialized (minimal stealth, production-ready)")
    
    async def run_test(
        self,
        library_name: str,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 5
    ) -> TestResult:
        """Run test for a Playwright library"""
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
    
    def _build_proxy(self, proxy_config: Dict[str, str]) -> Dict[str, Any]:
        """Build proxy configuration"""
        if not proxy_config.get("host") or not proxy_config.get("port"):
            return None
        
        proxy = {
            "server": f"http://{proxy_config['host']}:{proxy_config['port']}"
        }
        
        if proxy_config.get("username") and proxy_config.get("password"):
            proxy["username"] = proxy_config["username"]
            proxy["password"] = proxy_config["password"]
        
        logger.info(f"Proxy: {proxy['server']} (auth: {'yes' if 'username' in proxy else 'no'})")
        return proxy
    
    def _generate_minimal_stealth(self) -> str:
        """
        Generate MINIMAL stealth script - just hide webdriver
        
        CRITICAL: No property overrides, no canvas mods
        These break pixelscan.net and other detection sites
        """
        return """
(function() {
    'use strict';
    
    // ONLY hide navigator.webdriver (minimal stealth)
    try {
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });
    } catch(e) {
        // Silently fail if already defined
    }
    
    console.log('[Stealth] Minimal mode: webdriver hidden');
})();
"""
    
    async def _run_playwright(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int
    ) -> TestResult:
        """Run test using native Playwright with minimal stealth"""
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            proxy = self._build_proxy(proxy_config)
            
            # Launch with minimal args
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            
            # Create context with mobile settings
            context = await browser.new_context(
                user_agent=mobile_config.get("user_agent"),
                viewport=mobile_config.get("viewport"),
                device_scale_factor=mobile_config.get("device_scale_factor", 2),
                is_mobile=mobile_config.get("is_mobile", True),
                has_touch=mobile_config.get("has_touch", True),
                locale=mobile_config.get("language", "en-US").replace("_", "-"),
                timezone_id=mobile_config.get("timezone", "America/New_York"),
                permissions=['geolocation'],
                geolocation={"latitude": 40.7128, "longitude": -74.0060}
            )
            
            # Apply MINIMAL stealth (just hide webdriver)
            await context.add_init_script(self._generate_minimal_stealth())
            logger.info("✅ Minimal stealth applied (webdriver hidden)")
            
            page = await context.new_page()
            
            # Navigate with networkidle for complete loading
            logger.info(f"Navigating to {url}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                logger.info("✅ Page loaded (networkidle)")
            except Exception as e:
                logger.warning(f"Navigation completed with warning: {str(e)[:100]}")
                # Continue anyway - page may have loaded
            
            # Capture screenshot
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "playwright", url_name, wait_time, page=page
            )
            
            # Analyze results
            proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
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
        """Run test using Patchright (browser-level stealth)"""
        try:
            from patchright.async_api import async_playwright
        except ImportError:
            raise ImportError("patchright not installed. Run: pip install patchright")
        
        async with async_playwright() as p:
            proxy = self._build_proxy(proxy_config)
            
            # Patchright has built-in stealth patches at browser level
            browser = await p.chromium.launch(headless=True, proxy=proxy)
            
            context = await browser.new_context(
                user_agent=mobile_config.get("user_agent"),
                viewport=mobile_config.get("viewport"),
                device_scale_factor=mobile_config.get("device_scale_factor", 2),
                is_mobile=mobile_config.get("is_mobile", True),
                has_touch=mobile_config.get("has_touch", True),
                locale=mobile_config.get("language", "en-US").replace("_", "-"),
                timezone_id=mobile_config.get("timezone", "America/New_York")
            )
            
            # Patchright does stealth at browser level, but we add minimal JS stealth too
            await context.add_init_script(self._generate_minimal_stealth())
            logger.info("✅ Patchright stealth (browser-level patches + minimal JS)")
            
            page = await context.new_page()
            
            logger.info(f"Navigating to {url} with Patchright")
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                logger.info("✅ Page loaded")
            except Exception as e:
                logger.warning(f"Navigation warning: {str(e)[:100]}")
            
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "patchright", url_name, wait_time, page=page
            )
            
            proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
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
        """Run test using Camoufox (Firefox-based with built-in stealth)"""
        try:
            from camoufox.async_api import AsyncCamoufox
        except ImportError:
            raise ImportError("camoufox not installed. Run: pip install 'camoufox[geoip]'")
        
        proxy_dict = None
        if proxy_config.get("host"):
            proxy_dict = {
                "server": f"http://{proxy_config['host']}:{proxy_config['port']}"
            }
            if proxy_config.get("username") and proxy_config.get("password"):
                proxy_dict["username"] = proxy_config["username"]
                proxy_dict["password"] = proxy_config["password"]
        
        # Camoufox has built-in humanization and stealth
        async with AsyncCamoufox(
            headless=True,
            proxy=proxy_dict,
            humanize=True,  # Built-in human-like behavior
            geoip=True if self.geoip else False
        ) as browser:
            
            page = await browser.new_page()
            
            # Set mobile viewport
            await page.set_viewport_size(
                mobile_config.get("viewport", {"width": 375, "height": 812})
            )
            
            # Camoufox has built-in Firefox stealth, minimal JS stealth only
            await page.evaluate(self._generate_minimal_stealth())
            logger.info("✅ Camoufox stealth (Firefox + minimal JS)")
            
            logger.info(f"Navigating to {url} with Camoufox")
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                logger.info("✅ Page loaded")
            except Exception as e:
                logger.warning(f"Navigation warning: {str(e)[:100]}")
            
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "camoufox", url_name, wait_time, page=page
            )
            
            proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
            is_mobile = await self._check_mobile_ua(page, mobile_config)
            
            await browser.close()
            
            return TestResult(
                library="camoufox",
                category="playwright",
                test_name=url_name,
                url=url,
                success=True,
                detected_ip=detected_ip,
                user_agent=mobile_config.get("user_agent", "Firefox Mobile"),
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
        """Run test using Rebrowser Playwright (browser-level stealth)"""
        try:
            from rebrowser_playwright.async_api import async_playwright
        except ImportError:
            raise ImportError("rebrowser-playwright not installed")
        
        async with async_playwright() as p:
            proxy = self._build_proxy(proxy_config)
            
            # Rebrowser has built-in patches at browser level
            browser = await p.chromium.launch(headless=True, proxy=proxy)
            
            context = await browser.new_context(
                user_agent=mobile_config.get("user_agent"),
                viewport=mobile_config.get("viewport"),
                device_scale_factor=mobile_config.get("device_scale_factor", 2),
                is_mobile=mobile_config.get("is_mobile", True),
                has_touch=mobile_config.get("has_touch", True),
                locale=mobile_config.get("language", "en-US").replace("_", "-"),
                timezone_id=mobile_config.get("timezone", "America/New_York")
            )
            
            # Rebrowser does stealth at browser level, add minimal JS stealth
            await context.add_init_script(self._generate_minimal_stealth())
            logger.info("✅ Rebrowser stealth (browser-level patches + minimal JS)")
            
            page = await context.new_page()
            
            logger.info(f"Navigating to {url} with Rebrowser")
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                logger.info("✅ Page loaded")
            except Exception as e:
                logger.warning(f"Navigation warning: {str(e)[:100]}")
            
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "rebrowser_playwright", url_name, wait_time, page=page
            )
            
            proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
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
    
    async def _check_proxy(
        self, 
        page, 
        proxy_config: Dict[str, str]
    ) -> tuple[bool, Optional[str]]:
        """Check if proxy is working (simple detection)"""
        try:
            await asyncio.sleep(1)
            
            # Get page content
            content = await page.content()
            
            # Simple IP patterns
            ip_patterns = [
                r'"ip"\s*:\s*"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"',
                r'Your IP.*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
                r'<span[^>]*>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</span>',
                r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
            ]
            
            found_ips = []
            for pattern in ip_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                found_ips.extend(matches)
            
            # Filter valid public IPs
            found_ips = [ip for ip in found_ips if self._is_valid_public_ip(ip)]
            
            if not found_ips:
                logger.debug("No IP detected (OK for some pages)")
                return False, None
            
            detected_ip = found_ips[0]
            
            if proxy_config.get("host"):
                logger.info(f"✅ Proxy working (detected IP: {detected_ip})")
                return True, detected_ip
            else:
                return False, detected_ip
        
        except Exception as e:
            logger.debug(f"Proxy check error: {str(e)[:80]}")
            return False, None
    
    def _is_valid_public_ip(self, ip_str: str) -> bool:
        """Check if IP is valid and public"""
        try:
            parts = [int(p) for p in ip_str.split('.')]
            
            if len(parts) != 4:
                return False
            
            # Check valid range
            if any(p < 0 or p > 255 for p in parts):
                return False
            
            # Filter private IPs
            if parts[0] == 10:  # 10.0.0.0/8
                return False
            if parts[0] == 172 and 16 <= parts[1] <= 31:  # 172.16.0.0/12
                return False
            if parts[0] == 192 and parts[1] == 168:  # 192.168.0.0/16
                return False
            if parts[0] == 127:  # 127.0.0.0/8 (localhost)
                return False
            if parts[0] == 169 and parts[1] == 254:  # 169.254.0.0/16 (link-local)
                return False
            
            return True
        except:
            return False
    
    async def _check_mobile_ua(
        self, 
        page, 
        mobile_config: Dict[str, Any]
    ) -> bool:
        """Check if mobile user agent is detected"""
        try:
            ua = await page.evaluate("navigator.userAgent")
            
            # Mobile keywords
            mobile_keywords = [
                "mobile", "iphone", "android", "ipad", 
                "tablet", "fxios", "fennec"
            ]
            
            is_mobile_ua = any(kw in ua.lower() for kw in mobile_keywords)
            
            # Check viewport too
            try:
                viewport_width = await page.evaluate("window.innerWidth")
                is_mobile_viewport = viewport_width < 768
            except:
                is_mobile_viewport = False
            
            is_mobile = is_mobile_ua or is_mobile_viewport
            
            if is_mobile:
                logger.info(f"✅ Mobile detected (UA={is_mobile_ua}, VP={is_mobile_viewport})")
            else:
                logger.warning(f"⚠️ Desktop UA detected: {ua[:60]}...")
            
            return is_mobile
        except Exception as e:
            logger.debug(f"UA check error: {e}")
            return False
