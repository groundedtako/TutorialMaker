#!/usr/bin/env python3
"""
Start the TutorialMaker web server with recording support (safe mode)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    # Try importing with mock OCR first
    import sys
    import os
    
    # Set environment variable to use mock mode
    os.environ['TUTORIAL_MAKER_MOCK_MODE'] = '1'
    
    from src.core.app import TutorialMakerApp
    FULL_MODE = True
    print("Full recording mode available")
except Exception as e:
    print(f"Warning: Could not import full app ({e})")
    print("Starting in limited mode without recording support")
    try:
        from src.core.storage import TutorialStorage
        from src.web.server import TutorialWebServer
        FULL_MODE = False
    except Exception as e2:
        print(f"Critical error: Could not start server ({e2})")
        sys.exit(1)

def main():
    if FULL_MODE:
        print("Starting TutorialMaker Web Server with full recording support...")
        
        # Initialize full app instance (includes recording capabilities)
        app = TutorialMakerApp(debug_mode=False)
        server = app.web_server
        server.port = 5001
    else:
        print("Starting TutorialMaker Web Server (view-only mode)...")
        
        # Initialize storage and server without recording
        storage = TutorialStorage()
        server = TutorialWebServer(storage, port=5001)
    
    # Start server
    try:
        url = server.start(open_browser=True)
        print(f"Server running at: {url}")
        print("Press Ctrl+C to stop the server")
        
        # Keep the main thread alive
        import time
        while server.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop()
        if FULL_MODE:
            app.shutdown()
        print("Server stopped.")

if __name__ == "__main__":
    main()