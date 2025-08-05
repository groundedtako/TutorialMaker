#!/usr/bin/env python3
"""
Minimal GUI test to isolate the macOS version check issue
"""

print("Starting minimal GUI test...")

try:
    print("1. Importing tkinter...")
    import tkinter as tk
    print("   ✓ tkinter imported")
    
    print("2. Creating root window...")
    root = tk.Tk()
    print("   ✓ root window created")
    
    print("3. Setting window properties...")
    root.title("Test Window")
    root.geometry("300x200")
    print("   ✓ window properties set")
    
    print("4. Creating a simple widget...")
    label = tk.Label(root, text="Hello World!")
    label.pack()
    print("   ✓ widget created")
    
    print("5. Starting mainloop...")
    root.mainloop()
    print("   ✓ mainloop finished")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()