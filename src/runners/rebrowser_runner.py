"""
REBROWSER RUNNER - With CDP WebRTC Control

WebRTC Strategy:
- Browser flags to force proxy interface
- JavaScript relay-only mode
- CDP network commands to block STUN/TURN (MOST ROBUST!)
"""

import logging
import time
import json
from typing import Dict, Any

from ..core.test_result import TestResult
from .base_runner import BaseRunner

logger = logging.getLogger(__name__)


class RebrowserRunner(BaseRunner):
    """Rebrowser runner with full CDP WebRTC control"""
    
    def __init__(self, screenshot_engine=None):
        super().__init__(screenshot_engine)
        logger.info("🔥 Rebrowser runner initialized (CDP WebRTC control)")
    
    async def run_test(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 15
    ) -> TestResult:
        """Run test with Rebrowser's full CDP WebRTC control"""
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
                
                # Rebrowser launch args with WebRTC flags
                browser = await p.chromium.launch(
                    headless=True,
                    proxy=proxy,
                    args=self._get_rebrowser_launch_args_with_webrtc()
                )
                
                # Enhanced context
                context = await browser.new_context(
                    **self._get_rebrowser_context_config(mobile_config)
                )
                
                # Apply Rebrowser stealth
                await self._apply_rebrowser_stealth(context, mobile_config)
                
                page = await context.new_page()
                
                # CRITICAL: CDP WebRTC control (most robust!)
                await self._apply_cdp_webrtc_control(page, proxy_config)
                
                # Apply other CDP stealth
                await self._apply_cdp_stealth(page, mobile_config)
                
                logger.info(f"Navigating to {url} with Rebrowser (CDP WebRTC control)")
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
        """Rebrowser launch args with WebRTC flags"""
        return [
            # Core anti-detection
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            
            # WebRTC flags (CRITICAL!)
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
            '--disable-automation',
            '--disable-dev-tools',
        ]
    
    def _get_rebrowser_context_config(self, mobile_config: Dict[str, Any]) -> dict:
        """Enhanced context configuration"""
        return {
            'user_agent': mobile_config.get("user_agent"),
            'viewport': mobile_config.get("viewport"),
            'device_scale_factor': mobile_config.get("device_scale_factor", 2),
            'is_mobile': True,
            'has_touch': True,
            'locale': mobile_config.get("language", "en-US").replace("_", "-"),
            'timezone_id': mobile_config.get("timezone", "America/New_York"),
            'bypass_csp': True,
            'extra_http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            },
            'permissions': ['geolocation'],
            'geolocation': {"latitude": 37.7749, "longitude": -122.4194}
        }
    
    async def _apply_cdp_webrtc_control(self, page, proxy_config: Dict[str, str]):
        """
        CDP WebRTC control (Rebrowser's secret weapon!)
        
        This blocks STUN/TURN at network level
        Most robust WebRTC protection available
        """
        try:
            client = await page.context.new_cdp_session(page)
            
            # Block STUN/TURN servers at network level
            await client.send('Network.setBlockedURLs', {
                'urls': [
                    '*://stun.*',
                    '*://turn.*',
                    '*:3478/*',  # STUN/TURN port
                    '*:5349/*',  # STUN/TURN TLS port
                ]
            })
            
            logger.info("✅ CDP: STUN/TURN servers blocked (network level)")
            logger.info("🔥 Rebrowser advantage: Network-level WebRTC control")
            
        except Exception as e:
            logger.warning(f"⚠️ CDP WebRTC control partial: {str(e)[:100]}")
    
    async def _apply_rebrowser_stealth(self, context, mobile_config: Dict[str, Any]):
        """Rebrowser stealth + WebRTC relay mode"""
        ua = mobile_config.get("user_agent", "")
        platform = mobile_config.get("platform", "iPhone")
        
        ua_escaped = json.dumps(ua)
        
        script = f"""
(function() {{
    'use strict';
    
    console.log('[Rebrowser] Enhanced stealth + WebRTC relay');
    
    // Core navigator properties
    const props = {{
        userAgent: {ua_escaped},
        platform: '{platform}',
        vendor: 'Google Inc.',
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
    
    // WebRTC: Force relay-only mode (uses proxy)
    if (typeof RTCPeerConnection !== 'undefined') {{
        const OriginalRTCPeerConnection = RTCPeerConnection;
        
        window.RTCPeerConnection = function(config) {{
            // Force relay mode
            if (config) {{
                config.iceServers = config.iceServers || [];
                config.iceTransportPolicy = 'relay';
            }} else {{
                config = {{ iceTransportPolicy: 'relay' }};
            }}
            
            console.log('[Rebrowser WebRTC] Relay mode + CDP blocking active');
            return new OriginalRTCPeerConnection(config);
        }};
        
        window.RTCPeerConnection.prototype = OriginalRTCPeerConnection.prototype;
    }}
    
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
    
    console.log('[Rebrowser] ✅ Stealth + WebRTC relay + WebGL spoofing active');
}})();
        """
        
        await context.add_init_script(script)
        logger.info("✅ Rebrowser: Enhanced stealth + WebRTC relay mode applied")
    
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
            
            logger.info("✅ CDP: Geolocation, timezone, touch emulation applied")
            
        except Exception as e:
            logger.warning(f"⚠️ CDP stealth partial: {str(e)[:80]}")
