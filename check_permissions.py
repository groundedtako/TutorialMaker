#!/usr/bin/env python3
"""
Quick permission check without interactive monitoring
"""

import sys
import platform
import time
from src.core.events import EventMonitor, PYNPUT_AVAILABLE

def quick_permission_check():
    print("=== Quick Permission Check ===")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"pynput available: {PYNPUT_AVAILABLE}")
    
    if not PYNPUT_AVAILABLE:
        print("❌ pynput not available")
        return False
    
    # Create monitor
    monitor = EventMonitor()
    
    print("Testing event monitor initialization...")
    
    # Try to start monitoring (this will test permissions)
    print("Attempting to start monitoring...")
    success = monitor.start_monitoring()
    
    print(f"Start result: {success}")
    print(f"Mouse access: {monitor.has_mouse_access}")
    print(f"Keyboard access: {monitor.has_keyboard_access}")
    print(f"Is monitoring: {monitor.is_monitoring}")
    
    # Stop immediately
    monitor.stop_monitoring()
    
    if success:
        print("✓ Permissions OK - event monitoring should work")
    else:
        print("❌ Permission issues detected")
        print("\nTo fix on macOS:")
        print("1. Open System Settings > Privacy & Security > Accessibility")
        print("2. Add Terminal (or your Python executable) to the list")
        print("3. Enable the checkbox for Terminal")
        print("4. Restart Terminal and try again")
    
    return success

if __name__ == "__main__":
    quick_permission_check()