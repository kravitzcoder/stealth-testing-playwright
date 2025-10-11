# Add these methods to base_runner_enhanced.py

class BaseRunner:
    """Base class with shared functionality for all runners"""
    
    def __init__(self, screenshot_engine: Optional[ScreenshotEngine] = None):
        """Initialize base runner with BrowserForge enhancement"""
        self.screenshot_engine = screenshot_engine or ScreenshotEngine()
        
        # Initialize BrowserForge manager (NEW!)
        self.browserforge = BrowserForgeManager()
        
        # Log fingerprint capabilities
        stats = self.browserforge.get_fingerprint_stats()
        if stats['browserforge_available']:
            logger.info("🎭 BrowserForge enhancement enabled")
        else:
            logger.warning("⚠️ BrowserForge not available - using basic profiles")
        
        # Session management (NEW!)
        self._session_started = False
        
        # Optional GeoIP support
        self.geoip = None
        try:
            import pygeoip
            geoip_path = Path(__file__).parent.parent.parent / "profiles" / "GeoLiteCity.dat"
            if geoip_path.exists():
                self.geoip = pygeoip.GeoIP(str(geoip_path))
                logger.debug("GeoIP database loaded")
        except (ImportError, Exception):
            pass
    
    def start_session(self, device_type: str = "iphone_x"):
        """
        Start a new test session with consistent device
        
        CRITICAL: Call this ONCE at the start of a library test run
        
        Args:
            device_type: Device type for the session
        """
        if not self._session_started:
            self.browserforge.start_new_session(device_type)
            self._session_started = True
            logger.info(f"✅ Session started for {device_type}")
    
    def end_session(self):
        """
        End the current test session
        
        Call this after all tests for a library are complete
        """
        if self._session_started:
            self.browserforge.end_session()
            self._session_started = False
            logger.info("✅ Session ended")
    
    def get_enhanced_mobile_config(
        self,
        mobile_config: Dict[str, Any],
        device_type: str = "iphone_x",
        use_browserforge: bool = True
    ) -> Dict[str, Any]:
        """
        Get enhanced mobile config with BrowserForge fingerprints
        
        UPDATED: Now uses session-consistent device
        
        Args:
            mobile_config: Base mobile config from test_targets.json (NOT USED if session active)
            device_type: Device type for profile selection
            use_browserforge: Whether to apply BrowserForge enhancement
        
        Returns:
            Enhanced mobile configuration (SESSION CONSISTENT)
        """
        # Ensure session is started
        if not self._session_started:
            logger.warning("⚠️ Session not started, auto-starting")
            self.start_session(device_type)
        
        if use_browserforge and self.browserforge.is_browserforge_available():
            # Generate enhanced fingerprint (uses session device!)
            enhanced = self.browserforge.generate_enhanced_fingerprint(
                device_type=device_type,
                use_browserforge=True
            )
            
            return enhanced
        else:
            # Fallback to session config (still consistent!)
            session_config = self.browserforge.get_session_config()
            if session_config:
                return session_config
            else:
                # Last resort: use provided config
                return mobile_config

# Rest of your BaseRunner methods remain the same...
