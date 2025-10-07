# main.py

import argparse
import logging
import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
from src.utils.logging_config import setup_logging
setup_logging()

from src.core.test_orchestrator import StealthTestOrchestrator
from src.utils.config_loader import load_device_profile, get_proxy_config

class PlaywrightTestCLI:
    """
    Command-Line Interface for running Playwright stealth tests.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.parser = self._create_parser()
        self.args = self.parser.parse_args()
        
        # Load environment variables from .env file
        load_dotenv()

        self.proxy_config = None
        self.device_config = None
        self.orchestrator = StealthTestOrchestrator()
        self.logger.info("Playwright Test CLI initialized")

    def _create_parser(self):
        """Creates the argument parser for the CLI."""
        parser = argparse.ArgumentParser(
            description="CLI for running Playwright stealth tests.",
            formatter_class=argparse.RawTextHelpFormatter
        )
        parser.add_argument(
            "--proxy",
            required=True,
            help="Proxy configuration. Examples:\n"
                 "  'host:port'\n"
                 "  'user:pass@host:port'\n"
                 "  'env:' (loads from PROXY_HOST, PROXY_PORT, etc. env vars)"
        )
        parser.add_argument(
            "--library",
            choices=["playwright", "playwright_stealth", "patchright", "camoufox"],
            help="Run tests for a single specified library."
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Run tests for all configured libraries."
        )
        parser.add_argument(
            "--device",
            default="iphone_x",
            help="Device profile to use for testing (e.g., 'iphone_x', 'samsung_galaxy')."
        )
        parser.add_argument(
            "--mode",
            choices=["sequential", "parallel"],
            default="sequential",
            help="Execution mode for '--all' tests ('sequential' or 'parallel')."
        )
        parser.add_argument(
            "--output-prefix",
            default="test_run",
            help="Prefix for the output report files."
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose logging."
        )
        return parser

    def _setup_logging(self):
        """Sets the logging level based on the --verbose flag."""
        level = logging.DEBUG if self.args.verbose else logging.INFO
        logging.getLogger().setLevel(level)
        for handler in logging.getLogger().handlers:
            handler.setLevel(level)
        self.logger.info(f"Log level set to {'DEBUG' if self.args.verbose else 'INFO'}")

    async def run(self):
        """Main execution flow for the CLI."""
        self._setup_logging()

        if not self.args.library and not self.args.all:
            self.parser.error("Either --library or --all must be specified.")
            return

        # Load configurations
        self.proxy_config = get_proxy_config(self.args.proxy)
        if not self.proxy_config:
            self.logger.error("❌ Proxy configuration failed. Exiting.")
            return
        self.logger.info(f"✅ Proxy loaded from { 'environment' if self.args.proxy == 'env:' else 'argument' }: {self.proxy_config['server']}")

        self.device_config = load_device_profile(self.args.device)
        if not self.device_config:
            self.logger.error(f"❌ Failed to load device profile '{self.args.device}'. Exiting.")
            return
        self.logger.info(f"✅ Loaded device profile: '{self.args.device}'")

        try:
            await self.run_tests()
            self.orchestrator.save_results(self.args.output_prefix)
            self.logger.info(f"\n✅ Test completed! Results saved to: test_results/reports/{self.args.output_prefix}_*.json")

        except Exception as e:
            self.logger.error(f"❌ Test failed: {e}", exc_info=self.args.verbose)
            # Exit with a non-zero code to indicate failure, useful for CI/CD
            exit(1)

    async def run_tests(self):
        """Orchestrates the test execution based on CLI arguments."""
        if self.args.all:
            selected_libraries = list(self.orchestrator.library_matrix.keys())
            self.logger.info(f"Selected {len(selected_libraries)} Playwright libraries: {', '.join(selected_libraries)}")
            
            await self.orchestrator.start_all_tests(
                selected_libraries,
                self.proxy_config,
                self.device_config,
                self.args.mode
            )
        else:
            self.logger.info(f"\n=== Testing library: {self.args.library} ===")
            try:
                # THIS IS THE FIX: Changed method name to start_test
                await self.orchestrator.start_test(
                    self.args.library,
                    self.proxy_config,
                    self.device_config
                )
                self.logger.info(f"Completed {self.args.library}: {len(self.orchestrator.test_targets)} tests")
            except Exception as e:
                self.logger.error(f"❌ Test execution failed: {e}", exc_info=self.args.verbose)
                raise # Re-raise the exception to be caught by the main run loop

if __name__ == "__main__":
    cli = PlaywrightTestCLI()
    asyncio.run(cli.run())
