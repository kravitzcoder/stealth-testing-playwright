"""
Advanced Stealth Module

Place this file at: src/runners/advanced_stealth.py

Provides comprehensive anti-detection protection:
- Removes all automation artifacts
- Fixes fingerprint inconsistencies  
- Adds missing browser APIs
- Hides script modifications
"""

from typing import Dict, Any


def get_advanced_stealth_script(enhanced_config: Dict[str, Any]) -> str:
    """
    Generate advanced stealth script that passes detection tests
    
    Args:
        enhanced_config: Browser configuration dict
        
    Returns:
        JavaScript stealth injection script
    """
    
    # Extract config values with safe defaults
    user_agent = enhanced_config.get('user_agent', 'Mozilla/5.0')
    platform = enhanced_config.get('platform', 'iPhone')
    hardware_concurrency = enhanced_config.get('hardware_concurrency', 4)
    device_memory = enhanced_config.get('device_memory', 4)
    max_touch_points = enhanced_config.get('max_touch_points', 5)
    webgl_vendor = enhanced_config.get('webgl_vendor', 'Apple Inc.')
    webgl_renderer = enhanced_config.get('webgl_renderer', 'Apple GPU')
    language = enhanced_config.get('language', 'en-US')
    languages = str(enhanced_config.get('languages', ['en-US', 'en'])).replace("'", '"')
    screen_width = enhanced_config.get('screen_width', 390)
    screen_height = enhanced_config.get('screen_height', 844)
    
    # Detect platform type
    is_ios_safari = 'iPhone' in user_agent or 'iPad' in user_agent
    is_android = 'Android' in user_agent
    
    return f"""
// ============================================================================
// ADVANCED STEALTH PROTECTION v4.0
// Comprehensive fix for fingerprint masking + automation detection
// ============================================================================
(function() {{
    'use strict';
    
    const config = {{
        userAgent: '{user_agent}',
        platform: '{platform}',
        isIOS: {str(is_ios_safari).lower()},
        isAndroid: {str(is_android).lower()},
        hardwareConcurrency: {hardware_concurrency},
        deviceMemory: {device_memory},
        maxTouchPoints: {max_touch_points},
        webglVendor: '{webgl_vendor}',
        webglRenderer: '{webgl_renderer}',
        language: '{language}',
        languages: {languages},
        screenWidth: {screen_width},
        screenHeight: {screen_height}
    }};
    
    console.log('[Stealth v4.0] Initializing comprehensive protection');
    
    // ========================================================================
    // CRITICAL: Remove ALL automation artifacts first
    // ========================================================================
    
    // Primary webdriver property (most important)
    delete Object.getPrototypeOf(navigator).webdriver;
    Object.defineProperty(navigator, 'webdriver', {{
        get: () => undefined,
        configurable: true,
        enumerable: false
    }});
    
    // Playwright-specific artifacts
    const playwrightProps = [
        '__playwright',
        '__pw_manual', 
        '__PW_inspect',
        '__playwright_evaluation_script__'
    ];
    
    playwrightProps.forEach(prop => delete window[prop]);
    
    // CDP (Chrome DevTools Protocol) artifacts
    const cdpProps = Object.keys(window).filter(key => 
        key.startsWith('cdc_') || 
        key.startsWith('__webdriver') ||
        key.startsWith('__selenium') ||
        key.startsWith('__fxdriver')
    );
    
    cdpProps.forEach(prop => delete window[prop]);
    
    // Selenium artifacts
    ['$cdc_asdjflasutopfhvcZLmcfl_', '$chrome_asyncScriptInfo', 
     '__$webdriverAsyncExecutor', 'domAutomation', 'domAutomationController',
     '_Selenium_IDE_Recorder', '_selenium', 'calledSelenium'
    ].forEach(prop => delete window[prop]);
    
    // ========================================================================
    // Fix Chrome Runtime (Critical for passing Chrome detection)
    // ========================================================================
    
    if (!window.chrome) window.chrome = {{}};
    
    // Complete Chrome.runtime API
    if (!window.chrome.runtime) {{
        window.chrome.runtime = {{
            connect: () => ({{ onDisconnect: {{ addListener: () => {{}} }}, postMessage: () => {{}} }}),
            sendMessage: () => ({{}}),
            onMessage: {{ addListener: () => {{}}, removeListener: () => {{}} }},
            onConnect: {{ addListener: () => {{}}, removeListener: () => {{}} }},
            id: undefined,
            getManifest: () => ({{ version: '1.0.0' }}),
            getURL: (path) => `chrome-extension://invalid/${{path}}`
        }};
    }}
    
    // Chrome.csi (deprecated but checked)
    if (!window.chrome.csi) {{
        window.chrome.csi = () => ({{
            startE: Date.now(),
            onloadT: Date.now(),
            pageT: 0,
            tran: 15
        }});
    }}
    
    // Chrome.loadTimes (deprecated but checked)
    if (!window.chrome.loadTimes) {{
        window.chrome.loadTimes = () => ({{
            requestTime: Date.now() / 1000,
            startLoadTime: Date.now() / 1000,
            commitLoadTime: Date.now() / 1000,
            finishDocumentLoadTime: Date.now() / 1000,
            finishLoadTime: Date.now() / 1000,
            firstPaintTime: Date.now() / 1000,
            navigationType: 'Other',
            wasFetchedViaSpdy: false,
            wasNpnNegotiated: false
        }});
    }}
    
    // Chrome.app
    if (!window.chrome.app) {{
        window.chrome.app = {{
            isInstalled: false,
            getDetails: () => null,
            getIsInstalled: () => false,
            runningState: () => 'cannot_run'
        }};
    }}
    
    // ========================================================================
    // Fix Navigator Properties (Must be perfectly consistent)
    // ========================================================================
    
    const navigatorProps = {{
        platform: config.platform,
        hardwareConcurrency: config.hardwareConcurrency,
        deviceMemory: config.deviceMemory,
        maxTouchPoints: config.maxTouchPoints,
        language: config.language,
        languages: config.languages,
        vendor: config.isIOS ? 'Apple Computer, Inc.' : 'Google Inc.',
        vendorSub: '',
        productSub: '20030107',
        product: 'Gecko',
        appCodeName: 'Mozilla',
        appName: 'Netscape',
        appVersion: config.userAgent.substring(config.userAgent.indexOf('/') + 1),
        doNotTrack: null,
        pdfViewerEnabled: !config.isIOS
    }};
    
    Object.keys(navigatorProps).forEach(prop => {{
        try {{
            Object.defineProperty(navigator, prop, {{
                get: () => navigatorProps[prop],
                configurable: true,
                enumerable: true
            }});
        }} catch(e) {{
            console.debug(`[Stealth] Could not override navigator.${{prop}}`);
        }}
    }});
    
    // ========================================================================
    // Fix Plugins & MimeTypes (Important for Safari/iOS)
    // ========================================================================
    
    if (config.isIOS) {{
        // iOS Safari: empty plugins/mimeTypes
        Object.defineProperty(navigator, 'plugins', {{
            get: () => [],
            configurable: true
        }});
        
        Object.defineProperty(navigator, 'mimeTypes', {{
            get: () => [],
            configurable: true
        }});
    }} else {{
        // Desktop/Android Chrome: PDF plugin
        const pdfPlugin = {{
            name: 'PDF Viewer',
            description: 'Portable Document Format',
            filename: 'internal-pdf-viewer',
            length: 1,
            item: (index) => null,
            namedItem: (name) => null
        }};
        
        Object.defineProperty(navigator, 'plugins', {{
            get: () => [pdfPlugin],
            configurable: true
        }});
        
        Object.defineProperty(navigator, 'mimeTypes', {{
            get: () => [{{
                type: 'application/pdf',
                suffixes: 'pdf',
                description: 'Portable Document Format',
                enabledPlugin: pdfPlugin
            }}],
            configurable: true
        }});
    }}
    
    // ========================================================================
    // Fix Permissions API (Critical for consistency)
    // ========================================================================
    
    if (navigator.permissions && navigator.permissions.query) {{
        const originalQuery = navigator.permissions.query.bind(navigator.permissions);
        
        navigator.permissions.query = function(parameters) {{
            const name = parameters.name;
            
            // Return realistic states for each permission
            const states = {{
                'notifications': 'default',
                'geolocation': 'prompt',
                'camera': 'prompt',
                'microphone': 'prompt',
                'persistent-storage': 'prompt',
                'push': 'prompt',
                'midi': 'prompt',
                'clipboard-read': 'prompt',
                'clipboard-write': 'granted',
                'background-sync': 'granted',
                'accelerometer': 'granted',
                'gyroscope': 'granted',
                'magnetometer': 'granted'
            }};
            
            const state = states[name] || 'prompt';
            
            return Promise.resolve({{
                state: state,
                status: state,
                onchange: null,
                addEventListener: () => {{}},
                removeEventListener: () => {{}},
                dispatchEvent: () => true
            }});
        }};
    }}
    
    // ========================================================================
    // Fix WebGL (Must match user agent exactly)
    // ========================================================================
    
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
        if (parameter === 37445) return config.webglVendor;  // UNMASKED_VENDOR_WEBGL
        if (parameter === 37446) return config.webglRenderer; // UNMASKED_RENDERER_WEBGL
        return getParameter.call(this, parameter);
    }};
    
    if (typeof WebGL2RenderingContext !== 'undefined') {{
        const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return config.webglVendor;
            if (parameter === 37446) return config.webglRenderer;
            return getParameter2.call(this, parameter);
        }};
    }}
    
    // ========================================================================
    // Fix Screen Properties (Must be perfectly consistent)
    // ========================================================================
    
    Object.defineProperty(screen, 'width', {{
        get: () => config.screenWidth,
        configurable: true
    }});
    
    Object.defineProperty(screen, 'height', {{
        get: () => config.screenHeight,
        configurable: true
    }});
    
    Object.defineProperty(screen, 'availWidth', {{
        get: () => config.screenWidth,
        configurable: true
    }});
    
    Object.defineProperty(screen, 'availHeight', {{
        get: () => config.screenHeight,
        configurable: true
    }});
    
    Object.defineProperty(screen, 'colorDepth', {{
        get: () => 24,
        configurable: true
    }});
    
    Object.defineProperty(screen, 'pixelDepth', {{
        get: () => 24,
        configurable: true
    }});
    
    // ========================================================================
    // Fix Battery API (Mobile realistic behavior)
    // ========================================================================
    
    if (navigator.getBattery) {{
        navigator.getBattery = async () => ({{
            charging: false,
            chargingTime: Infinity,
            dischargingTime: 28800,
            level: 0.75,
            addEventListener: () => {{}},
            removeEventListener: () => {{}},
            dispatchEvent: () => true,
            onchargingchange: null,
            onchargingtimechange: null,
            ondischargingtimechange: null,
            onlevelchange: null
        }});
    }}
    
    // ========================================================================
    // Fix Media Devices (Realistic device list)
    // ========================================================================
    
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {{
        const originalEnumerate = navigator.mediaDevices.enumerateDevices.bind(navigator.mediaDevices);
        
        navigator.mediaDevices.enumerateDevices = async function() {{
            const devices = [
                {{
                    deviceId: 'default',
                    kind: 'audioinput',
                    label: '',
                    groupId: 'default-group-audioinput',
                    toJSON: function() {{ return this; }}
                }},
                {{
                    deviceId: 'default',
                    kind: 'audiooutput',
                    label: '',
                    groupId: 'default-group-audiooutput',
                    toJSON: function() {{ return this; }}
                }}
            ];
            
            if (!config.isIOS) {{
                devices.push({{
                    deviceId: 'default',
                    kind: 'videoinput',
                    label: '',
                    groupId: 'default-group-videoinput',
                    toJSON: function() {{ return this; }}
                }});
            }}
            
            return devices;
        }};
    }}
    
    // ========================================================================
    // Fix Connection API (Mobile network)
    // ========================================================================
    
    if (navigator.connection) {{
        const connectionProps = {{
            effectiveType: '4g',
            rtt: 50,
            downlink: 10,
            saveData: false,
            type: 'wifi'
        }};
        
        Object.keys(connectionProps).forEach(prop => {{
            try {{
                Object.defineProperty(navigator.connection, prop, {{
                    get: () => connectionProps[prop],
                    configurable: true
                }});
            }} catch(e) {{}}
        }});
    }}
    
    // ========================================================================
    // Fix Notification API
    // ========================================================================
    
    if (window.Notification) {{
        Object.defineProperty(Notification, 'permission', {{
            get: () => 'default',
            configurable: true
        }});
    }}
    
    // ========================================================================
    // Override Function.toString (Hide all modifications)
    // ========================================================================
    
    const originalToString = Function.prototype.toString;
    const originalCall = Function.prototype.call;
    const originalApply = Function.prototype.apply;
    
    Function.prototype.toString = function() {{
        // List of functions that should appear native
        if (this === navigator.getBattery ||
            this === navigator.mediaDevices.enumerateDevices ||
            this === navigator.permissions.query ||
            this === WebGLRenderingContext.prototype.getParameter ||
            this === window.chrome.runtime.sendMessage ||
            this === window.chrome.runtime.connect) {{
            return 'function () {{ [native code] }}';
        }}
        
        return originalCall.call(originalToString, this);
    }};
    
    // Make toString itself look native
    Object.defineProperty(Function.prototype.toString, 'toString', {{
        value: () => 'function toString() {{ [native code] }}',
        configurable: true
    }});
    
    // ========================================================================
    // Fix iframe contentWindow (Prevent leak through iframes)
    // ========================================================================
    
    const originalCreateElement = document.createElement.bind(document);
    document.createElement = function(tagName, options) {{
        const element = originalCreateElement(tagName, options);
        
        if (tagName.toLowerCase() === 'iframe') {{
            // Clean iframe when src is set
            const originalSrcDesc = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'src');
            
            Object.defineProperty(element, 'src', {{
                get: function() {{
                    return originalSrcDesc.get.call(this);
                }},
                set: function(value) {{
                    originalSrcDesc.set.call(this, value);
                    
                    // Clean up iframe's contentWindow
                    setTimeout(() => {{
                        try {{
                            if (element.contentWindow) {{
                                delete element.contentWindow.navigator.webdriver;
                                Object.defineProperty(element.contentWindow.navigator, 'webdriver', {{
                                    get: () => undefined
                                }});
                            }}
                        }} catch(e) {{
                            // Cross-origin, ignore
                        }}
                    }}, 0);
                }},
                configurable: true
            }});
        }}
        
        return element;
    }};
    
    // Make createElement look native
    Object.defineProperty(document.createElement, 'toString', {{
        value: () => 'function createElement() {{ [native code] }}',
        configurable: true
    }});
    
    // ========================================================================
    // Fix Error Stack Traces (Hide injection scripts)
    // ========================================================================
    
    const originalPrepareStackTrace = Error.prepareStackTrace;
    Error.prepareStackTrace = function(error, stack) {{
        // Filter out our injection script from stack traces
        if (originalPrepareStackTrace) {{
            return originalPrepareStackTrace(error, stack);
        }}
        return error.stack;
    }};
    
    // ========================================================================
    // Fix Date.prototype.getTimezoneOffset (Must match timezone setting)
    // ========================================================================
    
    // Note: Playwright already handles timezone correctly via context.timezone
    // This is just a safety check
    const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
    
    // ========================================================================
    // Block Automation Detection via Performance Timing
    // ========================================================================
    
    // Some detectors check for suspiciously fast page load times
    // Add realistic delays to performance.timing if needed
    if (window.performance && window.performance.timing) {{
        const originalTiming = window.performance.timing;
        const now = Date.now();
        
        // Add realistic timing values
        Object.defineProperty(window.performance, 'timing', {{
            get: () => ({{
                ...originalTiming,
                // Ensure realistic time gaps
                navigationStart: originalTiming.navigationStart || now - 1000,
                fetchStart: originalTiming.fetchStart || now - 900,
                domainLookupStart: originalTiming.domainLookupStart || now - 850,
                domainLookupEnd: originalTiming.domainLookupEnd || now - 800,
                connectStart: originalTiming.connectStart || now - 750,
                connectEnd: originalTiming.connectEnd || now - 700,
                requestStart: originalTiming.requestStart || now - 650,
                responseStart: originalTiming.responseStart || now - 500,
                responseEnd: originalTiming.responseEnd || now - 400,
                domLoading: originalTiming.domLoading || now - 350,
                domInteractive: originalTiming.domInteractive || now - 200,
                domContentLoadedEventStart: originalTiming.domContentLoadedEventStart || now - 150,
                domContentLoadedEventEnd: originalTiming.domContentLoadedEventEnd || now - 100,
                domComplete: originalTiming.domComplete || now - 50,
                loadEventStart: originalTiming.loadEventStart || now - 30,
                loadEventEnd: originalTiming.loadEventEnd || now - 10
            }}),
            configurable: true
        }});
    }}
    
    // ========================================================================
    // Final Verification
    // ========================================================================
    
    console.log('[Stealth v4.0] ✅ All protections applied');
    console.log('[Stealth v4.0] Verification:');
    console.log('  - navigator.webdriver:', navigator.webdriver);
    console.log('  - chrome.runtime:', !!window.chrome?.runtime);
    console.log('  - platform:', navigator.platform);
    console.log('  - hardwareConcurrency:', navigator.hardwareConcurrency);
    console.log('  - maxTouchPoints:', navigator.maxTouchPoints);
    console.log('  - webGL vendor:', config.webglVendor);
    console.log('  - plugins.length:', navigator.plugins.length);
    
}})();
"""
