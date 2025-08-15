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
        print(f"Warning: Recording functionality not available: {e}")
        recording_available = False
        
    if missing_deps:
        print("❌ Missing required dependencies:")
        for dep in missing_deps:
            print(f"   {dep}")
        print("\n💡 Install dependencies:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
        
    return recording_available

def setup_signal_handlers(server_instance):
    """Set up graceful shutdown signal handlers"""
    def signal_handler(sig, frame):
        print(f"\n🛑 Received signal {sig}, shutting down gracefully...")
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
                print("🚀 Starting with full recording support")
                from src.core.app import TutorialMakerApp
                self.app = TutorialMakerApp(debug_mode=self.args.debug)
                self.app.web_mode = True
                self.server = self.app.web_server
                self.server.port = self.args.port
            else:
                print("📖 Starting in view-only mode")
                from src.core.storage import TutorialStorage
                from src.web.server import TutorialWebServer
                storage = TutorialStorage()
                self.server = TutorialWebServer(storage, port=self.args.port)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create server: {e}")
            return False
    
    
    def run(self):
        """Run the server"""
        print("=" * 60)
        print("🎯 TutorialMaker Unified Web Server")
        print("=" * 60)
        
        # Show configuration
        recording = "Full" if self.recording_available else "View-only"
        print(f"🎬 Recording: {recording}")
        print(f"🌐 Port: {self.args.port}")
        print("")
        
        # Create server
        if not self.create_server():
            print("❌ Failed to create server")
            return 1
        
        # Set up signal handlers
        setup_signal_handlers(self)
        
        # Start server
        try:
            open_browser = not self.args.no_browser
            url = self.server.start(open_browser=open_browser)
            
            print(f"✅ Server running at: {url}")
            print("")
            print("🏭 Production Features:")
            print("  • Optimized performance")
            print("  • Stable operation")  
            print("  • Memory efficient")
            print("")
            print("⌨️  Press Ctrl+C to stop server")
            print("=" * 60)
            
            # Keep server running
            try:
                while self.server.running:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
                
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return 1
        
        finally:
            self.shutdown()
        
        return 0
    
    def shutdown(self):
        """Clean shutdown"""
        print("\n🧹 Shutting down server...")
        
        if self.server and hasattr(self.server, 'stop'):
            self.server.stop()
            print("✅ Web server stopped")
        
        if self.app and hasattr(self.app, 'shutdown'):
            self.app.shutdown()
            print("✅ App shutdown complete")
        
        print("👋 Server stopped")

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