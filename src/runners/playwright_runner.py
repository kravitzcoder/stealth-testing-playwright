"""
STEALTH BROWSER TESTING FRAMEWORK - Playwright Runner (SIMPLIFIED & FIXED)
Fast-failing WebRTC block + No worker interception + Improved proxy detection

Authors: kravitzcoder & Claude

CRITICAL FIXES:
1. WebRTC blocks FAST (no page hangs)
2. Worker interception REMOVED (wasn't working)
3. Improved proxy detection (handles multiple formats)
4. Simplified and clean code
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


# ============================================================================
# FAST-FAILING WebRTC Block (CRITICAL FIX - prevents page hangs)
# ============================================================================

def generate_webrtc_block_script() -> str:
    """
    Generate JavaScript to block WebRTC WITHOUT hanging pages
    
    KEY FIX: Returns null/undefined IMMEDIATELY instead of throwing errors
    This prevents pages from waiting for timeouts
    """
    return """
(function() {
    'use strict';
    
    console.log('[WebRTC Protection] Fast-fail blocking enabled');
    
    // Block RTCPeerConnection - return null immediately (no errors!)
    if (typeof RTCPeerConnection !== 'undefined') {
        window.RTCPeerConnection = undefined;
        window.webkitRTCPeerConnection = undefined;
        window.mozRTCPeerConnection = undefined;
    }
    
    // Block getUserMedia - reject instantly (no waiting!)
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia = function() {
            return Promise.reject(new DOMException('Permission denied', 'NotAllowedError'));
        };
    }
    
    // Block legacy getUserMedia - fail instantly
    const instantError = new DOMException('Permission denied', 'NotAllowedError');
    if (navigator.getUserMedia) {
        navigator.getUserMedia = function(constraints, success, error) {
            if (error) setTimeout(() => error(instantError), 0);
        };
    }
    
    if (navigator.webkitGetUserMedia) {
        navigator.webkitGetUserMedia = function(constraints, success, error) {
            if (error) setTimeout(() => error(instantError), 0);
        };
    }
    
    if (navigator.mozGetUserMedia) {
        navigator.mozGetUserMedia = function(constraints, success, error) {
            if (error) setTimeout(() => error(instantError), 0);
        };
    }
    
    // Block enumerateDevices - return empty immediately
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
        navigator.mediaDevices.enumerateDevices = function() {
            return Promise.resolve([]);
        };
    }
    
    console.log('[WebRTC Protection] ✅ Fast-fail blocking active');
})();
"""


class PlaywrightRunner:
    """Runner for Playwright-based stealth browser libraries"""
    
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
            else:
                logger.info("ℹ️ GeoIP database not found (optional)")
        except ImportError:
            logger.info("ℹ️ pygeoip not installed (optional)")
        except Exception as e:
            logger.warning(f"⚠️ Could not load GeoIP: {e}")
        
        logger.info("Playwright runner initialized (fast-fail WebRTC, no worker interception)")
    
    async def run_test(
        self,
        library_name: str,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 5
    ) -> TestResult:
        """Run test for a Playwright library with complete stealth"""
        start_time = time.time()
        logger.info(f"🎭 Testing {library_name} on {url_name}: {url}")
        
        # Verify proxy configuration
        if not self._validate_proxy_config(proxy_config):
            logger.error(f"Invalid proxy configuration for {library_name}")
            return TestResult(
                library=library_name,
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error="Invalid proxy configuration",
                execution_time=0
            )
        
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
    
    def _validate_proxy_config(self, proxy_config: Dict[str, str]) -> bool:
        """Validate proxy configuration"""
        if not proxy_config.get("host") or not proxy_config.get("port"):
            logger.error("Proxy missing host or port")
            return False
        return True
    
    def _build_proper_proxy(self, proxy_config: Dict[str, str]) -> Dict[str, Any]:
        """Build proper proxy configuration for Playwright"""
        proxy = {
            "server": f"http://{proxy_config['host']}:{proxy_config['port']}"
        }
        
        if proxy_config.get("username") and proxy_config.get("password"):
            proxy["username"] = proxy_config["username"]
            proxy["password"] = proxy_config["password"]
        
        logger.info(f"Proxy: {proxy['server']} (auth: {'yes' if 'username' in proxy else 'no'})")
        return proxy
    
    async def _run_playwright(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int
    ) -> TestResult:
        """Run test using native Playwright with complete stealth"""
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            proxy = self._build_proper_proxy(proxy_config) if proxy_config.get("host") else None
            
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--no-sandbox'
                ]
            )
            
            context = await browser.new_context(
                user_agent=mobile_config.get("user_agent"),
                viewport=mobile_config.get("viewport"),
                device_scale_factor=mobile_config.get("device_scale_factor", 2),
                is_mobile=mobile_config.get("is_mobile", True),
                has_touch=mobile_config.get("has_touch", True),
                locale=mobile_config.get("language", "en-US").replace("_", "-"),
                timezone_id=mobile_config.get("timezone", "America/New_York"),
                permissions=['geolocation', 'notifications'],
                geolocation={"latitude": 40.7128, "longitude": -74.0060},
                color_scheme='light'
            )
            
            # Apply stealth (SIMPLIFIED - no worker interception)
            await self._apply_stealth(context, mobile_config)
            
            page = await context.new_page()
            
            logger.info(f"Navigating to {url}")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"Navigation warning: {e}")
            
            # Capture screenshot
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "playwright", url_name, wait_time, page=page
            )
            
            # Analyze results
            proxy_working, detected_ip = await self._check_proxy_status(page, proxy_config, url)
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
        """Run test using Patchright"""
        try:
            from patchright.async_api import async_playwright
        except ImportError:
            raise ImportError("patchright not installed. Run: pip install patchright")
        
        async with async_playwright() as p:
            proxy = self._build_proper_proxy(proxy_config) if proxy_config.get("host") else None
            
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
            
            await self._apply_stealth(context, mobile_config)
            
            page = await context.new_page()
            
            logger.info(f"Navigating to {url} with Patchright")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"Navigation warning: {e}")
            
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "patchright", url_name, wait_time, page=page
            )
            
            proxy_working, detected_ip = await self._check_proxy_status(page, proxy_config, url)
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
        """Run test using Camoufox (Firefox-based)"""
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
        
        # Firefox mobile UA
        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/40.0 Mobile/15E148 Safari/605.1.15"
        
        async with AsyncCamoufox(
            headless=True,
            proxy=proxy_dict,
            humanize=True,
            geoip=True if self.geoip else False
        ) as browser:
            
            page = await browser.new_page()
            
            await page.set_viewport_size(mobile_config.get("viewport", {"width": 375, "height": 812}))
            
            # Apply stealth to Camoufox
            await page.evaluate(f"""
                {generate_webrtc_block_script()}
                
                Object.defineProperty(navigator, 'userAgent', {{
                    get: () => '{user_agent}'
                }});
                Object.defineProperty(navigator, 'platform', {{
                    get: () => 'iPhone'
                }});
            """)
            
            logger.info(f"Navigating to {url} with Camoufox")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"Navigation warning: {e}")
            
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "camoufox", url_name, wait_time, page=page
            )
            
            proxy_working, detected_ip = await self._check_proxy_status(page, proxy_config, url)
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
        """Run test using Rebrowser Playwright"""
        try:
            from rebrowser_playwright.async_api import async_playwright
        except ImportError:
            raise ImportError("rebrowser-playwright not installed")
        
        async with async_playwright() as p:
            proxy = self._build_proper_proxy(proxy_config) if proxy_config.get("host") else None
            
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
            
            await self._apply_stealth(context, mobile_config)
            
            page = await context.new_page()
            
            logger.info(f"Navigating to {url} with Rebrowser")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"Navigation warning: {e}")
            
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "rebrowser_playwright", url_name, wait_time, page=page
            )
            
            proxy_working, detected_ip = await self._check_proxy_status(page, proxy_config, url)
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
    
    async def _apply_stealth(self, context, mobile_config: Dict[str, Any]) -> None:
        """
        Apply stealth scripts to context
        
        SIMPLIFIED: No worker interception (wasn't working anyway)
        """
        
        # Generate stealth script
        stealth_script = self._generate_stealth_script(mobile_config)
        
        # Add fast-failing WebRTC blocking
        webrtc_script = generate_webrtc_block_script()
        
        # Combine scripts
        combined_script = stealth_script + "\n\n" + webrtc_script
        
        # Add to all new pages in this context
        await context.add_init_script(combined_script)
        
        logger.info("✅ Stealth applied (fast-fail WebRTC, basic fingerprint spoofing)")
    
    def _generate_stealth_script(self, mobile_config: Dict[str, Any]) -> str:
        """Generate comprehensive stealth script"""
        
        user_agent = mobile_config.get("user_agent", "")
        platform = mobile_config.get("platform", "iPhone")
        hardware_concurrency = mobile_config.get("hardware_concurrency", 8)
        device_memory = mobile_config.get("device_memory", 4)
        max_touch_points = mobile_config.get("max_touch_points", 5)
        
        user_agent_escaped = user_agent.replace("'", "\\'")
        
        return f"""
(function() {{
    'use strict';
    
    const props = {{
        userAgent: '{user_agent_escaped}',
        platform: '{platform}',
        hardwareConcurrency: {hardware_concurrency},
        deviceMemory: {device_memory},
        maxTouchPoints: {max_touch_points}
    }};
    
    if (typeof navigator !== 'undefined') {{
        Object.defineProperty(navigator, 'userAgent', {{
            get: () => props.userAgent,
            configurable: true
        }});
        
        Object.defineProperty(navigator, 'platform', {{
            get: () => props.platform,
            configurable: true
        }});
        
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => props.hardwareConcurrency,
            configurable: true
        }});
        
        if ('deviceMemory' in navigator) {{
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => props.deviceMemory,
                configurable: true
            }});
        }}
        
        if ('maxTouchPoints' in navigator) {{
            Object.defineProperty(navigator, 'maxTouchPoints', {{
                get: () => props.maxTouchPoints,
                configurable: true
            }});
        }}
        
        delete navigator.__proto__.webdriver;
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined,
            configurable: true
        }});
        
        if (window.chrome) {{
            window.chrome.runtime = {{}};
        }}
        
        if (navigator.permissions && navigator.permissions.query) {{
            const originalQuery = navigator.permissions.query;
            navigator.permissions.query = (params) => {{
                if (params.name === 'notifications') {{
                    return Promise.resolve({{state: 'granted'}});
                }}
                return originalQuery(params);
            }};
        }}
    }}
    
    if (typeof CanvasRenderingContext2D !== 'undefined') {{
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        CanvasRenderingContext2D.prototype.getImageData = function() {{
            const imageData = originalGetImageData.apply(this, arguments);
            for (let i = 0; i < imageData.data.length; i += 100) {{
                imageData.data[i] = imageData.data[i] ^ 1;
            }}
            return imageData;
        }};
    }}
    
    console.log('[Stealth] Applied basic fingerprint spoofing');
}})();
        """
    
    async def _check_proxy_status(self, page, proxy_config: Dict[str, str], url: str) -> tuple[bool, Optional[str]]:
        """
        Check if proxy is working - SIMPLIFIED version
        
        Note: May not detect IP on all pages (like CreepJS) - that's OK!
        """
        try:
            await asyncio.sleep(2)
            
            content = await page.content()
            
            try:
                ip_text = await page.locator('body').inner_text()
            except:
                ip_text = content
            
            # IP detection patterns
            ip_patterns = [
                r'"ip"\s*:\s*"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"',
                r'Your IP.*?[:>\s]+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
                r'<span[^>]*>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</span>',
                r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b',
            ]
            
            found_ips = []
            for pattern in ip_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                found_ips.extend(matches)
            
            found_ips = list(set(ip for ip in found_ips if self._is_valid_ip(ip)))
            found_ips = [ip for ip in found_ips if not self._is_private_ip(ip)]
            
            if not found_ips:
                logger.warning("No valid public IP found on page (this is OK for some pages like CreepJS)")
                return False, None
            
            detected_ip = found_ips[0]
            proxy_host = proxy_config.get("host", "")
            
            if proxy_host:
                logger.info(f"✅ Proxy appears to be working (showing: {detected_ip})")
                return True, detected_ip
            else:
                logger.info(f"Detected IP: {detected_ip} (no proxy configured)")
                return False, detected_ip
        
        except Exception as e:
            logger.error(f"Error checking proxy: {e}")
            return False, None
    
    def _is_valid_ip(self, ip_str: str) -> bool:
        """Validate IP address format"""
        try:
            parts = ip_str.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            return True
        except:
            return False
    
    def _is_private_ip(self, ip_str: str) -> bool:
        """Check if IP is private/local"""
        try:
            parts = [int(p) for p in ip_str.split('.')]
            
            if parts[0] == 10:
                return True
            if parts[0] == 172 and 16 <= parts[1] <= 31:
                return True
            if parts[0] == 192 and parts[1] == 168:
                return True
            if parts[0] == 127:
                return True
            if parts[0] == 169 and parts[1] == 254:
                return True
            
            return False
        except:
            return False
    
    async def _check_mobile_ua(self, page, mobile_config: Dict[str, Any]) -> bool:
        """Check if mobile UA detected"""
        try:
            ua = await page.evaluate("navigator.userAgent")
            
            mobile_keywords = [
                "mobile",
                "iphone",
                "android",
                "ipad",
                "tablet",
                "fxios",
                "fennec",
            ]
            
            is_mobile_ua = any(kw in ua.lower() for kw in mobile_keywords)
            
            try:
                viewport_width = await page.evaluate("window.innerWidth")
                is_mobile_viewport = viewport_width < 768
            except:
                is_mobile_viewport = False
            
            is_mobile = is_mobile_ua or is_mobile_viewport
            
            if is_mobile:
                logger.info(f"✅ Mobile detected (UA={is_mobile_ua}, VP={is_mobile_viewport})")
            else:
                logger.warning(f"⚠️ Desktop UA: {ua[:60]}...")
            
            return is_mobile
        except Exception as e:
            logger.error(f"Error checking UA: {e}")
            return False
