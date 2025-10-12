"""
BrowserForge Integration Manager - BALANCED WebRTC Protection

BALANCED FIX: Allows WebRTC but injects proxy IP instead of blocking completely
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
    Enhanced fingerprint manager with BALANCED WebRTC protection
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
        """Start a new session with a consistent device"""
        if "samsung" in device_type.lower() or "android" in device_type.lower():
            csv_profile = self.profile_loader.get_random_android_profile()
        else:
            csv_profile = self.profile_loader.get_random_iphone_profile()
        
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
        """Generate enhanced fingerprint with pre-resolved timezone"""
        if self._session_config is None:
            logger.warning("⚠️ No session active, starting new session")
            base_config = self.start_new_session(device_type)
        else:
            base_config = self._session_config.copy()
            logger.debug(f"🔒 Using session device: {base_config.get('device_name')}")
        
        if timezone:
            base_config['timezone'] = timezone
            logger.debug(f"🕐 Using pre-resolved timezone: {timezone}")
        
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
        """Apply BrowserForge fingerprint with pre-resolved timezone"""
        
        if "android" in device_type.lower() or "samsung" in device_type.lower():
            browsers = ['chrome']
            operating_systems = ['android']
        else:
            browsers = ['safari']
            operating_systems = ['ios']
        
        viewport_width = base_config['viewport']['width']
        viewport_height = base_config['viewport']['height']
        
        screen = Screen(
            min_width=viewport_width - 10,
            max_width=viewport_width + 10,
            min_height=viewport_height - 10,
            max_height=viewport_height + 10
        )
        
        fingerprint = self.fp_generator.generate(
            screen=screen,
            strict=False,
            browser=browsers,
            os=operating_systems,
            device='mobile',
            mock_webrtc=mock_webrtc
        )
        
        self._session_fingerprint = fingerprint
        
        enhanced_config = base_config.copy()
        
        enhanced_config.update({
            'user_agent': fingerprint.navigator.userAgent,
            'platform': fingerprint.navigator.platform,
            'hardware_concurrency': fingerprint.navigator.hardwareConcurrency,
            'device_memory': fingerprint.navigator.deviceMemory,
            'max_touch_points': fingerprint.navigator.maxTouchPoints,
            'language': fingerprint.navigator.language,
            'languages': fingerprint.navigator.languages,
            'webgl_vendor': fingerprint.videoCard.vendor if fingerprint.videoCard else base_config.get('webgl_vendor'),
            'webgl_renderer': fingerprint.videoCard.renderer if fingerprint.videoCard else base_config.get('webgl_renderer'),
            'screen_width': fingerprint.screen.width,
            'screen_height': fingerprint.screen.height,
            'viewport': base_config['viewport'],
            'device_name': base_config.get('device_name'),
            'os_version': base_config.get('os_version'),
            'canvas_seed': base_config.get('canvas_seed'),
            'audio_seed': base_config.get('audio_seed'),
            'battery_level': base_config.get('battery_level'),
            'battery_charging': base_config.get('battery_charging'),
            'timezone': timezone if timezone else base_config.get('timezone', 'America/New_York'),
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
        """Get BrowserForge's injection script"""
        fingerprint = enhanced_config.get('_browserforge_fingerprint')
        if not fingerprint:
            return ""
        
        try:
            return self._build_injection_script(fingerprint, enhanced_config)
        except Exception as e:
            logger.error(f"Failed to get injection script: {e}")
            return ""
    
    def get_browserforge_webrtc_script(self, enhanced_config: Dict[str, Any]) -> str:
        """Get BALANCED WebRTC script"""
        proxy_ip = enhanced_config.get('_proxy_ip', '')
        mock_webrtc = enhanced_config.get('_browserforge_webrtc_mock', False)
        
        if not mock_webrtc or not proxy_ip:
            return ""
        
        return self._build_webrtc_script_balanced(proxy_ip)
    
    def _build_webrtc_script_balanced(self, proxy_ip: str) -> str:
        """
        🔥 BALANCED FIX: Allows WebRTC but injects proxy IP
        
        This version:
        - Allows WebRTC to function (fingerprint tests complete)
        - Injects fake candidates with proxy IP
        - Blocks real private IP leaks
        - Works with detection sites
        """
        return f"""
// ============================================================================
// BALANCED WEBRTC PROTECTION v3.0 - Proxy IP Injection
// Strategy: Allow WebRTC but inject fake candidates with proxy IP
// ============================================================================
(function() {{
    'use strict';
    
    const PROXY_IP = '{proxy_ip}';
    const DEBUG = true;
    
    if (DEBUG) console.log('[WebRTC Balanced] Initializing proxy IP injection for:', PROXY_IP);
    
    const OriginalRTCPeerConnection = window.RTCPeerConnection || 
                                     window.webkitRTCPeerConnection || 
                                     window.mozRTCPeerConnection;
    
    if (!OriginalRTCPeerConnection) {{
        if (DEBUG) console.log('[WebRTC Balanced] No RTCPeerConnection available');
        return;
    }}
    
    // ========================================================================
    // STEP 1: RTCPeerConnection Constructor with Controlled STUN
    // ========================================================================
    function BalancedRTCPeerConnection(config) {{
        // Keep config but we'll filter candidates later
        const pc = new OriginalRTCPeerConnection(config || {{}});
        
        // Track if we've injected proxy candidate
        pc._proxyInjected = false;
        
        // ====================================================================
        // STEP 2: Inject Fake Proxy IP Candidate
        // ====================================================================
        function injectProxyCandidate() {{
            if (pc._proxyInjected) return;
            pc._proxyInjected = true;
            
            // Create fake ICE candidate with proxy IP
            const fakeCandidate = {{
                candidate: `candidate:1 1 udp 2113937151 ${{PROXY_IP}} 54321 typ host generation 0`,
                sdpMLineIndex: 0,
                sdpMid: '0'
            }};
            
            // Trigger the fake candidate event
            if (pc._onicecandidate) {{
                const event = {{ candidate: fakeCandidate }};
                setTimeout(() => pc._onicecandidate(event), 100);
                if (DEBUG) console.log('[WebRTC Balanced] ✅ Injected proxy candidate:', PROXY_IP);
            }}
        }}
        
        // ====================================================================
        // STEP 3: Hook onicecandidate (Filter real, inject fake)
        // ====================================================================
        Object.defineProperty(pc, 'onicecandidate', {{
            get: function() {{
                return this._onicecandidate;
            }},
            set: function(handler) {{
                this._onicecandidate = function(event) {{
                    if (event.candidate && event.candidate.candidate) {{
                        const original = event.candidate.candidate;
                        
                        // Check if it's a private/local IP
                        const ipMatch = original.match(/\\b(\\d{{1,3}}\\.\\d{{1,3}}\\.\\d{{1,3}}\\.\\d{{1,3}})\\b/);
                        if (ipMatch && isPrivateIP(ipMatch[0])) {{
                            if (DEBUG) console.log('[WebRTC Balanced] ❌ Blocked private candidate');
                            injectProxyCandidate();  // Inject proxy instead
                            return;
                        }}
                        
                        // Check for .local mDNS
                        if (original.includes('.local')) {{
                            if (DEBUG) console.log('[WebRTC Balanced] ❌ Blocked mDNS candidate');
                            injectProxyCandidate();  // Inject proxy instead
                            return;
                        }}
                        
                        // Allow proxy IP through
                        if (original.includes(PROXY_IP)) {{
                            if (DEBUG) console.log('[WebRTC Balanced] ✅ Allowed proxy candidate');
                            if (handler) return handler(event);
                            return;
                        }}
                        
                        // Block everything else but inject proxy
                        if (DEBUG) console.log('[WebRTC Balanced] ❌ Blocked non-proxy candidate');
                        injectProxyCandidate();
                        return;
                    }}
                    
                    // Handle null candidate (gathering complete)
                    if (!event.candidate && !this._proxyInjected) {{
                        injectProxyCandidate();
                    }}
                    
                    if (handler) return handler(event);
                }};
            }}
        }});
        
        // ====================================================================
        // STEP 4: Hook addEventListener for 'icecandidate'
        // ====================================================================
        const originalAddEventListener = pc.addEventListener.bind(pc);
        pc.addEventListener = function(type, listener, options) {{
            if (type === 'icecandidate') {{
                const wrappedListener = function(event) {{
                    if (event.candidate && event.candidate.candidate) {{
                        const original = event.candidate.candidate;
                        
                        const ipMatch = original.match(/\\b(\\d{{1,3}}\\.\\d{{1,3}}\\.\\d{{1,3}}\\.\\d{{1,3}})\\b/);
                        if (ipMatch && isPrivateIP(ipMatch[0])) {{
                            injectProxyCandidate();
                            return;
                        }}
                        
                        if (original.includes('.local')) {{
                            injectProxyCandidate();
                            return;
                        }}
                        
                        if (!original.includes(PROXY_IP)) {{
                            injectProxyCandidate();
                            return;
                        }}
                    }}
                    
                    if (!event.candidate && !pc._proxyInjected) {{
                        injectProxyCandidate();
                    }}
                    
                    return listener(event);
                }};
                return originalAddEventListener('icecandidate', wrappedListener, options);
            }}
            return originalAddEventListener(type, listener, options);
        }};
        
        // ====================================================================
        // STEP 5: Hook createOffer/Answer (inject candidate early)
        // ====================================================================
        const originalCreateOffer = pc.createOffer.bind(pc);
        pc.createOffer = function(options) {{
            return originalCreateOffer(options).then(offer => {{
                injectProxyCandidate();  // Inject early
                return offer;
            }});
        }};
        
        const originalCreateAnswer = pc.createAnswer.bind(pc);
        pc.createAnswer = function(options) {{
            return originalCreateAnswer(options).then(answer => {{
                injectProxyCandidate();  // Inject early
                return answer;
            }});
        }};
        
        return pc;
    }}
    
    // ========================================================================
    // STEP 6: Private IP Detection
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
        
        return false;
    }}
    
    // ========================================================================
    // STEP 7: Replace global RTCPeerConnection
    // ========================================================================
    window.RTCPeerConnection = BalancedRTCPeerConnection;
    window.RTCPeerConnection.prototype = OriginalRTCPeerConnection.prototype;
    Object.setPrototypeOf(window.RTCPeerConnection, OriginalRTCPeerConnection);
    
    if (window.webkitRTCPeerConnection) {{
        window.webkitRTCPeerConnection = window.RTCPeerConnection;
    }}
    if (window.mozRTCPeerConnection) {{
        window.mozRTCPeerConnection = window.RTCPeerConnection;
    }}
    
    if (DEBUG) console.log('[WebRTC Balanced] ✅ Protection active - proxy IP injection enabled');
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
            webrtc_script = self._build_webrtc_script_balanced(proxy_ip)
        
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
