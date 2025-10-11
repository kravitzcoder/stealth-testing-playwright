"""
BrowserForge Integration Manager with Native WebRTC Support
Uses BrowserForge's built-in WebRTC handling instead of custom blocking
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from browserforge.fingerprints import FingerprintGenerator, Screen
    from browserforge.headers import HeaderGenerator
    BROWSERFORGE_AVAILABLE = True
except ImportError:
    BROWSERFORGE_AVAILABLE = False
    FingerprintGenerator = None
    Screen = None
    HeaderGenerator = None
    logging.warning("BrowserForge not installed. Install with: pip install browserforge")

from .device_profile_loader import DeviceProfileLoader

logger = logging.getLogger(__name__)


class BrowserForgeManager:
    """
    Enhanced fingerprint manager with BrowserForge's native WebRTC handling
    """
    
    def __init__(self):
        self.profile_loader = DeviceProfileLoader()
        
        if BROWSERFORGE_AVAILABLE:
            self.fp_generator = FingerprintGenerator()
            self.header_generator = HeaderGenerator()
            logger.info("✅ BrowserForge initialized with WebRTC support")
        else:
            self.fp_generator = None
            self.header_generator = None
            logger.warning("⚠️ BrowserForge not available - using basic profiles only")
        
        # Session management
        self._session_device = None
        self._session_config = None
        self._session_device_type = None
        self._session_fingerprint = None  # Store raw fingerprint for WebRTC
    
    def start_new_session(self, device_type: str = "iphone_x"):
        """
        Start a new session with a consistent device
        
        Args:
            device_type: Device type hint (e.g., "iphone_x", "samsung_galaxy")
        """
        # Select ONE device for the entire session
        if "samsung" in device_type.lower() or "android" in device_type.lower():
            csv_profile = self.profile_loader.get_random_android_profile()
        else:
            csv_profile = self.profile_loader.get_random_iphone_profile()
        
        # Store for session
        self._session_device = csv_profile
        self._session_device_type = device_type
        self._session_config = self.profile_loader.convert_to_mobile_config(csv_profile)
        
        device_name = self._session_config.get('device_name', 'Unknown')
        logger.info(f"🔒 Session device locked: {device_name}")
        
        return self._session_config
    
    def get_session_config(self) -> Optional[Dict[str, Any]]:
        """Get the current session's device config"""
        if self._session_config is None:
            logger.warning("⚠️ No session started! Call start_new_session() first")
            return self.start_new_session()
        
        return self._session_config
    
    def end_session(self):
        """End the current session"""
        if self._session_config:
            device_name = self._session_config.get('device_name', 'Unknown')
            logger.info(f"🔓 Session ended for: {device_name}")
        
        self._session_device = None
        self._session_config = None
        self._session_device_type = None
        self._session_fingerprint = None
    
    def generate_enhanced_fingerprint(
        self,
        device_type: str = "iphone_x",
        use_browserforge: bool = True,
        proxy_ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate enhanced fingerprint with BrowserForge WebRTC support
        
        Args:
            device_type: Device type
            use_browserforge: Whether to use BrowserForge enhancement
            proxy_ip: Proxy IP address for WebRTC configuration
        
        Returns:
            Enhanced mobile config dictionary with WebRTC settings
        """
        # Get session config (consistent device)
        if self._session_config is None:
            logger.warning("⚠️ No session active, starting new session")
            base_config = self.start_new_session(device_type)
        else:
            base_config = self._session_config
            logger.debug(f"🔒 Using session device: {base_config.get('device_name')}")
        
        # Enhance with BrowserForge if available
        if use_browserforge and BROWSERFORGE_AVAILABLE and self.fp_generator:
            try:
                enhanced_config = self._apply_browserforge_enhancement(
                    base_config, 
                    self._session_device_type or device_type,
                    proxy_ip=proxy_ip
                )
                logger.debug(f"🎭 BrowserForge applied with WebRTC: {base_config.get('device_name')}")
                return enhanced_config
            except Exception as e:
                logger.warning(f"⚠️ BrowserForge enhancement failed: {str(e)[:100]}")
                logger.info("Falling back to base session profile")
                return base_config
        else:
            logger.debug(f"📱 Using base session profile: {base_config.get('device_name')}")
            return base_config
    
    def _apply_browserforge_enhancement(
        self,
        base_config: Dict[str, Any],
        device_type: str,
        proxy_ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Apply BrowserForge fingerprint with native WebRTC support
        
        Args:
            base_config: Base configuration from CSV profiles
            device_type: Device type
            proxy_ip: Proxy IP for WebRTC masking
        """
        
        # Determine browser and OS constraints
        if "android" in device_type.lower() or "samsung" in device_type.lower():
            browsers = ['chrome']
            operating_systems = ['android']
        else:
            browsers = ['safari']
            operating_systems = ['ios']
        
        # Create Screen object for BrowserForge
        viewport_width = base_config['viewport']['width']
        viewport_height = base_config['viewport']['height']
        
        screen = Screen(
            min_width=viewport_width - 10,
            max_width=viewport_width + 10,
            min_height=viewport_height - 10,
            max_height=viewport_height + 10
        )
        
        # Generate BrowserForge fingerprint
        fingerprint = self.fp_generator.generate(
            screen=screen,
            strict=False,
            browser=browsers,
            os=operating_systems,
            device='mobile'
        )
        
        # Store fingerprint for session
        self._session_fingerprint = fingerprint
        
        # Merge BrowserForge enhancements with base config
        enhanced_config = base_config.copy()
        
        # Update with BrowserForge values
        enhanced_config.update({
            # BrowserForge user agent
            'user_agent': fingerprint.navigator.userAgent,
            
            # Navigator properties
            'platform': fingerprint.navigator.platform,
            'hardware_concurrency': fingerprint.navigator.hardwareConcurrency,
            'device_memory': fingerprint.navigator.deviceMemory,
            'max_touch_points': fingerprint.navigator.maxTouchPoints,
            
            # Language preferences
            'language': fingerprint.navigator.language,
            'languages': fingerprint.navigator.languages,
            
            # WebGL fingerprinting
            'webgl_vendor': fingerprint.videoCard.vendor if fingerprint.videoCard else base_config.get('webgl_vendor'),
            'webgl_renderer': fingerprint.videoCard.renderer if fingerprint.videoCard else base_config.get('webgl_renderer'),
            
            # Screen properties
            'screen_width': fingerprint.screen.width,
            'screen_height': fingerprint.screen.height,
            
            # Keep viewport from CSV
            'viewport': base_config['viewport'],
            
            # Keep device-specific values
            'device_name': base_config.get('device_name'),
            'os_version': base_config.get('os_version'),
            'canvas_seed': base_config.get('canvas_seed'),
            'audio_seed': base_config.get('audio_seed'),
            'timezone': base_config.get('timezone'),
            'battery_level': base_config.get('battery_level'),
            'battery_charging': base_config.get('battery_charging'),
            
            # BrowserForge metadata
            '_browserforge_enhanced': True,
            '_browserforge_webrtc_enabled': True,
            '_session_consistent': True,
            
            # Store proxy IP for WebRTC
            '_proxy_ip': proxy_ip
        })
        
        return enhanced_config
    
    def get_browserforge_webrtc_script(
        self, 
        enhanced_config: Dict[str, Any]
    ) -> str:
        """
        Generate AGGRESSIVE WebRTC protection script
        
        This completely disables WebRTC to prevent ANY IP leaks
        Trade-off: Some WebRTC-dependent features won't work, but IP is protected
        
        Args:
            enhanced_config: Enhanced config with proxy IP
        
        Returns:
            JavaScript code for WebRTC protection
        """
        proxy_ip = enhanced_config.get('_proxy_ip', '0.0.0.0')
        
        script = f"""
(function() {{
    'use strict';
    
    console.log('[BrowserForge WebRTC] AGGRESSIVE protection mode enabled');
    console.log('[BrowserForge WebRTC] Target proxy IP: {proxy_ip}');
    
    // COMPLETE WebRTC DISABLE - Most reliable way to prevent leaks
    
    // Remove RTCPeerConnection completely
    if (typeof RTCPeerConnection !== 'undefined') {{
        delete window.RTCPeerConnection;
        
        // Make it return undefined
        Object.defineProperty(window, 'RTCPeerConnection', {{
            get: function() {{
                console.log('[BrowserForge WebRTC] RTCPeerConnection access blocked');
                return undefined;
            }},
            set: function() {{}},
            configurable: false,
            enumerable: false
        }});
    }}
    
    // Block webkitRTCPeerConnection
    if (typeof webkitRTCPeerConnection !== 'undefined') {{
        delete window.webkitRTCPeerConnection;
        
        Object.defineProperty(window, 'webkitRTCPeerConnection', {{
            get: function() {{
                console.log('[BrowserForge WebRTC] webkitRTCPeerConnection access blocked');
                return undefined;
            }},
            set: function() {{}},
            configurable: false,
            enumerable: false
        }});
    }}
    
    // Block mozRTCPeerConnection (Firefox)
    if (typeof mozRTCPeerConnection !== 'undefined') {{
        delete window.mozRTCPeerConnection;
        
        Object.defineProperty(window, 'mozRTCPeerConnection', {{
            get: function() {{
                console.log('[BrowserForge WebRTC] mozRTCPeerConnection access blocked');
                return undefined;
            }},
            set: function() {{}},
            configurable: false,
            enumerable: false
        }});
    }}
    
    // Block getUserMedia (prevents camera/microphone access that can leak)
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {{
        const originalGetUserMedia = navigator.mediaDevices.getUserMedia;
        navigator.mediaDevices.getUserMedia = function() {{
            console.log('[BrowserForge WebRTC] getUserMedia blocked');
            return Promise.reject(new DOMException('Permission denied', 'NotAllowedError'));
        }};
    }}
    
    // Block legacy getUserMedia
    if (navigator.getUserMedia) {{
        navigator.getUserMedia = function(constraints, success, error) {{
            console.log('[BrowserForge WebRTC] Legacy getUserMedia blocked');
            if (error) {{
                error(new DOMException('Permission denied', 'NotAllowedError'));
            }}
        }};
    }}
    
    // Block mozGetUserMedia
    if (navigator.mozGetUserMedia) {{
        navigator.mozGetUserMedia = function() {{
            return Promise.reject(new DOMException('Permission denied', 'NotAllowedError'));
        }};
    }}
    
    // Block webkitGetUserMedia
    if (navigator.webkitGetUserMedia) {{
        navigator.webkitGetUserMedia = function() {{
            return Promise.reject(new DOMException('Permission denied', 'NotAllowedError'));
        }};
    }}
    
    // Block RTCDataChannel
    if (typeof RTCDataChannel !== 'undefined') {{
        delete window.RTCDataChannel;
        Object.defineProperty(window, 'RTCDataChannel', {{
            get: () => undefined,
            configurable: false
        }});
    }}
    
    // Block RTCSessionDescription
    if (typeof RTCSessionDescription !== 'undefined') {{
        delete window.RTCSessionDescription;
        Object.defineProperty(window, 'RTCSessionDescription', {{
            get: () => undefined,
            configurable: false
        }});
    }}
    
    // Block RTCIceCandidate
    if (typeof RTCIceCandidate !== 'undefined') {{
        delete window.RTCIceCandidate;
        Object.defineProperty(window, 'RTCIceCandidate', {{
            get: () => undefined,
            configurable: false
        }});
    }}
    
    console.log('[BrowserForge WebRTC] ✅ COMPLETE WebRTC blocking active');
    console.log('[BrowserForge WebRTC] ✅ No IP leaks possible - all WebRTC APIs disabled');
}})();
        """
        
        return script
    
    def is_browserforge_available(self) -> bool:
        """Check if BrowserForge is available"""
        return BROWSERFORGE_AVAILABLE and self.fp_generator is not None
    
    def get_fingerprint_stats(self) -> Dict[str, Any]:
        """Get statistics about fingerprint generation capabilities"""
        stats = {
            "browserforge_available": self.is_browserforge_available(),
            "csv_profiles_loaded": {
                "iphone": len(self.profile_loader.iphone_profiles),
                "android": len(self.profile_loader.android_profiles)
            },
            "enhancement_enabled": self.is_browserforge_available(),
            "session_active": self._session_config is not None,
            "webrtc_protection": self.is_browserforge_available()
        }
        
        if self._session_config:
            stats["session_device"] = self._session_config.get('device_name', 'Unknown')
        
        return stats
