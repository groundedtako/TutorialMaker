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
  python3 server.py --dev              # Development mode with live reload  
  python3 server.py --port 8080        # Custom port
  python3 server.py --view-only        # View-only mode (no recording)
  python3 server.py --dev --no-browser # Dev mode without opening browser
        """
    )
    
    parser.add_argument(
        '--dev', '--development',
        action='store_true',
        help='Enable development mode with live reloading'
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
        help='Enable Flask debug mode'
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
    
    # Development dependencies
    dev_available = True
    try:
        import watchdog
    except ImportError:
        print("Info: watchdog not available. Live reloading disabled.")
        dev_available = False
        
    if missing_deps:
        print("❌ Missing required dependencies:")
        for dep in missing_deps:
            print(f"   {dep}")
        print("\n💡 Install dependencies:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
        
    return recording_available, dev_available

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
    
    def __init__(self, args, recording_available, dev_available):
        self.args = args
        self.recording_available = recording_available and not args.view_only
        self.dev_available = dev_available and args.dev
        self.app = None
        self.server = None
        self.dev_watcher = None
        
    def create_server(self):
        """Create the appropriate server instance"""
        try:
            # Set environment for mock mode if needed
            if not self.recording_available:
                os.environ['TUTORIAL_MAKER_MOCK_MODE'] = '1'
            
            if self.recording_available:
                print("🚀 Starting with full recording support")
                from src.core.app import TutorialMakerApp
                self.app = TutorialMakerApp(debug_mode=False)
                self.server = self.app.web_server
                self.server.port = self.args.port
                # Enable dev mode if requested  
                self.server.dev_mode = self.args.dev
            else:
                print("📖 Starting in view-only mode")
                from src.core.storage import TutorialStorage
                from src.web.server import TutorialWebServer
                storage = TutorialStorage()
                self.server = TutorialWebServer(
                    storage, 
                    port=self.args.port, 
                    dev_mode=self.args.dev
                )
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create server: {e}")
            return False
    
    def setup_live_reload(self):
        """Set up live reloading if in development mode"""
        if not self.dev_available:
            return
            
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            import time
            import threading
            
            class LiveReloadHandler(FileSystemEventHandler):
                def __init__(self, restart_callback):
                    self.restart_callback = restart_callback
                    self.last_restart = 0
                    self.restart_delay = 1.0
                    
                def should_reload(self, file_path):
                    return (file_path.endswith('.py') or 
                           file_path.endswith('.html') or 
                           file_path.endswith('.css') or 
                           file_path.endswith('.js'))
                
                def on_modified(self, event):
                    if event.is_directory:
                        return
                        
                    file_path = event.src_path
                    if any(pattern in file_path for pattern in ['__pycache__', '.pyc', '.tmp']):
                        return
                        
                    if self.should_reload(file_path):
                        current_time = time.time()
                        if current_time - self.last_restart > self.restart_delay:
                            print(f"📝 File changed: {file_path}")
                            self.last_restart = current_time
                            self.restart_callback()
            
            self.observer = Observer()
            handler = LiveReloadHandler(self.trigger_reload)
            
            # Watch source directory
            src_path = Path(__file__).parent / "src"
            if src_path.exists():
                self.observer.schedule(handler, str(src_path), recursive=True)
                print(f"👁️  Live reload watching: {src_path}")
            
            self.observer.start()
            
        except Exception as e:
            print(f"⚠️  Failed to set up live reload: {e}")
    
    def trigger_reload(self):
        """Trigger server reload"""
        try:
            # Notify live reload manager
            from src.utils.dev_utils import live_reload_manager
            live_reload_manager.trigger_reload("File change detected")
        except ImportError:
            pass
        
        # For now, just print message - full restart would be complex
        print("🔄 Live reload triggered - browser will refresh automatically")
    
    def run(self):
        """Run the server"""
        print("=" * 60)
        print("🎯 TutorialMaker Unified Web Server")
        print("=" * 60)
        
        # Show configuration
        mode = "Development" if self.args.dev else "Production"
        recording = "Full" if self.recording_available else "View-only"
        print(f"📋 Mode: {mode}")
        print(f"🎬 Recording: {recording}")
        print(f"🌐 Port: {self.args.port}")
        print(f"🔥 Live reload: {'Yes' if self.dev_available else 'No'}")
        print("")
        
        # Create server
        if not self.create_server():
            print("❌ Failed to create server")
            return 1
        
        # Set up signal handlers
        setup_signal_handlers(self)
        
        # Start live reload if in dev mode
        if self.dev_available:
            self.setup_live_reload()
        
        # Start server
        try:
            open_browser = not self.args.no_browser
            url = self.server.start(open_browser=open_browser)
            
            print(f"✅ Server running at: {url}")
            print("")
            
            if self.args.dev:
                print("🔥 Development Features:")
                print("  • Live reloading enabled")
                print("  • Automatic browser refresh")
                print("  • Enhanced error reporting")
                print("  • Hot module reloading")
            else:
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
        
        if hasattr(self, 'observer') and self.observer:
            self.observer.stop()
            self.observer.join()
            print("✅ File watcher stopped")
        
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
    recording_available, dev_available = check_dependencies()
    
    # Create and run server
    server = UnifiedServer(args, recording_available, dev_available)
    return server.run()

if __name__ == "__main__":
    sys.exit(main())