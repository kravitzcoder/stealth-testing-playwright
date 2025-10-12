"""
Device Profile Loader
Loads and manages device profiles from CSV files for realistic mobile emulation
"""

import logging
import random
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DeviceProfileLoader:
    """
    Loads device profiles from CSV files
    Provides fallback when CSV files are not available
    """
    
    def __init__(self, profiles_dir: Optional[Path] = None):
        """
        Initialize device profile loader
        
        Args:
            profiles_dir: Path to profiles directory (optional)
        """
        self.profiles_dir = profiles_dir
        self.iphone_profiles = self._load_iphone_profiles()
        self.android_profiles = self._load_android_profiles()
        
        logger.info(f"Loaded {len(self.iphone_profiles)} iPhone profiles")
        logger.info(f"Loaded {len(self.android_profiles)} Android profiles")
    
    def _load_iphone_profiles(self) -> List[Dict[str, Any]]:
        """Load iPhone profiles (from CSV or use defaults)"""
        # Try to load from CSV if available
        if self.profiles_dir:
            csv_path = self.profiles_dir / "iphone_profiles.csv"
            if csv_path.exists():
                try:
                    import csv
                    profiles = []
                    with open(csv_path, 'r') as f:
                        reader = csv.DictReader(f)
                        profiles = list(reader)
                    if profiles:
                        return profiles
                except Exception as e:
                    logger.warning(f"Failed to load iPhone CSV: {e}")
        
        # Fallback to default iPhone profiles
        return [
            {
                'device_name': 'iPhone 12 Pro',
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                'viewport_width': '390',
                'viewport_height': '844',
                'device_scale_factor': '3',
                'platform': 'iPhone',
                'max_touch_points': '5',
                'hardware_concurrency': '6',
                'device_memory': '4',
                'language': 'en-US',
                'languages': 'en-US,en',
                'timezone': 'America/Los_Angeles',
                'webgl_vendor': 'Apple Inc.',
                'webgl_renderer': 'Apple GPU',
                'os_version': '14.6',
                'battery_level': '0.85',
                'battery_charging': 'false'
            },
            {
                'device_name': 'iPhone 13 Pro Max',
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                'viewport_width': '428',
                'viewport_height': '926',
                'device_scale_factor': '3',
                'platform': 'iPhone',
                'max_touch_points': '5',
                'hardware_concurrency': '6',
                'device_memory': '6',
                'language': 'en-US',
                'languages': 'en-US,en',
                'timezone': 'America/Los_Angeles',
                'webgl_vendor': 'Apple Inc.',
                'webgl_renderer': 'Apple GPU',
                'os_version': '15.0',
                'battery_level': '0.72',
                'battery_charging': 'true'
            },
            {
                'device_name': 'iPhone 14',
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                'viewport_width': '390',
                'viewport_height': '844',
                'device_scale_factor': '3',
                'platform': 'iPhone',
                'max_touch_points': '5',
                'hardware_concurrency': '6',
                'device_memory': '6',
                'language': 'en-US',
                'languages': 'en-US,en',
                'timezone': 'America/Los_Angeles',
                'webgl_vendor': 'Apple Inc.',
                'webgl_renderer': 'Apple GPU',
                'os_version': '16.0',
                'battery_level': '0.65',
                'battery_charging': 'false'
            },
            {
                'device_name': 'iPhone 15 Pro',
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'viewport_width': '393',
                'viewport_height': '852',
                'device_scale_factor': '3',
                'platform': 'iPhone',
                'max_touch_points': '5',
                'hardware_concurrency': '6',
                'device_memory': '8',
                'language': 'en-US',
                'languages': 'en-US,en',
                'timezone': 'America/Chicago',
                'webgl_vendor': 'Apple Inc.',
                'webgl_renderer': 'Apple A17 Pro GPU',
                'os_version': '17.0',
                'battery_level': '0.91',
                'battery_charging': 'true'
            }
        ]
    
    def _load_android_profiles(self) -> List[Dict[str, Any]]:
        """Load Android profiles (from CSV or use defaults)"""
        # Try to load from CSV if available
        if self.profiles_dir:
            csv_path = self.profiles_dir / "android_profiles.csv"
            if csv_path.exists():
                try:
                    import csv
                    profiles = []
                    with open(csv_path, 'r') as f:
                        reader = csv.DictReader(f)
                        profiles = list(reader)
                    if profiles:
                        return profiles
                except Exception as e:
                    logger.warning(f"Failed to load Android CSV: {e}")
        
        # Fallback to default Android profiles
        return [
            {
                'device_name': 'Samsung Galaxy S21',
                'user_agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
                'viewport_width': '360',
                'viewport_height': '800',
                'device_scale_factor': '3',
                'platform': 'Linux armv8l',
                'max_touch_points': '5',
                'hardware_concurrency': '8',
                'device_memory': '8',
                'language': 'en-US',
                'languages': 'en-US,en',
                'timezone': 'America/Los_Angeles',
                'webgl_vendor': 'Qualcomm',
                'webgl_renderer': 'Adreno (TM) 660',
                'os_version': '11',
                'battery_level': '0.78',
                'battery_charging': 'false'
            },
            {
                'device_name': 'Samsung Galaxy S22',
                'user_agent': 'Mozilla/5.0 (Linux; Android 12; SM-S906B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36',
                'viewport_width': '360',
                'viewport_height': '780',
                'device_scale_factor': '3',
                'platform': 'Linux armv8l',
                'max_touch_points': '5',
                'hardware_concurrency': '8',
                'device_memory': '8',
                'language': 'en-US',
                'languages': 'en-US,en',
                'timezone': 'America/Los_Angeles',
                'webgl_vendor': 'Qualcomm',
                'webgl_renderer': 'Adreno (TM) 730',
                'os_version': '12',
                'battery_level': '0.82',
                'battery_charging': 'true'
            },
            {
                'device_name': 'Google Pixel 6',
                'user_agent': 'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.104 Mobile Safari/537.36',
                'viewport_width': '412',
                'viewport_height': '915',
                'device_scale_factor': '2.625',
                'platform': 'Linux armv8l',
                'max_touch_points': '5',
                'hardware_concurrency': '8',
                'device_memory': '8',
                'language': 'en-US',
                'languages': 'en-US,en',
                'timezone': 'America/Denver',
                'webgl_vendor': 'ARM',
                'webgl_renderer': 'Mali-G78',
                'os_version': '12',
                'battery_level': '0.69',
                'battery_charging': 'false'
            },
            {
                'device_name': 'Google Pixel 7 Pro',
                'user_agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36',
                'viewport_width': '412',
                'viewport_height': '892',
                'device_scale_factor': '3.5',
                'platform': 'Linux armv8l',
                'max_touch_points': '5',
                'hardware_concurrency': '8',
                'device_memory': '12',
                'language': 'en-US',
                'languages': 'en-US,en',
                'timezone': 'America/Phoenix',
                'webgl_vendor': 'ARM',
                'webgl_renderer': 'Mali-G710',
                'os_version': '13',
                'battery_level': '0.88',
                'battery_charging': 'true'
            }
        ]
    
    def get_random_iphone_profile(self) -> Dict[str, Any]:
        """Get a random iPhone profile"""
        return random.choice(self.iphone_profiles)
    
    def get_random_android_profile(self) -> Dict[str, Any]:
        """Get a random Android profile"""
        return random.choice(self.android_profiles)
    
    def get_profile_by_device_name(self, device_name: str) -> Optional[Dict[str, Any]]:
        """Get specific profile by device name"""
        all_profiles = self.iphone_profiles + self.android_profiles
        for profile in all_profiles:
            if profile.get('device_name', '').lower() == device_name.lower():
                return profile
        return None
    
    def convert_to_mobile_config(self, csv_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert CSV profile format to mobile_config format
        
        Args:
            csv_profile: Profile dict from CSV or defaults
        
        Returns:
            mobile_config dictionary
        """
        # Parse languages
        languages_str = csv_profile.get('languages', 'en-US,en')
        if isinstance(languages_str, str):
            languages = [lang.strip() for lang in languages_str.split(',')]
        else:
            languages = languages_str
        
        # Parse viewport
        viewport_width = int(csv_profile.get('viewport_width', 390))
        viewport_height = int(csv_profile.get('viewport_height', 844))
        
        # Parse device scale factor
        try:
            device_scale_factor = float(csv_profile.get('device_scale_factor', 3))
        except ValueError:
            device_scale_factor = 3.0
        
        # Parse battery
        try:
            battery_level = float(csv_profile.get('battery_level', 0.85))
        except ValueError:
            battery_level = 0.85
        
        battery_charging = csv_profile.get('battery_charging', 'false').lower() == 'true'
        
        # Parse hardware
        try:
            hardware_concurrency = int(csv_profile.get('hardware_concurrency', 4))
        except ValueError:
            hardware_concurrency = 4
        
        try:
            device_memory = int(csv_profile.get('device_memory', 4))
        except ValueError:
            device_memory = 4
        
        try:
            max_touch_points = int(csv_profile.get('max_touch_points', 5))
        except ValueError:
            max_touch_points = 5
        
        return {
            'device_name': csv_profile.get('device_name', 'Unknown Device'),
            'user_agent': csv_profile.get('user_agent'),
            'viewport': {
                'width': viewport_width,
                'height': viewport_height
            },
            'device_scale_factor': device_scale_factor,
            'platform': csv_profile.get('platform', 'iPhone'),
            'max_touch_points': max_touch_points,
            'hardware_concurrency': hardware_concurrency,
            'device_memory': device_memory,
            'language': csv_profile.get('language', 'en-US'),
            'languages': languages,
            'timezone': csv_profile.get('timezone', 'America/Los_Angeles'),
            'webgl_vendor': csv_profile.get('webgl_vendor', 'Apple Inc.'),
            'webgl_renderer': csv_profile.get('webgl_renderer', 'Apple GPU'),
            'os_version': csv_profile.get('os_version', '14.0'),
            'battery_level': battery_level,
            'battery_charging': battery_charging,
            'canvas_seed': csv_profile.get('canvas_seed', str(random.randint(1000, 9999))),
            'audio_seed': csv_profile.get('audio_seed', str(random.randint(1000, 9999)))
        }
