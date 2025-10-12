#!/usr/bin/env python3
"""
GeoIP Database Setup Utility

Downloads and installs the GeoLite City database for offline IP geolocation
"""

import sys
import urllib.request
import shutil
from pathlib import Path


def download_geoip_database():
    """Download GeoIP database for offline timezone detection"""
    
    print("=" * 70)
    print("GeoIP Database Setup")
    print("=" * 70)
    print()
    
    # Create profiles directory
    profiles_dir = Path(__file__).parent / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    
    geoip_path = profiles_dir / "GeoLiteCity.dat"
    
    # Check if already exists
    if geoip_path.exists():
        size_mb = geoip_path.stat().st_size / 1024 / 1024
        print(f"✅ GeoIP database already exists: {geoip_path}")
        print(f"   Size: {size_mb:.1f} MB")
        print()
        
        response = input("Download again? (y/N): ")
        if response.lower() != 'y':
            print("Skipping download.")
            return True
        
        print("Removing existing database...")
        geoip_path.unlink()
    
    # Download database
    url = "https://github.com/mbcc2006/GeoLiteCity-data/raw/master/GeoLiteCity.dat"
    
    print(f"📥 Downloading GeoIP database...")
    print(f"   Source: {url}")
    print(f"   Target: {geoip_path}")
    print()
    
    try:
        # Download with progress
        def show_progress(block_num, block_size, total_size):
            if total_size > 0:
                downloaded = block_num * block_size
                percent = (downloaded / total_size) * 100
                mb_downloaded = downloaded / 1024 / 1024
                mb_total = total_size / 1024 / 1024
                
                # Update progress every 5%
                if block_num % 50 == 0:
                    print(f"   Progress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='\r')
        
        temp_path = geoip_path.with_suffix('.tmp')
        
        urllib.request.urlretrieve(url, temp_path, reporthook=show_progress)
        
        print()  # New line after progress
        
        # Verify download
        if temp_path.exists() and temp_path.stat().st_size > 1000000:  # At least 1MB
            shutil.move(str(temp_path), str(geoip_path))
            
            size_mb = geoip_path.stat().st_size / 1024 / 1024
            print(f"✅ Download complete!")
            print(f"   File: {geoip_path}")
            print(f"   Size: {size_mb:.1f} MB")
            print()
            
            # Test the database
            print("🧪 Testing database...")
            try:
                import pygeoip
                
                db = pygeoip.GeoIP(str(geoip_path))
                test_record = db.record_by_addr("8.8.8.8")
                
                if test_record:
                    print(f"✅ Database is working!")
                    print(f"   Test lookup (8.8.8.8): {test_record.get('city')}, {test_record.get('country_name')}")
                    print()
                    return True
                else:
                    print("❌ Database test failed - no results")
                    return False
            
            except ImportError:
                print("⚠️ pygeoip not installed - cannot test database")
                print("   Install with: pip install pygeoip")
                print()
                return True
            
            except Exception as e:
                print(f"❌ Database test failed: {e}")
                return False
        
        else:
            print("❌ Download failed or incomplete")
            temp_path.unlink(missing_ok=True)
            return False
    
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    print()
    
    missing = []
    
    # Check pygeoip
    try:
        import pygeoip
        print("✅ pygeoip installed")
    except ImportError:
        print("❌ pygeoip NOT installed")
        missing.append("pygeoip")
    
    # Check browserforge
    try:
        import browserforge
        print("✅ browserforge installed")
    except ImportError:
        print("⚠️ browserforge NOT installed (optional)")
    
    # Check playwright
    try:
        import playwright
        print("✅ playwright installed")
    except ImportError:
        print("⚠️ playwright NOT installed")
    
    print()
    
    if missing:
        print("Missing required dependencies:")
        for dep in missing:
            print(f"   pip install {dep}")
        print()
        
        response = input("Install missing dependencies now? (y/N): ")
        if response.lower() == 'y':
            import subprocess
            for dep in missing:
                print(f"Installing {dep}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print("✅ Dependencies installed")
            print()
    
    return len(missing) == 0


def main():
    """Main setup function"""
    print()
    print("🌍 Playwright Stealth - GeoIP Setup")
    print()
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    if not deps_ok:
        print("⚠️ Some dependencies are missing. Please install them first.")
        print()
    
    # Download database
    success = download_geoip_database()
    
    if success:
        print("=" * 70)
        print("✅ Setup Complete!")
        print("=" * 70)
        print()
        print("You can now use IP pre-resolution with timezone detection:")
        print()
        print("  from utils.ip_resolver import IPResolver")
        print("  from utils.timezone_manager import TimezoneManager")
        print()
        print("  resolver = IPResolver(TimezoneManager())")
        print("  resolved = await resolver.resolve_proxy(proxy_config)")
        print("  print(f'Timezone: {resolved.timezone} for IP: {resolved.ip_address}')")
        print()
        print("The GeoIP database enables fast offline timezone detection!")
        print()
    else:
        print("=" * 70)
        print("❌ Setup Failed")
        print("=" * 70)
        print()
        print("The system will fall back to online IP-API for timezone detection.")
        print("This is slower but will still work.")
        print()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
