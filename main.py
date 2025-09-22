#!/usr/bin/env python3
"""
TutorialMaker - Privacy-focused tutorial maker
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

from src.core.logger import get_logger, set_debug_mode, set_log_level

# Module-level logger
logger = get_logger('main')

def signal_handler(sig, frame):
    """Handle graceful shutdown on Ctrl+C"""
    logger.info("\nShutting down gracefully...")
    sys.exit(0)

def start_web_interface(args):
    """Start the web interface"""
    logger.info("Starting web interface...")
    logger.info(f"Server will be available at http://localhost:{args.port}")
    if not args.no_browser:
        logger.info("Browser will open automatically")
    print()
    logger.info("Press Ctrl+C to stop the server")
    print()
    
    # Import and run the server
    import sys
    import os
    
    # Add server arguments to sys.argv for server.py to parse
    server_args = ['server.py', '--port', str(args.port)]
    if args.debug:
        server_args.append('--debug')
    if args.no_browser:
        server_args.append('--no-browser')
    
    # Store original argv and replace it
    original_argv = sys.argv[:]
    sys.argv = server_args
    
    try:
        # Import and run server main function
        from server import main as server_main
        server_main()
    finally:
        # Restore original argv
        sys.argv = original_argv

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description="TutorialMaker - Privacy-focused Tutorial Maker")
    parser.add_argument("--debug", action="store_true", 
                      help="Enable debug mode with precise click location markers")
    parser.add_argument("--log-level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                      default='INFO', help="Set logging level (default: INFO)")
    parser.add_argument("--cli", action="store_true",
                      help="Use command-line interface")
    parser.add_argument("--web", action="store_true",
                      help="Force web interface (default is desktop GUI)")
    parser.add_argument("--gui", "--desktop", action="store_true",
                      help="Force desktop GUI interface (default)")
    parser.add_argument("--port", type=int, default=5001,
                      help="Web server port (default: 5001)")
    parser.add_argument("--no-browser", action="store_true",
                      help="Don't open browser automatically")
    args = parser.parse_args()
    
    # Configure logging level based on arguments
    if args.debug:
        # Debug mode overrides log-level to DEBUG
        set_debug_mode(True)
        actual_level = 'DEBUG'
    else:
        # Use specified log level
        set_log_level(args.log_level)
        actual_level = args.log_level
    
    logger.info("TutorialMaker - Privacy-focused Tutorial Maker")
    logger.info("===========================================")
    logger.info(f"Logging level: {actual_level}")
    if args.debug:
        logger.info("DEBUG MODE ENABLED - Click locations will be marked with red dots")
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        if args.cli:
            # Use CLI interface
            logger.info("Starting CLI interface...")
            logger.info("Type 'help' for available commands")
            print()
            
            from src.core.app import TutorialMakerApp
            app = TutorialMakerApp(debug_mode=args.debug)
            app.run()
        elif args.web:
            # Force web interface
            start_web_interface(args)
        else:
            # Default: Try desktop GUI first, fallback to web
            logger.info("Attempting to start desktop GUI interface...")
            try:
                logger.debug("Importing desktop GUI...")
                from src.gui.desktop_app import TutorialMakerDesktopApp
                logger.debug("Desktop GUI imported successfully")
                
                logger.info("Starting desktop GUI interface...")
                if args.debug:
                    logger.info("DEBUG MODE ENABLED - Click locations will be marked with red dots")
                print()
                
                desktop_app = TutorialMakerDesktopApp(debug_mode=args.debug)
                if args.debug:
                    logger.debug("Desktop app created, initializing...")
                desktop_app.initialize()
                if args.debug:
                    logger.debug("Desktop app initialized, running...")
                desktop_app.run()
                
                logger.warning(f"Desktop GUI not available: {e}")
                logger.warning("Falling back to web interface...")
                print()
                start_web_interface(args)
            except Exception as e:
                logger.error(f"Desktop GUI failed to start: {e}")
                logger.warning("Falling back to web interface...")
                print()
                start_web_interface(args)
                
    except ImportError as e:
        logger.error(f"Error importing core modules: {e}")
        logger.error("Please ensure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()