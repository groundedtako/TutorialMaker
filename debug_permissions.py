#!/usr/bin/env python3
"""
Debug script to test event monitoring permissions on macOS
"""

import sys
import platform
from src.core.events import EventMonitor, PYNPUT_AVAILABLE

def test_permissions():
    print("=== Tutorial Maker Permission Test ===")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print()
    
    print(f"pynput available: {PYNPUT_AVAILABLE}")
    
    if not PYNPUT_AVAILABLE:
        print("❌ pynput is not installed or not working")
        return False
    
    print("\n=== Testing Event Monitor ===")
    
    # Create event monitor
    monitor = EventMonitor()
    
    def on_click(event):
        print(f"✓ Mouse click captured: ({event.x}, {event.y}) {event.button}")
    
    def on_key(event):
        print(f"✓ Key press captured: {event.key}")
    
    monitor.set_mouse_callback(on_click)
    monitor.set_keyboard_callback(on_key)
    
    print("Starting event monitoring...")
    success = monitor.start_monitoring()
    
    print(f"Monitoring started: {success}")
    print(f"Mouse access: {monitor.has_mouse_access}")
    print(f"Keyboard access: {monitor.has_keyboard_access}")
    
    if success:
        print("\n✓ Event monitoring is working!")
        print("Try clicking or typing to test event capture...")
        print("Press Ctrl+C to stop")
        
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
            monitor.stop_monitoring()
            return True
    else:
        print("\n❌ Event monitoring failed to start")
        print("\nPossible solutions:")
        print("1. Grant accessibility permissions to Terminal/Python in System Settings")
        print("2. Try running with sudo (not recommended)")
        print("3. Check if other security software is blocking access")
        return False

if __name__ == "__main__":
    test_permissions()