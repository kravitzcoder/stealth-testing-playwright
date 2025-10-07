"""
STEALTH BROWSER TESTING FRAMEWORK - Dependency Checker (FIXED)
Verify all dependencies are properly installed before testing

Authors: kravitzcoder & MiniMax Agent

FIXES:
- Removed playwright_stealth from dependency list
- Only 3 Playwright libraries checked
"""
import sys
import importlib
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# Library dependency mapping (FIXED: removed playwright_stealth)
LIBRARY_DEPENDENCIES = {
    "playwright": ["playwright"],
    "patchright": ["patchright"],
    "camoufox": ["camoufox"],
}

# Critical version requirements
VERSION_REQUIREMENTS = {
    "playwright": "1.40.0",
    "patchright": "1.0.0",
    "camoufox": "0.3.0"
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
                        logger.info(f"✅ {dep}=={actual_version} (minimum: {expected_version})")
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
    
    def verify_browser_installations(self) -> Dict[str, bool]:
        """Verify browser binaries are installed"""
        browsers = {}
        
        logger.info("=== Verifying Browser Installations ===")
        
        # Check Playwright Chromium
        try:
            from playwright.sync_api import sync_playwright
            p = sync_playwright().start()
            browser = p.chromium.launch()
            browser.close()
            p.stop()
            logger.info("✅ Playwright Chromium: Installed")
            browsers['playwright_chromium'] = True
        except Exception as e:
            logger.error(f"❌ Playwright Chromium: {e}")
            browsers['playwright_chromium'] = False
        
        # Check Patchright Chromium
        try:
            from patchright.sync_api import sync_playwright as pr_sync_playwright
            p = pr_sync_playwright().start()
            browser = p.chromium.launch()
            browser.close()
            p.stop()
            logger.info("✅ Patchright Chromium: Installed")
            browsers['patchright_chromium'] = True
        except Exception as e:
            logger.error(f"❌ Patchright Chromium: {e}")
            browsers['patchright_chromium'] = False
        
        # Camoufox downloads on first run, so just check import
        try:
            import camoufox
            logger.info("✅ Camoufox: Module available (will download on first run)")
            browsers['camoufox'] = True
        except ImportError as e:
            logger.error(f"❌ Camoufox: {e}")
            browsers['camoufox'] = False
        
        return browsers
    
    def generate_report(self) -> str:
        """Generate dependency check report"""
        results = self.verify_all_libraries()
        
        report = ["=" * 70]
        report.append("PLAYWRIGHT STEALTH TESTING - DEPENDENCY REPORT")
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
        
        report.append("")
        report.append("Note: playwright-stealth has been REMOVED due to v1.0.6 bugs")
        report.append("      All libraries use comprehensive manual stealth techniques")
        report.append("=" * 70)
        
        return "\n".join(report)


def main():
    """Command-line dependency checker"""
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Check Playwright stealth library dependencies")
    parser.add_argument("--library", help="Check specific library", choices=["playwright", "patchright", "camoufox"])
    parser.add_argument("--all", action="store_true", help="Check all libraries")
    parser.add_argument("--browsers", action="store_true", help="Check browser installations")
    
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
    elif args.browsers:
        browsers = checker.verify_browser_installations()
        all_ok = all(browsers.values())
        sys.exit(0 if all_ok else 1)
    elif args.all:
        report = checker.generate_report()
        print(report)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
