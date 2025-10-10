"""
Device Profile Loader - Fixed Version
Loads device profiles from CSV files in profiles subdirectory
"""
import csv
import random
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class DeviceProfileLoader:
    """Load and manage device profiles from CSV files"""
    
    def __init__(self, iphone_csv: str = "iphone-device-profiles.csv", 
                 android_csv: str = "android-device-profiles.csv"):
        # Fix: Look for profiles in the profiles subdirectory
        self.profiles_dir = Path(__file__).parent.parent.parent / "profiles"
        
        # Load profiles
        self.iphone_profiles = self._load_csv(self.profiles_dir / iphone_csv)
        self.android_profiles = self._load_csv(self.profiles_dir / android_csv)
        
        logger.info(f"Loaded {len(self.iphone_profiles)} iPhone profiles from {self.profiles_dir}")
        logger.info(f"Loaded {len(self.android_profiles)} Android profiles from {self.profiles_dir}")
    
    def _load_csv(self, csv_path: Path) -> List[Dict[str, str]]:
        """Load profiles from CSV file"""
        profiles = []
        
        if not csv_path.exists():
            logger.warning(f"CSV file not found: {csv_path}")
            return profiles
            
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    profiles.append(row)
            logger.info(f"Successfully loaded {len(profiles)} profiles from {csv_path.name}")
        except Exception as e:
            logger.error(f"Error loading CSV {csv_path}: {str(e)}")
            
        return profiles
    
    def get_profile_for_device(self, device_type: str = "iphone_x") -> Dict[str, Any]:
        """Get profile based on device type"""
        if "samsung" in device_type.lower() or "android" in device_type.lower() or "galaxy" in device_type.lower():
            return self.get_random_android_profile()
        else:
            return self.get_random_iphone_profile()
    
    def get_random_iphone_profile(self) -> Dict[str, Any]:
        """Get random iPhone profile"""
        if not self.iphone_profiles:
            logger.warning("No iPhone profiles loaded, returning empty dict")
            return {}
        profile = random.choice(self.iphone_profiles)
        logger.info(f"Selected iPhone profile: {profile.get('device_name', 'Unknown')}")
        return profile
    
    def get_random_android_profile(self) -> Dict[str, Any]:
        """Get random Android profile"""
        if not self.android_profiles:
            logger.warning("No Android profiles loaded, returning empty dict")
            return {}
        profile = random.choice(self.android_profiles)
        logger.info(f"Selected Android profile: {profile.get('device_name', 'Unknown')}")
        return profile
    
    def convert_to_mobile_config(self, profile: Dict[str, str]) -> Dict[str, Any]:
        """Convert CSV profile to mobile config format"""
        if not profile:
            logger.warning("Empty profile provided, using defaults")
            return {
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
                "viewport": {"width": 375, "height": 812},
                "device_scale_factor": 2.0,
                "is_mobile": True,
                "has_touch": True
            }
        
        try:
            config = {
                "user_agent": profile.get('user_agent', ''),
                "viewport": {
                    "width": int(profile.get('viewport_width', 375)),
                    "height": int(profile.get('viewport_height', 812))
                },
                "device_scale_factor": float(profile.get('pixel_ratio', 2.0)),
                "is_mobile": True,
                "has_touch": True,
                # Extended fingerprinting data
                "hardware_concurrency": int(profile.get('hardware_concurrency', 4)),
                "device_memory": int(profile.get('device_memory', 4)),
                "max_touch_points": int(profile.get('max_touch_points', 5)),
                "webgl_vendor": profile.get('webgl_vendor', 'Apple'),
                "webgl_renderer": profile.get('webgl_renderer', 'Apple GPU'),
                "platform": profile.get('platform', 'iPhone'),
                "canvas_seed": profile.get('canvas_fingerprint_seed', ''),
                "audio_seed": profile.get('audio_fingerprint_seed', ''),
                "device_name": profile.get('device_name', 'Unknown'),
                "os_version": profile.get('os_version', ''),
                "browser_version": profile.get('browser_version', ''),
                "timezone": profile.get('timezone', 'America/New_York'),
                "language": profile.get('language', 'en-US'),
                "battery_level": int(profile.get('battery_level', 50)),
                "battery_charging": profile.get('battery_charging', 'false').lower() == 'true'
            }
            return config
        except (ValueError, KeyError) as e:
            logger.error(f"Error converting profile: {str(e)}")
            return self.convert_to_mobile_config({})  # Return defaults on error
