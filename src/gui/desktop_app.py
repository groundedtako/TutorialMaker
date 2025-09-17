"""
Desktop GUI application for TutorialMaker
Combines main window, system tray, and global hotkeys
"""

import tkinter as tk
from tkinter import messagebox
import sys
import threading
import atexit
from typing import Optional

from ..core.app import TutorialMakerApp
from .main_window import MainWindow
from .system_tray import SystemTrayManager


class TutorialMakerDesktopApp:
    """Main desktop application class"""
    
    def __init__(self, debug_mode: bool = False, start_minimized: bool = False):
        self.debug_mode = debug_mode
        self.start_minimized = start_minimized
        
        # Core components
        self.core_app: Optional[TutorialMakerApp] = None
        self.main_window: Optional[MainWindow] = None
        self.tray_manager: Optional[SystemTrayManager] = None
        
        # Global hotkey manager
        self.hotkey_manager: Optional['GlobalHotkeyManager'] = None
        
        # Application state
        self.running = False
        
        # Register cleanup
        atexit.register(self.cleanup)
    
    def initialize(self):
        """Initialize all components"""
        try:
            # Initialize core app
            self.core_app = TutorialMakerApp(debug_mode=self.debug_mode)
            
            # Initialize main window
            self.main_window = MainWindow(self.core_app)
            
            # Initialize system tray
            self.tray_manager = SystemTrayManager(self.core_app, self.main_window)
            
            # Initialize global hotkeys
            self._setup_hotkeys()
            
            print("SUCCESS: TutorialMaker Desktop initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize TutorialMaker: {e}"
            print(f"ERROR: {error_msg}")
            if hasattr(tk, 'Tk'):
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Initialization Error", error_msg)
                root.destroy()
            sys.exit(1)
    
    def _setup_hotkeys(self):
        """Set up global hotkeys"""
        try:
            from .hotkeys import GlobalHotkeyManager
            self.hotkey_manager = GlobalHotkeyManager(self.core_app, self.main_window)
            
            # Default hotkeys (will be normalized to ctrl on Windows)
            hotkeys = {
                'ctrl+shift+r': self._hotkey_toggle_recording,
                'ctrl+shift+p': self._hotkey_pause_resume,
                'ctrl+shift+n': self._hotkey_new_tutorial,
                'ctrl+shift+h': self._hotkey_toggle_floating_window,
            }
            
            for hotkey, callback in hotkeys.items():
                try:
                    self.hotkey_manager.register_hotkey(hotkey, callback)
                except Exception as e:
                    print(f"Warning: Failed to register hotkey {hotkey}: {e}")
            
        except (ImportError, Exception) as e:
            print(f"Warning: Global hotkeys not available: {e}")
            print("The application will work normally without global hotkeys.")
            self.hotkey_manager = None
    
    def _hotkey_toggle_recording(self):
        """Hotkey callback: Toggle recording"""
        try:
            if not self.core_app.current_session:
                # No session - show main window to create one
                self.main_window.show()
                return
            
            status = self.core_app.get_current_session_status()
            if status.get('is_recording'):
                self.core_app.stop_recording()
            else:
                self.core_app.start_recording()
        except Exception as e:
            print(f"Hotkey error: {e}")
    
    def _hotkey_pause_resume(self):
        """Hotkey callback: Pause/resume recording"""
        try:
            if not self.core_app.current_session:
                return
            
            status = self.core_app.get_current_session_status()
            current_status = status.get('status')
            
            if current_status == 'recording':
                self.core_app.pause_recording()
            elif current_status == 'paused':
                self.core_app.resume_recording()
        except Exception as e:
            print(f"Hotkey error: {e}")
    
    def _hotkey_new_tutorial(self):
        """Hotkey callback: New tutorial"""
        try:
            self.main_window.show()
            # Focus on tutorial name entry
            self.main_window.tutorial_name_var.set("")
        except Exception as e:
            print(f"Hotkey error: {e}")
    
    def _hotkey_toggle_floating_window(self):
        """Hotkey callback: Hide/show floating recording controls"""
        try:
            # Check if we have a recording window
            if self.main_window.recording_window:
                if self.main_window.recording_window.is_visible:
                    self.main_window.recording_window.hide()
                else:
                    self.main_window.recording_window.show()
            else:
                # No floating window exists - this usually means not recording
                # Show main window instead
                self.main_window.show()
        except Exception as e:
            print(f"Hotkey error: {e}")
    
    def run(self):
        """Run the desktop application"""
        self.running = True
        
        try:
            # Start system tray
            if self.tray_manager and self.tray_manager.is_available():
                self.tray_manager.start()
                print("SUCCESS: System tray started")
            else:
                print("WARNING: System tray not available")
            
            # Start hotkey manager
            if self.hotkey_manager:
                self.hotkey_manager.start()
                print("SUCCESS: Global hotkeys registered")
            
            # Show or hide main window based on settings
            if not self.start_minimized:
                self.main_window.show()
            else:
                self.main_window.hide()
                if self.tray_manager and self.tray_manager.is_available():
                    print("Started minimized to system tray")
                else:
                    # If no tray, must show window
                    self.main_window.show()
                    print("INFO: System tray not available, showing main window")
            
            # Start main event loop
            print("TutorialMaker Desktop is ready!")
            self.main_window.run()
            
        except KeyboardInterrupt:
            print("\\nShutting down...")
        except Exception as e:
            print(f"ERROR: Application error: {e}")
        finally:
            self.cleanup()
    
    def show_main_window(self):
        """Show main window"""
        if self.main_window:
            self.main_window.show()
    
    def quit(self):
        """Quit the application"""
        self.cleanup()
        if self.main_window:
            self.main_window.root.quit()
    
    def cleanup(self):
        """Clean up resources"""
        if not self.running:
            return
        
        self.running = False
        
        try:
            # Stop hotkeys
            if self.hotkey_manager:
                self.hotkey_manager.stop()
            
            # Stop system tray
            if self.tray_manager:
                self.tray_manager.stop()
            
            # Stop core app
            if self.core_app:
                self.core_app.shutdown()
            
            print("SUCCESS: Cleanup completed")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")


def main():
    """Main entry point for desktop application"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TutorialMaker Desktop Application")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--minimized", action="store_true", help="Start minimized to system tray")
    parser.add_argument("--no-tray", action="store_true", help="Disable system tray")
    
    args = parser.parse_args()
    
    # Create and run app
    app = TutorialMakerDesktopApp(
        debug_mode=args.debug,
        start_minimized=args.minimized and not args.no_tray
    )
    
    app.initialize()
    app.run()


if __name__ == "__main__":
    main()