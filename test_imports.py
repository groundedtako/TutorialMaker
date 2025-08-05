#!/usr/bin/env python3
"""
Test individual imports to find which one triggers the macOS version check
"""

print("Testing imports one by one...")

try:
    print("1. Testing tkinter...")
    import tkinter as tk
    print("   ✓ tkinter works")
except Exception as e:
    print(f"   ✗ tkinter failed: {e}")

try:
    print("2. Testing threading...")
    import threading
    print("   ✓ threading works")
except Exception as e:
    print(f"   ✗ threading failed: {e}")

try:
    print("3. Testing pathlib...")
    from pathlib import Path
    print("   ✓ pathlib works")
except Exception as e:
    print(f"   ✗ pathlib failed: {e}")

try:
    print("4. Testing src.core.capture...")
    from src.core.capture import ScreenCapture
    print("   ✓ src.core.capture works")
except Exception as e:
    print(f"   ✗ src.core.capture failed: {e}")

try:
    print("5. Testing src.core.events...")
    from src.core.events import EventMonitor
    print("   ✓ src.core.events works")
except Exception as e:
    print(f"   ✗ src.core.events failed: {e}")

try:
    print("6. Testing src.core.ocr...")
    from src.core.ocr import OCREngine
    print("   ✓ src.core.ocr works")
except Exception as e:
    print(f"   ✗ src.core.ocr failed: {e}")

try:
    print("7. Testing src.core.storage...")
    from src.core.storage import TutorialStorage
    print("   ✓ src.core.storage works")
except Exception as e:
    print(f"   ✗ src.core.storage failed: {e}")

try:
    print("8. Testing src.core.exporters...")
    from src.core.exporters import TutorialExporter
    print("   ✓ src.core.exporters works")
except Exception as e:
    print(f"   ✗ src.core.exporters failed: {e}")

try:
    print("9. Testing src.web.server...")
    from src.web.server import TutorialWebServer
    print("   ✓ src.web.server works")
except Exception as e:
    print(f"   ✗ src.web.server failed: {e}")

try:
    print("10. Testing src.core.app...")
    from src.core.app import TutorialMakerApp
    print("   ✓ src.core.app works")
except Exception as e:
    print(f"   ✗ src.core.app failed: {e}")

print("Import test complete!")