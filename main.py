#!/usr/bin/env python3
"""
Scribe Local - Privacy-focused tutorial maker
Main entry point for the application
"""

import sys
import os
import argparse
import signal
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def signal_handler(sig, frame):
    """Handle graceful shutdown on Ctrl+C"""
    print("\nShutting down gracefully...")
    sys.exit(0)

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description="Scribe Local - Privacy-focused Tutorial Maker")
    parser.add_argument("--debug", action="store_true", 
                      help="Enable debug mode with precise click location markers")
    args = parser.parse_args()
    
    print("Scribe Local - Privacy-focused Tutorial Maker")
    print("===========================================")
    if args.debug:
        print("DEBUG MODE ENABLED - Click locations will be marked with red dots")
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Import and run the main application
        from src.core.app import TutorialMakerApp
        app = TutorialMakerApp(debug_mode=args.debug)
        app.run()
    except ImportError as e:
        print(f"Error importing core modules: {e}")
        print("Please ensure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()