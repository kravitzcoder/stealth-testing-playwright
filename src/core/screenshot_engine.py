"""
STEALTH BROWSER TESTING FRAMEWORK - Screenshot Engine (FIXED)
Enhanced screenshot capture with timeout handling

CRITICAL FIX:
- Disabled font loading wait (causing 30s timeouts)
- Reduced screenshot timeout from 30s to 10s
- Better error handling and fallbacks
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
        wait_time: int = 30,
        page: Any = None
    ) -> Optional[str]:
        """
        Capture screenshot after waiting for page to fully load (FIXED)
        
        FIXES:
        - Disabled font loading wait (causing timeouts)
        - Reduced screenshot timeout to 10s
        - Multiple fallback strategies
        """
        try:
            # Determine if this is a dynamic page needing extra time
            dynamic_pages = ['fingerprint', 'bot-check', 'creepjs']
            is_dynamic = any(keyword in url_name.lower() for keyword in dynamic_pages)
            
            if is_dynamic:
                extra_wait = 5
                logger.info(f"Dynamic page detected ({url_name}), adding {extra_wait}s extra wait")
                await asyncio.sleep(extra_wait)
            
            # Special handling for worker pages
            if 'worker' in url_name.lower():
                logger.info(f"Worker page detected, adding 20s for worker initialization")
                await asyncio.sleep(20)
            
            logger.info(f"Waiting {wait_time}s before screenshot for {library_name}/{url_name}")
            await asyncio.sleep(wait_time)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"{library_name}_{url_name}_{timestamp}.png"
            filepath = self.screenshots_dir / filename
            
            # Use page object if provided (Playwright case)
            if page is not None:
                logger.info(f"Taking screenshot using page object for {library_name}")
                
                # ULTIMATE FIX: Block font loading completely before taking screenshot
                try:
                    # Block all font requests to prevent font loading wait
                    logger.info("🚫 Blocking font loading to prevent timeout...")
                    await page.route("**/*.woff*", lambda route: route.abort())
                    await page.route("**/*.woff2*", lambda route: route.abort())
                    await page.route("**/*.ttf*", lambda route: route.abort())
                    await page.route("**/*.otf*", lambda route: route.abort())
                    await page.route("**/*.eot*", lambda route: route.abort())
                    
                    # Wait a moment for route setup
                    await asyncio.sleep(0.5)
                    
                    logger.info("Taking screenshot with fonts blocked...")
                    # Take screenshot with very aggressive settings
                    screenshot_bytes = await page.screenshot(
                        timeout=8000,  # 8 second timeout
                        type="png"
                    )
                    
                    # Save to file
                    with open(filepath, 'wb') as f:
                        f.write(screenshot_bytes)
                    
                    logger.info(f"✅ Screenshot captured (fonts blocked): {filepath}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Font-blocked screenshot failed: {str(e)[:100]}")
                    
                    # FINAL FALLBACK: Evaluate JavaScript to capture canvas
                    try:
                        logger.info("🔧 Using JavaScript canvas fallback...")
                        # Get page dimensions
                        dimensions = await page.evaluate('''() => {
                            return {
                                width: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
                                height: Math.max(document.documentElement.scrollHeight, document.body.scrollHeight)
                            }
                        }''')
                        
                        # Take screenshot of just viewport (no font wait)
                        screenshot_bytes = await page.screenshot(
                            type="png",
                            timeout=3000  # Very short timeout
                        )
                        
                        with open(filepath, 'wb') as f:
                            f.write(screenshot_bytes)
                        
                        logger.info(f"✅ Emergency viewport screenshot captured: {filepath}")
                        
                    except Exception as e3:
                        logger.error(f"❌ All screenshot methods exhausted: {str(e3)[:100]}")
                        return None
                
                # Verify file was created
                if filepath.exists() and filepath.stat().st_size > 0:
                    size_kb = filepath.stat().st_size / 1024
                    logger.info(f"✅ Screenshot verified: {filepath.name} ({size_kb:.1f} KB)")
                    return str(filepath)
                else:
                    logger.error(f"❌ Screenshot file not created or empty: {filepath}")
                    return None
            else:
                # Fall back to sync capture for other browsers
                return self.capture_screenshot(browser_instance, library_name, url_name)
                
        except Exception as e:
            logger.error(f"❌ Screenshot with wait failed: {str(e)[:200]}")
            # Last resort: try basic sync method
            try:
                return self.capture_screenshot(page or browser_instance, library_name, url_name)
            except:
                return None
    
    def capture_with_wait_sync(
        self,
        driver: Any,
        library_name: str,
        url_name: str,
        wait_time: int = 30
    ) -> Optional[str]:
        """Capture screenshot after waiting (sync version for Selenium)"""
        try:
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
            # Selenium-based libraries
            if hasattr(browser_instance, 'save_screenshot'):
                logger.info(f"Using save_screenshot method for {library_name}")
                browser_instance.save_screenshot(str(filepath))
            
            elif hasattr(browser_instance, 'get_screenshot_as_file'):
                logger.info(f"Using get_screenshot_as_file method for {library_name}")
                browser_instance.get_screenshot_as_file(str(filepath))
            
            elif hasattr(browser_instance, 'get_screenshot_as_base64'):
                logger.info(f"Using base64 screenshot method for {library_name}")
                screenshot_data = browser_instance.get_screenshot_as_base64()
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(screenshot_data))
            
            elif hasattr(browser_instance, 'get_screenshot_as_png'):
                logger.info(f"Using PNG screenshot method for {library_name}")
                screenshot_data = browser_instance.get_screenshot_as_png()
                with open(filepath, 'wb') as f:
                    f.write(screenshot_data)
            
            elif hasattr(browser_instance, 'take_screenshot'):
                logger.info(f"Using take_screenshot method for {library_name}")
                browser_instance.take_screenshot(str(filepath))
            
            elif hasattr(browser_instance, 'get_screenshot'):
                logger.info(f"Using get_screenshot method for {library_name}")
                screenshot_data = browser_instance.get_screenshot()
                if isinstance(screenshot_data, str):
                    with open(filepath, 'wb') as f:
                        f.write(base64.b64decode(screenshot_data))
                elif isinstance(screenshot_data, bytes):
                    with open(filepath, 'wb') as f:
                        f.write(screenshot_data)
                else:
                    raise Exception("Unknown screenshot data format")
            
            else:
                logger.warning(f"No screenshot method found for {library_name}")
                return None
            
            # Verify file was created
            if filepath.exists() and filepath.stat().st_size > 0:
                logger.info(f"Screenshot captured successfully: {filepath} (size: {filepath.stat().st_size} bytes)")
                return str(filepath)
            else:
                logger.error(f"Screenshot file not created or empty: {filepath}")
                return None
                
        except Exception as e:
            logger.error(f"Screenshot capture failed for {library_name}: {str(e)}")
            return None
    
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
