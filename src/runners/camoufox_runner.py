"""
CAMOUFOX RUNNER - Firefox-Based Stealth Browser

Camoufox is a Firefox-based browser with:
- Different browser engine (not Chromium)
- Built-in humanization
- GeoIP-based fingerprints
- Natural mouse movements and timing

Best for: Different fingerprint, Firefox-based detection evasion
"""

import logging
import time
from typing import Dict, Any

from ..core.test_result import TestResult
from .base_runner import BaseRunner

logger = logging.getLogger(__name__)


class CamoufoxRunner(BaseRunner):
    """Camoufox runner with Firefox-based stealth"""
    
    def __init__(self, screenshot_engine=None):
        super().__init__(screenshot_engine)
        logger.info("Camoufox runner initialized (Firefox-based, humanized)")
    
    async def run_test(
        self,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 15
    ) -> TestResult:
        """Run test with Camoufox's Firefox-based stealth"""
        start_time = time.time()
        logger.info(f"🎭 Testing Camoufox on {url_name}: {url}")
        
        try:
            from camoufox.async_api import AsyncCamoufox
        except ImportError:
            error_msg = "camoufox not installed. Run: pip install 'camoufox[geoip]'"
            logger.error(error_msg)
            return TestResult(
                library="camoufox",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=error_msg,
                execution_time=time.time() - start_time
            )
        
        try:
            # Build proxy dict (Camoufox uses different format)
            proxy_dict = None
            if proxy_config.get("host"):
                proxy_dict = {
                    "server": f"http://{proxy_config['host']}:{proxy_config['port']}"
                }
                if proxy_config.get("username") and proxy_config.get("password"):
                    proxy_dict["username"] = proxy_config["username"]
                    proxy_dict["password"] = proxy_config["password"]
                logger.info(f"Proxy: {proxy_dict['server']}")
            
            # Camoufox configuration
            async with AsyncCamoufox(
                headless=True,
                proxy=proxy_dict,
                humanize=True,  # Built-in human-like behavior
                geoip=True if self.geoip else False,  # GeoIP-based fingerprints
                # Camoufox handles stealth automatically!
            ) as browser:
                
                page = await browser.new_page()
                
                # Set mobile viewport
                viewport = mobile_config.get("viewport", {"width": 375, "height": 812})
                await page.set_viewport_size(viewport)
                
                # Camoufox has built-in Firefox stealth, minimal additional JS
                await self._apply_camoufox_stealth(page, mobile_config)
                
                logger.info(f"Navigating to {url} with Camoufox")
                await page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Extra wait for dynamic pages
                await self._extra_wait_for_dynamic_pages(url, url_name)
                
                # Capture screenshot
                screenshot_path = await self.screenshot_engine.capture_with_wait(
                    page, "camoufox", url_name, wait_time, page=page
                )
                
                # Check results
                proxy_working, detected_ip = await self._check_proxy(page, proxy_config)
                is_mobile = await self._check_mobile_ua(page, mobile_config)
                
                await browser.close()
                
                execution_time = time.time() - start_time
                logger.info(f"✅ Camoufox test completed in {execution_time:.2f}s")
                
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
                    execution_time=execution_time
                )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)[:500]
            logger.error(f"❌ Camoufox test failed: {error_msg}")
            
            return TestResult(
                library="camoufox",
                category="playwright",
                test_name=url_name,
                url=url,
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
    
    async def _apply_camoufox_stealth(self, page, mobile_config: Dict[str, Any]):
        """
        Minimal stealth for Camoufox
        
        Camoufox already has built-in Firefox stealth and humanization,
        so we only add minimal JavaScript-level hiding.
        """
        script = """
(function() {
    'use strict';
    
    // Firefox doesn't have navigator.webdriver in the same way,
    // but we hide it anyway
    try {
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });
    } catch(e) {}
    
    console.log('[Camoufox] Firefox stealth + humanization active');
})();
        """
        
        await page.evaluate(script)
        logger.info("✅ Camoufox stealth applied (Firefox + humanization)")
