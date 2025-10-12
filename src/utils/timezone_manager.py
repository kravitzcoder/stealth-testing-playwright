"""
Timezone Manager - Enhanced with hostname hints support

Handles timezone detection from IPs, cities, countries, and hostname patterns
"""

import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class TimezoneManager:
    """
    Manages timezone detection and mapping
    """
    
    # Comprehensive city timezone mapping
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
    
    # Country to default timezone mapping
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
    
    # Hostname pattern to timezone mapping
    HOSTNAME_PATTERNS = {
        # US regions
        'east': 'America/New_York',
        'newyork': 'America/New_York',
        'nyc': 'America/New_York',
        'virginia': 'America/New_York',
        'boston': 'America/New_York',
        'miami': 'America/New_York',
        'atlanta': 'America/New_York',
        
        'west': 'America/Los_Angeles',
        'losangeles': 'America/Los_Angeles',
        'california': 'America/Los_Angeles',
        'sanfrancisco': 'America/Los_Angeles',
        'seattle': 'America/Los_Angeles',
        'portland': 'America/Los_Angeles',
        
        'central': 'America/Chicago',
        'chicago': 'America/Chicago',
        'dallas': 'America/Chicago',
        'texas': 'America/Chicago',
        
        'mountain': 'America/Denver',
        'denver': 'America/Denver',
        'phoenix': 'America/Phoenix',
        
        # European cities
        'london': 'Europe/London',
        'paris': 'Europe/Paris',
        'berlin': 'Europe/Berlin',
        'frankfurt': 'Europe/Berlin',
        'amsterdam': 'Europe/Amsterdam',
        'madrid': 'Europe/Madrid',
        'rome': 'Europe/Rome',
        'stockholm': 'Europe/Stockholm',
        'warsaw': 'Europe/Warsaw',
        'moscow': 'Europe/Moscow',
        
        # Asian cities
        'tokyo': 'Asia/Tokyo',
        'singapore': 'Asia/Singapore',
        'hongkong': 'Asia/Hong_Kong',
        'shanghai': 'Asia/Shanghai',
        'beijing': 'Asia/Shanghai',
        'seoul': 'Asia/Seoul',
        'mumbai': 'Asia/Kolkata',
        'bangalore': 'Asia/Kolkata',
        'dubai': 'Asia/Dubai',
        'bangkok': 'Asia/Bangkok',
        
        # Australia
        'sydney': 'Australia/Sydney',
        'melbourne': 'Australia/Sydney',
        'brisbane': 'Australia/Brisbane',
        'perth': 'Australia/Perth',
    }
    
    def __init__(self):
        """Initialize timezone manager"""
        pass
    
    def detect_timezone_from_ip(self, ip_address: str) -> Optional[str]:
        """
        Detect timezone from IP address (used by IPResolver as fallback)
        
        Args:
            ip_address: IP address to lookup
        
        Returns:
            IANA timezone string or None
        """
        if not ip_address:
            return None
        
        logger.debug(f"🔍 Timezone detection for IP: {ip_address}")
        
        # This is now mainly a fallback - IPResolver handles the main logic
        # Just return default for US proxies
        logger.debug(f"   Using default US timezone")
        return 'America/New_York'
    
    def get_timezone_for_location(
        self,
        city: Optional[str] = None,
        country: Optional[str] = None
    ) -> Optional[str]:
        """
        Get timezone for a specific location
        
        Args:
            city: City name
            country: Country code (ISO 3166-1 alpha-2)
        
        Returns:
            IANA timezone string or None
        """
        # Try city first (most accurate)
        if city:
            city_lower = city.lower().strip()
            if city_lower in self.CITY_TIMEZONE_MAP:
                logger.debug(f"   City match: {city_lower} → {self.CITY_TIMEZONE_MAP[city_lower]}")
                return self.CITY_TIMEZONE_MAP[city_lower]
        
        # Fall back to country
        if country:
            country_upper = country.upper().strip()
            if country_upper in self.COUNTRY_TIMEZONE_MAP:
                logger.debug(f"   Country match: {country_upper} → {self.COUNTRY_TIMEZONE_MAP[country_upper]}")
                return self.COUNTRY_TIMEZONE_MAP[country_upper]
        
        return None
    
    def get_timezone_from_hostname_hints(self, hostname_parts: List[str]) -> Optional[str]:
        """
        Detect timezone from hostname patterns
        
        Args:
            hostname_parts: List of hostname parts (e.g., ['proxy', 'us', 'east', 'example', 'com'])
        
        Returns:
            IANA timezone string or None
        """
        hostname_lower = '.'.join(hostname_parts).lower()
        
        # Check each pattern
        for pattern, timezone in self.HOSTNAME_PATTERNS.items():
            if pattern in hostname_lower:
                logger.debug(f"   Hostname pattern match: {pattern} → {timezone}")
                return timezone
        
        # Check for country codes in hostname
        for part in hostname_parts:
            part_upper = part.upper()
            if part_upper in self.COUNTRY_TIMEZONE_MAP:
                timezone = self.COUNTRY_TIMEZONE_MAP[part_upper]
                logger.debug(f"   Hostname country code: {part_upper} → {timezone}")
                return timezone
        
        return None
    
    def override_timezone_in_config(
        self,
        config: Dict[str, Any],
        proxy_ip: Optional[str] = None,
        force_timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Override timezone in configuration (legacy method - prefer IPResolver)
        
        Args:
            config: Mobile configuration dictionary
            proxy_ip: Proxy IP address (optional)
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
        
        # Use fallback detection
        detected_timezone = self.detect_timezone_from_ip(proxy_ip)
        
        if detected_timezone:
            config['timezone'] = detected_timezone
            if detected_timezone != original_timezone:
                logger.info(f"🕐 Timezone corrected: {original_timezone} → {detected_timezone}")
        
        return config
    
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