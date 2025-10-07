# src/runners/playwright_runner.py

import logging
import asyncio
import re
import json
import pygeoip
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from ..core.screenshot_engine import ScreenshotEngine

class PlaywrightRunner:
    """
    A runner for executing web tests using Playwright, with capabilities for
    applying stealth techniques and spoofing browser properties.
    """
    def __init__(self, user_agent, proxy_config, spoof_options, use_stealth_plugin=False, screenshot_engine=None):
        self.logger = logging.getLogger(__name__)
        self.user_agent = user_agent
        self.proxy_config = proxy_config
        self.spoof_options = spoof_options
        self.use_stealth_plugin = use_stealth_plugin
        self.screenshot_engine = screenshot_engine or ScreenshotEngine()
        self.geoip = pygeoip.GeoIP('GeoLiteCity.dat')
        
        runner_type = "stealth" if use_stealth_plugin else "route-based worker spoofing"
        self.logger.info(f"Playwright runner initialized with {runner_type}")
        if not use_stealth_plugin:
            self.logger.info("ℹ️ playwright-stealth plugin DISABLED (using manual spoofing only)")

    async def run_test(self, library_name, test_name, url, browser_type='chromium'):
        """
        Runs a single test case using the specified Playwright library and configuration.
        """
        self.logger.info(f"Testing {library_name.capitalize()} ({browser_type.capitalize()}) on {test_name}")
        async with async_playwright() as p:
            try:
                browser_launcher = getattr(p, browser_type)
                browser = await browser_launcher.launch(headless=True, proxy=self.proxy_config)
                context = await browser.new_context(
                    user_agent=self.user_agent.get('userAgent'),
                    extra_http_headers=self.user_agent.get('headers')
                )
                
                # Apply spoofing and interception
                await self._apply_manual_spoofing(context)

                page = await context.new_page()

                if self.use_stealth_plugin:
                    try:
                        from playwright_stealth import stealth_async
                        await stealth_async(page)
                        self.logger.info("✅ playwright-stealth plugin applied successfully")
                    except ImportError:
                        self.logger.error("❌ playwright-stealth is not installed. Cannot apply stealth.")
                        # Decide if you want to continue or return
                    except Exception as e:
                        self.logger.error(f"❌ Error applying playwright-stealth: {e}")

                await page.goto(url, wait_until='networkidle', timeout=60000)

                # Capture screenshot after actions and waits
                screenshot_path = await self.screenshot_engine.capture_screenshot(
                    page, library_name, test_name, url
                )
                
                # Check IP and proxy status after page load
                proxy_works = await self._check_ip_and_proxy(page)
                
                await browser.close()
                return {"status": "success", "proxy_works": proxy_works, "screenshot": screenshot_path}

            except PlaywrightTimeoutError:
                self.logger.error(f"Timeout error on {url} for {library_name}")
                await browser.close()
                return {"status": "error", "reason": "timeout"}
            except Exception as e:
                self.logger.error(f"An error occurred during the test for {library_name}: {e}")
                if 'browser' in locals() and browser.is_connected():
                    await browser.close()
                return {"status": "error", "reason": str(e)}

    async def _apply_manual_spoofing(self, context):
        """Applies manual spoofing techniques to the browser context."""
        # Spoof navigator properties on the main window
        await context.add_init_script(
            f"""
            if (navigator && 'platform' in navigator) {{
                Object.defineProperty(navigator, 'platform', {{
                    get: () => '{self.spoof_options.get("platform", "Win32")}'
                }});
            }}
            """
        )
        self.logger.info("✅ Main window navigator spoofing applied")

        # Set up route-based interception for workers
        await context.route("**/*", self._intercept_worker_route)
        self.logger.info("✅ Route-based worker interception enabled")
        self.logger.info("✅ Enhanced stealth fully applied (manual spoofing only)")

    async def _check_ip_and_proxy(self, page):
        """
        Checks if the proxy is working by comparing the visible IP address
        with the proxy IP address.
        """
        try:
            content = await page.content()
            ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
            found_ips = re.findall(ip_pattern, content)
            
            proxy_ip = self.proxy_config['server'].split(':')[0]
            
            if not found_ips:
                self.logger.warning("No IP address found on the page.")
                return False

            page_ip = found_ips[0]
            self.logger.info(f"✅ Found IP via content search: {page_ip}")

            if page_ip == proxy_ip:
                self.logger.info(f"✅ Proxy working: {page_ip} == {proxy_ip}")
                return True
            else:
                self.logger.warning(f"Proxy mismatch: Page IP ({page_ip}) != Proxy IP ({proxy_ip})")
                return False
        except Exception as e:
            self.logger.error(f"Error checking IP address: {e}")
            return False

    async def _intercept_worker_route(self, route):
        """
        Intercepts requests to identify and modify worker scripts to ensure
        consistent navigator properties. This is the updated and working method.
        """
        try:
            request = route.request
            # Broaden detection to catch different ways workers are loaded
            is_worker_request = (
                request.resource_type == "script"
                and (
                    "worker" in request.url.lower() or
                    request.header_value("sec-fetch-dest") in ["worker", "sharedworker", "serviceworker"]
                )
            )

            if is_worker_request:
                self.logger.info(f"✅ Worker script intercepted: {request.url}")

                original_response = await route.fetch()
                body = await original_response.text()

                # Get user agent and platform from the runner's current configuration
                ua = self.user_agent.get("userAgent", "")
                platform = self.spoof_options.get("platform", "iPhone") # Default to iPhone if not set
                
                # Escape the user agent string for safe injection into JavaScript
                ua_escaped = json.dumps(ua)

                # Create the JavaScript snippet to prepend
                spoof_js = f"""
                try {{
                    Object.defineProperties(navigator, {{
                        'userAgent': {{ get: () => {ua_escaped} }},
                        'platform': {{ get: () => '{platform}' }}
                    }});
                }} catch (e) {{ console.error('Error spoofing worker navigator:', e); }}
                """

                new_body = spoof_js + body
                
                response_headers = original_response.headers
                
                # Remove content-encoding headers to prevent conflicts, as we're serving a modified body
                if 'content-encoding' in response_headers:
                    del response_headers['content-encoding']
                if 'content-length' in response_headers:
                     del response_headers['content-length']


                await route.fulfill(
                    status=original_response.status,
                    headers=response_headers,
                    body=new_body
                )
                return

        except Exception as e:
            # If fetching fails (e.g., for a data URL), just let it continue
            if "Target closed" not in str(e): # Avoid logging common race conditions on close
                 self.logger.error(f"❌ Error in worker interception for {route.request.url}: {e}")

        # Continue all other requests unmodified
        await route.continue_()
