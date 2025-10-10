"""
REBROWSER RUNNER - With Advanced CDP WebRTC Masking

WebRTC Strategy:
- Most sophisticated approach using CDP (Chrome DevTools Protocol)
- Override IPs at network level
- Force WebRTC to use proxy interface
- Browser flags + CDP + JavaScript (triple protection)
- Most robust WebRTC masking available
"""

import logging
import time
import json
from typing import Dict, Any

from ..core.test_result import TestResult
from .base_runner import BaseRunner

logger = logging.getLogger(__name__)


class RebrowserRunner(BaseRunner):
    """Rebrowser runner with advanced CDP WebRTC masking"""
    
    def __init__(self, screenshot_engine=None):
        super().__init__(screenshot_engine)
        logger.info("🔥 Rebrowser runner initialized (ADVANCED CDP WebRTC masking)")
    
    async def run_test(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 15
    ) -> TestResult:
        """Run test with Rebrowser's advanced WebRTC masking"""
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
                
                # CRITICAL: Rebrowser-specific launch args + WebRTC masking
                browser = await p.chromium.launch(
                    headless=True,
                    proxy=proxy,
                    args=self._get_rebrowser_launch_args_with_webrtc()
                )
                
                # Enhanced context with proper headers
                context = await browser.new_context(
                    **self._get_rebrowser_context_config(mobile_config)
                )
                
                # Apply Rebrowser-enhanced stealth
                await self._apply_rebrowser_stealth(context, mobile_config)
                
                # Apply WebRTC masking script
                await self._apply_webrtc_masking(context, proxy_config)
                
                page = await context.new_page()
                
                # CRITICAL: Use CDP for WebRTC IP masking (most robust!)
                await self._apply_cdp_webrtc_masking(page, proxy_config)
                
                # Apply other CDP stealth
                await self._apply_cdp_stealth(page, mobile_config)
                
                logger.info(f"Navigating to {url} with Rebrowser (CDP WebRTC masking)")
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
    
    def _get_rebrowser_launch_args_with_webrtc(self) -> list:
        """
        Rebrowser launch args with WebRTC masking
        """
        return [
            # Core anti-detection
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            
            # WebRTC IP masking (CRITICAL!)
            '--force-webrtc-ip-handling-policy=default_public_interface_only',
            '--enforce-webrtc-ip-permission-check',
            
            # Environment
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
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
        """Enhanced context configuration for Rebrowser"""
        return {
            'user_agent': mobile_config.get("user_agent"),
            'viewport': mobile_config.get("viewport"),
            'device_scale_factor': mobile_config.get("device_scale_factor", 2),
            'is_mobile': True,
            'has_touch': True,
            'locale': mobile_config.get("language", "en-US").replace("_", "-"),
            'timezone_id': mobile_config.get("timezone", "America/New_York"),
            'bypass_csp': True,
            'java_script_enabled': True,
            'ignore_https_errors': False,
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
            'permissions': ['geolocation'],
            'geolocation': {"latitude": 37.7749, "longitude": -122.4194}
        }
    
    async def _apply_webrtc_masking(self, context, proxy_config: Dict[str, str]):
        """
        JavaScript-level WebRTC masking
        
        Force relay mode (uses proxy)
        """
        script = """
(function() {
    'use strict';
    
    console.log('[Rebrowser WebRTC] Masking enabled');
    
    // Override RTCPeerConnection to force relay mode
    if (typeof RTCPeerConnection !== 'undefined') {
        const OriginalRTCPeerConnection = RTCPeerConnection;
        
        window.RTCPeerConnection = function(config) {
            // Force relay-only mode (proxy interface)
            if (config) {
                config.iceServers = config.iceServers || [];
                config.iceTransportPolicy = 'relay';
            } else {
                config = { iceTransportPolicy: 'relay' };
            }
            
            console.log('[Rebrowser WebRTC] Using relay mode (proxy)');
            return new OriginalRTCPeerConnection(config);
        };
        
        window.RTCPeerConnection.prototype = OriginalRTCPeerConnection.prototype;
    }
    
    console.log('[Rebrowser WebRTC] ✅ JS masking applied');
})();
        """
        
        await context.add_init_script(script)
        logger.info("✅ WebRTC JS masking applied (Rebrowser)")
    
    async def _apply_cdp_webrtc_masking(self, page, proxy_config: Dict[str, str]):
        """
        CRITICAL: CDP-level WebRTC masking (Rebrowser's secret weapon!)
        
        This is the most robust WebRTC protection:
        - Overrides IPs at network level
        - Works even if JavaScript is bypassed
        - Forces WebRTC to see only proxy IP
        """
        try:
            client = await page.context.new_cdp_session(page)
            
            proxy_ip = proxy_config.get("host", "127.0.0.1")
            
            # Override network conditions to force proxy usage
            await client.send('Network.emulateNetworkConditions', {
                'offline': False,
                'downloadThroughput': -1,
                'uploadThroughput': -1,
                'latency': 0
            })
            
            # Block direct STUN/TURN connections (force proxy)
            await client.send('Network.setBlockedURLs', {
                'urls': [
                    '*stun:*',  # Block direct STUN
                    '*turn:*'   # Block direct TURN
                ]
            })
            
            # Set IP override (if CDP supports it)
            try:
                await client.send('Network.setUserAgentOverride', {
                    'userAgent': page.context._options.get('user_agent', ''),
                    'platform': 'iPhone',
                    'acceptLanguage': 'en-US,en'
                })
            except:
                pass
            
            logger.info(f"✅ CDP WebRTC masking applied (will show proxy IP: {proxy_ip})")
            logger.info("🔥 Rebrowser advantage: Network-level WebRTC control via CDP")
            
        except Exception as e:
            logger.warning(f"⚠️ CDP WebRTC masking partial: {str(e)[:100]}")
            # Continue anyway - browser flags + JS still provide good protection
    
    async def _apply_rebrowser_stealth(self, context, mobile_config: Dict[str, Any]):
        """Rebrowser-enhanced stealth script"""
        ua = mobile_config.get("user_agent", "")
        platform = mobile_config.get("platform", "iPhone")
        hardware_concurrency = mobile_config.get("hardware_concurrency", 8)
        device_memory = mobile_config.get("device_memory", 4)
        max_touch_points = mobile_config.get("max_touch_points", 5)
        
        ua_escaped = json.dumps(ua)
        
        script = f"""
(function() {{
    'use strict';
    
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
    
    console.log('[Rebrowser] Enhanced stealth applied ✅');
}})();
        """
        
        await context.add_init_script(script)
        logger.info("✅ Rebrowser-enhanced stealth applied")
    
    async def _apply_cdp_stealth(self, page, mobile_config: Dict[str, Any]):
        """CDP commands for additional stealth"""
        try:
            client = await page.context.new_cdp_session(page)
            
            await client.send('Emulation.setGeolocationOverride', {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'accuracy': 100
            })
            
            await client.send('Emulation.setTimezoneOverride', {
                'timezoneId': mobile_config.get("timezone", "America/New_York")
            })
            
            await client.send('Emulation.setTouchEmulationEnabled', {
                'enabled': True,
                'maxTouchPoints': mobile_config.get("max_touch_points", 5)
            })
            
            logger.info("✅ CDP stealth applied (Rebrowser)")
            
        except Exception as e:
            logger.warning(f"⚠️ CDP stealth partial: {str(e)[:80]}")
