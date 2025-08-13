"""
System tray integration for TutorialMaker
Provides always-available recording controls and quick access
"""

import threading
import webbrowser
from typing import Optional, Callable
import sys
import os

try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    print("Warning: pystray not available. System tray functionality will be limited.")

from ..core.app import TutorialMakerApp


class SystemTrayManager:
    """Manages system tray icon and menu"""
    
    def __init__(self, app: TutorialMakerApp, main_window=None):
        self.app = app
        self.main_window = main_window
        self.icon: Optional[pystray.Icon] = None
        self.running = False
        
        if not PYSTRAY_AVAILABLE:
            print("System tray not available. Please install: pip install pystray pillow")
            return
        
        self._create_icon()
        self._setup_menu()
    
    def _create_icon(self):
        """Create system tray icon"""
        if not PYSTRAY_AVAILABLE:
            return
        
        # Create a simple icon programmatically
        icon_image = self._create_icon_image()
        
        self.icon = pystray.Icon(
            "TutorialMaker",
            icon_image,
            "TutorialMaker - Screen Recording Made Easy"
        )
    
    def _create_icon_image(self, recording=False):
        """Create icon image (red when recording, blue when idle)"""
        # Create a 64x64 image
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Choose color based on recording state
        color = '#FF0000' if recording else '#007BFF'  # Red when recording, blue when idle
        
        # Draw a circle with a camera icon
        margin = 8
        draw.ellipse([margin, margin, size-margin, size-margin], fill=color, outline='white', width=2)
        
        # Draw camera lens (simple rectangle)
        lens_size = size // 3
        lens_x = (size - lens_size) // 2
        lens_y = (size - lens_size) // 2
        draw.rectangle([lens_x, lens_y, lens_x + lens_size, lens_y + lens_size], 
                      fill='white', outline=color, width=2)
        
        return image
    
    def _setup_menu(self):
        """Set up system tray context menu"""
        if not PYSTRAY_AVAILABLE:
            return
        
        def create_menu():
            # Get current session status
            status = self.app.get_current_session_status()
            is_recording = status.get('is_recording', False)
            
            menu_items = []
            
            # Recording controls
            if not is_recording:
                menu_items.extend([
                    pystray.MenuItem("🎬 New Tutorial", self._new_tutorial),
                    pystray.MenuItem("▶️ Start Recording", self._start_recording, 
                                   enabled=bool(self.app.current_session)),
                ])
            else:
                menu_items.extend([
                    pystray.MenuItem("⏹️ Stop Recording", self._stop_recording),
                    pystray.MenuItem("⏸️ Pause Recording", self._pause_recording),
                ])
            
            menu_items.extend([
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("📊 Show Main Window", self._show_main_window),
                pystray.MenuItem("🎛️ Show Floating Controls", self._show_floating_controls),
                pystray.MenuItem("🌐 Open Web Editor", self._open_web_editor),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("⚙️ Settings", self._open_settings),
                pystray.MenuItem("ℹ️ About", self._show_about),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("🚪 Quit", self._quit_application),
            ])
            
            return pystray.Menu(*menu_items)
        
        if self.icon:
            self.icon.menu = create_menu()
    
    def _new_tutorial(self, icon=None, item=None):
        """Create new tutorial from tray"""
        # Simple dialog for tutorial name
        import tkinter as tk
        from tkinter import simpledialog, messagebox
        
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        
        name = simpledialog.askstring("New Tutorial", "Enter tutorial name:")
        if name and name.strip():
            try:
                tutorial_id = self.app.new_tutorial(name.strip())
                messagebox.showinfo("Success", f"Tutorial '{name}' created!\\nClick 'Start Recording' to begin.")
                self._update_icon()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create tutorial: {e}")
        
        root.destroy()
    
    def _start_recording(self, icon=None, item=None):
        """Start recording from tray"""
        try:
            success = self.app.start_recording()
            if success:
                self._update_icon(recording=True)
                self._setup_menu()  # Refresh menu
                # Show notification (platform-specific)
                self._show_notification("Recording Started", "Click the tray icon to stop recording")
            else:
                import tkinter.messagebox as messagebox
                messagebox.showerror("Error", "Failed to start recording")
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", f"Failed to start recording: {e}")
    
    def _stop_recording(self, icon=None, item=None):
        """Stop recording from tray"""
        try:
            tutorial_id = self.app.stop_recording()
            if tutorial_id:
                self._update_icon(recording=False)
                self._setup_menu()  # Refresh menu
                self._show_notification("Recording Complete", "Tutorial exported successfully!")
                
                # Ask if user wants to edit
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                
                if messagebox.askyesno("Recording Complete", 
                                     "Tutorial recorded and exported successfully!\\n\\n"
                                     "Would you like to edit it in the web browser?"):
                    self._open_tutorial_in_browser(tutorial_id)
                
                root.destroy()
            else:
                import tkinter.messagebox as messagebox
                messagebox.showerror("Error", "Failed to stop recording")
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", f"Failed to stop recording: {e}")
    
    def _pause_recording(self, icon=None, item=None):
        """Pause/resume recording from tray"""
        try:
            status = self.app.get_current_session_status()
            if status.get('status') == 'recording':
                self.app.pause_recording()
                self._show_notification("Recording Paused", "Click to resume recording")
            elif status.get('status') == 'paused':
                self.app.resume_recording()
                self._show_notification("Recording Resumed", "Recording is active again")
            
            self._setup_menu()  # Refresh menu
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", f"Failed to pause/resume recording: {e}")
    
    def _show_main_window(self, icon=None, item=None):
        """Show main application window"""
        if self.main_window:
            self.main_window.show()
    
    def _show_floating_controls(self, icon=None, item=None):
        """Show floating recording controls"""
        try:
            if self.main_window:
                self.main_window._show_recording_controls()
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", f"Failed to show floating controls: {e}")
    
    def _open_web_editor(self, icon=None, item=None):
        """Open web editor in browser"""
        try:
            url = self.app.start_web_server()
            if url:
                webbrowser.open(url)
            else:
                import tkinter.messagebox as messagebox
                messagebox.showerror("Error", "Failed to start web server")
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", f"Failed to open web editor: {e}")
    
    def _open_tutorial_in_browser(self, tutorial_id: str):
        """Open specific tutorial in browser"""
        try:
            url = self.app.start_web_server()
            if url:
                tutorial_url = f"{url}/tutorial/{tutorial_id}"
                webbrowser.open(tutorial_url)
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", f"Failed to open tutorial: {e}")
    
    def _open_settings(self, icon=None, item=None):
        """Open settings dialog"""
        if self.main_window:
            self.main_window.show()
            # Settings will be opened from main window
    
    def _show_about(self, icon=None, item=None):
        """Show about dialog"""
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()
        
        about_text = """TutorialMaker v1.0
        
A privacy-focused screen recording tool for creating step-by-step tutorials.

Features:
• Local-only processing (no cloud required)
• Cross-platform screen capture
• Smart click detection with OCR
• Multiple export formats (HTML, Word, PDF)
• Web-based editing interface

Created with ❤️ for documentation and training teams."""
        
        messagebox.showinfo("About TutorialMaker", about_text)
        root.destroy()
    
    def _quit_application(self, icon=None, item=None):
        """Quit the application"""
        # Stop any recording first
        if self.app.current_session and self.app.current_session.is_recording():
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()
            
            if messagebox.askyesno("Recording in Progress", 
                                 "A recording is in progress. Stop recording before quitting?"):
                self.app.stop_recording()
            else:
                root.destroy()
                return
            
            root.destroy()
        
        self.stop()
        if self.main_window:
            self.main_window.root.quit()
    
    def _update_icon(self, recording=False):
        """Update tray icon based on recording state"""
        if not PYSTRAY_AVAILABLE or not self.icon:
            return
        
        new_image = self._create_icon_image(recording)
        self.icon.icon = new_image
    
    def _show_notification(self, title: str, message: str):
        """Show system notification"""
        if not PYSTRAY_AVAILABLE or not self.icon:
            return
        
        # Use pystray's notification system
        try:
            self.icon.notify(message, title)
        except Exception as e:
            print(f"Failed to show notification: {e}")
    
    def start(self):
        """Start the system tray"""
        if not PYSTRAY_AVAILABLE or not self.icon:
            print("System tray not available")
            return
        
        self.running = True
        
        def run_tray():
            try:
                self.icon.run()
            except Exception as e:
                print(f"System tray error: {e}")
        
        # Run in separate thread
        tray_thread = threading.Thread(target=run_tray, daemon=True)
        tray_thread.start()
    
    def stop(self):
        """Stop the system tray"""
        self.running = False
        if self.icon:
            self.icon.stop()
    
    def is_available(self) -> bool:
        """Check if system tray is available"""
        return PYSTRAY_AVAILABLE and self.icon is not None