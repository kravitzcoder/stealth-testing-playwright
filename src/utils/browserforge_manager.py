"""
BrowserForge Integration Manager - FIXED WebRTC Protection

CRITICAL FIX: Complete WebRTC leak protection with STUN blocking
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from browserforge.fingerprints import FingerprintGenerator, Screen
    from browserforge.headers import HeaderGenerator
    BROWSERFORGE_AVAILABLE = True
except ImportError:
    BROWSERFORGE_AVAILABLE = False
    FingerprintGenerator = None
    Screen = None
    HeaderGenerator = None
    logging.warning("BrowserForge not installed. Install with: pip install browserforge")

from .device_profile_loader import DeviceProfileLoader

logger = logging.getLogger(__name__)


class BrowserForgeManager:
    """
    Enhanced fingerprint manager with FIXED WebRTC protection
    """
    
    def __init__(self):
        self.profile_loader = DeviceProfileLoader()
        
        if BROWSERFORGE_AVAILABLE:
            self.fp_generator = FingerprintGenerator()
            self.header_generator = HeaderGenerator()
            logger.info("✅ BrowserForge initialized")
        else:
            self.fp_generator = None
            self.header_generator = None
            logger.warning("⚠️ BrowserForge not available - using basic profiles only")
        
        # Session management
        self._session_device = None
        self._session_config = None
        self._session_device_type = None
        self._session_fingerprint = None
    
    def start_new_session(self, device_type: str = "iphone_x"):
        """
        Start a new session with a consistent device
        
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
        logger.info(f"🔒 Session device locked: {device_name}")
        
        return self._session_config
    
    def get_session_config(self) -> Optional[Dict[str, Any]]:
        """Get the current session's device config"""
        if self._session_config is None:
            logger.warning("⚠️ No session started! Call start_new_session() first")
            return self.start_new_session()
        
        return self._session_config
    
    def end_session(self):
        """End the current session"""
        if self._session_config:
            device_name = self._session_config.get('device_name', 'Unknown')
            logger.info(f"🔓 Session ended for: {device_name}")
        
        self._session_device = None
        self._session_config = None
        self._session_device_type = None
        self._session_fingerprint = None
    
    def generate_enhanced_fingerprint(
        self,
        device_type: str = "iphone_x",
        use_browserforge: bool = True,
        proxy_ip: Optional[str] = None,
        timezone: Optional[str] = None,
        mock_webrtc: bool = True
    ) -> Dict[str, Any]:
        """
        Generate enhanced fingerprint with pre-resolved timezone
        
        Args:
            device_type: Device type
            use_browserforge: Whether to use BrowserForge enhancement
            proxy_ip: Proxy IP address for WebRTC configuration
            timezone: Pre-resolved timezone (from IPResolver)
            mock_webrtc: Whether to mock WebRTC
        
        Returns:
            Enhanced mobile config dictionary with correct timezone
        """
        # Get session config (consistent device)
        if self._session_config is None:
            logger.warning("⚠️ No session active, starting new session")
            base_config = self.start_new_session(device_type)
        else:
            base_config = self._session_config.copy()
            logger.debug(f"🔒 Using session device: {base_config.get('device_name')}")
        
        # Override timezone with pre-resolved value
        if timezone:
            base_config['timezone'] = timezone
            logger.debug(f"🕐 Using pre-resolved timezone: {timezone}")
        
        # Enhance with BrowserForge if available
        if use_browserforge and BROWSERFORGE_AVAILABLE and self.fp_generator:
            try:
                enhanced_config = self._apply_browserforge_enhancement(
                    base_config, 
                    self._session_device_type or device_type,
                    proxy_ip=proxy_ip,
                    timezone=timezone,
                    mock_webrtc=mock_webrtc
                )
                logger.debug(f"🎭 BrowserForge applied: {base_config.get('device_name')}")
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
        device_type: str,
        proxy_ip: Optional[str] = None,
        timezone: Optional[str] = None,
        mock_webrtc: bool = True
    ) -> Dict[str, Any]:
        """
        Apply BrowserForge fingerprint with pre-resolved timezone
        
        Args:
            base_config: Base configuration from CSV profiles
            device_type: Device type
            proxy_ip: Proxy IP for WebRTC masking
            timezone: Pre-resolved timezone
            mock_webrtc: Whether to use WebRTC mocking
        """
        
        # Determine browser and OS constraints
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
        
        # Generate BrowserForge fingerprint
        fingerprint = self.fp_generator.generate(
            screen=screen,
            strict=False,
            browser=browsers,
            os=operating_systems,
            device='mobile',
            mock_webrtc=mock_webrtc
        )
        
        # Store fingerprint for session
        self._session_fingerprint = fingerprint
        
        # Merge BrowserForge enhancements with base config
        enhanced_config = base_config.copy()
        
        # Update with BrowserForge values
        enhanced_config.update({
            # BrowserForge user agent
            'user_agent': fingerprint.navigator.userAgent,
            
            # Navigator properties
            'platform': fingerprint.navigator.platform,
            'hardware_concurrency': fingerprint.navigator.hardwareConcurrency,
            'device_memory': fingerprint.navigator.deviceMemory,
            'max_touch_points': fingerprint.navigator.maxTouchPoints,
            
            # Language preferences
            'language': fingerprint.navigator.language,
            'languages': fingerprint.navigator.languages,
            
            # WebGL fingerprinting
            'webgl_vendor': fingerprint.videoCard.vendor if fingerprint.videoCard else base_config.get('webgl_vendor'),
            'webgl_renderer': fingerprint.videoCard.renderer if fingerprint.videoCard else base_config.get('webgl_renderer'),
            
            # Screen properties
            'screen_width': fingerprint.screen.width,
            'screen_height': fingerprint.screen.height,
            
            # Keep viewport from CSV
            'viewport': base_config['viewport'],
            
            # Keep device-specific values
            'device_name': base_config.get('device_name'),
            'os_version': base_config.get('os_version'),
            'canvas_seed': base_config.get('canvas_seed'),
            'audio_seed': base_config.get('audio_seed'),
            'battery_level': base_config.get('battery_level'),
            'battery_charging': base_config.get('battery_charging'),
            
            # Use pre-resolved timezone (overrides CSV value)
            'timezone': timezone if timezone else base_config.get('timezone', 'America/New_York'),
            
            # BrowserForge metadata
            '_browserforge_enhanced': True,
            '_browserforge_webrtc_mock': mock_webrtc,
            '_browserforge_fingerprint': fingerprint,
            '_browserforge_webrtc_enabled': mock_webrtc,
            '_session_consistent': True,
            '_proxy_ip': proxy_ip
        })
        
        return enhanced_config
    
    def get_browserforge_injection_script(
        self, 
        enhanced_config: Dict[str, Any]
    ) -> str:
        """
        Get BrowserForge's injection script
        
        Args:
            enhanced_config: Enhanced config with fingerprint
        
        Returns:
            JavaScript injection script
        """
        fingerprint = enhanced_config.get('_browserforge_fingerprint')
        if not fingerprint:
            return ""
        
        try:
            return self._build_injection_script(fingerprint, enhanced_config)
        except Exception as e:
            logger.error(f"Failed to get injection script: {e}")
            return ""
    
    def get_browserforge_webrtc_script(self, enhanced_config: Dict[str, Any]) -> str:
        """
        Get ONLY the WebRTC masking script from BrowserForge
        
        Args:
            enhanced_config: Enhanced config with proxy IP
        
        Returns:
            JavaScript WebRTC masking script
        """
        proxy_ip = enhanced_config.get('_proxy_ip', '')
        mock_webrtc = enhanced_config.get('_browserforge_webrtc_mock', False)
        
        if not mock_webrtc or not proxy_ip:
            return ""
        
        return self._build_webrtc_script(proxy_ip)
    
    def _build_webrtc_script(self, proxy_ip: str) -> str:
        """
        🔥 FIXED: Build comprehensive WebRTC protection with STUN blocking
        
        This version:
        - Blocks ALL STUN/TURN servers
        - Filters SDP candidates
        - Prevents host candidate leaks
        - Prevents srflx (reflexive) candidate leaks
        - Blocks mDNS .local leaks
        """
        return f"""
// ============================================================================
// ADVANCED WEBRTC LEAK PROTECTION v2.0 - PRODUCTION READY
// Blocks: Host candidates, STUN reflexive, TURN relay, mDNS
// ============================================================================
(function() {{
    'use strict';
    
    const PROXY_IP = '{proxy_ip}';
    const DEBUG = false;
    
    if (DEBUG) console.log('[WebRTC Shield] Initializing comprehensive protection for IP:', PROXY_IP);
    
    // ========================================================================
    // STEP 1: Block STUN/TURN servers (prevents srflx/relay candidates)
    // ========================================================================
    const OriginalRTCPeerConnection = window.RTCPeerConnection || 
                                     window.webkitRTCPeerConnection || 
                                     window.mozRTCPeerConnection;
    
    if (!OriginalRTCPeerConnection) {{
        if (DEBUG) console.log('[WebRTC Shield] No RTCPeerConnection available');
        return;
    }}
    
    // ========================================================================
    // STEP 2: RTCPeerConnection Constructor Override
    // ========================================================================
    function ProtectedRTCPeerConnection(config) {{
        // Strip STUN/TURN servers from config
        if (config && config.iceServers) {{
            if (DEBUG) console.log('[WebRTC Shield] Original ICE servers:', config.iceServers.length);
            
            // Remove all STUN/TURN servers
            config.iceServers = [];
            
            if (DEBUG) console.log('[WebRTC Shield] ✅ STUN/TURN servers blocked');
        }} else {{
            // Ensure no default STUN servers
            config = config || {{}};
            config.iceServers = [];
        }}
        
        // Force specific ICE policies to prevent leaks
        config.iceTransportPolicy = 'relay'; // Only use relay (but we provide none)
        config.bundlePolicy = 'max-bundle';
        config.rtcpMuxPolicy = 'require';
        
        const pc = new OriginalRTCPeerConnection(config);
        
        // ====================================================================
        // STEP 3: Hook createOffer to filter SDP
        // ====================================================================
        const originalCreateOffer = pc.createOffer.bind(pc);
        pc.createOffer = function(options) {{
            return originalCreateOffer(options).then(offer => {{
                if (offer && offer.sdp) {{
                    offer.sdp = filterSDP(offer.sdp);
                }}
                return offer;
            }});
        }};
        
        // ====================================================================
        // STEP 4: Hook createAnswer to filter SDP
        // ====================================================================
        const originalCreateAnswer = pc.createAnswer.bind(pc);
        pc.createAnswer = function(options) {{
            return originalCreateAnswer(options).then(answer => {{
                if (answer && answer.sdp) {{
                    answer.sdp = filterSDP(answer.sdp);
                }}
                return answer;
            }});
        }};
        
        // ====================================================================
        // STEP 5: Hook setLocalDescription to filter SDP
        // ====================================================================
        const originalSetLocalDescription = pc.setLocalDescription.bind(pc);
        pc.setLocalDescription = function(description) {{
            if (description && description.sdp) {{
                description.sdp = filterSDP(description.sdp);
            }}
            return originalSetLocalDescription(description);
        }};
        
        // ====================================================================
        // STEP 6: Hook setRemoteDescription to filter incoming SDP
        // ====================================================================
        const originalSetRemoteDescription = pc.setRemoteDescription.bind(pc);
        pc.setRemoteDescription = function(description) {{
            if (description && description.sdp) {{
                description.sdp = filterSDP(description.sdp);
            }}
            return originalSetRemoteDescription(description);
        }};
        
        // ====================================================================
        // STEP 7: Hook onicecandidate (last line of defense)
        // ====================================================================
        Object.defineProperty(pc, 'onicecandidate', {{
            get: function() {{
                return this._onicecandidate;
            }},
            set: function(handler) {{
                this._onicecandidate = function(event) {{
                    if (event.candidate && event.candidate.candidate) {{
                        const original = event.candidate.candidate;
                        
                        // Block ALL candidates except proxy IP
                        if (!original.includes(PROXY_IP)) {{
                            if (DEBUG) console.log('[WebRTC Shield] ❌ Blocked candidate:', original.substring(0, 80));
                            return; // Drop the candidate completely
                        }}
                        
                        if (DEBUG) console.log('[WebRTC Shield] ✅ Allowed candidate:', original.substring(0, 80));
                    }}
                    
                    if (handler) return handler(event);
                }};
            }}
        }});
        
        // ====================================================================
        // STEP 8: Hook addEventListener for 'icecandidate'
        // ====================================================================
        const originalAddEventListener = pc.addEventListener.bind(pc);
        pc.addEventListener = function(type, listener, options) {{
            if (type === 'icecandidate') {{
                const wrappedListener = function(event) {{
                    if (event.candidate && event.candidate.candidate) {{
                        const original = event.candidate.candidate;
                        
                        // Block non-proxy candidates
                        if (!original.includes(PROXY_IP)) {{
                            if (DEBUG) console.log('[WebRTC Shield] ❌ Blocked (addEventListener):', original.substring(0, 80));
                            return;
                        }}
                    }}
                    return listener(event);
                }};
                return originalAddEventListener('icecandidate', wrappedListener, options);
            }}
            return originalAddEventListener(type, listener, options);
        }};
        
        return pc;
    }}
    
    // ========================================================================
    // STEP 9: SDP Filter Function
    // ========================================================================
    function filterSDP(sdp) {{
        if (!sdp) return sdp;
        
        // Split SDP into lines
        const lines = sdp.split('\\n');
        const filteredLines = [];
        
        for (let line of lines) {{
            // Filter out candidate lines with private/non-proxy IPs
            if (line.startsWith('a=candidate:')) {{
                // Check if line contains any IP
                const ipMatch = line.match(/\\b(\\d{{1,3}}\\.\\d{{1,3}}\\.\\d{{1,3}}\\.\\d{{1,3}}|[0-9a-f:]+)\\b/gi);
                
                if (ipMatch) {{
                    let shouldBlock = false;
                    
                    for (let ip of ipMatch) {{
                        // Block private IPs
                        if (isPrivateIP(ip)) {{
                            shouldBlock = true;
                            break;
                        }}
                        
                        // Block non-proxy IPs
                        if (ip !== PROXY_IP) {{
                            shouldBlock = true;
                            break;
                        }}
                    }}
                    
                    if (shouldBlock) {{
                        if (DEBUG) console.log('[WebRTC Shield] Filtered SDP candidate:', line.substring(0, 80));
                        continue; // Skip this line
                    }}
                }}
            }}
            
            // Filter out c= (connection) lines with private IPs
            if (line.startsWith('c=')) {{
                const ipMatch = line.match(/\\b(\\d{{1,3}}\\.\\d{{1,3}}\\.\\d{{1,3}}\\.\\d{{1,3}}|[0-9a-f:]+)\\b/i);
                if (ipMatch && isPrivateIP(ipMatch[0])) {{
                    // Replace with proxy IP
                    line = line.replace(ipMatch[0], PROXY_IP);
                    if (DEBUG) console.log('[WebRTC Shield] Replaced c= line with proxy IP');
                }}
            }}
            
            filteredLines.push(line);
        }}
        
        return filteredLines.join('\\n');
    }}
    
    // ========================================================================
    // STEP 10: Private IP Detection (includes mDNS)
    // ========================================================================
    function isPrivateIP(ip) {{
        if (!ip) return false;
        
        // IPv4 private ranges
        if (ip.match(/^10\\./)) return true;
        if (ip.match(/^192\\.168\\./)) return true;
        if (ip.match(/^172\\.(1[6-9]|2[0-9]|3[0-1])\\./)) return true;
        if (ip.match(/^127\\./)) return true;
        if (ip.match(/^169\\.254\\./)) return true;
        if (ip === '0.0.0.0') return true;
        
        // IPv6 private ranges
        if (ip.match(/^fe80:/i)) return true;
        if (ip.match(/^fc00:/i)) return true;
        if (ip.match(/^fd00:/i)) return true;
        if (ip === '::1') return true;
        
        // mDNS .local addresses (CRITICAL FIX)
        if (ip.includes('.local')) return true;
        
        // UUID-like patterns (mDNS candidates)
        if (ip.match(/^[0-9a-f]{{8}}-[0-9a-f]{{4}}-/i)) return true;
        
        return false;
    }}
    
    // ========================================================================
    // STEP 11: Replace global RTCPeerConnection
    // ========================================================================
    window.RTCPeerConnection = ProtectedRTCPeerConnection;
    window.RTCPeerConnection.prototype = OriginalRTCPeerConnection.prototype;
    Object.setPrototypeOf(window.RTCPeerConnection, OriginalRTCPeerConnection);
    
    if (window.webkitRTCPeerConnection) {{
        window.webkitRTCPeerConnection = window.RTCPeerConnection;
    }}
    if (window.mozRTCPeerConnection) {{
        window.mozRTCPeerConnection = window.RTCPeerConnection;
    }}
    
    // ========================================================================
    // STEP 12: Block getUserMedia IP leaks
    // ========================================================================
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {{
        const originalGetUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
        navigator.mediaDevices.getUserMedia = function(constraints) {{
            if (DEBUG) console.log('[WebRTC Shield] getUserMedia called');
            // Allow but log (media won't leak IP if RTCPeerConnection is protected)
            return originalGetUserMedia(constraints);
        }};
    }}
    
    // ========================================================================
    // STEP 13: Block enumerateDevices (fingerprinting protection)
    // ========================================================================
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {{
        const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices.bind(navigator.mediaDevices);
        navigator.mediaDevices.enumerateDevices = function() {{
            return originalEnumerateDevices().then(devices => {{
                // Return minimal device info to prevent fingerprinting
                return devices.map(device => ({{
                    deviceId: 'default',
                    groupId: 'default',
                    kind: device.kind,
                    label: ''
                }}));
            }});
        }};
    }}
    
    if (DEBUG) console.log('[WebRTC Shield] ✅ Complete protection active for', PROXY_IP);
}})();
"""
    
    def _build_injection_script(self, fingerprint, enhanced_config: Dict[str, Any]) -> str:
        """Build JavaScript injection script from BrowserForge fingerprint"""
        proxy_ip = enhanced_config.get('_proxy_ip', '')
        mock_webrtc = enhanced_config.get('_browserforge_webrtc_mock', False)
        
        webgl_script = ""
        if fingerprint.videoCard:
            webgl_vendor = fingerprint.videoCard.vendor if fingerprint.videoCard.vendor else "Apple Inc."
            webgl_renderer = fingerprint.videoCard.renderer if fingerprint.videoCard.renderer else "Apple GPU"
            webgl_script = f"""
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{webgl_vendor}';
                if (parameter === 37446) return '{webgl_renderer}';
                return getParameter.call(this, parameter);
            }};
            
            if (typeof WebGL2RenderingContext !== 'undefined') {{
                const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
                WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                    if (parameter === 37445) return '{webgl_vendor}';
                    if (parameter === 37446) return '{webgl_renderer}';
                    return getParameter2.call(this, parameter);
                }};
            }}
            """
        
        webrtc_script = ""
        if mock_webrtc and proxy_ip:
            webrtc_script = self._build_webrtc_script(proxy_ip)
        
        script = f"""
(function() {{
    'use strict';
    console.log('[BrowserForge] Injecting fingerprint');
    
    Object.defineProperty(navigator, 'userAgent', {{
        get: () => '{fingerprint.navigator.userAgent}',
        configurable: true
    }});
    
    Object.defineProperty(navigator, 'platform', {{
        get: () => '{fingerprint.navigator.platform}',
        configurable: true
    }});
    
    Object.defineProperty(navigator, 'hardwareConcurrency', {{
        get: () => {fingerprint.navigator.hardwareConcurrency},
        configurable: true
    }});
    
    Object.defineProperty(navigator, 'deviceMemory', {{
        get: () => {fingerprint.navigator.deviceMemory if fingerprint.navigator.deviceMemory else 4},
        configurable: true
    }});
    
    Object.defineProperty(navigator, 'maxTouchPoints', {{
        get: () => {fingerprint.navigator.maxTouchPoints if fingerprint.navigator.maxTouchPoints else 5},
        configurable: true
    }});
    
    Object.defineProperty(navigator, 'language', {{
        get: () => '{fingerprint.navigator.language}',
        configurable: true
    }});
    
    Object.defineProperty(navigator, 'languages', {{
        get: () => {fingerprint.navigator.languages},
        configurable: true
    }});
    
    {webgl_script}
    
    Object.defineProperty(screen, 'width', {{
        get: () => {fingerprint.screen.width},
        configurable: true
    }});
    
    Object.defineProperty(screen, 'height', {{
        get: () => {fingerprint.screen.height},
        configurable: true  
    }});
    
    Object.defineProperty(screen, 'availWidth', {{
        get: () => {fingerprint.screen.availWidth},
        configurable: true
    }});
    
    Object.defineProperty(screen, 'availHeight', {{
        get: () => {fingerprint.screen.availHeight},
        configurable: true
    }});
    
    console.log('[BrowserForge] Fingerprint injection complete');
}})();

{webrtc_script}
        """
        
        return script
    
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
            "session_active": self._session_config is not None,
            "webrtc_protection": self.is_browserforge_available()
        }
        
        if self._session_config:
            stats["session_device"] = self._session_config.get('device_name', 'Unknown')
        
        return stats
