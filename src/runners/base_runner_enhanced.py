"""
BASE RUNNER - Enhanced with BrowserForge (WebRTC via BrowserForge only)

Contains common code used by all specialized runners:
- Proxy configuration
- IP detection
- Mobile UA checking
- Screenshot coordination
- BrowserForge fingerprint enhancement
- Session management for device consistency

NO custom WebRTC blocking - uses BrowserForge's native approach
"""

import logging
import asyncio
import re
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from ..core.test_result import TestResult
from ..core.screenshot_engine import ScreenshotEngine
from ..utils.browserforge_manager import BrowserForgeManager

logger = logging.getLogger(__name__)


class BaseRunner:
    """Base class with shared functionality for all runners"""
    
    def __init__(self, screenshot_engine: Optional[ScreenshotEngine] = None):
        """Initialize base runner with BrowserForge enhancement"""
        self.screenshot_engine = screenshot_engine or ScreenshotEngine()
        
        # Initialize BrowserForge manager
        self.browserforge = BrowserForgeManager()
        
        # Log fingerprint capabilities
        stats = self.browserforge.get_fingerprint_stats()
        if stats['browserforge_available']:
            logger.info("🎭 BrowserForge enhancement enabled (with WebRTC support)")
        else:
            logger.warning("⚠️ BrowserForge not available - using basic profiles")
        
        # Session management
        self._session_started = False
        
        # Optional GeoIP support
        self.geoip = None
        try:
            import pygeoip
            geoip_path = Path(__file__).parent.parent.parent / "profiles" / "GeoLiteCity.dat"
            if geoip_path.exists():
                self.geoip = pygeoip.GeoIP(str(geoip_path))
                logger.debug("GeoIP database loaded")
        except (ImportError, Exception):
            pass
    
    def start_session(self, device_type: str = "iphone_x"):
        """
        Start a new test session with consistent device
        
        CRITICAL: Call this ONCE at the start of a library test run
        
        Args:
            device_type: Device type for the session
        """
        if not self._session_started:
            self.browserforge.start_new_session(device_type)
            self._session_started = True
            logger.info(f"✅ Session started for {device_type}")
    
    def end_session(self):
        """
        End the current test session
        
        Call this after all tests for a library are complete
        """
        if self._session_started:
            self.browserforge.end_session()
            self._session_started = False
            logger.info("✅ Session ended")
    
    def get_enhanced_mobile_config(
        self,
        mobile_config: Dict[str, Any],
        device_type: str = "iphone_x",
        use_browserforge: bool = True,
        proxy_ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get enhanced mobile config with BrowserForge fingerprints
        
        Args:
            mobile_config: Base mobile config from test_targets.json (NOT USED if session active)
            device_type: Device type for profile selection
            use_browserforge: Whether to apply BrowserForge enhancement
            proxy_ip: Proxy IP address for WebRTC configuration
        
        Returns:
            Enhanced mobile configuration (SESSION CONSISTENT)
        """
        # Ensure session is started
        if not self._session_started:
            logger.warning("⚠️ Session not started, auto-starting")
            self.start_session(device_type)
        
        if use_browserforge and self.browserforge.is_browserforge_available():
            # Generate enhanced fingerprint with proxy IP for WebRTC
            enhanced = self.browserforge.generate_enhanced_fingerprint(
                device_type=device_type,
                use_browserforge=True,
                proxy_ip=proxy_ip
            )
            
            return enhanced
        else:
            # Fallback to session config (still consistent!)
            session_config = self.browserforge.get_session_config()
            if session_config:
                # Add proxy IP even for basic config
                if proxy_ip:
                    session_config['_proxy_ip'] = proxy_ip
                return session_config
            else:
                # Last resort: use provided config
                if proxy_ip:
                    mobile_config['_proxy_ip'] = proxy_ip
                return mobile_config
    
    def _build_proxy(self, proxy_config: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Build proxy configuration
        
        Returns:
            Proxy dict or None if no proxy configured
        """
        if not proxy_config.get("host") or not proxy_config.get("port"):
            return None
        
        proxy = {
            "server": f"http://{proxy_config['host']}:{proxy_config['port']}"
        }
        
        if proxy_config.get("username") and proxy_config.get("password"):
            proxy["username"] = proxy_config["username"]
            proxy["password"] = proxy_config["password"]
        
        logger.info(f"Proxy: {proxy['server']} (auth: {'yes' if 'username' in proxy else 'no'})")
        return proxy
    
    async def _check_proxy(
        self, 
        page, 
        proxy_config: Dict[str, str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if proxy is working by detecting IP on page
        
        Returns:
            Tuple of (proxy_working, detected_ip)
        """
        try:
            await asyncio.sleep(1)
            
            # Get page content
            content = await page.content()
            
            # IP detection patterns
            ip_patterns = [
                r'"ip"\s*:\s*"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"',
                r'Your IP.*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
                r'<span[^>]*>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</span>',
                r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
            ]
            
            found_ips = []
            for pattern in ip_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                found_ips.extend(matches)
            
            # Filter valid public IPs
            found_ips = [ip for ip in found_ips if self._is_valid_public_ip(ip)]
            
            if not found_ips:
                logger.debug("No IP detected on page (OK for some pages)")
                return False, None
            
            detected_ip = found_ips[0]
            
            if proxy_config.get("host"):
                logger.info(f"✅ Proxy working (detected IP: {detected_ip})")
                return True, detected_ip
            else:
                return False, detected_ip
        
        except Exception as e:
            logger.debug(f"Proxy check error: {str(e)[:80]}")
            return False, None
    
    def _is_valid_public_ip(self, ip_str: str) -> bool:
        """Check if IP is valid and public (not private/reserved)"""
        try:
            parts = [int(p) for p in ip_str.split('.')]
            
            if len(parts) != 4:
                return False
            
            # Check valid range
            if any(p < 0 or p > 255 for p in parts):
                return False
            
            # Filter private/reserved IPs
            if parts[0] == 10:  # 10.0.0.0/8
                return False
            if parts[0] == 172 and 16 <= parts[1] <= 31:  # 172.16.0.0/12
                return False
            if parts[0] == 192 and parts[1] == 168:  # 192.168.0.0/16
                return False
            if parts[0] == 127:  # 127.0.0.0/8 (localhost)
                return False
            if parts[0] == 169 and parts[1] == 254:  # 169.254.0.0/16 (link-local)
                return False
            
            return True
        except:
            return False
    
    async def _check_mobile_ua(
        self, 
        page, 
        mobile_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if mobile user agent is detected
        
        Returns:
            True if mobile UA detected
        """
        try:
            ua = await page.evaluate("navigator.userAgent")
            
            # Mobile keywords
            mobile_keywords = [
                "mobile", "iphone", "android", "ipad", 
                "tablet", "fxios", "fennec"
            ]
            
            is_mobile_ua = any(kw in ua.lower() for kw in mobile_keywords)
            
            # Check viewport too
            try:
                viewport_width = await page.evaluate("window.innerWidth")
                is_mobile_viewport = viewport_width < 768
            except:
                is_mobile_viewport = False
            
            is_mobile = is_mobile_ua or is_mobile_viewport
            
            if is_mobile:
                logger.info(f"✅ Mobile detected (UA={is_mobile_ua}, VP={is_mobile_viewport})")
            else:
                logger.warning(f"⚠️ Desktop UA detected: {ua[:60]}...")
            
            return is_mobile
        except Exception as e:
            logger.debug(f"UA check error: {e}")
            return False
    
    async def _extra_wait_for_dynamic_pages(self, url: str, url_name: str, seconds: int = 15):
        """Extra wait for pages with dynamic content (CreepJS, etc.)"""
        if "creepjs" in url.lower() or "worker" in url_name.lower():
            logger.info(f"⏳ Extra {seconds}s wait for dynamic page")
            await asyncio.sleep(seconds)
