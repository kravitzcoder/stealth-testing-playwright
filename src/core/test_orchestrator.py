# src/core/test_orchestrator.py (Corrected and Merged)

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import logging

# Import category runners
from ..runners.playwright_runner import PlaywrightRunner

# Import core components
from .screenshot_engine import ScreenshotEngine
from .test_result import TestResult

logger = logging.getLogger(__name__)


class StealthTestOrchestrator:
    """Main orchestrator for coordinating stealth browser tests"""
    
    def __init__(self):
        self.screenshot_engine = ScreenshotEngine()
        
        # --- FIX ---
        # The runner is no longer initialized here. It's created for each test.
        # self.playwright_runner = PlaywrightRunner(self.screenshot_engine)
        
        self.library_matrix = self._load_library_matrix()
        self.test_targets = self._load_test_targets()
        
        logger.info("Test orchestrator initialized")
    
    def _load_library_matrix(self) -> Dict[str, Any]:
        """Load the library testing matrix configuration"""
        try:
            matrix_path = Path(__file__).parent.parent / "config" / "library_matrix.json"
            if matrix_path.exists():
                logger.info(f"Loading library matrix from: {matrix_path}")
                with open(matrix_path, 'r') as f:
                    return json.load(f)
            logger.error(f"Could not find library_matrix.json at {matrix_path}")
            return {"library_matrix": {}}
        except Exception as e:
            logger.error(f"Failed to load library matrix: {e}")
            return {"library_matrix": {}}
    
    def _load_test_targets(self) -> Dict[str, Any]:
        """Load test targets configuration"""
        try:
            target_path = Path(__file__).parent.parent / "config" / "test_targets.json"
            if target_path.exists():
                logger.info(f"Loading test targets from: {target_path}")
                with open(target_path, 'r') as f:
                    return json.load(f)
            logger.error(f"Could not find test_targets.json at {target_path}")
            return {"test_targets": {}}
        except Exception as e:
            logger.error(f"Failed to load test targets: {e}")
            return {"test_targets": {}}
    
    def _get_library_info(self, library_name: str) -> Optional[Dict[str, Any]]:
        """Get library information from the matrix"""
        for category_data in self.library_matrix.get("library_matrix", {}).values():
            libraries = category_data.get("libraries", {})
            if library_name in libraries:
                return libraries[library_name].copy()
        logger.warning(f"Library '{library_name}' not found in matrix")
        return None

    def _create_runner_for_test(self, library_info: Dict, device_config: Dict, proxy_config: Dict) -> PlaywrightRunner:
        """Creates and configures a new PlaywrightRunner instance for a test."""
        user_agent_data = {"userAgent": device_config.get("user_agent")}
        spoof_options = {
            "platform": device_config.get("platform", "iPhone")
        }
        
        return PlaywrightRunner(
            user_agent=user_agent_data,
            proxy_config=proxy_config,
            spoof_options=spoof_options,
            use_stealth_plugin=library_info.get("stealth_plugin", False),
            screenshot_engine=self.screenshot_engine
        )

    async def test_single_library(
        self, 
        library_name: str,
        proxy_config: Dict[str, str],
        device_config: Dict[str, Any]
    ) -> List[TestResult]:
        """Test a single library against all target URLs"""
        logger.info(f"Starting test for library: {library_name}")
        
        lib_info = self._get_library_info(library_name)
        if not lib_info:
            error_msg = f"Library '{library_name}' not found in matrix"
            return [TestResult(library=library_name, category="unknown", test_name="config_error", url="", success=False, error=error_msg)]
        
        category = lib_info.get("category")
        if category != "playwright":
             error_msg = f"Runner for category '{category}' not implemented yet"
             return [TestResult(library=library_name, category=category, test_name="runner_error", url="", success=False, error=error_msg)]

        # --- FIX ---
        # Create a new runner instance configured for this specific test
        runner = self._create_runner_for_test(lib_info, device_config, proxy_config)

        results = []
        for target_name, target_data in self.test_targets.get("test_targets", {}).items():
            url = target_data.get("url")
            logger.info(f"Testing {library_name} on {target_name}: {url}")
            
            try:
                # The run_test method now gets a simplified signature
                result_dict = await runner.run_test(
                    library_name=library_name,
                    test_name=target_name,
                    url=url,
                    browser_type=lib_info.get("browser", "chromium")
                )
                
                # Convert dict to TestResult object
                results.append(TestResult(
                    library=library_name,
                    category=category,
                    test_name=target_name,
                    url=url,
                    success=result_dict.get("status") == "success",
                    proxy_working=result_dict.get("proxy_works", False),
                    screenshot_path=result_dict.get("screenshot"),
                    error=result_dict.get("reason"),
                    user_agent=device_config.get("user_agent")
                ))
                
            except Exception as e:
                logger.error(f"Test failed for {library_name} on {target_name}: {str(e)}")
                results.append(TestResult(library=library_name, category=category, test_name=target_name, url=url, success=False, error=str(e)[:200]))
        
        return results
    
    async def test_multiple_libraries(
        self,
        library_names: List[str],
        proxy_config: Dict[str, str],
        device_config: Dict[str, Any],
        parallel: bool = False
    ) -> List[TestResult]:
        """Test multiple libraries"""
        all_results = []
        if parallel:
            tasks = [self.test_single_library(lib_name, proxy_config, device_config) for lib_name in library_names]
            results_lists = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results_lists):
                if isinstance(result, Exception):
                    all_results.append(TestResult(library=library_names[i], category="unknown", test_name="execution_error", url="", success=False, error=str(result)))
                else:
                    all_results.extend(result)
        else:
            for lib_name in library_names:
                results = await self.test_single_library(lib_name, proxy_config, device_config)
                all_results.extend(results)
        
        return all_results
    
    def save_results(
        self,
        results: List[TestResult],
        filename_prefix: str = "stealth_test"
    ) -> str:
        """Save test results to JSON and Markdown files"""
        results_dir = Path("test_results") / "reports"
        results_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        filepath = results_dir / filename
        
        summary_data = {
            "metadata": {"timestamp": timestamp},
            "all_results": [r.to_dict() for r in results]
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(summary_data, f, indent=2, default=str)
            logger.info(f"Results saved to: {filepath}")
            self._save_markdown_summary(results, filename_prefix, timestamp)
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return ""

    def _save_markdown_summary(self, results: List[TestResult], prefix: str, timestamp: str):
        """Generates a markdown summary of the test results."""
        # This is a placeholder for your existing markdown logic
        pass

    def get_libraries_by_status(self, status: str) -> List[str]:
        """Get libraries with a specific status (e.g., 'working')."""
        libraries = []
        for category_data in self.library_matrix.get("library_matrix", {}).values():
            for lib_name, lib_info in category_data.get("libraries", {}).items():
                if lib_info.get("status") == status:
                    libraries.append(lib_name)
        return sorted(libraries)
