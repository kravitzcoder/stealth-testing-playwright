# src/core/test_orchestrator.py

import logging
import json
import asyncio
from datetime import datetime
from pathlib import Path
from ..runners.playwright_runner import PlaywrightRunner
from ..core.screenshot_engine import ScreenshotEngine

class StealthTestOrchestrator:
    """
    Orchestrates the execution of stealth tests across different Playwright libraries
    and configurations.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.library_matrix = self._load_config("library_matrix.json")
        self.test_targets = self._load_config("test_targets.json")
        
        # Initialize components
        self.screenshot_engine = ScreenshotEngine()
        
        # The runner is now created inside the start_test method, specific to each test.
        self.results = []
        self.start_time = None
        self.logger.info("Test orchestrator initialized")

    def _load_config(self, filename):
        """Loads a JSON configuration file from the config directory."""
        config_path = Path(__file__).parent.parent / "config" / filename
        self.logger.info(f"Loading configuration from: {config_path}")
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to load configuration '{filename}': {e}")
            return {}

    async def start_all_tests(self, selected_libraries, proxy_config, device_config, mode='sequential'):
        """Starts tests for all specified libraries."""
        self.start_time = datetime.now()
        
        test_tasks = []
        for library_name in selected_libraries:
            task = self.start_test(library_name, proxy_config, device_config)
            if mode == 'parallel':
                test_tasks.append(asyncio.create_task(task))
            else:
                await task

        if mode == 'parallel':
            await asyncio.gather(*test_tasks)

    async def start_test(self, library_name, proxy_config, device_config):
        """Prepares and runs tests for a single library."""
        self.logger.info(f"Starting test for library: {library_name}")
        library_info = self.library_matrix.get(library_name)

        if not library_info:
            self.logger.error(f"Library '{library_name}' not found in matrix configuration.")
            self.results.append({
                "library": library_name,
                "test": "configuration_error",
                "status": "error",
                "reason": f"Library '{library_name}' not found in matrix configuration."
            })
            return

        user_agent_data = device_config.get('user_agent', {})
        spoof_options = self._get_spoof_options(library_info.get("browser"), device_config.get("platform"))
        
        runner = self._get_runner(library_name, library_info, user_agent_data, proxy_config, spoof_options)

        for test_name, url in self.test_targets.items():
            self.logger.info(f"Testing {library_name} on {test_name}: {url}")
            test_result = await runner.run_test(
                library_name=library_name,
                test_name=test_name,
                url=url,
                browser_type=library_info.get("browser", "chromium")
            )
            
            test_result['library'] = library_name
            test_result['test'] = test_name
            self.results.append(test_result)
        
        self.logger.info(f"Completed all tests for {library_name}")

    def _get_runner(self, library_name, library_info, user_agent, proxy_config, spoof_options):
        """Factory method to create a configured runner instance."""
        use_stealth = library_info.get("stealth_plugin", False)
        
        return PlaywrightRunner(
            user_agent=user_agent,
            proxy_config=proxy_config,
            spoof_options=spoof_options,
            use_stealth_plugin=use_stealth,
            screenshot_engine=self.screenshot_engine
        )

    def _get_spoof_options(self, browser, platform):
        """Determines spoofing options based on browser and platform."""
        return {"platform": platform or "iPhone"}

    def save_results(self, output_prefix):
        """Saves the test results to a JSON file and a markdown summary."""
        if not self.results:
            self.logger.warning("No results to save.")
            return

        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        
        report_path = Path("test_results/reports") / f"{output_prefix}_{timestamp}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=4)
        self.logger.info(f"Results saved to: {report_path}")

        summary_path = Path("test_results/reports") / f"{output_prefix}_{timestamp}_summary.md"
        self._generate_markdown_summary(summary_path)
        self.logger.info(f"Markdown summary saved to: {summary_path}")

    def _generate_markdown_summary(self, file_path):
        """Generates a markdown summary of the test results."""
        summary_data = {}
        failed_tests = []

        for result in self.results:
            lib = result['library']
            if lib not in summary_data:
                summary_data[lib] = {'total': 0, 'success': 0, 'proxy_ok': 0}
            
            summary_data[lib]['total'] += 1
            if result['status'] == 'success':
                summary_data[lib]['success'] += 1
                if result.get('proxy_works'):
                    summary_data[lib]['proxy_ok'] += 1
            else:
                failed_tests.append(result)

        total_tests = len(self.results)
        total_successful = sum(lib['success'] for lib in summary_data.values())
        total_failed = total_tests - total_successful

        summary_md = [
            "| Library | Status | Success Rate | Proxy Health |",
            "|---|---|---|---|"
        ]

        for lib, data in summary_data.items():
            status = "✅" if data['success'] == data['total'] else "❌"
            success_rate = f"{data['success'] / data['total']:.0%}" if data['total'] > 0 else "N/A"
            proxy_health = f"{data['proxy_ok'] / data['total']:.0%}" if data['total'] > 0 else "N/A"
            summary_md.append(f"| **{lib}** | {status} | `{success_rate}` ({data['success']}/{data['total']}) | `{proxy_health}` ({data['proxy_ok']}/{data['total']}) |")

        summary_md.append("\n### Failed Tests\n")
        if failed_tests:
            summary_md.append("| Library | Test | Reason |")
            summary_md.append("|---|---|---|")
            for test in failed_tests:
                summary_md.append(f"| {test['library']} | `{test['test']}` | {test.get('reason', 'Unknown')} |")
        else:
            summary_md.append("🎉 All tests passed successfully!")

        with open(file_path, 'w') as f:
            f.write("\n".join(summary_md))
