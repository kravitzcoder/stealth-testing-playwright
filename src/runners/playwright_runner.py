"""
REBROWSER-OPTIMIZED STEALTH RUNNER
Properly configures Rebrowser with all its stealth features enabled

Key differences from vanilla Playwright:
1. Rebrowser-specific launch args
2. Advanced CDP commands
3. Proper fingerprint randomization
4. Enhanced headers and context settings
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

logger = logging.getLogger(__name__)


class PlaywrightRunner:
    """Optimized runner with proper Rebrowser configuration"""
    
    def __init__(self, screenshot_engine: Optional[ScreenshotEngine] = None):
        self.screenshot_engine = screenshot_engine or ScreenshotEngine()
        self.profile_loader = DeviceProfileLoader()
        logger.info("Playwright runner initialized with REBROWSER OPTIMIZATIONS")
    
    async def run_test(
        self,
        library_name: str,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 30
    ) -> TestResult:
        """Run test with library-specific optimizations"""
        start_time = time.time()
        logger.info(f"🎭 Testing {library_name} on {url_name}: {url}")
        
        try:
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
                result = await self._run_rebrowser_optimized(
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
            logger.error(f"❌ Test failed: {error_msg}")
            
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
        if not proxy_config.get("host"):
            return None
            
        proxy = {
            "server": f"http://{proxy_config['host']}:{proxy_config['port']}"
        }
        
        if proxy_config.get("username") and proxy_config.get("password"):
            proxy["username"] = proxy_config["username"]
            proxy["password"] = proxy_config["password"]
        
        logger.info(f"Proxy: {proxy['server']}")
        return proxy
    
    async def _run_playwright(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int
    ) -> TestResult:
        """Run with standard Playwright + manual stealth"""
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            proxy = self._build_proxy(proxy_config)
            
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            context = await browser.new_context(
                user_agent=mobile_config.get("user_agent"),
                viewport=mobile_config.get("viewport"),
                device_scale_factor=mobile_config.get("device_scale_factor", 2),
                is_mobile=True,
                has_touch=True,
                locale="en-US",
                timezone_id="America/New_York"
            )
            
            # Apply manual stealth
            await self._apply_basic_stealth(context, mobile_config)
            
            page = await context.new_page()
            
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Extra wait for dynamic pages
            if "creepjs" in url.lower() or "worker" in url_name.lower():
                await asyncio.sleep(15)
            
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "playwright", url_name, wait_time, page=page
            )
            
            proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
            is_mobile = await self._check_mobile_ua(page)
            
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
    
    async def _run_rebrowser_optimized(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int
    ) -> TestResult:
        """
        REBROWSER-OPTIMIZED VERSION
        
        This is what unlocks Rebrowser's true potential!
        """
        from rebrowser_playwright.async_api import async_playwright
        
        logger.info("🔥 Using REBROWSER-OPTIMIZED configuration")
        
        async with async_playwright() as p:
            proxy = self._build_proxy(proxy_config)
            
            # CRITICAL: Rebrowser-specific launch args
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy,
                args=[
                    # Core anti-detection
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    
                    # Additional stealth
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    
                    # Disable automation flags
                    '--disable-dev-tools',
                    '--disable-automation',
                    '--disable-background-networking',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-breakpad',
                    '--disable-client-side-phishing-detection',
                    '--disable-component-update',
                    '--disable-default-apps',
                    '--disable-domain-reliability',
                    '--disable-extensions',
                    '--disable-features=AudioServiceOutOfProcess',
                    '--disable-hang-monitor',
                    '--disable-ipc-flooding-protection',
                    '--disable-notifications',
                    '--disable-offer-store-unmasked-wallet-cards',
                    '--disable-popup-blocking',
                    '--disable-print-preview',
                    '--disable-prompt-on-repost',
                    '--disable-renderer-backgrounding',
                    '--disable-sync',
                    '--disable-translate',
                    '--metrics-recording-only',
                    '--mute-audio',
                    '--no-default-browser-check',
                    '--safebrowsing-disable-auto-update',
                    '--enable-automation=false',
                    '--password-store=basic',
                    '--use-mock-keychain'
                ]
            )
            
            # CRITICAL: Enhanced context with proper headers
            context = await browser.new_context(
                user_agent=mobile_config.get("user_agent"),
                viewport=mobile_config.get("viewport"),
                device_scale_factor=mobile_config.get("device_scale_factor", 2),
                is_mobile=True,
                has_touch=True,
                locale="en-US",
                timezone_id="America/New_York",
                
                # Rebrowser-specific settings
                bypass_csp=True,
                java_script_enabled=True,
                ignore_https_errors=False,
                
                # Enhanced headers for mobile
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'sec-ch-ua': '"Chromium";v="120", "Not_A Brand";v="99", "Google Chrome";v="120"',
                    'sec-ch-ua-mobile': '?1',
                    'sec-ch-ua-platform': '"Android"',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            
            # CRITICAL: Apply Rebrowser-optimized stealth scripts
            await self._apply_rebrowser_stealth(context, mobile_config)
            
            page = await context.new_page()
            
            # CRITICAL: Use CDP to further mask automation
            await self._apply_cdp_stealth(page, mobile_config)
            
            logger.info(f"Navigating to {url} with Rebrowser optimizations")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Extra wait for dynamic pages
            if "creepjs" in url.lower() or "worker" in url_name.lower():
                logger.info("⏳ Extra wait for CreepJS analysis")
                await asyncio.sleep(15)
            
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "rebrowser_playwright", url_name, wait_time, page=page
            )
            
            proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
            is_mobile = await self._check_mobile_ua(page)
            
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
    
    async def _apply_basic_stealth(self, context, mobile_config: Dict[str, Any]) -> None:
        """Basic stealth for Playwright/Patchright"""
        ua = mobile_config.get("user_agent", "")
        platform = mobile_config.get("platform", "iPhone")
        
        script = f"""
        Object.defineProperty(navigator, 'webdriver', {{get: () => undefined}});
        Object.defineProperty(navigator, 'platform', {{get: () => '{platform}'}});
        """
        
        await context.add_init_script(script)
        logger.info("✅ Basic stealth applied")
    
    async def _apply_rebrowser_stealth(self, context, mobile_config: Dict[str, Any]) -> None:
        """
        REBROWSER-SPECIFIC STEALTH
        
        This is what makes Rebrowser better than vanilla Playwright!
        """
        ua = mobile_config.get("user_agent", "")
        platform = mobile_config.get("platform", "iPhone")
        hardware_concurrency = mobile_config.get("hardware_concurrency", 8)
        device_memory = mobile_config.get("device_memory", 4)
        max_touch_points = mobile_config.get("max_touch_points", 5)
        
        ua_escaped = json.dumps(ua)
        
        # ENHANCED stealth script for Rebrowser
        script = f"""
(function() {{
    'use strict';
    
    const isWorker = typeof WorkerGlobalScope !== 'undefined' && self instanceof WorkerGlobalScope;
    
    // Core navigator properties
    const props = {{
        userAgent: {ua_escaped},
        platform: '{platform}',
        hardwareConcurrency: {hardware_concurrency},
        deviceMemory: {device_memory},
        maxTouchPoints: {max_touch_points},
        vendor: 'Google Inc.',
        vendorSub: '',
        productSub: '20030107',
        language: 'en-US',
        languages: ['en-US', 'en']
    }};
    
    // Apply to navigator
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
    
    // Permissions API spoofing
    if (navigator.permissions && navigator.permissions.query) {{
        const originalQuery = navigator.permissions.query;
        navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({{ state: Notification.permission, onchange: null }}) :
                originalQuery(parameters)
        );
    }}
    
    // Plugin array spoofing
    Object.defineProperty(navigator, 'plugins', {{
        get: () => [
            {{
                0: {{type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"}},
                description: "Portable Document Format",
                filename: "internal-pdf-viewer",
                length: 1,
                name: "PDF Viewer"
            }}
        ]
    }});
    
    // WebGL vendor/renderer spoofing
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
        if (parameter === 37445) return 'Apple Inc.';
        if (parameter === 37446) return 'Apple GPU';
        return getParameter.call(this, parameter);
    }};
    
    if (typeof WebGL2RenderingContext !== 'undefined') {{
        const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return 'Apple Inc.';
            if (parameter === 37446) return 'Apple GPU';
            return getParameter2.call(this, parameter);
        }};
    }}
    
    // Canvas fingerprint noise
    const toDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function() {{
        const context = this.getContext('2d');
        if (context) {{
            const imageData = context.getImageData(0, 0, this.width, this.height);
            for (let i = 0; i < imageData.data.length; i += 4) {{
                imageData.data[i] = imageData.data[i] ^ 1;
            }}
            context.putImageData(imageData, 0, 0);
        }}
        return toDataURL.apply(this, arguments);
    }};
    
    // Chrome runtime
    if (!window.chrome) {{
        window.chrome = {{}};
    }}
    window.chrome.runtime = {{
        connect: () => ({{}}),
        sendMessage: () => ({{}})
    }};
    
    console.log('[Rebrowser] Enhanced stealth applied');
}})();
        """
        
        await context.add_init_script(script)
        logger.info("✅ Rebrowser-enhanced stealth applied")
    
    async def _apply_cdp_stealth(self, page, mobile_config: Dict[str, Any]) -> None:
        """
        CRITICAL: Use CDP (Chrome DevTools Protocol) for deeper spoofing
        
        This is Rebrowser's secret sauce!
        """
        try:
            client = await page.context.new_cdp_session(page)
            
            # Override user agent at CDP level
            await client.send('Network.setUserAgentOverride', {
                'userAgent': mobile_config.get("user_agent"),
                'platform': mobile_config.get("platform", "iPhone"),
                'acceptLanguage': 'en-US,en'
            })
            
            # Override geolocation
            await client.send('Emulation.setGeolocationOverride', {
                'latitude': 37.7749,  # San Francisco
                'longitude': -122.4194,
                'accuracy': 100
            })
            
            # Override timezone
            await client.send('Emulation.setTimezoneOverride', {
                'timezoneId': 'America/New_York'
            })
            
            # Set touch emulation
            await client.send('Emulation.setTouchEmulationEnabled', {
                'enabled': True,
                'maxTouchPoints': mobile_config.get("max_touch_points", 5)
            })
            
            logger.info("✅ CDP-level stealth applied (Rebrowser)")
            
        except Exception as e:
            logger.warning(f"⚠️ CDP stealth failed (non-critical): {e}")
    
    async def _run_patchright(self, url: str, url_name: str, proxy_config: Dict[str, str],
                             mobile_config: Dict[str, Any], wait_time: int) -> TestResult:
        """Patchright with basic stealth"""
        from patchright.async_api import async_playwright
        
        async with async_playwright() as p:
            proxy = self._build_proxy(proxy_config)
            browser = await p.chromium.launch(headless=True, proxy=proxy)
            
            context = await browser.new_context(
                user_agent=mobile_config.get("user_agent"),
                viewport=mobile_config.get("viewport"),
                device_scale_factor=mobile_config.get("device_scale_factor", 2),
                is_mobile=True,
                has_touch=True
            )
            
            await self._apply_basic_stealth(context, mobile_config)
            
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            if "creepjs" in url.lower():
                await asyncio.sleep(15)
            
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "patchright", url_name, wait_time, page=page
            )
            
            proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
            is_mobile = await self._check_mobile_ua(page)
            
            await browser.close()
            
            return TestResult(
                library="patchright",
                category="playwright",
                test_name=url_name,
                url=url,
                success=True,
                detected_ip=detected_ip,
                proxy_working=proxy_working,
                is_mobile_ua=is_mobile,
                screenshot_path=screenshot_path,
                execution_time=0
            )
    
    async def _run_camoufox(self, url: str, url_name: str, proxy_config: Dict[str, str],
                           mobile_config: Dict[str, Any], wait_time: int) -> TestResult:
        """Camoufox (Firefox-based)"""
        from camoufox.async_api import AsyncCamoufox
        
        proxy_dict = None
        if proxy_config.get("host"):
            proxy_dict = {
                "server": f"http://{proxy_config['host']}:{proxy_config['port']}"
            }
            if proxy_config.get("username"):
                proxy_dict["username"] = proxy_config["username"]
                proxy_dict["password"] = proxy_config["password"]
        
        async with AsyncCamoufox(headless=True, proxy=proxy_dict, humanize=True) as browser:
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            if "creepjs" in url.lower():
                await asyncio.sleep(15)
            
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "camoufox", url_name, wait_time, page=page
            )
            
            proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
            is_mobile = await self._check_mobile_ua(page)
            
            await browser.close()
            
            return TestResult(
                library="camoufox",
                category="playwright",
                test_name=url_name,
                url=url,
                success=True,
                detected_ip=detected_ip,
                proxy_working=proxy_working,
                is_mobile_ua=is_mobile,
                screenshot_path=screenshot_path,
                execution_time=0
            )
    
    async def _check_proxy(self, page, proxy_config: Dict[str, str]) -> tuple:
        """Check if proxy is working"""
        try:
            content = await page.content()
            ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
            found_ips = re.findall(ip_pattern, content)
            
            if not found_ips:
                return False, None
            
            detected_ip = found_ips[0]
            proxy_ip = proxy_config.get("host")
            
            if proxy_ip and detected_ip == proxy_ip:
                logger.info(f"✅ Proxy working: {detected_ip}")
                return True, detected_ip
            else:
                logger.warning(f"⚠️ IP mismatch: {detected_ip} vs {proxy_ip}")
                return False, detected_ip
        except:
            return False, None
    
    async def _check_mobile_ua(self, page) -> bool:
        """Check if mobile UA detected"""
        try:
            ua = await page.evaluate("navigator.userAgent")
            is_mobile = any(kw in ua.lower() for kw in ["mobile", "iphone", "android"])
            
            if is_mobile:
                logger.info(f"✅ Mobile UA: {ua[:50]}...")
            else:
                logger.warning(f"⚠️ Desktop UA: {ua[:50]}...")
            
            return is_mobile
        except:
            return False
