"""
BASE RUNNER - Enhanced with IP Pre-Resolution (FIXED)

Now resolves proxy IP and detects timezone BEFORE browser launch
"""

import logging
import asyncio
import re
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from ..core.test_result import TestResult
from ..core.screenshot_engine import ScreenshotEngine
from ..utils.browserforge_manager import BrowserForgeManager
from ..utils.timezone_manager import TimezoneManager
from ..utils.ip_resolver import IPResolver, ResolvedProxy

logger = logging.getLogger(__name__)


class BaseRunner:
    """Base class with IP pre-resolution support"""
    
    def __init__(self, screenshot_engine: Optional[ScreenshotEngine] = None):
        """Initialize base runner with IP resolver"""
        self.screenshot_engine = screenshot_engine or ScreenshotEngine()
        
        # Initialize managers
        self.browserforge = BrowserForgeManager()
        self.timezone_manager = TimezoneManager()
        self.ip_resolver = IPResolver(self.timezone_manager)  # 🆕 IP Resolver
        
        logger.info("🌐 IP Resolver initialized")
        
        # Log fingerprint capabilities
        stats = self.browserforge.get_fingerprint_stats()
        if stats['browserforge_available']:
            logger.info("🎭 BrowserForge enhancement enabled")
        else:
            logger.warning("⚠️ BrowserForge not available - using basic profiles")
        
        # Session management
        self._session_started = False
        self._resolved_proxy: Optional[ResolvedProxy] = None  # 🆕 Cache resolved proxy
    
    def start_session(self, device_type: str = "iphone_x"):
        """
        Start a new test session with consistent device
        
        Args:
            device_type: Device type for the session
        """
        if not self._session_started:
            self.browserforge.start_new_session(device_type)
            self._session_started = True
            logger.info(f"✅ Session started for {device_type}")
    
    def end_session(self):
        """End the current test session"""
        if self._session_started:
            self.browserforge.end_session()
            self._session_started = False
            self._resolved_proxy = None  # Clear cached proxy
            logger.info("✅ Session ended")
    
    async def resolve_proxy_before_launch(
        self,
        proxy_config: Dict[str, str]
    ) -> ResolvedProxy:
        """
        🆕 Resolve proxy IP and timezone BEFORE browser launch
        
        This is the critical fix - call this FIRST!
        
        Args:
            proxy_config: Proxy configuration dict
        
        Returns:
            ResolvedProxy with IP and timezone
        """
        # Use cached resolution if available
        if self._resolved_proxy is not None:
            logger.debug(f"📋 Using cached proxy resolution: {self._resolved_proxy.ip_address}")
            return self._resolved_proxy
        
        # Resolve proxy
        resolved = await self.ip_resolver.resolve_proxy(proxy_config)
        
        # Cache for this session
        self._resolved_proxy = resolved
        
        return resolved
    
    def get_enhanced_mobile_config(
        self,
        mobile_config: Dict[str, Any],
        device_type: str = "iphone_x",
        use_browserforge: bool = True,
        resolved_proxy: Optional[ResolvedProxy] = None  # 🆕 Use resolved proxy
    ) -> Dict[str, Any]:
        """
        Get enhanced mobile config with pre-resolved timezone
        
        Args:
            mobile_config: Base mobile config (NOT USED if session active)
            device_type: Device type for profile selection
            use_browserforge: Whether to apply BrowserForge enhancement
            resolved_proxy: Pre-resolved proxy info (with timezone) 🆕
        
        Returns:
            Enhanced mobile configuration with CORRECT timezone
        """
        # Ensure session is started
        if not self._session_started:
            logger.warning("⚠️ Session not started, auto-starting")
            self.start_session(device_type)
        
        # Extract resolved data
        proxy_ip = resolved_proxy.ip_address if resolved_proxy else None
        timezone = resolved_proxy.timezone if resolved_proxy else None
        
        if use_browserforge and self.browserforge.is_browserforge_available():
            # Generate enhanced fingerprint with pre-resolved timezone
            enhanced = self.browserforge.generate_enhanced_fingerprint(
                device_type=device_type,
                use_browserforge=True,
                proxy_ip=proxy_ip,
                timezone=timezone,  # 🆕 Pre-resolved timezone!
                mock_webrtc=True
            )
            
            # Log what we're using
            if resolved_proxy:
                logger.info(f"🎭 BrowserForge config created:")
                logger.info(f"   Device: {enhanced.get('device_name')}")
                logger.info(f"   Timezone: {timezone}")
                logger.info(f"   Proxy IP: {proxy_ip}")
                if resolved_proxy.city:
                    logger.info(f"   Location: {resolved_proxy.city}, {resolved_proxy.country}")
            
            return enhanced
        else:
            # Fallback to session config
            session_config = self.browserforge.get_session_config()
            if session_config:
                # Add proxy IP and override timezone
                if proxy_ip:
                    session_config['_proxy_ip'] = proxy_ip
                if timezone:
                    session_config['timezone'] = timezone
                    logger.info(f"📱 Basic config with timezone: {timezone}")
                
                return session_config
            else:
                # Last resort: use provided config
                if proxy_ip:
                    mobile_config['_proxy_ip'] = proxy_ip
                if timezone:
                    mobile_config['timezone'] = timezone
                
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
