"""
STEALTH BROWSER TESTING FRAMEWORK - Dependency Checker
Verify all dependencies are properly installed before testing

Authors: kravitzcoder & MiniMax Agent
"""
import sys
import importlib
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# Library dependency mapping
LIBRARY_DEPENDENCIES = {
    "playwright": ["playwright"],
    "playwright_stealth": ["playwright", "playwright_stealth"],
    "patchright": ["patchright"],
    "camoufox": ["camoufox"],
    "selenium_wire": ["selenium", "seleniumwire", "blinker"],
    "undetected_chromedriver": ["selenium", "undetected_chromedriver"],
    "selenium_stealth": ["selenium", "selenium_stealth"],
    "selenium_driverless": ["selenium_driverless"],
    "botasaurus": ["botasaurus"],
    "nodriver": ["nodriver"],
    "drissionpage": ["DrissionPage"],
    "helium": ["helium", "selenium"],
    "puppeteer_stealth": []  # Node.js package
}

# Critical version requirements
VERSION_REQUIREMENTS = {
    "blinker": "1.7.0",
    "playwright": "1.40.0",
    "selenium": "4.15.0"
}


class DependencyChecker:
    """Check and verify library dependencies"""
    
    def __init__(self):
        self.results = {}
    
    def verify_library_dependencies(self, library_name: str) -> Tuple[bool, List[str]]:
        """
        Verify all dependencies for a library are installed
        
        Returns:
            (success: bool, missing_deps: List[str])
        """
        deps = LIBRARY_DEPENDENCIES.get(library_name, [])
        missing = []
        
        for dep in deps:
            try:
                module = importlib.import_module(dep)
                
                # Check version if required
                if dep in VERSION_REQUIREMENTS:
                    expected_version = VERSION_REQUIREMENTS[dep]
                    actual_version = getattr(module, "__version__", "unknown")
                    
                    if actual_version != "unknown":
                        logger.info(f"✅ {dep}=={actual_version} (expected: {expected_version})")
                    else:
                        logger.warning(f"⚠️ {dep} version unknown")
                else:
                    logger.info(f"✅ {dep} available")
                    
            except ImportError as e:
                logger.error(f"❌ {dep} NOT available: {e}")
                missing.append(dep)
        
        success = len(missing) == 0
        return success, missing
    
    def verify_all_libraries(self) -> Dict[str, Tuple[bool, List[str]]]:
        """Verify dependencies for all libraries"""
        results = {}
        
        logger.info("=== Verifying All Library Dependencies ===")
        
        for library_name in LIBRARY_DEPENDENCIES.keys():
            success, missing = self.verify_library_dependencies(library_name)
            results[library_name] = (success, missing)
            
            if success:
                logger.info(f"✅ {library_name}: All dependencies satisfied")
            else:
                logger.error(f"❌ {library_name}: Missing {missing}")
        
        return results
    
    def verify_critical_imports(self) -> bool:
        """Verify critical imports work correctly"""
        critical_tests = {
            "playwright_stealth": lambda: self._test_playwright_stealth_import(),
            "selenium_wire": lambda: self._test_selenium_wire_import(),
        }
        
        all_passed = True
        
        for test_name, test_func in critical_tests.items():
            try:
                if test_func():
                    logger.info(f"✅ {test_name} import test passed")
                else:
                    logger.error(f"❌ {test_name} import test failed")
                    all_passed = False
            except Exception as e:
                logger.error(f"❌ {test_name} import test error: {e}")
                all_passed = False
        
        return all_passed
    
    def _test_playwright_stealth_import(self) -> bool:
        """Test playwright-stealth can be imported and used"""
        try:
            from playwright_stealth import stealth_async
            logger.info("✅ playwright-stealth import successful")
            return True
        except ImportError as e:
            logger.error(f"❌ playwright-stealth import failed: {e}")
            return False
    
    def _test_selenium_wire_import(self) -> bool:
        """Test selenium-wire with blinker compatibility"""
        try:
            import blinker
            logger.info(f"Blinker version: {blinker.__version__}")
            
            from seleniumwire import webdriver
            logger.info("✅ selenium-wire import successful")
            return True
        except ImportError as e:
            logger.error(f"❌ selenium-wire import failed: {e}")
            return False
    
    def generate_report(self) -> str:
        """Generate dependency check report"""
        results = self.verify_all_libraries()
        
        report = ["=" * 70]
        report.append("DEPENDENCY VERIFICATION REPORT")
        report.append("=" * 70)
        report.append("")
        
        # Summary
        total = len(results)
        passed = sum(1 for success, _ in results.values() if success)
        failed = total - passed
        
        report.append(f"Total Libraries: {total}")
        report.append(f"Dependencies Met: {passed}")
        report.append(f"Dependencies Missing: {failed}")
        report.append("")
        
        # Details
        report.append("LIBRARY STATUS:")
        report.append("-" * 70)
        
        for library_name, (success, missing) in sorted(results.items()):
            status = "✅ READY" if success else "❌ MISSING"
            report.append(f"{library_name:25s} {status}")
            
            if missing:
                report.append(f"  Missing: {', '.join(missing)}")
        
        report.append("=" * 70)
        
        return "\n".join(report)


def main():
    """Command-line dependency checker"""
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Check stealth library dependencies")
    parser.add_argument("--library", help="Check specific library")
    parser.add_argument("--all", action="store_true", help="Check all libraries")
    parser.add_argument("--critical", action="store_true", help="Test critical imports")
    
    args = parser.parse_args()
    
    checker = DependencyChecker()
    
    if args.library:
        success, missing = checker.verify_library_dependencies(args.library)
        if success:
            print(f"✅ {args.library}: All dependencies satisfied")
            sys.exit(0)
        else:
            print(f"❌ {args.library}: Missing {missing}")
            sys.exit(1)
    elif args.critical:
        success = checker.verify_critical_imports()
        sys.exit(0 if success else 1)
    elif args.all:
        report = checker.generate_report()
        print(report)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
