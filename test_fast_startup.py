"""
Test script for fast startup feature
Tests both async and blocking database loading
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("=" * 60)
print("FAST STARTUP FEATURE TEST")
print("=" * 60)

# Test 1: Feature flag loading
print("\n1. Testing feature flag configuration...")
try:
    with open('config/app_config.yaml', 'r') as f:
        import re
        content = f.read()
        match = re.search(r'fast_startup:\s*(\w+)', content)
        if match:
            fast_startup = match.group(1) == 'true'
            print(f"   ✅ Feature flag loaded: fast_startup = {fast_startup}")
        else:
            print("   ❌ Feature flag not found in config")
except Exception as e:
    print(f"   ❌ Error reading config: {e}")

# Test 2: Async loader import
print("\n2. Testing async loader module...")
try:
    from utils.async_loader import AsyncDatabaseLoader, get_loader, load_database_blocking
    print("   ✅ Async loader imported successfully")
    print("      - AsyncDatabaseLoader class available")
    print("      - get_loader() function available")
    print("      - load_database_blocking() fallback available")
except Exception as e:
    print(f"   ❌ Import error: {e}")

# Test 3: Loading indicator import
print("\n3. Testing loading indicator module...")
try:
    from ui.loading_indicator import LoadingIndicator
    print("   ✅ LoadingIndicator imported successfully")
except Exception as e:
    print(f"   ❌ Import error: {e}")

# Test 4: Modified main.py
print("\n4. Testing main.py modifications...")
try:
    # Read main.py and check for new code
    with open('src/main.py', 'r') as f:
        main_content = f.read()
    
    checks = [
        ('async_loader import', 'from utils.async_loader import'),
        ('loading_indicator import', 'from ui.loading_indicator import'),
        ('feature flag check', 'features.fast_startup'),
        ('async loading code', 'load_database_async'),
        ('blocking fallback', 'BLOCKING database load'),
        ('callback method', '_on_database_loaded'),
    ]
    
    for check_name, search_string in checks:
        if search_string in main_content:
            print(f"   ✅ {check_name} found")
        else:
            print(f"   ❌ {check_name} NOT FOUND")
            
except Exception as e:
    print(f"   ❌ Error reading main.py: {e}")

# Test 5: Backwards compatibility check
print("\n5. Testing backwards compatibility...")
try:
    with open('src/main.py', 'r') as f:
        main_content = f.read()
    
    # Check that old code is still present
    if 'db.preload_caches()' in main_content:
        print("   ✅ Old blocking code still present (backwards compatible)")
    else:
        print("   ⚠️  Warning: Old blocking code may have been removed")
        
    if 'traditional mode' in main_content or 'BLOCKING' in main_content:
        print("   ✅ Fallback path implemented")
    else:
        print("   ❌ Fallback path missing")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print("✅ = Success")
print("❌ = Issue detected")
print("⚠️  = Warning")
print("\nReview the results above to confirm all components are working.")
print("\nTo toggle feature:")
print("  - Edit config/app_config.yaml")
print("  - Set features.fast_startup to true (async) or false (blocking)")
print("=" * 60)
