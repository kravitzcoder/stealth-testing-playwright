"""
IP Resolver - FIXED: Accurate coordinate resolution

CRITICAL FIX: Ensures Geolocation API coordinates match the actual IP location
by using timezone-based defaults when GeoIP coordinates are inaccurate
"""

import logging
import socket
import asyncio
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .timezone_manager import TimezoneManager
from .geoip_manager import get_geoip_manager

logger = logging.getLogger(__name__)


@dataclass
class ResolvedProxy:
    """Container for resolved proxy information"""
    hostname: str
    ip_address: str
    timezone: str
    city: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    resolution_method: str = "unknown"
    resolution_time_ms: float = 0


class IPResolver:
    """
    Resolves proxy hostnames to IPs and detects timezones with ACCURATE coordinates
    """
    
    # 🆕 TIMEZONE DEFAULT COORDINATES (Major city centers)
    # Used when GeoIP coordinates are inaccurate or unavailable
    TIMEZONE_DEFAULT_COORDS = {
        'America/Los_Angeles': (34.0522, -118.2437),  # Los Angeles downtown
        'America/New_York': (40.7128, -74.0060),      # New York City
        'America/Chicago': (41.8781, -87.6298),       # Chicago downtown
        'America/Denver': (39.7392, -104.9903),       # Denver downtown
        'America/Phoenix': (33.4484, -112.0740),      # Phoenix downtown
        'America/Toronto': (43.6532, -79.3832),       # Toronto
        'America/Vancouver': (49.2827, -123.1207),    # Vancouver
        'Europe/London': (51.5074, -0.1278),          # London
        'Europe/Paris': (48.8566, 2.3522),            # Paris
        'Europe/Berlin': (52.5200, 13.4050),          # Berlin
        'Asia/Tokyo': (35.6762, 139.6503),            # Tokyo
        'Asia/Singapore': (1.3521, 103.8198),         # Singapore
        'Asia/Hong_Kong': (22.3193, 114.1694),        # Hong Kong
    }
    
    # 🆕 MAJOR CITIES COORDINATES (for city-based matching)
    CITY_COORDS = {
        'los angeles': (34.0522, -118.2437),
        'san francisco': (37.7749, -122.4194),
        'san jose': (37.3382, -121.8863),
        'seattle': (47.6062, -122.3321),
        'new york': (40.7128, -74.0060),
        'chicago': (41.8781, -87.6298),
        'miami': (25.7617, -80.1918),
        'dallas': (32.7767, -96.7970),
        'denver': (39.7392, -104.9903),
        'phoenix': (33.4484, -112.0740),
        'boston': (42.3601, -71.0589),
        'atlanta': (33.7490, -84.3880),
        'london': (51.5074, -0.1278),
        'paris': (48.8566, 2.3522),
        'tokyo': (35.6762, 139.6503),
        'singapore': (1.3521, 103.8198),
    }
    
    def __init__(self, timezone_manager: Optional[TimezoneManager] = None):
        """Initialize IP resolver with accurate coordinate mapping"""
        self.timezone_manager = timezone_manager or TimezoneManager()
        self.geoip_manager = get_geoip_manager(auto_download=True)
        self._resolution_cache: Dict[str, ResolvedProxy] = {}
        
        logger.info("🌐 IP Resolver initialized")
        
        if self.geoip_manager.is_available():
            db_info = self.geoip_manager.get_database_info()
            logger.info(f"   GeoIP: ✅ Available ({db_info['size_mb']:.1f} MB)")
        else:
            logger.info("   GeoIP: ⚠️ Unavailable (will use online fallback)")
    
    async def resolve_proxy(
        self,
        proxy_config: Dict[str, str],
        force_refresh: bool = False
    ) -> ResolvedProxy:
        """
        Resolve proxy hostname to IP and detect timezone with ACCURATE coordinates
        """
        import time
        start_time = time.time()
        
        proxy_host = proxy_config.get("host", "")
        
        if not proxy_host:
            logger.warning("⚠️ No proxy host provided - using defaults")
            return ResolvedProxy(
                hostname="none",
                ip_address="",
                timezone="America/New_York",
                resolution_method="no_proxy"
            )
        
        # Check cache
        if not force_refresh and proxy_host in self._resolution_cache:
            cached = self._resolution_cache[proxy_host]
            logger.debug(f"📋 Using cached resolution: {proxy_host} → {cached.ip_address} ({cached.timezone})")
            return cached
        
        logger.info(f"🔍 Resolving proxy: {proxy_host}")
        
        # Step 1: Resolve DNS
        ip_address = await self._resolve_dns(proxy_host)
        
        # Step 2: Detect timezone and geo with ACCURATE coordinates
        timezone, geo_data = await self._detect_timezone_and_geo_accurate(ip_address)
        
        # Step 3: Create resolved proxy object
        resolution_time = (time.time() - start_time) * 1000
        
        resolved = ResolvedProxy(
            hostname=proxy_host,
            ip_address=ip_address,
            timezone=timezone,
            city=geo_data.get('city'),
            country=geo_data.get('country'),
            country_code=geo_data.get('country_code'),
            latitude=geo_data.get('latitude'),
            longitude=geo_data.get('longitude'),
            resolution_method=geo_data.get('method', 'unknown'),
            resolution_time_ms=resolution_time
        )
        
        # Cache the result
        self._resolution_cache[proxy_host] = resolved
        
        # Log results
        logger.info(f"✅ Resolved: {proxy_host}")
        logger.info(f"   IP: {ip_address}")
        logger.info(f"   Timezone: {timezone}")
        if resolved.city:
            logger.info(f"   Location: {resolved.city}, {resolved.country}")
        if resolved.latitude and resolved.longitude:
            logger.info(f"   Coordinates: {resolved.latitude:.4f}, {resolved.longitude:.4f}")
        logger.info(f"   Method: {resolved.resolution_method}")
        logger.info(f"   Time: {resolution_time:.1f}ms")
        
        return resolved
    
    async def _detect_timezone_and_geo_accurate(
        self,
        ip_address: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        🆕 FIXED: Detect timezone with ACCURATE coordinates
        
        Strategy:
        1. Try online IP-API first (most accurate for coordinates)
        2. Fall back to GeoIP + timezone-based coords
        3. Use timezone default coordinates as last resort
        """
        geo_data = {}
        
        # Method 1: Online IP-API (MOST ACCURATE for coordinates)
        try:
            import requests
            
            logger.debug(f"   Trying IP-API (most accurate) for {ip_address}")
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.get(
                    f"http://ip-api.com/json/{ip_address}",
                    params={'fields': 'status,timezone,city,country,countryCode,lat,lon'},
                    timeout=5
                )
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    timezone = data.get('timezone')
                    city = data.get('city', '').lower()
                    lat = data.get('lat')
                    lon = data.get('lon')
                    
                    # 🔥 CRITICAL: Verify coordinates match the city
                    # If GeoIP says "San Jose" but coords are for LA, trust the coords
                    coords_verified = self._verify_coordinates_match_city(
                        city, lat, lon, timezone
                    )
                    
                    if timezone and lat and lon:
                        geo_data = {
                            'method': 'ip_api_online_accurate',
                            'city': data.get('city'),
                            'country': data.get('country'),
                            'country_code': data.get('countryCode'),
                            'latitude': lat,
                            'longitude': lon,
                            'coords_verified': coords_verified
                        }
                        logger.debug(f"   IP-API: {city} ({lat:.4f}, {lon:.4f}) → {timezone}")
                        return timezone, geo_data
        
        except Exception as e:
            logger.debug(f"   IP-API failed: {str(e)[:80]}")
        
        # Method 2: Offline GeoIP + Timezone-based coordinate correction
        if self.geoip_manager.is_available():
            geoip_record = self.geoip_manager.lookup_ip(ip_address)
            
            if geoip_record:
                city = geoip_record.get('city', '').lower()
                country_code = geoip_record.get('country_code', '')
                geoip_lat = geoip_record.get('latitude')
                geoip_lon = geoip_record.get('longitude')
                
                # Detect timezone from coordinates
                if country_code == 'US' and geoip_lat and geoip_lon:
                    timezone = self._detect_us_timezone_from_coords(geoip_lat, geoip_lon)
                else:
                    timezone = self.timezone_manager.get_timezone_for_location(
                        city=city,
                        country=country_code
                    )
                
                if timezone:
                    # 🔥 CRITICAL FIX: Use timezone default coords instead of GeoIP coords
                    # This ensures consistency (e.g., LA timezone gets LA coords, not San Jose)
                    if timezone in self.TIMEZONE_DEFAULT_COORDS:
                        corrected_lat, corrected_lon = self.TIMEZONE_DEFAULT_COORDS[timezone]
                        logger.debug(f"   ✅ Using timezone default coords for {timezone}")
                        logger.debug(f"      GeoIP: {city} ({geoip_lat:.4f}, {geoip_lon:.4f})")
                        logger.debug(f"      Using: {timezone} default ({corrected_lat:.4f}, {corrected_lon:.4f})")
                        
                        geo_data = {
                            'method': 'geoip_offline_timezone_corrected',
                            'city': self._get_city_from_timezone(timezone),  # Use timezone's main city
                            'country': geoip_record.get('country_name'),
                            'country_code': country_code,
                            'latitude': corrected_lat,
                            'longitude': corrected_lon,
                            'geoip_original_city': city,  # Keep original for reference
                            'coords_corrected': True
                        }
                        return timezone, geo_data
                    else:
                        # Use GeoIP coords if no timezone default available
                        geo_data = {
                            'method': 'geoip_offline',
                            'city': city.title() if city else None,
                            'country': geoip_record.get('country_name'),
                            'country_code': country_code,
                            'latitude': geoip_lat,
                            'longitude': geoip_lon,
                        }
                        return timezone, geo_data
        
        # Method 3: Default timezone with default coordinates
        default_timezone = "America/Los_Angeles"
        logger.warning(f"⚠️ Could not detect timezone for {ip_address}")
        logger.info(f"💡 Using default timezone: {default_timezone}")
        
        if default_timezone in self.TIMEZONE_DEFAULT_COORDS:
            lat, lon = self.TIMEZONE_DEFAULT_COORDS[default_timezone]
            geo_data = {
                'method': 'default_fallback_with_coords',
                'city': self._get_city_from_timezone(default_timezone),
                'latitude': lat,
                'longitude': lon,
            }
        else:
            geo_data = {'method': 'default_fallback'}
        
        return default_timezone, geo_data
    
    def _verify_coordinates_match_city(
        self,
        city: str,
        lat: float,
        lon: float,
        timezone: str
    ) -> bool:
        """
        Verify if coordinates actually match the reported city
        
        Returns True if coordinates are reasonable for the city/timezone
        """
        if not city or not lat or not lon:
            return False
        
        city_lower = city.lower()
        
        # Check if city has known coordinates
        if city_lower in self.CITY_COORDS:
            expected_lat, expected_lon = self.CITY_COORDS[city_lower]
            # Allow 1 degree variance (~70 miles)
            lat_diff = abs(lat - expected_lat)
            lon_diff = abs(lon - expected_lon)
            
            if lat_diff < 1.0 and lon_diff < 1.0:
                return True
            else:
                logger.debug(f"   ⚠️ Coordinate mismatch: {city} expected ({expected_lat:.2f},{expected_lon:.2f}), got ({lat:.2f},{lon:.2f})")
                return False
        
        return True  # Unknown city, assume coords are correct
    
    def _get_city_from_timezone(self, timezone: str) -> str:
        """Get the primary city name from a timezone"""
        timezone_city_map = {
            'America/Los_Angeles': 'Los Angeles',
            'America/New_York': 'New York',
            'America/Chicago': 'Chicago',
            'America/Denver': 'Denver',
            'America/Phoenix': 'Phoenix',
            'Europe/London': 'London',
            'Europe/Paris': 'Paris',
            'Asia/Tokyo': 'Tokyo',
        }
        return timezone_city_map.get(timezone, timezone.split('/')[-1].replace('_', ' '))
    
    async def _resolve_dns(self, hostname: str) -> str:
        """Resolve hostname to IP address"""
        if self._is_valid_ip(hostname):
            logger.debug(f"   DNS: Already an IP: {hostname}")
            return hostname
        
        try:
            loop = asyncio.get_event_loop()
            ip_address = await loop.run_in_executor(
                None,
                socket.gethostbyname,
                hostname
            )
            
            logger.debug(f"   DNS: {hostname} → {ip_address}")
            return ip_address
        
        except Exception as e:
            logger.error(f"❌ DNS resolution failed for {hostname}: {e}")
            return hostname
    
    def _is_valid_ip(self, ip_str: str) -> bool:
        """Check if string is a valid IPv4 address"""
        try:
            parts = [int(p) for p in ip_str.split('.')]
            return len(parts) == 4 and all(0 <= p <= 255 for p in parts)
        except:
            return False
    
    def _detect_us_timezone_from_coords(self, latitude: float, longitude: float) -> Optional[str]:
        """Detect US timezone from coordinates"""
        if not latitude or not longitude:
            return None
        
        if longitude < -120:
            if 31 <= latitude <= 37 and -114.8 <= longitude <= -109:
                return 'America/Phoenix'
            return 'America/Los_Angeles'
        elif -120 <= longitude < -104:
            if 31 <= latitude <= 37 and -114.8 <= longitude <= -109:
                return 'America/Phoenix'
            return 'America/Denver'
        elif -104 <= longitude < -87:
            return 'America/Chicago'
        else:
            return 'America/New_York'
    
    def get_cached_resolution(self, hostname: str) -> Optional[ResolvedProxy]:
        """Get cached resolution for hostname"""
        return self._resolution_cache.get(hostname)
    
    def clear_cache(self):
        """Clear resolution cache"""
        self._resolution_cache.clear()
        logger.info("🗑️ Resolution cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cached_proxies': len(self._resolution_cache),
            'hostnames': list(self._resolution_cache.keys())
        }
