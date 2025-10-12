"""
IP Resolver - Pre-resolve proxy hostnames and detect timezones BEFORE browser launch

This is the critical fix for timezone-IP synchronization issues
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
    Resolves proxy hostnames to IPs and detects timezones BEFORE browser launch
    
    This prevents timezone-IP mismatches that cause bot detection
    """
    
    def __init__(self, timezone_manager: Optional[TimezoneManager] = None):
        """
        Initialize IP resolver
        
        Args:
            timezone_manager: TimezoneManager instance (creates new if None)
        """
        self.timezone_manager = timezone_manager or TimezoneManager()
        self.geoip_manager = get_geoip_manager(auto_download=True)
        
        # Cache for resolved proxies (hostname -> ResolvedProxy)
        self._resolution_cache: Dict[str, ResolvedProxy] = {}
        
        logger.info("🌐 IP Resolver initialized")
        
        # Log capabilities
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
        Resolve proxy hostname to IP and detect timezone
        
        This is the MAIN method - call this BEFORE browser launch
        
        Args:
            proxy_config: Dict with 'host', 'port', 'username', 'password'
            force_refresh: Force re-resolution even if cached
        
        Returns:
            ResolvedProxy with IP, timezone, and geo data
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
        
        # Step 1: Resolve DNS (hostname → IP)
        ip_address = await self._resolve_dns(proxy_host)
        
        # Step 2: Detect timezone and geo from IP
        timezone, geo_data = await self._detect_timezone_and_geo(ip_address)
        
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
        logger.info(f"   Method: {resolved.resolution_method}")
        logger.info(f"   Time: {resolution_time:.1f}ms")
        
        return resolved
    
    async def _resolve_dns(self, hostname: str) -> str:
        """
        Resolve hostname to IP address
        
        Args:
            hostname: Hostname or IP address
        
        Returns:
            IP address string
        """
        # Check if already an IP
        if self._is_valid_ip(hostname):
            logger.debug(f"   DNS: Already an IP: {hostname}")
            return hostname
        
        try:
            # Async DNS resolution
            loop = asyncio.get_event_loop()
            ip_address = await loop.run_in_executor(
                None,
                socket.gethostbyname,
                hostname
            )
            
            logger.debug(f"   DNS: {hostname} → {ip_address}")
            return ip_address
        
        except socket.gaierror as e:
            logger.error(f"❌ DNS resolution failed for {hostname}: {e}")
            logger.warning(f"   Treating as IP address: {hostname}")
            return hostname
        
        except Exception as e:
            logger.error(f"❌ Unexpected DNS error: {e}")
            return hostname
    
    async def _detect_timezone_and_geo(
        self,
        ip_address: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Detect timezone and geo data from IP address
        
        Uses multiple methods with fallback:
        1. Offline GeoIP database (fastest)
        2. Online IP-API (fallback)
        3. Reverse DNS hints (last resort)
        4. Default timezone (ultimate fallback)
        
        Args:
            ip_address: IP address to lookup
        
        Returns:
            Tuple of (timezone, geo_data_dict)
        """
        geo_data = {}
        
        # Method 1: Offline GeoIP database (preferred)
        if self.geoip_manager.is_available():
            geoip_record = self.geoip_manager.lookup_ip(ip_address)
            
            if geoip_record:
                city = geoip_record.get('city', '')
                country_code = geoip_record.get('country_code', '')
                latitude = geoip_record.get('latitude')
                longitude = geoip_record.get('longitude')
                
                # 🆕 ENHANCED: Use lat/lon for US timezone detection
                if country_code == 'US' and latitude and longitude:
                    timezone = self._detect_us_timezone_from_coords(latitude, longitude)
                    if timezone:
                        geo_data = {
                            'method': 'geoip_offline_latlon',
                            'city': city.title() if city else None,
                            'country': geoip_record.get('country_name'),
                            'country_code': country_code,
                            'latitude': latitude,
                            'longitude': longitude,
                        }
                        logger.debug(f"   GeoIP (Lat/Lon): {latitude:.2f}, {longitude:.2f} → {timezone}")
                        return timezone, geo_data
                
                # Try city-based timezone (fallback)
                timezone = self.timezone_manager.get_timezone_for_location(
                    city=city,
                    country=country_code
                )
                
                if timezone:
                    geo_data = {
                        'method': 'geoip_offline',
                        'city': city.title() if city else None,
                        'country': geoip_record.get('country_name'),
                        'country_code': country_code,
                        'latitude': latitude,
                        'longitude': longitude,
                    }
                    logger.debug(f"   GeoIP: {city}, {country_code} → {timezone}")
                    return timezone, geo_data
        
        # Method 2: Online IP-API (fallback)
        try:
            import requests
            
            logger.debug(f"   Trying online IP-API for {ip_address}")
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.get(
                    f"http://ip-api.com/json/{ip_address}",
                    params={'fields': 'status,timezone,city,country,countryCode,lat,lon'},
                    timeout=3
                )
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    timezone = data.get('timezone')
                    
                    if timezone:
                        geo_data = {
                            'method': 'ip_api_online',
                            'city': data.get('city'),
                            'country': data.get('country'),
                            'country_code': data.get('countryCode'),
                            'latitude': data.get('lat'),
                            'longitude': data.get('lon'),
                        }
                        logger.debug(f"   IP-API: {data.get('city')}, {data.get('country')} → {timezone}")
                        return timezone, geo_data
        
        except Exception as e:
            logger.debug(f"   IP-API failed: {str(e)[:80]}")
        
        # Method 3: Reverse DNS hints (last resort)
        try:
            loop = asyncio.get_event_loop()
            hostname_parts = await loop.run_in_executor(
                None,
                lambda: socket.gethostbyaddr(ip_address)[0].lower().split('.')
            )
            
            # Check hostname for city/region hints
            timezone = self.timezone_manager.get_timezone_from_hostname_hints(hostname_parts)
            
            if timezone:
                geo_data = {
                    'method': 'reverse_dns',
                }
                logger.debug(f"   Reverse DNS: hints → {timezone}")
                return timezone, geo_data
        
        except Exception as e:
            logger.debug(f"   Reverse DNS failed: {str(e)[:50]}")
        
        # Method 4: Default timezone (ultimate fallback)
        default_timezone = "America/New_York"
        logger.warning(f"⚠️ Could not detect timezone for {ip_address}")
        logger.info(f"💡 Using default timezone: {default_timezone}")
        
        geo_data = {
            'method': 'default_fallback',
        }
        
        return default_timezone, geo_data
    
    def _is_valid_ip(self, ip_str: str) -> bool:
        """Check if string is a valid IPv4 address"""
        try:
            parts = [int(p) for p in ip_str.split('.')]
            return len(parts) == 4 and all(0 <= p <= 255 for p in parts)
        except:
            return False
    
    def _detect_us_timezone_from_coords(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Detect US timezone from latitude/longitude coordinates
        
        Uses approximate longitude boundaries for US timezones:
        - Pacific: < -120 (More negative = further West)
        - Mountain: -120 to -104
        - Central: -104 to -87  
        - Eastern: > -87 (Less negative = further East)
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
        
        Returns:
            IANA timezone string or None
        """
        if not latitude or not longitude:
            return None
        
        # US timezone boundaries (longitude gets MORE negative going West)
        # Pacific is most negative (westernmost)
        if longitude < -120:  # 🆕 FIXED: West of -120° = Pacific
            # Check if Arizona (Phoenix area) - doesn't observe DST
            if 31 <= latitude <= 37 and -114.8 <= longitude <= -109:
                return 'America/Phoenix'  # No DST
            return 'America/Los_Angeles'  # Pacific Time
        
        elif -120 <= longitude < -104:  # Mountain timezone
            # Check if Arizona/Phoenix area
            if 31 <= latitude <= 37 and -114.8 <= longitude <= -109:
                return 'America/Phoenix'
            return 'America/Denver'  # Mountain Time
        
        elif -104 <= longitude < -87:  # Central timezone
            return 'America/Chicago'
        
        else:  # East of -87° = Eastern (least negative)
            return 'America/New_York'
    
    def get_cached_resolution(self, hostname: str) -> Optional[ResolvedProxy]:
        """
        Get cached resolution for hostname
        
        Args:
            hostname: Proxy hostname
        
        Returns:
            ResolvedProxy if cached, None otherwise
        """
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
