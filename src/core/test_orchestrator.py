"""
STEALTH BROWSER TESTING FRAMEWORK - Test Orchestrator
Main orchestrator for coordinating stealth browser tests (COMPLETE)

Authors: kravitzcoder & MiniMax Agent
Phase: 1 - Foundation & Workflows
"""
import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import logging

# Import category runners
from ..categories.playwright_runner import PlaywrightRunner
from ..categories.selenium_runner import SeleniumRunner
from ..categories.specialized_runner import SpecializedRunner
from ..categories.puppeteer_runner import PuppeteerRunner

# Import core components
from .screenshot_engine import ScreenshotEngine
from .test_result import TestResult

logger = logging.getLogger(__name__)


class StealthTestOrchestrator:
    """Main orchestrator for coordinating stealth browser tests"""
    
    def __init__(self):
        # Initialize screenshot engine
        self.screenshot_engine = ScreenshotEngine()
        
        # Initialize all runners with screenshot engine
        self.playwright_runner = PlaywrightRunner(self.screenshot_engine)
        self.selenium_runner = SeleniumRunner(self.screenshot_engine) 
        self.specialized_runner = SpecializedRunner(self.screenshot_engine)
        self.puppeteer_runner = PuppeteerRunner()
        
        # Load configurations
        self.library_matrix = self._load_library_matrix()
        self.test_targets = self._load_test_targets()
        
        logger.info("Test orchestrator initialized")
    
    def _load_library_matrix(self) -> Dict[str, Any]:
        """Load the library testing matrix configuration"""
        try:
            # Try multiple possible paths
            possible_paths = [
                Path(__file__).parent.parent / "config" / "library_matrix.json",
                Path(__file__).parent.parent.parent / "src" / "config" / "library_matrix.json",
                Path("src/config/library_matrix.json"),
                Path("config/library_matrix.json")
            ]
            
            for matrix_path in possible_paths:
                if matrix_path.exists():
                    logger.info(f"Loading library matrix from: {matrix_path}")
                    with open(matrix_path, 'r') as f:
                        return json.load(f)
            
            logger.error("Could not find library_matrix.json in any expected location")
            return {"library_matrix": {}}
            
        except Exception as e:
            logger.error(f"Failed to load library matrix: {e}")
            return {"library_matrix": {}}
    
    def _load_test_targets(self) -> Dict[str, Any]:
        """Load test targets configuration"""
        try:
            possible_paths = [
                Path(__file__).parent.parent / "config" / "test_targets.json",
                Path(__file__).parent.parent.parent / "src" / "config" / "test_targets.json",
                Path("src/config/test_targets.json"),
                Path("config/test_targets.json")
            ]
            
            for target_path in possible_paths:
                if target_path.exists():
                    logger.info(f"Loading test targets from: {target_path}")
                    with open(target_path, 'r') as f:
                        return json.load(f)
            
            logger.error("Could not find test_targets.json in any expected location")
            return {"test_targets": {}, "mobile_configurations": {}}
            
        except Exception as e:
            logger.error(f"Failed to load test targets: {e}")
            return {"test_targets": {}, "mobile_configurations": {}}
    
    def _get_library_info(self, library_name: str) -> Optional[Dict[str, Any]]:
        """Get library information from the matrix"""
        for category_name, category_data in self.library_matrix.get("library_matrix", {}).items():
            libraries = category_data.get("libraries", {})
            if library_name in libraries:
                lib_info = libraries[library_name].copy()
                return lib_info
        
        logger.warning(f"Library '{library_name}' not found in matrix")
        return None
    
    def _get_runner_for_category(self, category: str):
        """Get the appropriate runner for a category"""
        category_mapping = {
            "playwright": self.playwright_runner,
            "selenium": self.selenium_runner,
            "specialized": self.specialized_runner,
            "puppeteer": self.puppeteer_runner
        }
        
        runner = category_mapping.get(category)
        if not runner:
            logger.error(f"No runner found for category: {category}")
        return runner
    
    async def test_single_library(
        self, 
        library_name: str,
        proxy_config: Dict[str, str],
        device: str = "iphone_x"
    ) -> List[TestResult]:
        """
        Test a single library against all target URLs
        
        Args:
            library_name: Name of the library to test
            proxy_config: Proxy configuration dictionary
            device: Mobile device to emulate
        
        Returns:
            List of TestResult objects (one per URL)
        """
        logger.info(f"Starting test for library: {library_name}")
        
        # Get library info
        lib_info = self._get_library_info(library_name)
        if not lib_info:
            error_msg = f"Library '{library_name}' not found in matrix configuration"
            logger.error(error_msg)
            return [TestResult(
                library=library_name,
                category="unknown",
                test_name="configuration_error",
                url="",
                success=False,
                error=error_msg,
                execution_time=0
            )]
        
        category = lib_info.get("category")
        if not category:
            error_msg = f"No category found for library: {library_name}"
            logger.error(error_msg)
            return [TestResult(
                library=library_name,
                category="unknown",
                test_name="configuration_error",
                url="",
                success=False,
                error=error_msg,
                execution_time=0
            )]
        
        # Get runner for this category
        runner = self._get_runner_for_category(category)
        if not runner:
            error_msg = f"No runner found for category: {category}"
            logger.error(error_msg)
            return [TestResult(
                library=library_name,
                category=category,
                test_name="runner_error",
                url="",
                success=False,
                error=error_msg,
                execution_time=0
            )]
        
        # Get mobile configuration
        mobile_configs = self.test_targets.get("mobile_configurations", {})
        mobile_config = mobile_configs.get(device, mobile_configs.get("iphone_x", {}))
        
        # Get wait configuration
        wait_config = self.test_targets.get("wait_configuration", {})
        default_wait = wait_config.get("default_wait_time", 30)
        
        # Test against all target URLs
        test_targets = self.test_targets.get("test_targets", {})
        results = []
        
        for target_name, target_data in test_targets.items():
            url = target_data.get("url")
            wait_time = target_data.get("expected_load_time", default_wait)
            
            logger.info(f"Testing {library_name} on {target_name}: {url}")
            
            try:
                result = await runner.run_test(
                    library_name=library_name,
                    url=url,
                    url_name=target_name,
                    proxy_config=proxy_config,
                    mobile_config=mobile_config,
                    wait_time=wait_time
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Test failed for {library_name} on {target_name}: {str(e)}")
                results.append(TestResult(
                    library=library_name,
                    category=category,
                    test_name=target_name,
                    url=url,
                    success=False,
                    error=str(e)[:200],
                    execution_time=0
                ))
        
        return results
    
    async def run_single_library_test(
        self, 
        library_name: str,
        proxy_config: Dict[str, str],
        device: str = "iphone_x"
    ) -> List[TestResult]:
        """Wrapper for test_single_library for backward compatibility"""
        return await self.test_single_library(library_name, proxy_config, device)
    
    async def run_category_test(
        self,
        category: str,
        proxy_config: Dict[str, str],
        device: str = "iphone_x"
    ) -> List[TestResult]:
        """Test all libraries in a category"""
        libraries = self.get_libraries_by_category(category)
        if not libraries:
            logger.error(f"No libraries found for category: {category}")
            return []
        
        logger.info(f"Testing {len(libraries)} libraries in category '{category}': {', '.join(libraries)}")
        return await self.test_multiple_libraries(libraries, proxy_config, device, parallel=False)
    
    async def test_multiple_libraries(
        self,
        library_names: List[str],
        proxy_config: Dict[str, str],
        device: str = "iphone_x",
        parallel: bool = False
    ) -> List[TestResult]:
        """
        Test multiple libraries
        
        Args:
            library_names: List of library names to test
            proxy_config: Proxy configuration
            device: Mobile device to emulate
            parallel: Whether to run tests in parallel
        
        Returns:
            List of all TestResult objects
        """
        logger.info(f"Starting tests for {len(library_names)} libraries")
        
        all_results = []
        
        if parallel:
            # Run libraries in parallel
            tasks = [
                self.test_single_library(lib_name, proxy_config, device)
                for lib_name in library_names
            ]
            
            results_lists = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results_lists):
                if isinstance(result, Exception):
                    logger.error(f"Library test failed: {str(result)}")
                    all_results.append(TestResult(
                        library=library_names[i],
                        category="unknown",
                        test_name="execution_error",
                        url="",
                        success=False,
                        error=str(result),
                        execution_time=0
                    ))
                else:
                    all_results.extend(result)
        else:
            # Run libraries sequentially
            for lib_name in library_names:
                results = await self.test_single_library(lib_name, proxy_config, device)
                all_results.extend(results)
        
        return all_results
    
    def save_results(
        self,
        results: List[TestResult],
        filename_prefix: str = "stealth_test"
    ) -> str:
        """
        Save test results to JSON file
        
        Args:
            results: List of TestResult objects
            filename_prefix: Prefix for the output filename
        
        Returns:
            Path to saved results file
        """
        # Ensure results directory exists
        results_dir = Path("test_results") / "reports"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        filepath = results_dir / filename
        
        # Calculate summary statistics
        total_tests = len(results)
        passed = len([r for r in results if r.success])
        failed = total_tests - passed
        
        # Group by library
        by_library = {}
        for result in results:
            if result.library not in by_library:
                by_library[result.library] = []
            by_library[result.library].append(result.to_dict())
        
        # Prepare summary data
        summary_data = {
            "metadata": {
                "timestamp": timestamp,
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "success_rate": f"{(passed/total_tests*100):.1f}%" if total_tests > 0 else "0%",
                "libraries_tested": len(by_library)
            },
            "results_by_library": by_library,
            "all_results": [r.to_dict() for r in results]
        }
        
        # Save to file
        try:
            with open(filepath, 'w') as f:
                json.dump(summary_data, f, indent=2, default=str)
            logger.info(f"Results saved to: {filepath}")
            
            # Also create a summary markdown file
            self._save_markdown_summary(results, filename_prefix, timestamp)
            
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return ""
    
    def _save_markdown_summary(
        self,
        results: List[TestResult],
        prefix: str,
        timestamp: str
    ) -> None:
        """Generate markdown summary report"""
        try:
            results_dir = Path("test_results") / "reports"
            md_path = results_dir / f"{prefix}_{timestamp}_summary.md"
            
            with open(md_path, 'w') as f:
                f.write(f"# Stealth Browser Testing Results\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Overall statistics
                total = len(results)
                passed = len([r for r in results if r.success])
                f.write(f"## Overall Statistics\n\n")
                f.write(f"- **Total Tests:** {total}\n")
                f.write(f"- **Passed:** {passed} ({passed/total*100:.1f}%)\n")
                f.write(f"- **Failed:** {total-passed} ({(total-passed)/total*100:.1f}%)\n\n")
                
                # Group by library
                by_lib = {}
                for r in results:
                    if r.library not in by_lib:
                        by_lib[r.library] = []
                    by_lib[r.library].append(r)
                
                f.write(f"## Results by Library\n\n")
                for lib_name, lib_results in sorted(by_lib.items()):
                    lib_passed = len([r for r in lib_results if r.success])
                    lib_total = len(lib_results)
                    
                    f.write(f"### {lib_name}\n\n")
                    f.write(f"- **Success Rate:** {lib_passed}/{lib_total} ({lib_passed/lib_total*100:.1f}%)\n")
                    f.write(f"- **Category:** {lib_results[0].category}\n")
                    
                    proxy_working = len([r for r in lib_results if r.proxy_working])
                    mobile_ua = len([r for r in lib_results if r.is_mobile_ua])
                    
                    f.write(f"- **Proxy Working:** {proxy_working}/{lib_total}\n")
                    f.write(f"- **Mobile UA Detected:** {mobile_ua}/{lib_total}\n\n")
                    
                    # Test details
                    f.write(f"| Test | Success | Proxy | Mobile UA | Time |\n")
                    f.write(f"|------|---------|-------|-----------|------|\n")
                    for r in lib_results:
                        success_icon = "✅" if r.success else "❌"
                        proxy_icon = "🔗" if r.proxy_working else "🚫"
                        mobile_icon = "📱" if r.is_mobile_ua else "🖥️"
                        f.write(f"| {r.test_name} | {success_icon} | {proxy_icon} | {mobile_icon} | {r.execution_time:.2f}s |\n")
                    
                    f.write("\n")
            
            logger.info(f"Markdown summary saved to: {md_path}")
            
        except Exception as e:
            logger.error(f"Failed to save markdown summary: {e}")
    
    def get_available_libraries(self) -> List[str]:
        """Get list of all available libraries"""
        libraries = []
        for category_data in self.library_matrix.get("library_matrix", {}).values():
            libraries.extend(category_data.get("libraries", {}).keys())
        return sorted(libraries)
    
    def get_libraries_by_category(self, category: str) -> List[str]:
        """Get libraries in a specific category"""
        for category_key, category_data in self.library_matrix.get("library_matrix", {}).items():
            if category in category_key.lower():
                return list(category_data.get("libraries", {}).keys())
        return []
    
    def get_libraries_by_status(self, status: str) -> List[str]:
        """Get libraries with a specific status (working, testing, issues)"""
        libraries = []
        for category_data in self.library_matrix.get("library_matrix", {}).values():
            for lib_name, lib_info in category_data.get("libraries", {}).items():
                if lib_info.get("status") == status:
                    libraries.append(lib_name)
        return sorted(libraries)
