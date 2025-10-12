"""
GeoIP Manager - Robust offline/online GeoIP database management

Handles GeoIP database initialization, auto-download, and fallback strategies
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
import urllib.request
import shutil

logger = logging.getLogger(__name__)


class GeoIPManager:
    """
    Manages GeoIP database with automatic download and fallback support
    """
    
    # GeoIP database sources (in priority order)
    GEOIP_SOURCES = [
        {
            'name': 'GeoLite Legacy',
            'url': 'https://github.com/mbcc2006/GeoLiteCity-data/raw/master/GeoLiteCity.dat',
            'filename': 'GeoLiteCity.dat',
            'format': 'legacy'
        },
    ]
    
    # Search paths for existing database
    SEARCH_PATHS = [
        Path(__file__).parent.parent.parent / "profiles" / "GeoLiteCity.dat",
        Path.home() / ".playwright-stealth" / "GeoLiteCity.dat",
        Path("/usr/share/GeoIP/GeoLiteCity.dat"),
        Path("/usr/local/share/GeoIP/GeoLiteCity.dat"),
        Path("./profiles/GeoLiteCity.dat"),
        Path("./GeoLiteCity.dat"),
    ]
    
    def __init__(self, auto_download: bool = True):
        """
        Initialize GeoIP manager
        
        Args:
            auto_download: Automatically download database if not found
        """
        self.geoip_db = None
        self.geoip_path = None
        self.auto_download = auto_download
        
        # Try to initialize
        self._initialize_geoip()
    
    def _initialize_geoip(self):
        """Initialize GeoIP database with fallback strategies"""
        
        # Try to import pygeoip
        try:
            import pygeoip
            self.pygeoip = pygeoip
        except ImportError:
            logger.warning("⚠️ pygeoip not installed. Install with: pip install pygeoip")
            logger.info("💡 Will use online fallback for IP geolocation")
            return
        
        # Search for existing database
        for path in self.SEARCH_PATHS:
            if path.exists():
                try:
                    self.geoip_db = pygeoip.GeoIP(str(path), pygeoip.MEMORY_CACHE)
                    self.geoip_path = path
                    
                    # Verify it works
                    test_record = self.geoip_db.record_by_addr("8.8.8.8")
                    if test_record:
                        logger.info(f"✅ GeoIP database loaded: {path}")
                        logger.info(f"   Database size: {path.stat().st_size / 1024 / 1024:.1f} MB")
                        return
                
                except Exception as e:
                    logger.debug(f"Failed to load GeoIP from {path}: {e}")
                    continue
        
        # Database not found
        logger.warning("⚠️ GeoIP database not found in any search path")
        
        # Try to auto-download
        if self.auto_download:
            logger.info("📥 Attempting to download GeoIP database...")
            if self._download_geoip_database():
                logger.info("✅ GeoIP database downloaded and initialized")
            else:
                logger.warning("⚠️ GeoIP download failed - will use online fallback")
        else:
            logger.info("💡 Auto-download disabled - will use online fallback")
    
    def _download_geoip_database(self) -> bool:
        """
        Download GeoIP database from available sources
        
        Returns:
            True if successful, False otherwise
        """
        # Create profiles directory if it doesn't exist
        profiles_dir = Path(__file__).parent.parent.parent / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Try each source
        for source in self.GEOIP_SOURCES:
            try:
                download_path = profiles_dir / source['filename']
                temp_path = download_path.with_suffix('.tmp')
                
                logger.info(f"📥 Downloading from: {source['name']}")
                logger.info(f"   URL: {source['url']}")
                
                # Download with progress
                def report_progress(block_num, block_size, total_size):
                    if total_size > 0:
                        percent = block_num * block_size / total_size * 100
                        if block_num % 100 == 0:  # Log every 100 blocks
                            logger.debug(f"   Progress: {percent:.1f}%")
                
                urllib.request.urlretrieve(
                    source['url'],
                    temp_path,
                    reporthook=report_progress
                )
                
                # Verify download
                if temp_path.exists() and temp_path.stat().st_size > 1000000:  # At least 1MB
                    # Move to final location
                    shutil.move(str(temp_path), str(download_path))
                    
                    # Try to initialize
                    try:
                        self.geoip_db = self.pygeoip.GeoIP(
                            str(download_path),
                            self.pygeoip.MEMORY_CACHE
                        )
                        self.geoip_path = download_path
                        
                        # Verify it works
                        test_record = self.geoip_db.record_by_addr("8.8.8.8")
                        if test_record:
                            logger.info(f"✅ Downloaded and verified: {download_path}")
                            return True
                    
                    except Exception as e:
                        logger.error(f"❌ Downloaded file is corrupted: {e}")
                        download_path.unlink(missing_ok=True)
                else:
                    logger.error(f"❌ Download incomplete or corrupted")
                    temp_path.unlink(missing_ok=True)
            
            except Exception as e:
                logger.error(f"❌ Download from {source['name']} failed: {e}")
                continue
        
        return False
    
    def lookup_ip(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """
        Lookup IP address in GeoIP database
        
        Args:
            ip_address: IP address to lookup
        
        Returns:
            Dict with city, country_code, country_name, region, etc.
            or None if lookup fails
        """
        if not self.geoip_db:
            return None
        
        try:
            record = self.geoip_db.record_by_addr(ip_address)
            if record:
                return {
                    'city': record.get('city', '').lower(),
                    'country_code': record.get('country_code', ''),
                    'country_name': record.get('country_name', ''),
                    'region': record.get('region', ''),
                    'region_name': record.get('region_name', ''),
                    'latitude': record.get('latitude'),
                    'longitude': record.get('longitude'),
                    'time_zone': record.get('time_zone'),  # Some GeoIP DBs include this
                    'metro_code': record.get('metro_code'),
                }
            return None
        
        except Exception as e:
            logger.debug(f"GeoIP lookup failed for {ip_address}: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if GeoIP database is available and working"""
        return self.geoip_db is not None
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the loaded database"""
        if not self.geoip_db or not self.geoip_path:
            return {
                'available': False,
                'path': None,
                'size_mb': 0
            }
        
        return {
            'available': True,
            'path': str(self.geoip_path),
            'size_mb': self.geoip_path.stat().st_size / 1024 / 1024
        }
    
    @classmethod
    def download_database_cli(cls) -> bool:
        """
        CLI method to manually download GeoIP database
        
        Usage:
            python -c "from utils.geoip_manager import GeoIPManager; GeoIPManager.download_database_cli()"
        """
        logger.info("=== GeoIP Database Download Utility ===")
        manager = cls(auto_download=False)
        
        if manager.is_available():
            logger.info(f"✅ Database already exists: {manager.geoip_path}")
            response = input("Download anyway? (y/N): ")
            if response.lower() != 'y':
                return True
        
        return manager._download_geoip_database()


# Singleton instance
_geoip_instance = None


def get_geoip_manager(auto_download: bool = True) -> GeoIPManager:
    """
    Get singleton GeoIP manager instance
    
    Args:
        auto_download: Auto-download database if not found (first call only)
    
    Returns:
        GeoIPManager instance
    """
    global _geoip_instance
    
    if _geoip_instance is None:
        _geoip_instance = GeoIPManager(auto_download=auto_download)
    
    return _geoip_instance
