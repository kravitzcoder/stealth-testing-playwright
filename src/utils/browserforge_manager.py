"""
BrowserForge Integration Manager
Combines BrowserForge's intelligent fingerprint generation with existing device profiles
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from browserforge import FingerprintGenerator, Fingerprint
    BROWSERFORGE_AVAILABLE = True
except ImportError:
    BROWSERFORGE_AVAILABLE = False
    logging.warning("BrowserForge not installed. Install with: pip install browserforge")

from .device_profile_loader import DeviceProfileLoader

logger = logging.getLogger(__name__)


class BrowserForgeManager:
    """
    Enhanced fingerprint manager combining:
    1. BrowserForge's Bayesian network-based fingerprints
    2. Your existing realistic device profiles from CSV
    """
    
    def __init__(self):
        self.profile_loader = DeviceProfileLoader()
        
        if BROWSERFORGE_AVAILABLE:
            self.fp_generator = FingerprintGenerator()
            logger.info("✅ BrowserForge initialized successfully")
        else:
            self.fp_generator = None
            logger.warning("⚠️ BrowserForge not available - using basic profiles only")
    
    def generate_enhanced_fingerprint(
        self,
        device_type: str = "iphone_x",
        use_browserforge: bool = True
    ) -> Dict[str, Any]:
        """
        Generate enhanced fingerprint combining BrowserForge + CSV profiles
        
        Args:
            device_type: Device type (e.g., "iphone_x", "samsung_galaxy")
            use_browserforge: Whether to use BrowserForge enhancement
        
        Returns:
            Enhanced mobile config dictionary
        """
        # Start with base CSV profile
        if "samsung" in device_type.lower() or "android" in device_type.lower():
            csv_profile = self.profile_loader.get_random_android_profile()
        else:
            csv_profile = self.profile_loader.get_random_iphone_profile()
        
        # Convert to mobile config
        base_config = self.profile_loader.convert_to_mobile_config(csv_profile)
        
        # Enhance with BrowserForge if available
        if use_browserforge and BROWSERFORGE_AVAILABLE and self.fp_generator:
            try:
                enhanced_config = self._apply_browserforge_enhancement(base_config, device_type)
                logger.info(f"🎭 BrowserForge enhancement applied to {base_config.get('device_name', 'device')}")
                return enhanced_config
            except Exception as e:
                logger.warning(f"⚠️ BrowserForge enhancement failed: {str(e)[:100]}")
                logger.info("Falling back to base CSV profile")
                return base_config
        else:
            logger.info(f"📱 Using base CSV profile for {base_config.get('device_name', 'device')}")
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
        
        # Generate BrowserForge fingerprint with constraints
        fingerprint = self.fp_generator.generate(
            screen={
                'min_width': base_config['viewport']['width'] - 10,
                'max_width': base_config['viewport']['width'] + 10,
                'min_height': base_config['viewport']['height'] - 10,
                'max_height': base_config['viewport']['height'] + 10,
            },
            strict=False,
            browsers=browsers,
            operating_systems=operating_systems,
            devices=['mobile']
        )
        
        # Merge BrowserForge enhancements with base config
        enhanced_config = base_config.copy()
        
        # Update with BrowserForge values where they're more sophisticated
        enhanced_config.update({
            # BrowserForge provides more realistic user agent
            'user_agent': fingerprint.navigator.user_agent,
            
            # Enhanced navigator properties
            'platform': fingerprint.navigator.platform,
            'hardware_concurrency': fingerprint.navigator.hardware_concurrency,
            'device_memory': fingerprint.navigator.device_memory,
            'max_touch_points': fingerprint.navigator.max_touch_points,
            
            # BrowserForge language preferences
            'language': fingerprint.navigator.language,
            'languages': fingerprint.navigator.languages,
            
            # Enhanced WebGL fingerprinting
            'webgl_vendor': fingerprint.navigator.webgl.vendor if fingerprint.navigator.webgl else base_config.get('webgl_vendor'),
            'webgl_renderer': fingerprint.navigator.webgl.renderer if fingerprint.navigator.webgl else base_config.get('webgl_renderer'),
            
            # Screen properties from BrowserForge
            'screen_width': fingerprint.screen.width,
            'screen_height': fingerprint.screen.height,
            
            # Keep viewport from CSV (it's already accurate)
            'viewport': base_config['viewport'],
            
            # Keep other CSV values that are device-specific
            'device_name': base_config.get('device_name'),
            'os_version': base_config.get('os_version'),
            'canvas_seed': base_config.get('canvas_seed'),
            'audio_seed': base_config.get('audio_seed'),
            'timezone': base_config.get('timezone'),
            'battery_level': base_config.get('battery_level'),
            'battery_charging': base_config.get('battery_charging'),
            
            # Add BrowserForge metadata
            '_browserforge_enhanced': True,
            '_browserforge_fingerprint_id': getattr(fingerprint, 'fingerprint_id', 'unknown')
        })
        
        return enhanced_config
    
    def get_browserforge_fingerprint_only(
        self,
        device_type: str = "mobile"
    ) -> Optional['Fingerprint']:
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
                    devices=['mobile'],
                    operating_systems=['ios', 'android'],
                    strict=False
                )
            else:
                fingerprint = self.fp_generator.generate(
                    devices=['desktop'],
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
        return {
            "browserforge_available": self.is_browserforge_available(),
            "csv_profiles_loaded": {
                "iphone": len(self.profile_loader.iphone_profiles),
                "android": len(self.profile_loader.android_profiles)
            },
            "enhancement_enabled": self.is_browserforge_available()
        }
