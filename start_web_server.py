#!/usr/bin/env python3
"""
Start the TutorialMaker web server for editing tutorials
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.app import TutorialMakerApp

def main():
    print("Starting TutorialMaker Web Server with full recording support...")
    
    # Initialize full app instance (includes recording capabilities)
    app = TutorialMakerApp(debug_mode=False)
    server = app.web_server
    server.port = 5001
    
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
        print("Server stopped.")

if __name__ == "__main__":
    main()