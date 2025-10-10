"""
STEALTH BROWSER TESTING FRAMEWORK - Screenshot Engine (COMPLETE FIXED)
Intelligent screenshot capture with proper wait times for heavy pages

Authors: kravitzcoder & Claude

CRITICAL FIX: Increased wait times for pixelscan.net and other heavy detection sites
"""
import logging
import asyncio
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Any
import base64

logger = logging.getLogger(__name__)


class ScreenshotEngine:
    """Engine for capturing and managing screenshots during tests"""
    
    def __init__(self):
        self.screenshots_dir = Path("test_results") / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Screenshot engine initialized. Directory: {self.screenshots_dir}")
    
    async def capture_with_wait(
        self, 
        browser_instance: Any, 
        library_name: str, 
        url_name: str,
        wait_time: int = 30,  # Default 30 seconds
        page: Any = None
    ) -> Optional[str]:
        """
        Capture screenshot with intelligent wait times
        
        FIXED: Proper wait times for heavy pages like pixelscan.net
        """
        try:
            # Intelligent wait configuration for different page types
            wait_config = {
                'pixelscan': 45,     # Pixelscan needs LONG time (was 35s, now 45s)
                'fingerprint': 45,   # Fingerprint analysis is heavy (was 35s, now 45s)
                'ip_check': 35,      # IP check with WebRTC analysis (was 30s, now 35s)
                'bot_check': 35,     # Bot detection analysis (was 30s, now 35s)
                'creepjs': 30,       # CreepJS analysis (was 25s, now 30s)
                'workers': 25,       # Worker analysis
                'ip': 30,            # Generic IP check
            }
            
            # Determine wait time based on URL/test name
            determined_wait = wait_time  # Default from parameter
            
            for keyword, configured_wait in wait_config.items():
                if keyword in url_name.lower():
                    determined_wait = configured_wait
                    logger.info(f"⏱️ Using {configured_wait}s wait for {url_name} (detected: {keyword})")
                    break
            else:
                # No keyword matched, use default
                logger.info(f"⏱️ Using default {determined_wait}s wait for {url_name}")
            
            # CRITICAL: Wait for the page to fully load
            logger.info(f"⏳ Waiting {determined_wait} seconds for page to complete...")
            await asyncio.sleep(determined_wait)
            logger.info(f"✅ Wait complete, now capturing screenshot")
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"{library_name}_{url_name}_{timestamp}.png"
            filepath = self.screenshots_dir / filename
            
            # Use page object if provided (Playwright case)
            if page is not None:
                logger.info(f"📸 Taking screenshot for {library_name}/{url_name}")
                
                # Try multiple screenshot methods in order
                screenshot_methods = [
                    ("full_page", self._capture_full_page),
                    ("viewport", self._capture_viewport),
                    ("element", self._capture_element),
                    ("binary", self._capture_binary)
                ]
                
                for method_name, method_func in screenshot_methods:
                    try:
                        logger.debug(f"Trying screenshot method: {method_name}")
                        
                        if await method_func(page, filepath):
                            if filepath.exists() and filepath.stat().st_size > 1000:
                                size_kb = filepath.stat().st_size / 1024
                                logger.info(f"✅ Screenshot captured via {method_name}: {filepath.name} ({size_kb:.1f} KB)")
                                return str(filepath)
                        
                    except Exception as e:
                        logger.debug(f"{method_name} failed: {str(e)[:100]}")
                        continue
                
                logger.warning(f"⚠️ All screenshot methods failed for {library_name}/{url_name}")
                return None
                    
            else:
                # Fall back to sync capture for other browsers
                return self.capture_screenshot(browser_instance, library_name, url_name)
                
        except Exception as e:
            logger.error(f"Screenshot capture error: {str(e)[:200]}")
            return None
    
    async def _capture_full_page(self, page, filepath: Path) -> bool:
        """Method 1: Full page screenshot with font fix"""
        try:
            # Force fonts to be ready immediately
            await page.evaluate("""
                if (document.fonts && document.fonts.ready) {
                    document.fonts.ready = Promise.resolve();
                }
                document.querySelectorAll('link[rel="stylesheet"]').forEach(link => {
                    if (link.href.includes('font')) {
                        link.remove();
                    }
                });
            """)
            
            await page.screenshot(
                path=str(filepath),
                full_page=True,
                timeout=5000,  # 5 second timeout
                animations='disabled'
            )
            return True
            
        except Exception as e:
            logger.debug(f"Full page screenshot failed: {str(e)[:100]}")
            return False
    
    async def _capture_viewport(self, page, filepath: Path) -> bool:
        """Method 2: Viewport screenshot (faster)"""
        try:
            await page.screenshot(
                path=str(filepath),
                full_page=False,
                timeout=3000  # 3 second timeout
            )
            return True
            
        except Exception as e:
            logger.debug(f"Viewport screenshot failed: {str(e)[:100]}")
            return False
    
    async def _capture_element(self, page, filepath: Path) -> bool:
        """Method 3: Element screenshot of main content"""
        try:
            # Try to find main content area
            main_element = await page.query_selector('main') or \
                           await page.query_selector('body') or \
                           await page.query_selector('html')
            
            if main_element:
                await main_element.screenshot(path=str(filepath), timeout=3000)
                return True
            return False
                        
        except Exception as e:
            logger.debug(f"Element screenshot failed: {str(e)[:100]}")
            return False
    
    async def _capture_binary(self, page, filepath: Path) -> bool:
        """Method 4: Binary screenshot (last resort)"""
        try:
            screenshot_bytes = await page.screenshot(timeout=2000, full_page=False)
            with open(filepath, 'wb') as f:
                f.write(screenshot_bytes)
            return True
            
        except Exception as e:
            logger.debug(f"Binary screenshot failed: {str(e)[:100]}")
            return False
    
    def capture_with_wait_sync(
        self,
        driver: Any,
        library_name: str,
        url_name: str,
        wait_time: int = 30
    ) -> Optional[str]:
        """Capture screenshot after wait (sync version for Selenium)"""
        try:
            # Intelligent wait based on page
            wait_config = {
                'pixelscan: 45,
                'fingerprint: 45,
                'ip_check: 35,
                'bot_check: 35,
                'creepjs: 30,
                'workers': 25,
                'ip': 30,
            }
            
            for keyword, wait in wait_config.items():
                if keyword in url_name.lower():
                    wait_time = wait
                    break
            
            logger.info(f"Waiting {wait_time}s before screenshot for {library_name}/{url_name}")
            time.sleep(wait_time)
            
            return self.capture_screenshot(driver, library_name, url_name)
            
        except Exception as e:
            logger.error(f"Sync screenshot with wait failed: {str(e)}")
            return None
    
    def capture_screenshot(
        self, 
        browser_instance: Any, 
        library_name: str, 
        test_name: str = "test"
    ) -> Optional[str]:
        """Capture screenshot using appropriate method for the browser library"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{library_name}_{test_name}_{timestamp}.png"
        filepath = self.screenshots_dir / filename
        
        try:
            # Try multiple methods in order of preference
            screenshot_methods = [
                ('save_screenshot', lambda: browser_instance.save_screenshot(str(filepath))),
                ('get_screenshot_as_file', lambda: browser_instance.get_screenshot_as_file(str(filepath))),
                ('get_screenshot_as_png', lambda: self._save_png_screenshot(browser_instance, filepath)),
                ('get_screenshot_as_base64', lambda: self._save_base64_screenshot(browser_instance, filepath)),
                ('take_screenshot', lambda: browser_instance.take_screenshot(str(filepath))),
                ('get_screenshot', lambda: self._save_generic_screenshot(browser_instance, filepath))
            ]
            
            for method_name, method_func in screenshot_methods:
                if hasattr(browser_instance, method_name):
                    try:
                        logger.debug(f"Trying {method_name} method for {library_name}")
                        method_func()
                        
                        if filepath.exists() and filepath.stat().st_size > 0:
                            logger.info(f"Screenshot captured via {method_name}: {filepath}")
                            return str(filepath)
                    except Exception as e:
                        logger.debug(f"{method_name} failed: {str(e)[:100]}")
                        continue
            
            logger.warning(f"No working screenshot method found for {library_name}")
            return None
                
        except Exception as e:
            logger.error(f"Screenshot capture failed for {library_name}: {str(e)}")
            return None
    
    def _save_png_screenshot(self, browser_instance, filepath):
        """Helper to save PNG screenshot data"""
        screenshot_data = browser_instance.get_screenshot_as_png()
        with open(filepath, 'wb') as f:
            f.write(screenshot_data)
    
    def _save_base64_screenshot(self, browser_instance, filepath):
        """Helper to save base64 screenshot data"""
        screenshot_data = browser_instance.get_screenshot_as_base64()
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(screenshot_data))
    
    def _save_generic_screenshot(self, browser_instance, filepath):
        """Helper to save generic screenshot data"""
        screenshot_data = browser_instance.get_screenshot()
        if isinstance(screenshot_data, str):
            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(screenshot_data))
        elif isinstance(screenshot_data, bytes):
            with open(filepath, 'wb') as f:
                f.write(screenshot_data)
        else:
            raise Exception("Unknown screenshot data format")
    
    def cleanup_old_screenshots(self, days_old: int = 7) -> None:
        """Remove screenshots older than specified days"""
        try:
            import time
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            
            removed_count = 0
            for screenshot_file in self.screenshots_dir.glob("*.png"):
                if screenshot_file.stat().st_mtime < cutoff_time:
                    screenshot_file.unlink()
                    removed_count += 1
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old screenshots")
                
        except Exception as e:
            logger.error(f"Screenshot cleanup failed: {str(e)}")
    
    def get_screenshot_info(self, filepath: str) -> dict:
        """Get metadata about a screenshot file"""
        try:
            path = Path(filepath)
            if path.exists():
                stat = path.stat()
                return {
                    "filename": path.name,
                    "size_bytes": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "path": str(path.absolute())
                }
            else:
                return {"error": "File not found"}
        except Exception as e:
            return {"error": str(e)}
