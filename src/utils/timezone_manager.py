"""
Timezone Manager - Automatically detect and set timezone based on proxy IP

Handles timezone synchronization between proxy geolocation and browser fingerprint
to prevent timezone-based detection.
"""

import logging
from typing import Optional, Dict, Any
import socket

logger = logging.getLogger(__name__)


class TimezoneManager:
    """
    Manages timezone detection and mapping based on proxy IP geolocation
    """
    
    # Comprehensive mapping of countries/cities to IANA timezones
    CITY_TIMEZONE_MAP = {
        # United States - Major Cities
        'los angeles': 'America/Los_Angeles',
        'san francisco': 'America/Los_Angeles',
        'seattle': 'America/Los_Angeles',
        'portland': 'America/Los_Angeles',
        'las vegas': 'America/Los_Angeles',
        'san diego': 'America/Los_Angeles',
        'phoenix': 'America/Phoenix',
        'denver': 'America/Denver',
        'salt lake city': 'America/Denver',
        'chicago': 'America/Chicago',
        'dallas': 'America/Chicago',
        'houston': 'America/Chicago',
        'austin': 'America/Chicago',
        'new york': 'America/New_York',
        'boston': 'America/New_York',
        'miami': 'America/New_York',
        'atlanta': 'America/New_York',
        'washington': 'America/New_York',
        'philadelphia': 'America/New_York',
        
        # Canada
        'toronto': 'America/Toronto',
        'montreal': 'America/Toronto',
        'ottawa': 'America/Toronto',
        'vancouver': 'America/Vancouver',
        'calgary': 'America/Edmonton',
        'edmonton': 'America/Edmonton',
        
        # Europe
        'london': 'Europe/London',
        'manchester': 'Europe/London',
        'paris': 'Europe/Paris',
        'marseille': 'Europe/Paris',
        'berlin': 'Europe/Berlin',
        'munich': 'Europe/Berlin',
        'frankfurt': 'Europe/Berlin',
        'amsterdam': 'Europe/Amsterdam',
        'brussels': 'Europe/Brussels',
        'madrid': 'Europe/Madrid',
        'barcelona': 'Europe/Madrid',
        'rome': 'Europe/Rome',
        'milan': 'Europe/Rome',
        'vienna': 'Europe/Vienna',
        'zurich': 'Europe/Zurich',
        'stockholm': 'Europe/Stockholm',
        'oslo': 'Europe/Oslo',
        'copenhagen': 'Europe/Copenhagen',
        'dublin': 'Europe/Dublin',
        'lisbon': 'Europe/Lisbon',
        'prague': 'Europe/Prague',
        'warsaw': 'Europe/Warsaw',
        'budapest': 'Europe/Budapest',
        'moscow': 'Europe/Moscow',
        
        # Asia
        'tokyo': 'Asia/Tokyo',
        'osaka': 'Asia/Tokyo',
        'singapore': 'Asia/Singapore',
        'hong kong': 'Asia/Hong_Kong',
        'shanghai': 'Asia/Shanghai',
        'beijing': 'Asia/Shanghai',
        'seoul': 'Asia/Seoul',
        'mumbai': 'Asia/Kolkata',
        'delhi': 'Asia/Kolkata',
        'bangalore': 'Asia/Kolkata',
        'dubai': 'Asia/Dubai',
        'bangkok': 'Asia/Bangkok',
        'manila': 'Asia/Manila',
        'jakarta': 'Asia/Jakarta',
        'kuala lumpur': 'Asia/Kuala_Lumpur',
        'taipei': 'Asia/Taipei',
        
        # Australia
        'sydney': 'Australia/Sydney',
        'melbourne': 'Australia/Sydney',
        'brisbane': 'Australia/Brisbane',
        'perth': 'Australia/Perth',
        'adelaide': 'Australia/Adelaide',
        
        # Africa
        'nairobi': 'Africa/Nairobi',
        'johannesburg': 'Africa/Johannesburg',
        'cairo': 'Africa/Cairo',
        'lagos': 'Africa/Lagos',
        
        # South America
        'sao paulo': 'America/Sao_Paulo',
        'rio de janeiro': 'America/Sao_Paulo',
        'buenos aires': 'America/Argentina/Buenos_Aires',
        'santiago': 'America/Santiago',
        'bogota': 'America/Bogota',
        'lima': 'America/Lima',
    }
    
    # Country to default timezone mapping (fallback)
    COUNTRY_TIMEZONE_MAP = {
        'US': 'America/New_York',
        'CA': 'America/Toronto',
        'GB': 'Europe/London',
        'UK': 'Europe/London',
        'DE': 'Europe/Berlin',
        'FR': 'Europe/Paris',
        'IT': 'Europe/Rome',
        'ES': 'Europe/Madrid',
        'NL': 'Europe/Amsterdam',
        'BE': 'Europe/Brussels',
        'CH': 'Europe/Zurich',
        'AT': 'Europe/Vienna',
        'SE': 'Europe/Stockholm',
        'NO': 'Europe/Oslo',
        'DK': 'Europe/Copenhagen',
        'FI': 'Europe/Helsinki',
        'PL': 'Europe/Warsaw',
        'CZ': 'Europe/Prague',
        'RU': 'Europe/Moscow',
        'JP': 'Asia/Tokyo',
        'CN': 'Asia/Shanghai',
        'KR': 'Asia/Seoul',
        'SG': 'Asia/Singapore',
        'HK': 'Asia/Hong_Kong',
        'IN': 'Asia/Kolkata',
        'TH': 'Asia/Bangkok',
        'PH': 'Asia/Manila',
        'ID': 'Asia/Jakarta',
        'MY': 'Asia/Kuala_Lumpur',
        'TW': 'Asia/Taipei',
        'AU': 'Australia/Sydney',
        'NZ': 'Pacific/Auckland',
        'BR': 'America/Sao_Paulo',
        'AR': 'America/Argentina/Buenos_Aires',
        'CL': 'America/Santiago',
        'MX': 'America/Mexico_City',
        'ZA': 'Africa/Johannesburg',
        'KE': 'Africa/Nairobi',
        'EG': 'Africa/Cairo',
        'NG': 'Africa/Lagos',
        'AE': 'Asia/Dubai',
        'SA': 'Asia/Riyadh',
        'TR': 'Europe/Istanbul',
        'IL': 'Asia/Jerusalem',
    }
    
    def __init__(self):
        """Initialize timezone manager"""
        self.geoip_db = None
        self._init_geoip()
    
    def _init_geoip(self):
        """Initialize GeoIP database if available"""
        try:
            import pygeoip
            from pathlib import Path
            
            # Try common GeoIP database locations
            possible_paths = [
                Path(__file__).parent.parent.parent / "profiles" / "GeoLiteCity.dat",
                Path(__file__).parent.parent / "profiles" / "GeoLiteCity.dat",
                Path("profiles/GeoLiteCity.dat"),
                Path("/usr/share/GeoIP/GeoLiteCity.dat"),
            ]
            
            for geoip_path in possible_paths:
                if geoip_path.exists():
                    self.geoip_db = pygeoip.GeoIP(str(geoip_path))
                    logger.info(f"✅ GeoIP database loaded from {geoip_path}")
                    return
            
            logger.warning("⚠️ GeoIP database not found - will use fallback mapping")
            
        except ImportError:
            logger.warning("⚠️ pygeoip not installed - using fallback timezone mapping")
        except Exception as e:
            logger.warning(f"⚠️ GeoIP init failed: {e}")
    
    def detect_timezone_from_ip(self, ip_address: str) -> Optional[str]:
        """
        Detect timezone from IP address using multiple methods
        
        Args:
            ip_address: IP address to lookup
        
        Returns:
            IANA timezone string or None
        """
        if not ip_address:
            return None
        
        logger.debug(f"🔍 Attempting timezone detection for IP: {ip_address}")
        
        # Try GeoIP database first (most accurate)
        if self.geoip_db:
            try:
                record = self.geoip_db.record_by_addr(ip_address)
                if record:
                    city = record.get('city', '').lower()
                    country_code = record.get('country_code', '')
                    
                    logger.debug(f"GeoIP lookup: {ip_address} → {city}, {country_code}")
                    
                    # Try city-based mapping first (most accurate)
                    if city and city in self.CITY_TIMEZONE_MAP:
                        timezone = self.CITY_TIMEZONE_MAP[city]
                        logger.info(f"🌍 Timezone detected from city: {city} → {timezone}")
                        return timezone
                    
                    # Fall back to country mapping
                    if country_code and country_code in self.COUNTRY_TIMEZONE_MAP:
                        timezone = self.COUNTRY_TIMEZONE_MAP[country_code]
                        logger.info(f"🌍 Timezone detected from country: {country_code} → {timezone}")
                        return timezone
            
            except Exception as e:
                logger.debug(f"GeoIP lookup failed for {ip_address}: {e}")
        
        # Method 2: Try online IP API (fallback when GeoIP unavailable)
        try:
            import requests
            response = requests.get(
                f"http://ip-api.com/json/{ip_address}?fields=status,timezone,city,country",
                timeout=3
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    detected_timezone = data.get('timezone')
                    city = data.get('city', 'Unknown')
                    country = data.get('country', 'Unknown')
                    
                    if detected_timezone:
                        logger.info(f"🌍 Timezone detected from IP-API: {city}, {country} → {detected_timezone}")
                        return detected_timezone
        
        except Exception as e:
            logger.debug(f"IP-API lookup failed: {e}")
        
        # Method 3: Reverse DNS lookup
        try:
            hostname = socket.gethostbyaddr(ip_address)[0].lower()
            logger.debug(f"Reverse DNS: {ip_address} → {hostname}")
            
            # Check hostname for city/country hints
            for city, timezone in self.CITY_TIMEZONE_MAP.items():
                city_key = city.replace(' ', '')
                if city_key in hostname:
                    logger.info(f"🌍 Timezone detected from hostname: {city} → {timezone}")
                    return timezone
            
            # Check for US regions in hostname
            if '.us' in hostname or 'usa' in hostname or 'united-states' in hostname:
                # Try to detect region from hostname
                if 'east' in hostname or 'newyork' in hostname or 'virginia' in hostname:
                    logger.info(f"🌍 Timezone detected from US East hostname → America/New_York")
                    return 'America/New_York'
                elif 'west' in hostname or 'losangeles' in hostname or 'california' in hostname:
                    logger.info(f"🌍 Timezone detected from US West hostname → America/Los_Angeles")
                    return 'America/Los_Angeles'
                elif 'central' in hostname or 'chicago' in hostname or 'texas' in hostname:
                    logger.info(f"🌍 Timezone detected from US Central hostname → America/Chicago")
                    return 'America/Chicago'
        
        except Exception as e:
            logger.debug(f"Reverse DNS failed: {e}")
        
        # No timezone detected - return default based on common US proxy
        logger.warning(f"⚠️ Could not detect timezone for IP: {ip_address}")
        logger.info(f"💡 Defaulting to America/New_York (most common US timezone)")
        return 'America/New_York'  # Safe default for US proxies
    
    def override_timezone_in_config(
        self,
        config: Dict[str, Any],
        proxy_ip: Optional[str] = None,
        force_timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Override timezone in configuration based on proxy IP
        
        Args:
            config: Mobile configuration dictionary
            proxy_ip: Proxy IP address for timezone detection
            force_timezone: Force a specific timezone (overrides detection)
        
        Returns:
            Updated configuration with corrected timezone
        """
        original_timezone = config.get('timezone', 'America/New_York')
        
        # If force_timezone is provided, use it
        if force_timezone:
            config['timezone'] = force_timezone
            logger.info(f"🕐 Timezone forced: {original_timezone} → {force_timezone}")
            return config
        
        # If no proxy IP, keep original
        if not proxy_ip:
            logger.debug(f"🕐 No proxy IP provided - keeping timezone: {original_timezone}")
            return config
        
        # Detect timezone from proxy IP
        detected_timezone = self.detect_timezone_from_ip(proxy_ip)
        
        if detected_timezone:
            config['timezone'] = detected_timezone
            if detected_timezone != original_timezone:
                logger.info(f"🕐 Timezone corrected: {original_timezone} → {detected_timezone} (IP: {proxy_ip})")
            else:
                logger.debug(f"🕐 Timezone already correct: {detected_timezone}")
        else:
            # Keep original if detection completely failed (shouldn't happen now with default)
            logger.debug(f"🕐 No timezone detected - keeping original: {original_timezone}")
        
        return config
    
    def get_timezone_for_location(self, city: Optional[str] = None, country: Optional[str] = None) -> Optional[str]:
        """
        Get timezone for a specific location
        
        Args:
            city: City name
            country: Country code (ISO 3166-1 alpha-2)
        
        Returns:
            IANA timezone string or None
        """
        # Try city first
        if city:
            city_lower = city.lower()
            if city_lower in self.CITY_TIMEZONE_MAP:
                return self.CITY_TIMEZONE_MAP[city_lower]
        
        # Fall back to country
        if country:
            country_upper = country.upper()
            if country_upper in self.COUNTRY_TIMEZONE_MAP:
                return self.COUNTRY_TIMEZONE_MAP[country_upper]
        
        return None
    
    def validate_timezone(self, timezone: str) -> bool:
        """
        Validate if timezone is a valid IANA timezone
        
        Args:
            timezone: Timezone string to validate
        
        Returns:
            True if valid, False otherwise
        """
        try:
            import pytz
            return timezone in pytz.all_timezones
        except ImportError:
            # Fallback: Check if it's in our known timezones
            all_known = set(self.CITY_TIMEZONE_MAP.values()) | set(self.COUNTRY_TIMEZONE_MAP.values())
            return timezone in all_known
