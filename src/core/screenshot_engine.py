"""
STEALTH BROWSER TESTING FRAMEWORK - Screenshot Engine (FIXED)
Immediate screenshot capture without font loading delays

Authors: kravitzcoder & MiniMax Agent
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
        wait_time: int = 5,  # Reduced from 30 to 5 seconds
        page: Any = None
    ) -> Optional[str]:
        """
        Capture screenshot with minimal wait - stealth should work immediately
        
        FIXED: No more font wait timeouts, immediate capture approach
        """
        try:
            # Minimal intelligent wait based on page type
            wait_config = {
                'creepjs': 8,      # Needs slightly more for worker analysis
                'workers': 8,      # Worker initialization
                'fingerprint': 5,  # Standard wait
                'bot-check': 5,    # Standard wait
                'ip': 3            # Quick page
            }
            
            for keyword, wait in wait_config.items():
                if keyword in url_name.lower():
                    wait_time = wait
                    logger.info(f"Using {wait}s wait for {url_name}")
                    break
            
            # Wait for the specified time
            await asyncio.sleep(wait_time)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"{library_name}_{url_name}_{timestamp}.png"
            filepath = self.screenshots_dir / filename
            
            # Use page object if provided (Playwright case)
            if page is not None:
                logger.info(f"Taking immediate screenshot for {library_name}")
                
                # Method 1: Force immediate screenshot without waiting for fonts
                try:
                    # Inject script to mark fonts as loaded immediately
                    await page.evaluate("""
                        // Force font ready state
                        if (document.fonts && document.fonts.ready) {
                            document.fonts.ready = Promise.resolve();
                        }
                        // Remove any custom fonts to avoid loading delays
                        document.querySelectorAll('link[rel="stylesheet"]').forEach(link => {
                            if (link.href.includes('font')) {
                                link.remove();
                            }
                        });
                    """)
                    
                    # Take screenshot with very short timeout
                    await page.screenshot(
                        path=str(filepath),
                        full_page=True,
                        timeout=3000,  # 3 second timeout max
                        animations='disabled'
                    )
                    
                    if filepath.exists() and filepath.stat().st_size > 1000:
                        size_kb = filepath.stat().st_size / 1024
                        logger.info(f"✅ Screenshot captured: {filepath.name} ({size_kb:.1f} KB)")
                        return str(filepath)
                    
                except Exception as e:
                    logger.debug(f"Full page screenshot attempt failed: {str(e)[:100]}")
                
                # Method 2: Viewport screenshot (faster, no full page)
                try:
                    await page.screenshot(
                        path=str(filepath),
                        full_page=False,  # Just viewport
                        timeout=2000
                    )
                    
                    if filepath.exists() and filepath.stat().st_size > 1000:
                        size_kb = filepath.stat().st_size / 1024
                        logger.info(f"✅ Viewport screenshot captured: {filepath.name} ({size_kb:.1f} KB)")
                        return str(filepath)
                        
                except Exception as e:
                    logger.debug(f"Viewport screenshot failed: {str(e)[:100]}")
                
                # Method 3: Element screenshot of main content
                try:
                    # Try to find main content area
                    main_element = await page.query_selector('main') or \
                                   await page.query_selector('body') or \
                                   await page.query_selector('html')
                    
                    if main_element:
                        await main_element.screenshot(path=str(filepath), timeout=2000)
                        
                        if filepath.exists() and filepath.stat().st_size > 1000:
                            logger.info(f"✅ Element screenshot captured: {filepath.name}")
                            return str(filepath)
                            
                except Exception as e:
                    logger.debug(f"Element screenshot failed: {str(e)[:100]}")
                
                # Method 4: Base64 screenshot (last resort)
                try:
                    screenshot_bytes = await page.screenshot(timeout=1000, full_page=False)
                    with open(filepath, 'wb') as f:
                        f.write(screenshot_bytes)
                    logger.info(f"✅ Binary screenshot captured: {filepath.name}")
                    return str(filepath)
                    
                except Exception as e:
                    logger.warning(f"All screenshot methods failed for {library_name}/{url_name}")
                    # Return None but don't fail the test
                    return None
                    
            else:
                # Fall back to sync capture for other browsers
                return self.capture_screenshot(browser_instance, library_name, url_name)
                
        except Exception as e:
            logger.error(f"Screenshot capture error: {str(e)[:200]}")
            # Don't fail the test due to screenshot issues
            return None
    
    def capture_with_wait_sync(
        self,
        driver: Any,
        library_name: str,
        url_name: str,
        wait_time: int = 5  # Reduced from 30
    ) -> Optional[str]:
        """Capture screenshot after minimal wait (sync version for Selenium)"""
        try:
            # Intelligent wait based on page
            wait_config = {
                'creepjs': 8,
                'workers': 8,
                'fingerprint': 5,
                'bot-check': 5,
                'ip': 3
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
