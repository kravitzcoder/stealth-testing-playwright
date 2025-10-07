"""
STEALTH BROWSER TESTING FRAMEWORK - Playwright Runner (FIXED)
Handles Playwright-based libraries with comprehensive stealth features

Authors: kravitzcoder & MiniMax Agent
Repository: https://github.com/kravitzcoder/stealth-testing-playwright

FIXES:
- Corrected constructor to match test_orchestrator expectations
- Proper run_test signature matching framework
- Support for all 3 Playwright libraries (playwright, patchright, camoufox)
- Manual stealth techniques (playwright-stealth REMOVED due to bugs)
- Optional GeoIP with graceful fallback
- Enhanced fingerprint spoofing
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
        
        logger.info("Playwright runner initialized with MANUAL stealth only")
        logger.info("ℹ️ playwright-stealth plugin DISABLED (removed due to v1.0.6 bugs)")
    
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
            library_name: Name of library (playwright, patchright, camoufox)
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
        
        browser = None
        context = None
        page = None
        
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
            # Build proxy URL
            proxy_url = self._build_proxy_url(proxy_config)
            
            # Launch browser with proxy
            browser = await p.chromium.launch(
                headless=True,
                proxy={"server": proxy_url} if proxy_url else None
            )
            
            # Create context with mobile emulation
            context = await browser.new_context(
                user_agent=mobile_config.get("user_agent"),
                viewport=mobile_config.get("viewport"),
                device_scale_factor=mobile_config.get("device_scale_factor", 2),
                is_mobile=mobile_config.get("is_mobile", True),
                has_touch=mobile_config.get("has_touch", True),
                locale=mobile_config.get("language", "en-US").replace("_", "-"),
                timezone_id=mobile_config.get("timezone", "America/New_York")
            )
            
            # Apply comprehensive stealth techniques
            await self._apply_manual_stealth(context, mobile_config)
            
            # Create page and navigate
            page = await context.new_page()
            
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Capture screenshot
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
                execution_time=0  # Will be set by caller
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
            
            # Patchright has built-in stealth, but we still apply manual techniques
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
            
            # Apply additional stealth on top of Patchright's built-in stealth
            await self._apply_manual_stealth(context, mobile_config)
            
            page = await context.new_page()
            
            logger.info(f"Navigating to {url} with Patchright")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
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
        
        # Camoufox uses Firefox, so we need Firefox-compatible user agent
        user_agent = mobile_config.get("user_agent", "")
        if "Chrome" in user_agent or "Safari" in user_agent:
            # Convert to Firefox mobile UA
            user_agent = "Mozilla/5.0 (Android 11; Mobile; rv:109.0) Gecko/109.0 Firefox/115.0"
            logger.info("🦊 Converted to Firefox mobile user agent for Camoufox")
        
        async with AsyncCamoufox(
            headless=True,
            proxy=proxy_dict,
            humanize=True,  # Enable humanization
            geoip=True if self.geoip else False  # Enable GeoIP if available
        ) as browser:
            
            page = await browser.new_page()
            
            # Set viewport and user agent
            await page.set_viewport_size(mobile_config.get("viewport", {"width": 375, "height": 812}))
            await page.evaluate(f"Object.defineProperty(navigator, 'userAgent', {{get: () => '{user_agent}'}})")
            
            logger.info(f"Navigating to {url} with Camoufox (Firefox)")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
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
    
    async def _apply_manual_stealth(self, context, mobile_config: Dict[str, Any]) -> None:
        """Apply comprehensive manual stealth techniques"""
        
        # Generate fingerprint injection script
        fingerprint_script = generate_fingerprint_script(mobile_config)
        
        # Add initialization script to every page
        await context.add_init_script(fingerprint_script)
        
        logger.info("✅ Manual stealth techniques applied (fingerprint injection)")
        
        # Set up route interception for worker scripts
        await context.route("**/*", lambda route: self._handle_worker_interception(route, mobile_config))
        
        logger.info("✅ Worker script interception enabled")
    
    async def _handle_worker_interception(self, route, mobile_config: Dict[str, Any]) -> None:
        """Intercept and modify worker scripts to maintain consistent fingerprint"""
        try:
            request = route.request
            
            # Detect worker requests
            is_worker = (
                request.resource_type == "script" and (
                    "worker" in request.url.lower() or
                    request.header_value("sec-fetch-dest") in ["worker", "sharedworker", "serviceworker"]
                )
            )
            
            if is_worker:
                logger.info(f"🔧 Intercepting worker script: {request.url}")
                
                # Fetch original response
                response = await route.fetch()
                body = await response.text()
                
                # Inject fingerprint spoofing at the beginning
                spoof_script = generate_fingerprint_script(mobile_config)
                modified_body = spoof_script + "\n" + body
                
                # Fulfill with modified body
                headers = response.headers.copy()
                headers.pop("content-encoding", None)
                headers.pop("content-length", None)
                
                await route.fulfill(
                    status=response.status,
                    headers=headers,
                    body=modified_body
                )
                return
        
        except Exception as e:
            logger.debug(f"Worker interception error (continuing): {e}")
        
        # Continue with original request
        await route.continue_()
    
    async def _check_proxy_status(self, page, proxy_config: Dict[str, str]) -> tuple[bool, Optional[str]]:
        """Check if proxy is working by analyzing page content"""
        try:
            content = await page.content()
            
            # Find IP addresses in page content
            ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
            found_ips = re.findall(ip_pattern, content)
            
            if not found_ips:
                logger.warning("No IP address found on page")
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
            logger.error(f"Error checking proxy status: {e}")
            return False, None
    
    async def _check_mobile_ua(self, page, mobile_config: Dict[str, Any]) -> bool:
        """Check if mobile user agent is detected correctly"""
        try:
            ua = await page.evaluate("navigator.userAgent")
            
            # Check for mobile indicators
            is_mobile = any(keyword in ua.lower() for keyword in ["mobile", "iphone", "android", "ipad"])
            
            if is_mobile:
                logger.info(f"✅ Mobile UA detected: {ua[:50]}...")
            else:
                logger.warning(f"⚠️ Desktop UA detected: {ua[:50]}...")
            
            return is_mobile
        
        except Exception as e:
            logger.error(f"Error checking user agent: {e}")
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
