"""
BASE RUNNER - Enhanced with BrowserForge

Contains common code used by all specialized runners:
- Proxy configuration
- IP detection
- Mobile UA checking
- Screenshot coordination
- WebRTC blocking (UNIVERSAL)
- BrowserForge fingerprint enhancement (NEW!)
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
        
        # Initialize BrowserForge manager (NEW!)
        self.browserforge = BrowserForgeManager()
        
        # Log fingerprint capabilities
        stats = self.browserforge.get_fingerprint_stats()
        if stats['browserforge_available']:
            logger.info("🎭 BrowserForge enhancement enabled")
        else:
            logger.warning("⚠️ BrowserForge not available - using basic profiles")
        
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
    
    def get_enhanced_mobile_config(
        self,
        mobile_config: Dict[str, Any],
        device_type: str = "iphone_x",
        use_browserforge: bool = True
    ) -> Dict[str, Any]:
        """
        Get enhanced mobile config with BrowserForge fingerprints
        
        NEW METHOD: Use this instead of plain mobile_config for better stealth
        
        Args:
            mobile_config: Base mobile config from test_targets.json
            device_type: Device type for profile selection
            use_browserforge: Whether to apply BrowserForge enhancement
        
        Returns:
            Enhanced mobile configuration
        """
        if use_browserforge and self.browserforge.is_browserforge_available():
            # Generate enhanced fingerprint
            enhanced = self.browserforge.generate_enhanced_fingerprint(
                device_type=device_type,
                use_browserforge=True
            )
            
            # Merge with original config (keep original viewport if present)
            if 'viewport' in mobile_config:
                enhanced['viewport'] = mobile_config['viewport']
            
            return enhanced
        else:
            # Fallback to original config
            return mobile_config
    
    def _get_universal_webrtc_blocker(self) -> str:
        """
        Universal WebRTC blocking script
        
        Works across all libraries (Playwright, Patchright, Camoufox, Rebrowser)
        
        Blocks:
        - RTCPeerConnection
        - getUserMedia
        - WebRTC data channels
        - STUN/TURN connections
        """
        return """
(function() {
    'use strict';
    
    console.log('[WebRTC Blocker] Universal blocking enabled');
    
    // Block RTCPeerConnection
    if (typeof RTCPeerConnection !== 'undefined') {
        window.RTCPeerConnection = function() {
            console.log('[WebRTC Blocker] RTCPeerConnection blocked');
            throw new Error('RTCPeerConnection is disabled for privacy');
        };
        
        Object.defineProperty(window, 'RTCPeerConnection', {
            get: function() {
                return function() {
                    throw new Error('RTCPeerConnection is disabled');
                };
            },
            set: function() {},
            configurable: false
        });
    }
    
    // Block webkitRTCPeerConnection (Safari/older Chrome)
    if (typeof webkitRTCPeerConnection !== 'undefined') {
        window.webkitRTCPeerConnection = function() {
            throw new Error('webkitRTCPeerConnection is disabled');
        };
        
        Object.defineProperty(window, 'webkitRTCPeerConnection', {
            get: function() {
                return function() {
                    throw new Error('webkitRTCPeerConnection is disabled');
                };
            },
            set: function() {},
            configurable: false
        });
    }
    
    // Block getUserMedia (prevents camera/mic access)
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia = function() {
            console.log('[WebRTC Blocker] getUserMedia blocked');
            return Promise.reject(new Error('getUserMedia is disabled'));
        };
    }
    
    // Block legacy getUserMedia
    if (navigator.getUserMedia) {
        navigator.getUserMedia = function(constraints, success, error) {
            console.log('[WebRTC Blocker] Legacy getUserMedia blocked');
            if (error) {
                error(new Error('getUserMedia is disabled'));
            }
        };
    }
    
    // Block mozGetUserMedia (Firefox)
    if (navigator.mozGetUserMedia) {
        navigator.mozGetUserMedia = function() {
            return Promise.reject(new Error('mozGetUserMedia is disabled'));
        };
    }
    
    // Block webkitGetUserMedia (Safari/older Chrome)
    if (navigator.webkitGetUserMedia) {
        navigator.webkitGetUserMedia = function() {
            return Promise.reject(new Error('webkitGetUserMedia is disabled'));
        };
    }
    
    // Block RTCDataChannel
    if (typeof RTCDataChannel !== 'undefined') {
        window.RTCDataChannel = function() {
            throw new Error('RTCDataChannel is disabled');
        };
    }
    
    // Block RTCSessionDescription (return empty to avoid detection)
    if (typeof RTCSessionDescription !== 'undefined') {
        window.RTCSessionDescription = function() {
            return {};
        };
    }
    
    // Block RTCIceCandidate (return empty to avoid detection)
    if (typeof RTCIceCandidate !== 'undefined') {
        window.RTCIceCandidate = function() {
            return {};
        };
    }
    
    console.log('[WebRTC Blocker] ✅ All WebRTC APIs blocked');
})();
        """
    
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
