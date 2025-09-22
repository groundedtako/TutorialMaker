#!/usr/bin/env python3
"""
Unified TutorialMaker Web Server
Single server with optional development mode, recording support, and live reloading
"""

import sys
import os
import signal
import argparse
from pathlib import Path

from main import logger

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="TutorialMaker Web Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 server.py                    # Production mode
  python3 server.py --port 8080        # Custom port
  python3 server.py --view-only        # View-only mode (no recording)
        """
    )
    
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5001,
        help='Server port (default: 5001)'
    )
    
    parser.add_argument(
        '--view-only',
        action='store_true', 
        help='View-only mode (no recording capabilities)'
    )
    
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Don\'t open browser automatically'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode (Flask debug + OCR debug images with click markers)'
    )
    
    return parser.parse_args()

def check_dependencies():
    """Check if required dependencies are available"""
    missing_deps = []
    
    # Core dependencies
    try:
        from src.core.storage import TutorialStorage
        from src.web.server import TutorialWebServer
    except ImportError as e:
        missing_deps.append(f"Core modules: {e}")
    
    # Recording dependencies  
    try:
        from src.core.app import TutorialMakerApp
        recording_available = True
    except ImportError as e:
        logger.warning("Recording functionality not available: {e}")
        recording_available = False
        
    if missing_deps:
        # Build complete error message
        error_msg = "❌ Missing required dependencies:\n"
        for dep in missing_deps:
            error_msg += f"   {dep}\n"
        error_msg += "\n💡 Install dependencies:\n"
        error_msg += "   pip install -r requirements.txt"
        
        logger.error(error_msg)
        sys.exit(1)
        
    return recording_available

def setup_signal_handlers(server_instance):
    """Set up graceful shutdown signal handlers"""
    def signal_handler(sig, frame):
        logger.info(f"\n🛑 Received signal {sig}, shutting down gracefully...")
        if hasattr(server_instance, 'shutdown'):
            server_instance.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

class UnifiedServer:
    """Unified server that handles all modes"""
    
    def __init__(self, args, recording_available):
        self.args = args
        self.recording_available = recording_available and not args.view_only
        self.app = None
        self.server = None
        
    def create_server(self):
        """Create the appropriate server instance"""
        try:
            # Set environment for mock mode if needed
            if not self.recording_available:
                os.environ['TUTORIAL_MAKER_MOCK_MODE'] = '1'
            
            if self.recording_available:
                logger.info("🚀 Starting with full recording support")
                from src.core.app import TutorialMakerApp
                self.app = TutorialMakerApp(debug_mode=self.args.debug)
                self.app.web_mode = True
                self.server = self.app.web_server
                self.server.port = self.args.port
            else:
                logger.info("📖 Starting in view-only mode")
                from src.core.storage import TutorialStorage
                from src.web.server import TutorialWebServer
                storage = TutorialStorage()
                self.server = TutorialWebServer(storage, port=self.args.port)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create server: {e}")
            return False
    
    
    def run(self):
        """Run the server"""
        # Build server startup info message
        startup_msg = "=" * 60 + "\n"
        startup_msg += "🎯 TutorialMaker Unified Web Server\n"
        startup_msg += "=" * 60 + "\n\n"
        
        # Show configuration
        recording = "Full" if self.recording_available else "View-only"
        startup_msg += f"🎬 Recording: {recording}\n"
        startup_msg += f"🌐 Port: {self.args.port}"
        
        logger.info(startup_msg)
        
        # Create server
        if not self.create_server():
            logger.error("❌ Failed to create server")
            return 1
        
        # Set up signal handlers
        setup_signal_handlers(self)
        
        # Start server
        try:
            open_browser = not self.args.no_browser
            url = self.server.start(open_browser=open_browser)
            
            # Build server running info message
            running_msg = f"✅ Server running at: {url}\n\n"
            running_msg += "🏭 Production Features:\n"
            running_msg += "  • Optimized performance\n"
            running_msg += "  • Stable operation\n"
            running_msg += "  • Memory efficient\n\n"
            running_msg += "⌨️  Press Ctrl+C to stop server\n"
            running_msg += "=" * 60
            
            logger.info(running_msg)
            
            # Keep server running
            try:
                while self.server.running:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
                
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            return 1
        
        finally:
            self.shutdown()
        
        return 0
    
    def shutdown(self):
        """Clean shutdown"""
        logger.info("\n🧹 Shutting down server...")
        
        if self.server and hasattr(self.server, 'stop'):
            self.server.stop()
            logger.info("✅ Web server stopped")
        
        if self.app and hasattr(self.app, 'shutdown'):
            self.app.shutdown()
            logger.info("✅ App shutdown complete")
        
        logger.info("👋 Server stopped")
fo
def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Check dependencies
    recording_available = check_dependencies()
    
    # Create and run server
    server = UnifiedServer(args, recording_available)
    return server.run()

if __name__ == "__main__":
    sys.exit(main())