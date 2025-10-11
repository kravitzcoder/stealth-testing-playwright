"""
BrowserForge Integration Manager with Session Persistence
Combines BrowserForge's intelligent fingerprint generation with existing device profiles
CRITICAL: Maintains consistent device profile across entire test session
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from browserforge.fingerprints import FingerprintGenerator, Screen
    BROWSERFORGE_AVAILABLE = True
except ImportError:
    BROWSERFORGE_AVAILABLE = False
    FingerprintGenerator = None
    Screen = None
    logging.warning("BrowserForge not installed. Install with: pip install browserforge")

from .device_profile_loader import DeviceProfileLoader

logger = logging.getLogger(__name__)


class BrowserForgeManager:
    """
    Enhanced fingerprint manager combining:
    1. BrowserForge's Bayesian network-based fingerprints
    2. Your existing realistic device profiles from CSV
    3. SESSION PERSISTENCE - same device across all pages in a session
    """
    
    def __init__(self):
        self.profile_loader = DeviceProfileLoader()
        
        if BROWSERFORGE_AVAILABLE:
            self.fp_generator = FingerprintGenerator()
            logger.info("✅ BrowserForge initialized successfully")
        else:
            self.fp_generator = None
            logger.warning("⚠️ BrowserForge not available - using basic profiles only")
        
        # SESSION PERSISTENCE (NEW!)
        self._session_device = None
        self._session_config = None
        self._session_device_type = None
    
    def start_new_session(self, device_type: str = "iphone_x"):
        """
        Start a new session with a consistent device
        
        CRITICAL: Call this at the START of each test run (per library)
        This ensures all pages visited use the SAME device profile
        
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
        logger.info(f"🔒 Session device locked: {device_name} (will be used for ALL pages)")
        
        return self._session_config
    
    def get_session_config(self) -> Optional[Dict[str, Any]]:
        """
        Get the current session's device config
        
        Returns the same device config for consistency
        """
        if self._session_config is None:
            logger.warning("⚠️ No session started! Call start_new_session() first")
            # Auto-start with default
            return self.start_new_session()
        
        return self._session_config
    
    def end_session(self):
        """
        End the current session
        
        Call this when finishing a test run (before starting a new library test)
        """
        if self._session_config:
            device_name = self._session_config.get('device_name', 'Unknown')
            logger.info(f"🔓 Session ended for: {device_name}")
        
        self._session_device = None
        self._session_config = None
        self._session_device_type = None
    
    def generate_enhanced_fingerprint(
        self,
        device_type: str = "iphone_x",
        use_browserforge: bool = True
    ) -> Dict[str, Any]:
        """
        Generate enhanced fingerprint using SESSION device (CONSISTENT)
        
        IMPORTANT: This now uses the session device, not a random one!
        
        Args:
            device_type: Device type (used only if no session exists)
            use_browserforge: Whether to use BrowserForge enhancement
        
        Returns:
            Enhanced mobile config dictionary (SAME device as session)
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
                    self._session_device_type or device_type
                )
                logger.debug(f"🎭 BrowserForge applied to session device: {base_config.get('device_name')}")
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
        device_type: str
    ) -> Dict[str, Any]:
        """Apply BrowserForge fingerprint to enhance base config"""
        
        # Determine browser and OS constraints based on device
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
        
        # Generate BrowserForge fingerprint with proper parameters
        fingerprint = self.fp_generator.generate(
            screen=screen,
            strict=False,
            browser=browsers,
            os=operating_systems,
            device='mobile'
        )
        
        # Merge BrowserForge enhancements with base config
        enhanced_config = base_config.copy()
        
        # Update with BrowserForge values where they're more sophisticated
        enhanced_config.update({
            # BrowserForge provides more realistic user agent
            'user_agent': fingerprint.navigator.userAgent,
            
            # Enhanced navigator properties
            'platform': fingerprint.navigator.platform,
            'hardware_concurrency': fingerprint.navigator.hardwareConcurrency,
            'device_memory': fingerprint.navigator.deviceMemory,
            'max_touch_points': fingerprint.navigator.maxTouchPoints,
            
            # BrowserForge language preferences
            'language': fingerprint.navigator.language,
            'languages': fingerprint.navigator.languages,
            
            # Enhanced WebGL fingerprinting
            'webgl_vendor': fingerprint.videoCard.vendor if fingerprint.videoCard else base_config.get('webgl_vendor'),
            'webgl_renderer': fingerprint.videoCard.renderer if fingerprint.videoCard else base_config.get('webgl_renderer'),
            
            # Screen properties from BrowserForge
            'screen_width': fingerprint.screen.width,
            'screen_height': fingerprint.screen.height,
            
            # Keep viewport from CSV (it's already accurate)
            'viewport': base_config['viewport'],
            
            # Keep other CSV values that are device-specific (SESSION CONSISTENT)
            'device_name': base_config.get('device_name'),
            'os_version': base_config.get('os_version'),
            'canvas_seed': base_config.get('canvas_seed'),
            'audio_seed': base_config.get('audio_seed'),
            'timezone': base_config.get('timezone'),
            'battery_level': base_config.get('battery_level'),
            'battery_charging': base_config.get('battery_charging'),
            
            # Add BrowserForge metadata
            '_browserforge_enhanced': True,
            '_browserforge_version': '1.2.3',
            '_session_consistent': True  # Mark as session-consistent
        })
        
        return enhanced_config
    
    def get_browserforge_fingerprint_only(
        self,
        device_type: str = "mobile"
    ) -> Optional[Any]:
        """
        Get raw BrowserForge fingerprint (for advanced usage)
        
        Args:
            device_type: "mobile" or "desktop"
        
        Returns:
            BrowserForge Fingerprint object or None
        """
        if not BROWSERFORGE_AVAILABLE or not self.fp_generator:
            return None
        
        try:
            if device_type == "mobile":
                fingerprint = self.fp_generator.generate(
                    device='mobile',
                    os=('ios', 'android'),
                    strict=False
                )
            else:
                fingerprint = self.fp_generator.generate(
                    device='desktop',
                    strict=False
                )
            
            return fingerprint
        except Exception as e:
            logger.error(f"Failed to generate BrowserForge fingerprint: {e}")
            return None
    
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
            "session_active": self._session_config is not None
        }
        
        if self._session_config:
            stats["session_device"] = self._session_config.get('device_name', 'Unknown')
        
        return stats
