"""
MINIMAL STEALTH VERSION - For diagnosis
Remove aggressive blocking to see what's causing "collecting data..."
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
    """Minimal stealth runner for diagnosis"""
    
    def __init__(self, screenshot_engine: Optional[ScreenshotEngine] = None):
        self.screenshot_engine = screenshot_engine or ScreenshotEngine()
        self.profile_loader = DeviceProfileLoader()
        logger.info("Playwright runner initialized (MINIMAL STEALTH MODE)")
    
    async def run_test(
        self,
        library_name: str,
        url: str,
        url_name: str,
        proxy_config: Dict[str, str],
        mobile_config: Dict[str, Any],
        wait_time: int = 5
    ) -> TestResult:
        """Run test with minimal stealth"""
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
        """Run with MINIMAL stealth - just basic mobile config"""
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            proxy = self._build_proxy(proxy_config) if proxy_config.get("host") else None
            
            # Launch with minimal args
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            # Create context with just mobile settings - NO STEALTH
            context = await browser.new_context(
                user_agent=mobile_config.get("user_agent"),
                viewport=mobile_config.get("viewport"),
                device_scale_factor=mobile_config.get("device_scale_factor", 2),
                is_mobile=mobile_config.get("is_mobile", True),
                has_touch=mobile_config.get("has_touch", True),
                locale="en-US",
                timezone_id="America/New_York"
            )
            
            # NO INIT SCRIPT - Let's see if pages load without any stealth
            logger.info("⚠️ MINIMAL MODE: No stealth scripts applied")
            
            page = await context.new_page()
            
            logger.info(f"Navigating to {url}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                logger.info("✅ Page loaded (networkidle)")
            except Exception as e:
                logger.warning(f"Navigation warning: {e}")
                # Try to continue anyway
            
            # Capture screenshot
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "playwright", url_name, wait_time, page=page
            )
            
            # Check results
            proxy_working = False
            detected_ip = None
            is_mobile = True  # Assume yes for now
            
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
    
    async def _run_patchright(self, url: str, url_name: str, proxy_config: Dict[str, str], 
                             mobile_config: Dict[str, Any], wait_time: int) -> TestResult:
        """Patchright implementation"""
        from patchright.async_api import async_playwright
        
        async with async_playwright() as p:
            proxy = self._build_proxy(proxy_config) if proxy_config.get("host") else None
            browser = await p.chromium.launch(headless=True, proxy=proxy)
            
            context = await browser.new_context(
                user_agent=mobile_config.get("user_agent"),
                viewport=mobile_config.get("viewport"),
                device_scale_factor=mobile_config.get("device_scale_factor", 2),
                is_mobile=True,
                has_touch=True
            )
            
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "patchright", url_name, wait_time, page=page
            )
            
            await browser.close()
            
            return TestResult(
                library="patchright",
                category="playwright",
                test_name=url_name,
                url=url,
                success=True,
                screenshot_path=screenshot_path,
                execution_time=0
            )
    
    async def _run_camoufox(self, url: str, url_name: str, proxy_config: Dict[str, str],
                           mobile_config: Dict[str, Any], wait_time: int) -> TestResult:
        """Camoufox implementation"""
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
            
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "camoufox", url_name, wait_time, page=page
            )
            
            await browser.close()
            
            return TestResult(
                library="camoufox",
                category="playwright",
                test_name=url_name,
                url=url,
                success=True,
                screenshot_path=screenshot_path,
                execution_time=0
            )
    
    async def _run_rebrowser(self, url: str, url_name: str, proxy_config: Dict[str, str],
                            mobile_config: Dict[str, Any], wait_time: int) -> TestResult:
        """Rebrowser implementation"""
        from rebrowser_playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            proxy = self._build_proxy(proxy_config) if proxy_config.get("host") else None
            browser = await p.chromium.launch(headless=True, proxy=proxy)
            
            context = await browser.new_context(
                user_agent=mobile_config.get("user_agent"),
                viewport=mobile_config.get("viewport"),
                device_scale_factor=mobile_config.get("device_scale_factor", 2),
                is_mobile=True,
                has_touch=True
            )
            
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            screenshot_path = await self.screenshot_engine.capture_with_wait(
                page, "rebrowser_playwright", url_name, wait_time, page=page
            )
            
            await browser.close()
            
            return TestResult(
                library="rebrowser_playwright",
                category="playwright",
                test_name=url_name,
                url=url,
                success=True,
                screenshot_path=screenshot_path,
                execution_time=0
            )
