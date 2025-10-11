"""
PATCHRIGHT RUNNER ENHANCED - With COMPLETE WebRTC Blocking + BrowserForge

WebRTC Strategy - COMPLETE BLOCKING:
- Leverage Patchright's browser patches
- Disable WebRTC at browser flag level
- Block all WebRTC APIs via JavaScript
- Prevent STUN/TURN connections
- BrowserForge intelligent fingerprints
"""

import logging
import time
from typing import Dict, Any

from ..core.test_result import TestResult
from .base_runner_enhanced import BaseRunner

logger = logging.getLogger(__name__)


class PatchrightRunnerEnhanced(BaseRunner):
    """Patchright runner with browser patches + COMPLETE WebRTC blocking + BrowserForge"""
    
    def __init__(self, screenshot_engine=None):
        super().__init__(screenshot_engine)
        logger.info("Patchright runner initialized (patches + WebRTC BLOCKED + BrowserForge)")
    
    async def run_test(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 15
    ) -> TestResult:
        """Run test with Patchright's patches + COMPLETE WebRTC blocking + BrowserForge"""
        start_time = time.time()
        logger.info(f"🎭 Testing Patchright (BrowserForge) on {url_name}: {url}")
        
        try:
            from patchright.async_api import async_playwright
        except ImportError:
            error_msg = "patchright not installed. Run: pip install patchright"
            logger.error(error_msg)
            return TestResult(
                library="patchright",
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
                
                # Get enhanced mobile config with BrowserForge
                enhanced_config = self.get_enhanced_mobile_config(
                    mobile_config=mobile_config,
                    device_type="iphone_x",
                    use_browserforge=True
                )
                
                # Log enhancement status
                if enhanced_config.get('_browserforge_enhanced'):
                    logger.info(f"🎭 Using BrowserForge fingerprint: {enhanced_config.get('device_name')}")
                else:
                    logger.info(f"📱 Using standard profile: {enhanced_config.get('device_name')}")
                
                # Patchright launch args + AGGRESSIVE WebRTC blocking
                browser = await p.chromium.launch(
                    headless=True,
                    proxy=proxy,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        
                        # AGGRESSIVE WebRTC blocking flags
                        '--disable-webrtc',
                        '--disable-rtc-smoothness-algorithm',
                        '--disable-webrtc-hw-decoding',
                        '--disable-webrtc-hw-encoding',
                        '--disable-webrtc-encryption',
                        '--disable-webrtc-hw-vp8-encoding',
                        '--disable-webrtc-hw-vp9-encoding',
                        '--enforce-webrtc-ip-permission-check',
                        '--force-webrtc-ip-handling-policy=disable_non_proxied_udp',
                        '--webrtc-ip-handling-policy=disable_non_proxied_udp',
                    ]
                )
                
                # Enhanced mobile context
                context = await browser.new_context(
                    user_agent=enhanced_config.get("user_agent"),
                    viewport=enhanced_config.get("viewport"),
                    device_scale_factor=enhanced_config.get("device_scale_factor", 2),
                    is_mobile=True,
                    has_touch=True,
                    locale=enhanced_config.get("language", "en-US").replace("_", "-"),
                    timezone_id=enhanced_config.get("timezone", "America/New_York"),
                    permissions=['geolocation'],
                    geolocation={"latitude": 37.7749, "longitude": -122.4194}
                )
                
                # Apply Patchright stealth + COMPLETE WebRTC blocking + BrowserForge
                await self._apply_complete_webrtc_block_with_browserforge(context, enhanced_config)
                
                page = await context.new_page()
                
                logger.info(f"Navigating to {url}")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Extra wait for dynamic pages
                await self._extra_wait_for_dynamic_pages(url, url_name)
                
                # Capture screenshot
                screenshot_path = await self.screenshot_engine.capture_with_wait(
                    page, "patchright_browserforge", url_name, wait_time, page=page
                )
                
                # Check results
                proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
                is_mobile = await self._check_mobile_ua(page, enhanced_config)
                
                await browser.close()
                
                execution_time = time.time() - start_time
                logger.info(f"✅ Patchright (BrowserForge) test completed in {execution_time:.2f}s")
                
                return TestResult(
                    library="patchright_browserforge",
                    category="playwright",
                    test_name=url_name,
                    url=url,
                    success=True,
                    detected_ip=detected_ip,
                    user_agent=enhanced_config.get("user_agent"),
                    proxy_working=proxy_working,
                    is_mobile_ua=is_mobile,
                    screenshot_path=screenshot_path,
                    execution_time=execution_time,
                    additional_data={
                        'browserforge_enhanced': enhanced_config.get('_browserforge_enhanced', False),
                        'device_name': enhanced_config.get('device_name'),
                        'webrtc_blocked': True
                    }
                )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)[:500]
            logger.error(f"❌ Patchright (BrowserForge) test failed: {error_msg}")
            
            return TestResult(
                library="patchright_browserforge",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
    
    async def _apply_complete_webrtc_block_with_browserforge(self, context, enhanced_config: Dict[str, Any]):
        """
        COMPLETE WebRTC blocking + Patchright stealth + BrowserForge
        
        Combines Patchright's browser-level patches with complete WebRTC blocking
        """
        platform = enhanced_config.get("platform", "iPhone")
        hardware_concurrency = enhanced_config.get('hardware_concurrency', 4)
        device_memory = enhanced_config.get('device_memory', 4)
        webgl_vendor = enhanced_config.get('webgl_vendor', 'Apple Inc.')
        webgl_renderer = enhanced_config.get('webgl_renderer', 'Apple GPU')
        language = enhanced_config.get('language', 'en-US')
        languages = enhanced_config.get('languages', ['en-US', 'en'])
        max_touch_points = enhanced_config.get('max_touch_points', 5)
        
        # Convert languages list to JavaScript array
        languages_str = str(languages).replace("'", '"')
        
        script = f"""
(function() {{
    'use strict';
    
    console.log('[Patchright + BrowserForge] Enhanced stealth + COMPLETE WebRTC blocking active');
    
    // ==========================================
    // COMPLETE WebRTC BLOCKING - IP LEAK PREVENTION
    // ==========================================
    
    // Block RTCPeerConnection COMPLETELY
    if (typeof RTCPeerConnection !== 'undefined') {{
        const blockMessage = 'RTCPeerConnection is disabled for privacy';
        
        window.RTCPeerConnection = class {{
            constructor() {{
                throw new Error(blockMessage);
            }}
        }};
        
        Object.defineProperty(window, 'RTCPeerConnection', {{
            value: window.RTCPeerConnection,
            writable: false,
            configurable: false
        }});
    }}
    
    // Block webkitRTCPeerConnection
    if (typeof webkitRTCPeerConnection !== 'undefined') {{
        window.webkitRTCPeerConnection = class {{
            constructor() {{
                throw new Error('webkitRTCPeerConnection is disabled');
            }}
        }};
        
        Object.defineProperty(window, 'webkitRTCPeerConnection', {{
            value: window.webkitRTCPeerConnection,
            writable: false,
            configurable: false
        }});
    }}
    
    // Block mozRTCPeerConnection (Firefox)
    if (typeof mozRTCPeerConnection !== 'undefined') {{
        window.mozRTCPeerConnection = class {{
            constructor() {{
                throw new Error('mozRTCPeerConnection is disabled');
            }}
        }};
    }}
    
    // Block getUserMedia (all variants)
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {{
        navigator.mediaDevices.getUserMedia = function() {{
            return Promise.reject(new DOMException('Permission denied', 'NotAllowedError'));
        }};
    }}
    
    if (navigator.getUserMedia) {{
        navigator.getUserMedia = function(constraints, success, error) {{
            if (error) error(new DOMException('Permission denied', 'NotAllowedError'));
        }};
    }}
    
    if (navigator.webkitGetUserMedia) {{
        navigator.webkitGetUserMedia = function(constraints, success, error) {{
            if (error) error(new DOMException('Permission denied', 'NotAllowedError'));
        }};
    }}
    
    if (navigator.mozGetUserMedia) {{
        navigator.mozGetUserMedia = function(constraints, success, error) {{
            if (error) error(new DOMException('Permission denied', 'NotAllowedError'));
        }};
    }}
    
    // Block enumerateDevices
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {{
        navigator.mediaDevices.enumerateDevices = function() {{
            return Promise.resolve([]);
        }};
    }}
    
    // Block RTCDataChannel
    if (typeof RTCDataChannel !== 'undefined') {{
        window.RTCDataChannel = class {{
            constructor() {{
                throw new Error('RTCDataChannel is disabled');
            }}
        }};
    }}
    
    // Block RTCSessionDescription
    if (typeof RTCSessionDescription !== 'undefined') {{
        window.RTCSessionDescription = undefined;
    }}
    
    // Block RTCIceCandidate
    if (typeof RTCIceCandidate !== 'undefined') {{
        window.RTCIceCandidate = undefined;
    }}
    
    console.log('[WebRTC] ✅ COMPLETE blocking applied - NO IP LEAKS');
    
    // ==========================================
    // PATCHRIGHT STEALTH + BROWSERFORGE ENHANCEMENTS
    // ==========================================
    
    // Hide webdriver
    Object.defineProperty(navigator, 'webdriver', {{
        get: () => undefined,
        configurable: true
    }});
    
    // BrowserForge: Platform override
    Object.defineProperty(navigator, 'platform', {{
        get: () => '{platform}',
        configurable: true
    }});
    
    // BrowserForge: Hardware concurrency
    Object.defineProperty(navigator, 'hardwareConcurrency', {{
        get: () => {hardware_concurrency},
        configurable: true
    }});
    
    // BrowserForge: Device memory
    Object.defineProperty(navigator, 'deviceMemory', {{
        get: () => {device_memory},
        configurable: true
    }});
    
    // BrowserForge: Max touch points
    Object.defineProperty(navigator, 'maxTouchPoints', {{
        get: () => {max_touch_points},
        configurable: true
    }});
    
    // BrowserForge: Languages
    Object.defineProperty(navigator, 'language', {{
        get: () => '{language}',
        configurable: true
    }});
    
    Object.defineProperty(navigator, 'languages', {{
        get: () => {languages_str},
        configurable: true
    }});
    
    // Chrome runtime
    if (!window.chrome) {{
        window.chrome = {{}};
    }}
    window.chrome.runtime = {{
        connect: () => ({{}}),
        sendMessage: () => ({{}})
    }};
    
    // BrowserForge: WebGL fingerprint
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
        if (parameter === 37445) return '{webgl_vendor}';
        if (parameter === 37446) return '{webgl_renderer}';
        return getParameter.call(this, parameter);
    }};
    
    if (typeof WebGL2RenderingContext !== 'undefined') {{
        const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return '{webgl_vendor}';
            if (parameter === 37446) return '{webgl_renderer}';
            return getParameter2.call(this, parameter);
        }};
    }}
    
    console.log('[Patchright + BrowserForge] ✅ Browser patches + stealth + WebRTC blocking + fingerprints active');
}})();
        """
        
        await context.add_init_script(script)
        logger.info("✅ Patchright: Browser patches + COMPLETE WebRTC blocking + BrowserForge stealth applied")
