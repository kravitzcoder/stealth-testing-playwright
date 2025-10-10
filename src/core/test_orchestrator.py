"""
STEALTH BROWSER TESTING FRAMEWORK - Test Orchestrator with BrowserForge
Main orchestrator with specialized runners and BrowserForge enhancement

Authors: kravitzcoder & Claude
"""
import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import logging

# Import specialized runners (standard)
from ..runners import (
    playwright_runner,
    patchright_runner,
    camoufox_runner,
    rebrowser_runner
)

# Import core components
from .screenshot_engine import ScreenshotEngine
from .test_result import TestResult

logger = logging.getLogger(__name__)


class StealthTestOrchestrator:
    """Main orchestrator for coordinating stealth browser tests"""
    
    def __init__(self):
        # Initialize screenshot engine
        self.screenshot_engine = ScreenshotEngine()
        
        # Initialize standard runners
        self.runners = {
            'playwright': playwright_runner.PlaywrightRunner(self.screenshot_engine),
            'patchright': patchright_runner.PatchrightRunner(self.screenshot_engine),
            'camoufox': camoufox_runner.CamoufoxRunner(self.screenshot_engine),
            'rebrowser_playwright': rebrowser_runner.RebrowserRunner(self.screenshot_engine)
        }
        
        # Enhanced runners cache (loaded on demand)
        self.enhanced_runners = {}
        
        # Check BrowserForge availability
        self.browserforge_available = self._check_browserforge()
        
        logger.info(f"✅ Initialized with {len(self.runners)} specialized runners")
        if self.browserforge_available:
            logger.info("🎭 BrowserForge available - enhanced runners ready")
        else:
            logger.info("📱 BrowserForge not available - using standard runners only")
        
        # Load configurations with standardized approach
        self.library_matrix = self._load_config_file("library_matrix.json")
        self.test_targets = self._load_config_file("test_targets.json")
        
        logger.info("Test orchestrator initialized")
    
    def _check_browserforge(self) -> bool:
        """Check if BrowserForge is available"""
        try:
            from browserforge.fingerprints import FingerprintGenerator
            return True
        except ImportError:
            return False
    
    def _load_config_file(self, filename: str) -> Dict[str, Any]:
        """Standardized configuration file loading"""
        # Priority order for config file locations
        search_paths = [
            # 1. Check if we're in standard src/config structure
            Path("src/config") / filename,
            # 2. Relative to this file
            Path(__file__).parent.parent / "config" / filename,
            # 3. From project root
            Path.cwd() / "src" / "config" / filename,
            # 4. Legacy location
            Path("config") / filename
        ]
        
        for config_path in search_paths:
            if config_path.exists():
                logger.info(f"Loading {filename} from: {config_path}")
                try:
                    with open(config_path, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"Failed to parse {filename}: {e}")
                    continue
        
        logger.error(f"Could not find {filename} in any expected location")
        logger.error(f"Searched paths: {[str(p) for p in search_paths]}")
        
        # Return minimal valid structure to avoid crashes
        if filename == "library_matrix.json":
            return {"library_matrix": {}}
        elif filename == "test_targets.json":
            return {"test_targets": {}, "mobile_configurations": {}, "wait_configuration": {}}
        else:
            return {}
    
    def _get_library_info(self, library_name: str) -> Optional[Dict[str, Any]]:
        """Get library information from the matrix"""
        for category_name, category_data in self.library_matrix.get("library_matrix", {}).items():
            libraries = category_data.get("libraries", {})
            if library_name in libraries:
                lib_info = libraries[library_name].copy()
                lib_info["category"] = category_name.replace("_category", "")
                return lib_info
        
        logger.warning(f"Library '{library_name}' not found in matrix")
        return None
    
    def _get_enhanced_runner(self, library_name: str):
        """
        Get or create enhanced runner for a library (with BrowserForge)
        
        Lazy loading to avoid import errors if enhanced runners don't exist
        """
        if library_name in self.enhanced_runners:
            return self.enhanced_runners[library_name]
        
        try:
            if library_name == 'playwright':
                from ..runners.playwright_runner_enhanced import PlaywrightRunnerEnhanced
                runner = PlaywrightRunnerEnhanced(self.screenshot_engine)
            elif library_name == 'patchright':
                from ..runners.patchright_runner_enhanced import PatchrightRunnerEnhanced
                runner = PatchrightRunnerEnhanced(self.screenshot_engine)
            elif library_name == 'camoufox':
                from ..runners.camoufox_runner_enhanced import CamoufoxRunnerEnhanced
                runner = CamoufoxRunnerEnhanced(self.screenshot_engine)
            elif library_name == 'rebrowser_playwright':
                from ..runners.rebrowser_runner_enhanced import RebrowserRunnerEnhanced
                runner = RebrowserRunnerEnhanced(self.screenshot_engine)
            else:
                logger.warning(f"No enhanced runner for {library_name}, using standard")
                return None
            
            self.enhanced_runners[library_name] = runner
            logger.info(f"🎭 Loaded enhanced runner for {library_name}")
            return runner
            
        except ImportError as e:
            logger.warning(f"Enhanced runner not available for {library_name}: {e}")
            return None
    
    def _get_runner_for_library(self, library_name: str, use_browserforge: bool = False):
        """
        Get the appropriate runner for a library
        
        Args:
            library_name: Name of the library
            use_browserforge: Whether to use BrowserForge enhanced runner
        
        Returns:
            Runner instance or None
        """
        # If BrowserForge is requested and available, try enhanced runner
        if use_browserforge and self.browserforge_available:
            enhanced_runner = self._get_enhanced_runner(library_name)
            if enhanced_runner:
                logger.info(f"🎭 Using enhanced runner for {library_name}")
                return enhanced_runner
            else:
                logger.warning(f"Enhanced runner not available for {library_name}, using standard")
        
        # Fall back to standard runner
        runner = self.runners.get(library_name)
        
        if not runner:
            logger.error(f"❌ No runner found for: {library_name}")
            logger.error(f"Available runners: {list(self.runners.keys())}")
        else:
            if use_browserforge:
                logger.info(f"📱 Using standard runner for {library_name} (enhanced not available)")
            else:
                logger.info(f"📱 Using standard runner for {library_name}")
        
        return runner
    
    async def test_single_library(
        self, 
        library_name: str,
        proxy_config: Dict[str, str],
        device: str = "iphone_x",
        use_browserforge: bool = False
    ) -> List[TestResult]:
        """
        Test a single library against all target URLs
        
        Args:
            library_name: Name of the library to test
            proxy_config: Proxy configuration dictionary
            device: Mobile device to emulate
            use_browserforge: Whether to use BrowserForge enhanced fingerprints
        
        Returns:
            List of TestResult objects (one per URL)
        """
        logger.info(f"Starting test for library: {library_name}")
        
        if use_browserforge:
            if self.browserforge_available:
                logger.info(f"🎭 BrowserForge mode ENABLED for {library_name}")
            else:
                logger.warning(f"⚠️ BrowserForge requested but not available, using standard mode")
                use_browserforge = False
        
        # Get library info (for logging/metadata)
        lib_info = self._get_library_info(library_name)
        if not lib_info:
            logger.warning(f"Library '{library_name}' not found in matrix, but will try to run anyway")
            category = "playwright"  # Default category
        else:
            category = lib_info.get("category", "playwright")
        
        # Get appropriate runner (enhanced or standard)
        runner = self._get_runner_for_library(library_name, use_browserforge=use_browserforge)
        if not runner:
            error_msg = f"No runner found for library: {library_name}"
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
        
        # Get wait configuration with reduced defaults
        wait_config = self.test_targets.get("wait_configuration", {})
        default_wait = wait_config.get("default_wait_time", 5)  # Reduced from 30
        
        # Test against all target URLs
        test_targets = self.test_targets.get("test_targets", {})
        results = []
        
        for target_name, target_data in test_targets.items():
            url = target_data.get("url")
            # Use intelligent wait times based on page complexity
            if "creepjs" in target_name.lower() or "worker" in target_name.lower():
                wait_time = 8  # Worker pages need more time
            elif "fingerprint" in target_name.lower() or "bot" in target_name.lower():
                wait_time = 5  # Standard complex pages
            else:
                wait_time = 3  # Simple pages like IP check
            
            mode_indicator = "🎭" if use_browserforge else "📱"
            logger.info(f"{mode_indicator} Testing {library_name} on {target_name}: {url} (wait: {wait_time}s)")
            
            try:
                # Call runner's run_test method
                result = await runner.run_test(
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
        device: str = "iphone_x",
        use_browserforge: bool = False
    ) -> List[TestResult]:
        """
        Wrapper for test_single_library with BrowserForge support
        
        Args:
            library_name: Library to test
            proxy_config: Proxy configuration
            device: Device to emulate
            use_browserforge: Whether to use BrowserForge enhanced fingerprints
        """
        return await self.test_single_library(
            library_name, 
            proxy_config, 
            device, 
            use_browserforge=use_browserforge
        )
    
    async def run_category_test(
        self,
        category: str,
        proxy_config: Dict[str, str],
        device: str = "iphone_x",
        use_browserforge: bool = False
    ) -> List[TestResult]:
        """
        Test all libraries in a category
        
        Args:
            category: Category name
            proxy_config: Proxy configuration
            device: Device to emulate
            use_browserforge: Whether to use BrowserForge
        """
        libraries = self.get_libraries_by_category(category)
        if not libraries:
            logger.error(f"No libraries found for category: {category}")
            return []
        
        logger.info(f"Testing {len(libraries)} libraries in category '{category}': {', '.join(libraries)}")
        return await self.test_multiple_libraries(
            libraries, 
            proxy_config, 
            device, 
            parallel=False, 
            use_browserforge=use_browserforge
        )
    
    async def test_multiple_libraries(
        self,
        library_names: List[str],
        proxy_config: Dict[str, str],
        device: str = "iphone_x",
        parallel: bool = False,
        use_browserforge: bool = False
    ) -> List[TestResult]:
        """
        Test multiple libraries
        
        Args:
            library_names: List of library names to test
            proxy_config: Proxy configuration
            device: Mobile device to emulate
            parallel: Whether to run tests in parallel
            use_browserforge: Whether to use BrowserForge enhanced fingerprints
        
        Returns:
            List of all TestResult objects
        """
        logger.info(f"Starting tests for {len(library_names)} libraries")
        
        if use_browserforge:
            if self.browserforge_available:
                logger.info("🎭 BrowserForge mode ENABLED for all libraries")
            else:
                logger.warning("⚠️ BrowserForge requested but not available")
                use_browserforge = False
        
        all_results = []
        
        if parallel:
            # Run libraries in parallel (limit concurrency to avoid resource issues)
            semaphore = asyncio.Semaphore(2)  # Max 2 concurrent browser instances
            
            async def run_with_semaphore(lib_name):
                async with semaphore:
                    return await self.test_single_library(
                        lib_name, 
                        proxy_config, 
                        device, 
                        use_browserforge=use_browserforge
                    )
            
            tasks = [run_with_semaphore(lib_name) for lib_name in library_names]
            
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
                results = await self.test_single_library(
                    lib_name, 
                    proxy_config, 
                    device, 
                    use_browserforge=use_browserforge
                )
                all_results.extend(results)
        
        return all_results
    
    def save_results(
        self,
        results: List[TestResult],
        filename_prefix: str = "stealth_test"
    ) -> str:
        """
        Save test results to JSON file with enhanced summary
        
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
        
        # Check BrowserForge usage
        browserforge_count = 0
        for result in results:
            additional = getattr(result, 'additional_data', {})
            if isinstance(additional, dict) and additional.get('browserforge_enhanced'):
                browserforge_count += 1
        
        # Group by library
        by_library = {}
        for result in results:
            if result.library not in by_library:
                by_library[result.library] = {
                    "results": [],
                    "stats": {
                        "total": 0,
                        "passed": 0,
                        "failed": 0,
                        "proxy_working": 0,
                        "mobile_ua_detected": 0,
                        "browserforge_enhanced": 0,
                        "avg_execution_time": 0
                    }
                }
            
            lib_data = by_library[result.library]
            lib_data["results"].append(result.to_dict())
            lib_data["stats"]["total"] += 1
            
            if result.success:
                lib_data["stats"]["passed"] += 1
            else:
                lib_data["stats"]["failed"] += 1
            
            if result.proxy_working:
                lib_data["stats"]["proxy_working"] += 1
            if result.is_mobile_ua:
                lib_data["stats"]["mobile_ua_detected"] += 1
            
            # Check BrowserForge usage
            additional = getattr(result, 'additional_data', {})
            if isinstance(additional, dict) and additional.get('browserforge_enhanced'):
                lib_data["stats"]["browserforge_enhanced"] += 1
            
            # Track execution time
            lib_data["stats"]["avg_execution_time"] += result.execution_time
        
        # Calculate averages
        for lib_name, lib_data in by_library.items():
            if lib_data["stats"]["total"] > 0:
                lib_data["stats"]["avg_execution_time"] /= lib_data["stats"]["total"]
                lib_data["stats"]["success_rate"] = (lib_data["stats"]["passed"] / lib_data["stats"]["total"]) * 100
                lib_data["stats"]["proxy_success_rate"] = (lib_data["stats"]["proxy_working"] / lib_data["stats"]["total"]) * 100
                lib_data["stats"]["mobile_ua_rate"] = (lib_data["stats"]["mobile_ua_detected"] / lib_data["stats"]["total"]) * 100
                lib_data["stats"]["browserforge_rate"] = (lib_data["stats"]["browserforge_enhanced"] / lib_data["stats"]["total"]) * 100
        
        # Prepare summary data
        summary_data = {
            "metadata": {
                "timestamp": timestamp,
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "success_rate": f"{(passed/total_tests*100):.1f}%" if total_tests > 0 else "0%",
                "libraries_tested": len(by_library),
                "browserforge_enhanced_tests": browserforge_count,
                "browserforge_enabled": browserforge_count > 0
            },
            "library_summaries": {
                lib_name: lib_data["stats"] 
                for lib_name, lib_data in by_library.items()
            },
            "results_by_library": {
                lib_name: lib_data["results"]
                for lib_name, lib_data in by_library.items()
            },
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
        """Generate markdown summary report with insights"""
        try:
            results_dir = Path("test_results") / "reports"
            md_path = results_dir / f"{prefix}_{timestamp}_summary.md"
            
            # Check BrowserForge usage
            browserforge_count = 0
            for result in results:
                additional = getattr(result, 'additional_data', {})
                if isinstance(additional, dict) and additional.get('browserforge_enhanced'):
                    browserforge_count += 1
            
            with open(md_path, 'w') as f:
                f.write(f"# Playwright Stealth Testing Results\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                if browserforge_count > 0:
                    f.write(f"🎭 **BrowserForge Enhanced:** {browserforge_count}/{len(results)} tests\n\n")
                
                # Overall statistics
                total = len(results)
                passed = len([r for r in results if r.success])
                f.write(f"## Overall Statistics\n\n")
                f.write(f"- **Total Tests:** {total}\n")
                f.write(f"- **Passed:** {passed} ({passed/total*100:.1f}%)\n")
                f.write(f"- **Failed:** {total-passed} ({(total-passed)/total*100:.1f}%)\n")
                if browserforge_count > 0:
                    f.write(f"- **BrowserForge Enhanced:** {browserforge_count} ({browserforge_count/total*100:.1f}%)\n")
                f.write("\n")
                
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
                    
                    # Check BrowserForge usage for this library
                    lib_bf_count = 0
                    for r in lib_results:
                        additional = getattr(r, 'additional_data', {})
                        if isinstance(additional, dict) and additional.get('browserforge_enhanced'):
                            lib_bf_count += 1
                    
                    bf_indicator = f" 🎭" if lib_bf_count > 0 else ""
                    f.write(f"### {lib_name}{bf_indicator}\n\n")
                    f.write(f"- **Success Rate:** {lib_passed}/{lib_total} ({lib_passed/lib_total*100:.1f}%)\n")
                    f.write(f"- **Category:** {lib_results[0].category}\n")
                    
                    if lib_bf_count > 0:
                        f.write(f"- **BrowserForge Enhanced:** {lib_bf_count}/{lib_total} tests\n")
                    
                    proxy_working = len([r for r in lib_results if r.proxy_working])
                    mobile_ua = len([r for r in lib_results if r.is_mobile_ua])
                    
                    f.write(f"- **Proxy Working:** {proxy_working}/{lib_total} ({proxy_working/lib_total*100:.1f}%)\n")
                    f.write(f"- **Mobile UA Detected:** {mobile_ua}/{lib_total} ({mobile_ua/lib_total*100:.1f}%)\n")
                    
                    # Average execution time
                    avg_time = sum(r.execution_time for r in lib_results) / lib_total
                    f.write(f"- **Avg Execution Time:** {avg_time:.2f}s\n\n")
                    
                    # Test details table
                    f.write(f"| Test | Success | Proxy | Mobile UA | Time | BF |\n")
                    f.write(f"|------|---------|-------|-----------|------|----|\n")
                    for r in lib_results:
                        success_icon = "✅" if r.success else "❌"
                        proxy_icon = "🔗" if r.proxy_working else "🚫"
                        mobile_icon = "📱" if r.is_mobile_ua else "🖥️"
                        
                        # Check BrowserForge for this test
                        additional = getattr(r, 'additional_data', {})
                        bf_icon = "🎭" if (isinstance(additional, dict) and additional.get('browserforge_enhanced')) else "📱"
                        
                        f.write(f"| {r.test_name} | {success_icon} | {proxy_icon} | {mobile_icon} | {r.execution_time:.2f}s | {bf_icon} |\n")
                    
                    f.write("\n")
                
                # Add insights section
                f.write("## Key Insights\n\n")
                
                # BrowserForge insights
                if browserforge_count > 0:
                    f.write(f"### 🎭 BrowserForge Enhancement\n\n")
                    f.write(f"- **Tests Enhanced:** {browserforge_count}/{total}\n")
                    f.write(f"- **Features Applied:**\n")
                    f.write(f"  - Intelligent User-Agent generation\n")
                    f.write(f"  - Realistic hardware fingerprints\n")
                    f.write(f"  - Enhanced WebGL properties\n")
                    f.write(f"  - Consistent navigator properties\n\n")
                
                # Proxy effectiveness
                total_proxy_working = len([r for r in results if r.proxy_working])
                f.write(f"- **Proxy Effectiveness:** {total_proxy_working}/{total} tests showed correct proxy IP\n")
                
                # Mobile UA success
                total_mobile = len([r for r in results if r.is_mobile_ua])
                f.write(f"- **Mobile UA Success:** {total_mobile}/{total} tests detected mobile user agent\n")
                
                # Fastest library
                if by_lib:
                    fastest_lib = min(by_lib.items(), 
                                    key=lambda x: sum(r.execution_time for r in x[1]) / len(x[1]))
                    avg_time = sum(r.execution_time for r in fastest_lib[1]) / len(fastest_lib[1])
                    f.write(f"- **Fastest Library:** {fastest_lib[0]} (avg {avg_time:.2f}s per test)\n")
                
                f.write("\n")
            
            logger.info(f"Markdown summary saved to: {md_path}")
            
        except Exception as e:
            logger.error(f"Failed to save markdown summary: {e}")
    
    def get_available_libraries(self) -> List[str]:
        """Get list of all available libraries"""
        # Return libraries from specialized runners
        return sorted(list(self.runners.keys()))
    
    def get_libraries_by_category(self, category: str) -> List[str]:
        """Get libraries in a specific category"""
        # Normalize category name
        category = category.replace("_category", "")
        
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
