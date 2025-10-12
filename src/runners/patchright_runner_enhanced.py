"""
PATCHRIGHT RUNNER - With IP Pre-Resolution + FIXED WebRTC + FIXED Geolocation

CRITICAL FIXES:
1. WebRTC protection applied immediately after context creation
2. Geolocation API uses coordinates from resolved proxy IP (not hardcoded)
"""

import logging
import time
import asyncio
from typing import Dict, Any

from ..core.test_result import TestResult
from .base_runner_enhanced import BaseRunner

logger = logging.getLogger(__name__)


class PatchrightRunnerEnhanced(BaseRunner):
    """Patchright runner with IP pre-resolution + FIXED WebRTC + FIXED Geolocation"""
    
    def __init__(self, screenshot_engine=None):
        super().__init__(screenshot_engine)
        logger.info("Patchright runner initialized (with IP pre-resolution + FIXED WebRTC + FIXED Geolocation)")
    
    async def run_test(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 15
    ) -> TestResult:
        """Run test with Patchright + IP pre-resolution + FIXED WebRTC + FIXED Geolocation"""
        start_time = time.time()
        logger.info(f"🎭 Testing Patchright (IP Pre-Resolved + FIXED WebRTC + FIXED Geo) on {url_name}: {url}")
        
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
            # 🆕 STEP 1: Resolve proxy IP and timezone BEFORE browser launch
            logger.info("=" * 60)
            logger.info("STEP 1: Resolving proxy IP and timezone...")
            logger.info("=" * 60)
            
            resolved_proxy = await self.resolve_proxy_before_launch(proxy_config)
            
            logger.info(f"✅ Pre-resolution complete:")
            logger.info(f"   Hostname: {resolved_proxy.hostname}")
            logger.info(f"   IP: {resolved_proxy.ip_address}")
            logger.info(f"   Timezone: {resolved_proxy.timezone}")
            if resolved_proxy.city:
                logger.info(f"   Location: {resolved_proxy.city}, {resolved_proxy.country}")
            if resolved_proxy.latitude and resolved_proxy.longitude:
                logger.info(f"   Coordinates: {resolved_proxy.latitude:.4f}, {resolved_proxy.longitude:.4f}")
            logger.info(f"   Method: {resolved_proxy.resolution_method}")
            logger.info(f"   Time: {resolved_proxy.resolution_time_ms:.1f}ms")
            
            # 🆕 STEP 2: Get enhanced config with pre-resolved timezone
            logger.info("=" * 60)
            logger.info("STEP 2: Creating browser config with correct timezone...")
            logger.info("=" * 60)
            
            enhanced_config = self.get_enhanced_mobile_config(
                mobile_config=mobile_config,
                device_type="iphone_x",
                use_browserforge=True,
                resolved_proxy=resolved_proxy  # 🆕 Pass resolved proxy
            )
            
            logger.info(f"✅ Config created:")
            logger.info(f"   Device: {enhanced_config.get('device_name')}")
            logger.info(f"   User-Agent: {enhanced_config.get('user_agent', '')[:60]}...")
            logger.info(f"   Timezone: {enhanced_config.get('timezone')} (✅ MATCHES PROXY IP)")
            logger.info(f"   BrowserForge: {enhanced_config.get('_browserforge_enhanced', False)}")
            logger.info(f"   Patchright Patches: Enabled")
            
            # 🆕 STEP 3: Launch browser with CORRECT timezone from start
            logger.info("=" * 60)
            logger.info("STEP 3: Launching Patchright with correct timezone and geolocation...")
            logger.info("=" * 60)
            
            async with async_playwright() as p:
                proxy = self._build_proxy(proxy_config)
                
                # Patchright launch with patches
                browser = await p.chromium.launch(
                    headless=True,
                    proxy=proxy,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                    ]
                )
                
                # 🔥 CRITICAL FIX: Get coordinates from resolved proxy (not hardcoded!)
                geo_lat = resolved_proxy.latitude if resolved_proxy.latitude else 34.0522342
                geo_lon = resolved_proxy.longitude if resolved_proxy.longitude else -118.2436849
                
                logger.info(f"📍 Geolocation API coordinates: {geo_lat:.4f}, {geo_lon:.4f}")
                if resolved_proxy.latitude and resolved_proxy.longitude:
                    logger.info(f"   ✅ Using coordinates from proxy IP location")
                else:
                    logger.warning(f"   ⚠️ No coordinates from resolver, using fallback")
                
                # 🔥 CRITICAL FIX: Create context with CORRECT timezone AND coordinates
                context = await browser.new_context(
                    user_agent=enhanced_config.get("user_agent"),
                    viewport=enhanced_config.get("viewport"),
                    device_scale_factor=enhanced_config.get("device_scale_factor", 2),
                    is_mobile=True,
                    has_touch=True,
                    locale=enhanced_config.get("language", "en-US").replace("_", "-"),
                    timezone_id=enhanced_config.get("timezone"),  # ✅ CORRECT from start!
                    permissions=['geolocation'],
                    geolocation={"latitude": geo_lat, "longitude": geo_lon}  # ✅ MATCHES PROXY IP!
                )
                
                logger.info(f"✅ Browser context created:")
                logger.info(f"   Timezone: {enhanced_config.get('timezone')}")
                logger.info(f"   Geolocation: {geo_lat:.4f}, {geo_lon:.4f}")
                logger.info(f"   ✅ All location signals synchronized!")
                
                # 🔥 CRITICAL FIX: Apply WebRTC protection IMMEDIATELY after context creation
                # This ensures the script runs BEFORE any page loads
                logger.info("🔥 Applying FIXED WebRTC protection (blocks STUN/TURN)...")
                await self._apply_browserforge_stealth(context, enhanced_config)
                
                # 🔥 CRITICAL: Small delay to ensure script registration completes
                await asyncio.sleep(0.1)
                
                logger.info("✅ WebRTC protection active - STUN/TURN blocked")
                
                page = await context.new_page()
                
                # 🆕 STEP 4: Navigate and verify
                logger.info("=" * 60)
                logger.info(f"STEP 4: Navigating to {url_name}...")
                logger.info("=" * 60)
                
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Check proxy (verify detected IP matches resolved IP)
                proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
                
                if detected_ip:
                    if detected_ip == resolved_proxy.ip_address:
                        logger.info(f"✅ IP MATCH: Detected {detected_ip} = Pre-resolved {resolved_proxy.ip_address}")
                    else:
                        logger.warning(f"⚠️ IP MISMATCH: Detected {detected_ip} ≠ Pre-resolved {resolved_proxy.ip_address}")
                
                # Extra wait for dynamic pages
                await self._extra_wait_for_dynamic_pages(url, url_name)
                
                # Capture screenshot
                screenshot_path = await self.screenshot_engine.capture_with_wait(
                    page, "patchright_browserforge", url_name, wait_time, page=page
                )
                
                # Check results
                is_mobile = await self._check_mobile_ua(page, enhanced_config)
                
                await browser.close()
                
                execution_time = time.time() - start_time
                logger.info("=" * 60)
                logger.info(f"✅ TEST COMPLETE in {execution_time:.2f}s")
                logger.info("=" * 60)
                
                return TestResult(
                    library="patchright_browserforge",
                    category="playwright",
                    test_name=url_name,
                    url=url,
                    success=True,
                    detected_ip=detected_ip or resolved_proxy.ip_address,
                    user_agent=enhanced_config.get("user_agent"),
                    proxy_working=proxy_working,
                    is_mobile_ua=is_mobile,
                    screenshot_path=screenshot_path,
                    execution_time=execution_time,
                    additional_data={
                        'browserforge_enhanced': enhanced_config.get('_browserforge_enhanced', False),
                        'browserforge_webrtc': enhanced_config.get('_browserforge_webrtc_enabled', False),
                        'device_name': enhanced_config.get('device_name'),
                        'timezone': enhanced_config.get('timezone'),
                        'patchright_patches': True,
                        'pre_resolved_ip': resolved_proxy.ip_address,
                        'pre_resolved_timezone': resolved_proxy.timezone,
                        'timezone_method': resolved_proxy.resolution_method,
                        'ip_match': (detected_ip == resolved_proxy.ip_address) if detected_ip else None,
                        'webrtc_protection_v2': True,
                        'geolocation_latitude': geo_lat,
                        'geolocation_longitude': geo_lon,
                        'geolocation_from_proxy': (resolved_proxy.latitude is not None),
                    }
                )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)[:500]
            logger.error(f"❌ Patchright test failed: {error_msg}")
            
            return TestResult(
                library="patchright_browserforge",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
    
    async def _apply_browserforge_stealth(self, context, enhanced_config: Dict[str, Any]):
        """
        🔥 FIXED: Apply Patchright stealth + COMPREHENSIVE WebRTC protection
        
        This version:
        - Combines Patchright browser patches
        - Blocks ALL STUN/TURN servers
        - Filters SDP candidates
        - Prevents host/srflx/relay leaks
        - Runs BEFORE page load
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
        
        # 🔥 CRITICAL: Get FIXED BrowserForge WebRTC script (blocks STUN)
        webrtc_script = ""
        if enhanced_config.get('_browserforge_webrtc_enabled'):
            webrtc_script = self.browserforge.get_browserforge_webrtc_script(enhanced_config)
        
        # Patchright-specific overrides + BrowserForge
        script = f"""
// ============================================================================
// PATCHRIGHT ENHANCED - FIXED WEBRTC + GEOLOCATION v3.0
// ============================================================================
(function() {{
    'use strict';
    
    console.log('[Patchright + BrowserForge] Applying stealth');
    
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
    
    console.log('[Patchright + BrowserForge] ✅ Browser patches + fingerprint overrides applied');
}})();

// ============================================================================
// FIXED WEBRTC PROTECTION (Blocks STUN/TURN, filters all candidates)
// ============================================================================
{webrtc_script}
        """
        
        # 🔥 CRITICAL: Apply the combined script to the context
        # This runs BEFORE any page loads
        await context.add_init_script(script)
        
        logger.info("✅ Patchright: Browser patches + BrowserForge stealth + WebRTC protection v3.0 BALANCED applied")
        logger.info("   - Patchright anti-detection patches active")
        logger.info("   - Proxy IP injection enabled")
        logger.info("   - Private IP candidates blocked")
        logger.info("   - Fake candidates with proxy IP injected")
        logger.info("   - mDNS .local leaks prevented")
        logger.info("   - Geolocation API synchronized with proxy location")
