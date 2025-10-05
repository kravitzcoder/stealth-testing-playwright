"""
Enhanced Fingerprint Injector with Comprehensive Device Spoofing
"""

def generate_fingerprint_script(profile: dict) -> str:
    """Generate comprehensive JavaScript to inject device fingerprint"""
    
    # Get values with defaults
    hardware_concurrency = profile.get('hardware_concurrency', 4)
    device_memory = profile.get('device_memory', 4)
    max_touch_points = profile.get('max_touch_points', 5)
    platform = profile.get('platform', 'iPhone')
    webgl_vendor = profile.get('webgl_vendor', 'Apple Inc.')
    webgl_renderer = profile.get('webgl_renderer', 'Apple GPU')
    language = profile.get('language', 'en-US').replace('_', '-')
    languages = f"['{language}', 'en']"
    timezone = profile.get('timezone', 'America/New_York')
    battery_level = profile.get('battery_level', 50) / 100.0
    battery_charging = str(profile.get('battery_charging', False)).lower()
    
    return f"""
    (function() {{
        'use strict';
        
        // Override hardware concurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {hardware_concurrency}
        }});
        
        // Override device memory
        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => {device_memory}
        }});
        
        // Override max touch points
        Object.defineProperty(navigator, 'maxTouchPoints', {{
            get: () => {max_touch_points}
        }});
        
        // Override platform
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{platform}'
        }});
        
        // Override languages
        Object.defineProperty(navigator, 'language', {{
            get: () => '{language}'
        }});
        
        Object.defineProperty(navigator, 'languages', {{
            get: () => {languages}
        }});
        
        // Override WebGL vendor/renderer
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return '{webgl_vendor}';
            if (parameter === 37446) return '{webgl_renderer}';
            if (parameter === 7936) return '{webgl_vendor}';
            if (parameter === 7937) return '{webgl_renderer}';
            return getParameter.call(this, parameter);
        }};
        
        // Apply to WebGL2 as well
        if (typeof WebGL2RenderingContext !== 'undefined') {{
            const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{webgl_vendor}';
                if (parameter === 37446) return '{webgl_renderer}';
                if (parameter === 7936) return '{webgl_vendor}';
                if (parameter === 7937) return '{webgl_renderer}';
                return getParameter2.call(this, parameter);
            }};
        }}
        
        // Override battery API
        if (navigator.getBattery) {{
            navigator.getBattery = async () => ({{
                charging: {battery_charging},
                chargingTime: 0,
                dischargingTime: Infinity,
                level: {battery_level},
                onchargingchange: null,
                onchargingtimechange: null,
                ondischargingtimechange: null,
                onlevelchange: null
            }});
        }}
        
        // Override timezone
        const DateTimeFormat = Intl.DateTimeFormat;
        Intl.DateTimeFormat = function(...args) {{
            const options = args[1] || {{}};
            if (!options.timeZone) {{
                options.timeZone = '{timezone}';
                args[1] = options;
            }}
            return new DateTimeFormat(...args);
        }};
        
        // Remove automation indicators
        delete navigator.__proto__.webdriver;
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined
        }});
        
        // Chrome specific
        if (window.chrome) {{
            window.chrome.runtime = {{}};
        }}
        
        // Notification permissions
        const originalQuery = window.navigator.permissions ? window.navigator.permissions.query : undefined;
        if (originalQuery) {{
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({{ state: Notification.permission }}) :
                    originalQuery(parameters)
            );
        }}
        
        console.log('Enhanced device fingerprint injected');
    }})();
    """
