"""
REBROWSER RUNNER - Fully Optimized for Rebrowser-Playwright

This runner unlocks Rebrowser's full potential with:
1. Rebrowser-specific launch args
2. Enhanced context with proper mobile headers
3. CDP (Chrome DevTools Protocol) commands for deep spoofing
4. Canvas and WebGL fingerprint randomization
5. Advanced navigator property spoofing
6. Permissions API handling

Key differences from vanilla Playwright:
- Browser-level patches (not just JavaScript)
- CDP commands for undetectable spoofing
- Consistent fingerprints across contexts
- Regular updates for latest bot detection bypasses
"""

import logging
import asyncio
import time
import json
from typing import Dict, Any

from ..core.test_result import TestResult
from .base_runner import BaseRunner

logger = logging.getLogger(__name__)


class RebrowserRunner(BaseRunner):
    """Rebrowser-Playwright runner with full optimization"""
    
    def __init__(self, screenshot_engine=None):
        super().__init__(screenshot_engine)
        logger.info("🔥 Rebrowser runner initialized (FULLY OPTIMIZED)")
    
    async def run_test(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 15
    ) -> TestResult:
        """
        Run test with full Rebrowser optimization
        
        This unlocks Rebrowser's true potential!
        """
        start_time = time.time()
        logger.info(f"🎭 Testing Rebrowser on {url_name}: {url}")
        
        try:
            from rebrowser_playwright.async_api import async_playwright
        except ImportError:
            error_msg = "rebrowser-playwright not installed. Run: pip install rebrowser-playwright"
            logger.error(error_msg)
            return TestResult(
                library="rebrowser_playwright",
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
                
                # CRITICAL: Rebrowser-specific launch args
                browser = await p.chromium.launch(
                    headless=True,
                    proxy=proxy,
                    args=self._get_rebrowser_launch_args()
                )
                
                # CRITICAL: Enhanced context with proper headers
                context = await browser.new_context(
                    **self._get_rebrowser_context_config(mobile_config)
                )
                
                # CRITICAL: Apply Rebrowser-enhanced stealth scripts
                await self._apply_rebrowser_stealth(context, mobile_config)
                
                page = await context.new_page()
                
                # CRITICAL: Use CDP for deeper spoofing
                await self._apply_cdp_stealth(page, mobile_config)
                
                logger.info(f"Navigating to {url} with Rebrowser optimizations")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Extra wait for dynamic pages
                await self._extra_wait_for_dynamic_pages(url, url_name)
                
                # Capture screenshot
                screenshot_path = await self.screenshot_engine.capture_with_wait(
                    page, "rebrowser_playwright", url_name, wait_time, page=page
                )
                
                # Check results
                proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
                is_mobile = await self._check_mobile_ua(page, mobile_config)
                
                await browser.close()
                
                execution_time = time.time() - start_time
                logger.info(f"✅ Rebrowser test completed in {execution_time:.2f}s")
                
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
                    execution_time=execution_time
                )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)[:500]
            logger.error(f"❌ Rebrowser test failed: {error_msg}")
            
            return TestResult(
                library="rebrowser_playwright",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
    
    def _get_rebrowser_launch_args(self) -> list:
        """
        CRITICAL: Rebrowser-specific launch arguments
        
        These args are what make Rebrowser better than vanilla Playwright!
        They remove automation markers and enable deeper spoofing.
        """
        return [
            # Core anti-detection (CRITICAL)
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            
            # Environment
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            
            # Performance & detection
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu',
            
            # Automation markers removal
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
    
    def _get_rebrowser_context_config(self, mobile_config: Dict[str, Any]) -> dict:
        """
        CRITICAL: Enhanced context configuration for Rebrowser
        
        Proper headers are essential for mobile detection!
        """
        return {
            'user_agent': mobile_config.get("user_agent"),
            'viewport': mobile_config.get("viewport"),
            'device_scale_factor': mobile_config.get("device_scale_factor", 2),
            'is_mobile': True,
            'has_touch': True,
            'locale': mobile_config.get("language", "en-US").replace("_", "-"),
            'timezone_id': mobile_config.get("timezone", "America/New_York"),
            
            # Rebrowser-specific settings
            'bypass_csp': True,
            'java_script_enabled': True,
            'ignore_https_errors': False,
            
            # CRITICAL: Enhanced headers for mobile detection
            'extra_http_headers': {
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
            },
            
            # Permissions
            'permissions': ['geolocation'],
            'geolocation': {"latitude": 37.7749, "longitude": -122.4194}
        }
    
    async def _apply_rebrowser_stealth(self, context, mobile_config: Dict[str, Any]):
        """
        CRITICAL: Rebrowser-enhanced stealth script
        
        This applies JavaScript-level spoofing that works with Rebrowser's
        browser-level patches. Together they create undetectable automation.
        """
        ua = mobile_config.get("user_agent", "")
        platform = mobile_config.get("platform", "iPhone")
        hardware_concurrency = mobile_config.get("hardware_concurrency", 8)
        device_memory = mobile_config.get("device_memory", 4)
        max_touch_points = mobile_config.get("max_touch_points", 5)
        
        # Escape UA for JavaScript
        ua_escaped = json.dumps(ua)
        
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
    
    // Remove webdriver completely
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
    
    // Plugin array spoofing (mobile has limited plugins)
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
    
    // WebGL vendor/renderer spoofing (Apple GPU for iPhone)
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
    
    // Canvas fingerprint noise (subtle randomization)
    const toDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function() {{
        const context = this.getContext('2d');
        if (context) {{
            const imageData = context.getImageData(0, 0, this.width, this.height);
            // Add minimal noise (flip 1 bit every 4 pixels)
            for (let i = 0; i < imageData.data.length; i += 4) {{
                imageData.data[i] = imageData.data[i] ^ 1;
            }}
            context.putImageData(imageData, 0, 0);
        }}
        return toDataURL.apply(this, arguments);
    }};
    
    // Chrome runtime (some sites check for this)
    if (!window.chrome) {{
        window.chrome = {{}};
    }}
    window.chrome.runtime = {{
        connect: () => ({{}}),
        sendMessage: () => ({{}})
    }};
    
    // Screen properties for mobile
    Object.defineProperty(screen, 'availWidth', {{
        get: () => window.innerWidth
    }});
    Object.defineProperty(screen, 'availHeight', {{
        get: () => window.innerHeight
    }});
    
    console.log('[Rebrowser] Enhanced stealth applied ✅');
}})();
        """
        
        await context.add_init_script(script)
        logger.info("✅ Rebrowser-enhanced stealth script applied")
    
    async def _apply_cdp_stealth(self, page, mobile_config: Dict[str, Any]):
        """
        CRITICAL: CDP (Chrome DevTools Protocol) commands
        
        This is Rebrowser's secret sauce! CDP commands spoof at a level
        that JavaScript cannot detect.
        """
        try:
            client = await page.context.new_cdp_session(page)
            
            # Override user agent at CDP level (deeper than JavaScript)
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
                'timezoneId': mobile_config.get("timezone", "America/New_York")
            })
            
            # Set touch emulation
            await client.send('Emulation.setTouchEmulationEnabled', {
                'enabled': True,
                'maxTouchPoints': mobile_config.get("max_touch_points", 5)
            })
            
            # Set mobile device metrics
            await client.send('Emulation.setDeviceMetricsOverride', {
                'width': mobile_config.get("viewport", {}).get("width", 375),
                'height': mobile_config.get("viewport", {}).get("height", 812),
                'deviceScaleFactor': mobile_config.get("device_scale_factor", 2),
                'mobile': True,
                'screenOrientation': {
                    'type': 'portraitPrimary',
                    'angle': 0
                }
            })
            
            logger.info("✅ CDP-level stealth applied (Rebrowser's secret sauce)")
            
        except Exception as e:
            logger.warning(f"⚠️ CDP stealth partial failure (non-critical): {e}")
            # Continue anyway - Rebrowser still works without full CDP
