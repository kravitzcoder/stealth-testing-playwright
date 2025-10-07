# main.py (Corrected Version)

import argparse
import logging
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
from src.utils.logging_config import setup_logging
setup_logging()

# --- KEY CHANGES ---
# REMOVED the import for the incorrect JSON loader
# from src.utils.config_loader import load_device_profile, get_proxy_config

# ADDED the import for YOUR correct CSV-based device loader
from src.core.device_profile_loader import DeviceProfileLoader 

# A function for proxy loading (was previously in the deleted config_loader.py)
def get_proxy_config(proxy_arg):
    logger = logging.getLogger(__name__)
    if not proxy_arg: return None
    
    if proxy_arg.lower() == 'env:':
        host = os.environ.get('PROXY_HOST')
        port = os.environ.get('PROXY_PORT')
        username = os.environ.get('PROXY_USERNAME')
        password = os.environ.get('PROXY_PASSWORD')
        
        if not host or not port:
            logger.error("Proxy env vars PROXY_HOST and PROXY_PORT must be set.")
            return None
        
        server = f"http://{host}:{port}"
        proxy_dict = {"server": server}
        if username: proxy_dict["username"] = username
        if password: proxy_dict["password"] = password
        return proxy_dict
    try:
        if '@' in proxy_arg:
            creds, endpoint = proxy_arg.split('@')
            user, pw = creds.split(':')
            host, port = endpoint.split(':')
            return {"server": f"http://{host}:{port}", "username": user, "password": pw}
        elif ':' in proxy_arg:
            host, port = proxy_arg.split(':')
            return {"server": f"http://{host}:{port}"}
        else:
            raise ValueError("Invalid proxy format.")
    except ValueError as e:
        logger.error(f"Failed to parse proxy argument: {e}")
        return None

# The main Orchestrator
from src.core.test_orchestrator import StealthTestOrchestrator

class PlaywrightTestCLI:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.parser = self._create_parser()
        self.args = self.parser.parse_args()
        
        load_dotenv()

        self.proxy_config = None
        self.device_config = None
        self.orchestrator = StealthTestOrchestrator()
        self.logger.info("Playwright Test CLI initialized")

    def _create_parser(self):
        parser = argparse.ArgumentParser(description="CLI for running Playwright stealth tests.")
        parser.add_argument("--proxy", required=True, help="Proxy configuration (e.g., 'host:port' or 'env:')")
        parser.add_argument("--library", help="Run tests for a single specified library.")
        parser.add_argument("--all", action="store_true", help="Run tests for all configured libraries.")
        parser.add_argument("--device", default="iphone_x", help="Device type to use for testing (e.g., 'iphone_x', 'samsung_galaxy').")
        parser.add_argument("--mode", choices=["sequential", "parallel"], default="sequential", help="Execution mode for '--all' tests.")
        parser.add_argument("--output-prefix", default="test_run", help="Prefix for the output report files.")
        parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
        return parser

    def _setup_logging(self):
        level = logging.DEBUG if self.args.verbose else logging.INFO
        logging.getLogger().setLevel(level)
        for handler in logging.getLogger().handlers:
            handler.setLevel(level)
        self.logger.info(f"Log level set to {'DEBUG' if self.args.verbose else 'INFO'}")

    async def run(self):
        self._setup_logging()

        if not self.args.library and not self.args.all:
            self.parser.error("Either --library or --all must be specified.")
            return

        self.proxy_config = get_proxy_config(self.args.proxy)
        if not self.proxy_config:
            self.logger.error("❌ Proxy configuration failed. Exiting.")
            return
        self.logger.info(f"✅ Proxy loaded from { 'environment' if self.args.proxy == 'env:' else 'argument' }: {self.proxy_config['server']}")

        # --- KEY CHANGES ---
        # Use your DeviceProfileLoader to get the device configuration
        try:
            profile_loader = DeviceProfileLoader()
            # Get a random profile based on the device type (e.g., 'iphone_x' -> iphone)
            raw_profile = profile_loader.get_profile_for_device(self.args.device)
            # Convert it to the format the application needs
            self.device_config = profile_loader.convert_to_mobile_config(raw_profile)
            if not self.device_config or not raw_profile:
                raise ValueError("No profile returned from loader.")
            self.logger.info(f"✅ Loaded device profile: '{self.device_config.get('device_name', 'Unknown')}'")
        except Exception as e:
            self.logger.error(f"❌ Failed to load device profile for '{self.args.device}'. Error: {e}", exc_info=self.args.verbose)
            return

        try:
            results = await self.run_tests()
            if results:
                self.orchestrator.save_results(results, self.args.output_prefix)
                self.logger.info(f"\n✅ Test completed! Results saved to: test_results/reports/{self.args.output_prefix}_*.json")
            else:
                 self.logger.warning("Test run produced no results.")

        except Exception as e:
            self.logger.error(f"❌ Test run failed: {e}", exc_info=self.args.verbose)
            exit(1)

    async def run_tests(self):
        if self.args.all:
            selected_libraries = self.orchestrator.get_libraries_by_status("working")
            self.logger.info(f"Selected {len(selected_libraries)} working Playwright libraries: {', '.join(selected_libraries)}")
            
            return await self.orchestrator.test_multiple_libraries(
                selected_libraries,
                self.proxy_config,
                self.device_config,
                parallel=(self.args.mode == 'parallel')
            )
        else:
            self.logger.info(f"\n=== Testing library: {self.args.library} ===")
            return await self.orchestrator.test_single_library(
                self.args.library,
                self.proxy_config,
                self.device_config
            )

if __name__ == "__main__":
    cli = PlaywrightTestCLI()
    asyncio.run(cli.run())
