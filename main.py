#!/usr/bin/env python3
"""
PLAYWRIGHT STEALTH TESTING FRAMEWORK - Main CLI (FIXED)
Command-line interface for Playwright-based stealth libraries

Authors: kravitzcoder & MiniMax Agent
Repository: https://github.com/kravitzcoder/stealth-testing-playwright

FIXES:
- Removed playwright_stealth (buggy v1.0.6)
- Only 3 libraries: playwright, patchright, camoufox
- Matches library_matrix.json configuration
"""

import asyncio
import argparse
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.test_orchestrator import StealthTestOrchestrator
from src.core.screenshot_engine import ScreenshotEngine
from src.core.dependency_checker import DependencyChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Playwright-specific libraries (FIXED: 3 only, no playwright_stealth)
PLAYWRIGHT_LIBRARIES = [
    "playwright",
    "patchright",
    "camoufox"
]

class PlaywrightTestCLI:
    """Command-line interface for Playwright stealth browser testing"""
    
    def __init__(self):
        self.orchestrator = StealthTestOrchestrator()
        self.config_dir = Path(__file__).parent / "src" / "config"
        self.dependency_checker = DependencyChecker()
        
        # Load configurations
        self.target_config = self._load_json_config("test_targets.json")
        self.library_config = self._load_json_config("library_matrix.json")
        self.proxy_config = self._load_json_config("proxy_config.json")
        
        logger.info("Playwright Test CLI initialized")
        logger.info(f"📚 Available libraries: {', '.join(PLAYWRIGHT_LIBRARIES)}")
    
    def _load_json_config(self, filename: str) -> Dict[str, Any]:
        """Load JSON configuration file"""
        config_path = self.config_dir / filename
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {filename}: {str(e)}")
            return {}
    
    def _parse_proxy_config(self, proxy_string: str) -> Dict[str, str]:
        """Parse proxy configuration from string or environment"""
        if proxy_string.startswith("env:"):
            # Load from environment variables
            config = {
                "host": os.getenv("PROXY_HOST", ""),
                "port": os.getenv("PROXY_PORT", ""),
                "username": os.getenv("PROXY_USERNAME", ""),
                "password": os.getenv("PROXY_PASSWORD", "")
            }
            
            # Validate
            if not config["host"] or not config["port"]:
                logger.error("❌ Proxy configuration incomplete!")
                logger.error("Required: PROXY_HOST and PROXY_PORT environment variables")
                return {}
            
            logger.info(f"✅ Proxy loaded from environment: {config['host']}:{config['port']}")
            return config
            
        elif "://" in proxy_string:
            # Parse proxy URL format: http://username:password@host:port
            from urllib.parse import urlparse
            parsed = urlparse(proxy_string)
            return {
                "host": parsed.hostname or "",
                "port": str(parsed.port or ""),
                "username": parsed.username or "",
                "password": parsed.password or ""
            }
        else:
            logger.error(f"Invalid proxy format: {proxy_string}")
            return {}
    
    def _get_mobile_config(self, device: str = "iphone_x") -> Dict[str, Any]:
        """Get mobile device configuration"""
        mobile_configs = self.target_config.get("mobile_configurations", {})
        return mobile_configs.get(device, mobile_configs.get("iphone_x", {}))
    
    def _get_libraries_by_filter(self, filter_type: str, filter_value: str) -> List[str]:
        """Get library names based on filter"""
        if filter_type == "all":
            return PLAYWRIGHT_LIBRARIES
        elif filter_type == "status":
            status_libraries = []
            playwright_category = self.library_config.get("library_matrix", {}).get("playwright_category", {})
            libraries = playwright_category.get("libraries", {})
            
            for lib_name, lib_data in libraries.items():
                if lib_data.get("status") == filter_value:
                    status_libraries.append(lib_name)
            return status_libraries
        elif filter_type == "single":
            return [filter_value] if filter_value in PLAYWRIGHT_LIBRARIES else []
        else:
            return []
    
    def _verify_dependencies(self, libraries: List[str]) -> bool:
        """Verify dependencies for selected libraries"""
        logger.info("=== Verifying Library Dependencies ===")
        
        all_satisfied = True
        for library in libraries:
            success, missing = self.dependency_checker.verify_library_dependencies(library)
            
            if not success:
                logger.warning(f"⚠️ {library}: Missing dependencies: {missing}")
                all_satisfied = False
            else:
                logger.info(f"✅ {library}: All dependencies satisfied")
        
        return all_satisfied
    
    async def run_tests(self, args) -> None:
        """Main test execution method"""
        try:
            # Parse proxy configuration
            proxy_config = self._parse_proxy_config(args.proxy)
            if not proxy_config.get("host"):
                logger.error("❌ Invalid proxy configuration")
                logger.error("Use --proxy env: to load from environment variables")
                logger.error("Or --proxy http://user:pass@host:port")
                return
            
            # Get mobile configuration
            mobile_config = self._get_mobile_config(args.device)
            
            # Determine which libraries to test
            if args.library:
                libraries = self._get_libraries_by_filter("single", args.library)
            elif args.status:
                libraries = self._get_libraries_by_filter("status", args.status)
            elif args.all:
                libraries = self._get_libraries_by_filter("all", "")
            else:
                # Default to working libraries
                libraries = self._get_libraries_by_filter("status", "working")
            
            if not libraries:
                logger.error("❌ No libraries selected for testing")
                return
            
            logger.info(f"🎭 Selected {len(libraries)} Playwright libraries: {', '.join(libraries)}")
            
            # Verify dependencies (optional, won't block execution)
            if args.verify_deps:
                logger.info("\n--- Dependency Check ---")
                self._verify_dependencies(libraries)
                logger.info("--- End Dependency Check ---\n")
            
            # Run tests
            all_results = []
            
            if args.mode == "sequential":
                # Run libraries one by one
                for library in libraries:
                    logger.info(f"\n=== Testing library: {library} ===")
                    library_results = await self.orchestrator.run_single_library_test(
                        library, proxy_config, args.device
                    )
                    all_results.extend(library_results)
                    logger.info(f"✅ Completed {library}: {len(library_results)} tests")
                    
            elif args.mode == "parallel":
                # Run libraries in parallel
                logger.info("🔄 Running tests in parallel mode")
                all_results = await self.orchestrator.test_multiple_libraries(
                    libraries, proxy_config, args.device, parallel=True
                )
            
            # Save results
            if all_results:
                results_file = self.orchestrator.save_results(
                    all_results, 
                    args.output_prefix or "playwright_test"
                )
                logger.info(f"\n✅ Test completed! Results saved to: {results_file}")
                
                # Print summary
                self._print_summary(all_results)
            else:
                logger.warning("⚠️ No test results generated")
                
        except KeyboardInterrupt:
            logger.info("\n⚠️ Test interrupted by user")
        except Exception as e:
            logger.error(f"❌ Test execution failed: {str(e)}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            raise
    
    def _print_summary(self, results: List) -> None:
        """Print test results summary"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        print("\n" + "="*70)
        print("PLAYWRIGHT STEALTH TESTING - RESULTS SUMMARY")
        print("="*70)
        print(f"Total Tests: {len(results)}")
        print(f"Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
        print(f"Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
        
        if successful:
            print(f"\n✅ Working Libraries:")
            lib_summary = {}
            for result in successful:
                if result.library not in lib_summary:
                    lib_summary[result.library] = {
                        'proxy': 0,
                        'mobile': 0,
                        'total': 0
                    }
                lib_summary[result.library]['total'] += 1
                if result.proxy_working:
                    lib_summary[result.library]['proxy'] += 1
                if result.is_mobile_ua:
                    lib_summary[result.library]['mobile'] += 1
            
            for lib, stats in lib_summary.items():
                proxy_pct = (stats['proxy']/stats['total']*100) if stats['total'] > 0 else 0
                mobile_pct = (stats['mobile']/stats['total']*100) if stats['total'] > 0 else 0
                print(f"  • {lib}: {stats['total']} tests | Proxy: {proxy_pct:.0f}% | Mobile UA: {mobile_pct:.0f}%")
        
        if failed:
            print(f"\n❌ Failed Tests:")
            for result in failed[:5]:  # Show first 5 failures
                error = (result.error or "Unknown error")[:60]
                print(f"  • {result.library} ({result.test_name}): {error}...")
            
            if len(failed) > 5:
                print(f"  ... and {len(failed)-5} more failures")
        
        print("\n" + "="*70)

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Playwright Stealth Browser Testing Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test specific library
  python main.py --proxy env: --library playwright
  
  # Test all working libraries
  python main.py --proxy env: --status working
  
  # Test all Playwright libraries
  python main.py --proxy env: --all
  
  # Test with dependency verification
  python main.py --proxy env: --all --verify-deps
  
  # GitHub Actions environment
  python main.py --proxy env: --all --mode parallel --output-prefix github_test

Note: playwright-stealth has been REMOVED due to v1.0.6 bugs (undefined 'opts')
      All libraries now use comprehensive manual stealth techniques
        """
    )
    
    # Proxy configuration
    parser.add_argument("--proxy", required=True,
                       help="Proxy configuration. Use 'env:' for environment variables or full URL")
    
    # Library selection (mutually exclusive)
    selection_group = parser.add_mutually_exclusive_group(required=True)
    selection_group.add_argument("--library", 
                                choices=PLAYWRIGHT_LIBRARIES,
                                help="Test specific Playwright library")
    selection_group.add_argument("--status", 
                                choices=["working", "testing", "issues"],
                                help="Test libraries by status")
    selection_group.add_argument("--all", action="store_true",
                                help="Test all Playwright libraries")
    
    # Test configuration
    parser.add_argument("--device", default="iphone_x",
                       choices=["iphone_x", "iphone_12", "samsung_galaxy"],
                       help="Mobile device to emulate")
    parser.add_argument("--mode", choices=["sequential", "parallel"], default="sequential",
                       help="Test execution mode")
    parser.add_argument("--output-prefix", 
                       help="Prefix for output files")
    parser.add_argument("--verify-deps", action="store_true",
                       help="Verify dependencies before testing")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize and run CLI
    cli = PlaywrightTestCLI()
    
    try:
        asyncio.run(cli.run_tests(args))
    except KeyboardInterrupt:
        logger.info("\n⚠️ Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
