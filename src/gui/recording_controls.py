"""
Floating recording control window
Provides minimal, always-on-top controls during recording
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, TYPE_CHECKING
import time

if TYPE_CHECKING:
    from .main_window import MainWindow
    from ..core.app import TutorialMakerApp


class RecordingControlWindow:
    """Floating control panel for recording sessions"""
    
    def __init__(self, app: 'TutorialMakerApp', main_window: 'MainWindow'):
        self.app = app
        self.main_window = main_window
        self.window: Optional[tk.Toplevel] = None
        self.is_visible = False
        self.debug_mode = getattr(app, 'debug_mode', False)
        
        # Control variables
        self.step_count_var = tk.StringVar(value="0")
        self.duration_var = tk.StringVar(value="00:00")
        self.status_var = tk.StringVar(value="Recording")
        self.tutorial_name_var = tk.StringVar(value="No Tutorial")
        
        # Update timer
        self.update_timer: Optional[str] = None
        
    def _create_window(self):
        """Create the floating control window"""
        if self.window:
            return
        
        self.window = tk.Toplevel(self.main_window.root)
        self.window.title("Recording Controls")
        # Initial size - will be adjusted after widgets are created
        self.window.geometry("320x180")
        self.window.resizable(True, True)
        
        # Make window stay on top
        self.window.attributes('-topmost', True)
        
        # Remove window decorations on some platforms
        try:
            self.window.attributes('-toolwindow', True)  # Windows
        except:
            pass
        
        self._create_widgets()
        self._setup_bindings()
        
        # Dynamically size window to fit content
        self._auto_size_window()
        
        # Position window in top-right corner after sizing
        self._position_window()
        
        # Start update timer
        self._start_updates()
    
    def _create_widgets(self):
        """Create control widgets"""
        if not self.window:
            return
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status indicator
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Recording indicator (red dot)
        self.indicator_canvas = tk.Canvas(status_frame, width=12, height=12, 
                                        highlightthickness=0, bg='white')
        self.indicator_canvas.pack(side=tk.LEFT, padx=(0, 5))
        self._draw_indicator()
        
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                               font=('Helvetica', 10, 'bold'))
        status_label.pack(side=tk.LEFT)
        
        # Tutorial name frame
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(name_frame, text="Tutorial:", font=('Helvetica', 9)).pack(side=tk.LEFT)
        tutorial_name_label = ttk.Label(name_frame, textvariable=self.tutorial_name_var, 
                                      font=('Helvetica', 9, 'bold'), foreground='blue')
        tutorial_name_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Stats frame
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(stats_frame, text="Steps:").pack(side=tk.LEFT)
        ttk.Label(stats_frame, textvariable=self.step_count_var, 
                 font=('Helvetica', 10, 'bold')).pack(side=tk.LEFT, padx=(5, 15))
        
        ttk.Label(stats_frame, text="Duration:").pack(side=tk.LEFT)
        ttk.Label(stats_frame, textvariable=self.duration_var, 
                 font=('Helvetica', 10, 'bold')).pack(side=tk.LEFT, padx=(5, 0))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        self.pause_btn = ttk.Button(button_frame, text="Pause", 
                                   command=self._toggle_pause, width=8)
        self.pause_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop", 
                                  command=self._stop_recording, width=8)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Keystroke filtering toggle
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill=tk.X, pady=(8, 0))
        
        self.keystroke_filter_var = tk.BooleanVar()
        self.keystroke_filter_check = ttk.Checkbutton(
            filter_frame, 
            text="Filter keystrokes (clicks only)",
            variable=self.keystroke_filter_var,
            command=self._toggle_keystroke_filtering
        )
        self.keystroke_filter_check.pack(side=tk.LEFT)
        
        # Removed minimize button - users can move the panel or use system tray instead
    
    def _auto_size_window(self):
        """Automatically size window to fit all content"""
        if not self.window:
            return
        
        # Update window to calculate required size
        self.window.update_idletasks()
        
        # Get the required width and height from the main frame
        main_frame = self.window.winfo_children()[0] if self.window.winfo_children() else None
        if main_frame:
            main_frame.update_idletasks()
            
            # Get required size with some padding
            req_width = main_frame.winfo_reqwidth() + 20  # Add padding
            req_height = main_frame.winfo_reqheight() + 40  # Add padding for title bar
            
            # Set minimum and maximum sizes
            min_width, max_width = 300, 400
            min_height, max_height = 160, 300
            
            # Constrain to reasonable bounds
            final_width = max(min_width, min(max_width, req_width))
            final_height = max(min_height, min(max_height, req_height))
            
            # Apply the new size
            self.window.geometry(f"{final_width}x{final_height}")
            
            if self.debug_mode:
                print(f"Auto-sized recording controls: {final_width}x{final_height} (required: {req_width}x{req_height})")
    
    def _position_window(self):
        """Position window intelligently - on different monitor when possible"""
        if not self.window:
            return
        
        # Get window dimensions
        self.window.update_idletasks()
        window_width = self.window.winfo_width()
        
        # Try to get smart positioning based on recording monitor
        x_pos, y_pos = self._get_smart_position(window_width)
        
        self.window.geometry(f"+{x_pos}+{y_pos}")
    
    def _get_smart_position(self, window_width: int) -> tuple[int, int]:
        """Get smart position for controls - prefer different monitor than recording"""
        try:
            # Get current session and recording monitor
            current_session = getattr(self.app, 'current_session', None)
            recording_monitor = None
            
            if current_session and hasattr(current_session, 'monitor_id'):
                recording_monitor = current_session.monitor_id
                print(f"DEBUG: Recording on monitor {recording_monitor}")
            
            # Get screen info
            screen_info = self.app.screen_capture.get_screen_info()
            monitors = screen_info.get('monitors', [])
            
            if len(monitors) > 1 and recording_monitor is not None:
                # Multiple monitors - try to place on different monitor
                for i, monitor in enumerate(monitors, 1):
                    if i != recording_monitor:  # Different monitor
                        # Position on top-right of this monitor
                        monitor_x = monitor.get('x', 0)
                        monitor_width = monitor.get('width', 1920)
                        x_pos = monitor_x + monitor_width - window_width - 20
                        y_pos = monitor.get('y', 0) + 50
                        print(f"DEBUG: Placing controls on monitor {i} at ({x_pos}, {y_pos})")
                        return x_pos, y_pos
            
            # Fallback to primary monitor or single monitor
            screen_width = self.window.winfo_screenwidth()
            x_pos = screen_width - window_width - 20
            y_pos = 50
            print(f"DEBUG: Using fallback position at ({x_pos}, {y_pos})")
            return x_pos, y_pos
            
        except Exception as e:
            print(f"DEBUG: Error in smart positioning: {e}")
            # Fallback to simple positioning
            screen_width = self.window.winfo_screenwidth()
            return screen_width - window_width - 20, 50
    
    def _setup_bindings(self):
        """Set up event bindings"""
        if not self.window:
            return
        
        # Allow dragging the window
        self.window.bind("<Button-1>", self._on_window_click)
        self.window.bind("<B1-Motion>", self._on_window_drag)
        
        # Close button handling
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _draw_indicator(self, recording=True):
        """Draw recording indicator dot"""
        if not hasattr(self, 'indicator_canvas'):
            return
        
        self.indicator_canvas.delete("all")
        color = "#FF0000" if recording else "#FFA500"  # Red when recording, orange when paused
        self.indicator_canvas.create_oval(2, 2, 10, 10, fill=color, outline="")
    
    def _toggle_pause(self):
        """Toggle pause/resume recording"""
        try:
            status = self.app.get_current_session_status()
            current_status = status.get('status', 'stopped')
            
            if current_status == 'recording':
                self.app.pause_recording()
                self.pause_btn.config(text="Resume")
                self.status_var.set("Paused")
                self._draw_indicator(recording=False)
            elif current_status == 'paused':
                self.app.resume_recording()
                self.pause_btn.config(text="Pause")
                self.status_var.set("Recording")
                self._draw_indicator(recording=True)
        except Exception as e:
            print(f"Error toggling pause: {e}")
    
    def _stop_recording(self):
        """Stop recording"""
        self.main_window._stop_recording()
    
    def _on_window_click(self, event):
        """Handle window click for dragging"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def _on_window_drag(self, event):
        """Handle window dragging"""
        if hasattr(self, 'drag_start_x') and hasattr(self, 'drag_start_y'):
            x = self.window.winfo_x() + (event.x - self.drag_start_x)
            y = self.window.winfo_y() + (event.y - self.drag_start_y)
            self.window.geometry(f"+{x}+{y}")
    
    def _toggle_keystroke_filtering(self):
        """Toggle keystroke filtering on/off"""
        try:
            enabled = self.app.toggle_keystroke_filtering()
            status = "enabled" if enabled else "disabled"
            print(f"Keystroke filtering {status}")
            
            # Update checkbox to reflect actual state
            self.keystroke_filter_var.set(enabled)
            
        except Exception as e:
            print(f"Failed to toggle keystroke filtering: {e}")
            # Revert checkbox state on error
            self.keystroke_filter_var.set(not self.keystroke_filter_var.get())
    
    def _start_updates(self):
        """Start periodic updates of recording stats"""
        if self.window and self.is_visible:
            self._update_stats()
            self.update_timer = self.window.after(1000, self._start_updates)  # Update every second
    
    def _update_stats(self):
        """Update recording statistics"""
        try:
            status = self.app.get_current_session_status()
            
            if status.get('status') != 'no_session':
                # Update step count
                step_count = status.get('step_count', 0)
                self.step_count_var.set(str(step_count))
                
                # Update duration
                duration = status.get('duration', 0)
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                self.duration_var.set(f"{minutes:02d}:{seconds:02d}")
                
                # Update tutorial name
                tutorial_title = status.get('title', 'No Tutorial')
                # Truncate long titles
                if len(tutorial_title) > 25:
                    tutorial_title = tutorial_title[:22] + "..."
                self.tutorial_name_var.set(tutorial_title)
                
                # Update status
                session_status = status.get('status', 'stopped')
                if session_status == 'recording':
                    self.status_var.set("Recording")
                    self._draw_indicator(recording=True)
                elif session_status == 'paused':
                    self.status_var.set("Paused")
                    self._draw_indicator(recording=False)
        except Exception as e:
            print(f"Error updating stats: {e}")
    
    def _on_close(self):
        """Handle window close"""
        self.hide()
    
    def show(self):
        """Show the recording control window"""
        if not self.window:
            self._create_window()
        
        if self.window:
            self.window.deiconify()
            self.window.lift()
            self.is_visible = True
            
            # Ensure proper sizing when showing
            self.window.after(100, self._auto_size_window)
            self.window.after(150, self._position_window)
            
            self._start_updates()
    
    def hide(self):
        """Hide the recording control window"""
        if self.window:
            self.window.withdraw()
            self.is_visible = False
            
            # Cancel update timer
            if self.update_timer:
                self.window.after_cancel(self.update_timer)
                self.update_timer = None
    
    def show_completion_stats(self, final_step_count: int, tutorial_name: str):
        """Show final recording stats before hiding"""
        if self.window and self.is_visible:
            # Update final stats
            self.step_count_var.set(str(final_step_count))
            self.status_var.set("SUCCESS: Completed")
            
            # Truncate tutorial name if too long
            if len(tutorial_name) > 25:
                tutorial_name = tutorial_name[:22] + "..."
            self.tutorial_name_var.set(tutorial_name)
            
            # Stop blinking indicator
            self._draw_indicator(recording=False)
            
            # Adjust window size for completion message
            self.window.after(50, self._auto_size_window)
            
            # Stop updates
            if self.update_timer:
                self.window.after_cancel(self.update_timer)
                self.update_timer = None
    
    def destroy(self):
        """Destroy the recording control window"""
        if self.update_timer and self.window:
            self.window.after_cancel(self.update_timer)
        
        if self.window:
            self.window.destroy()
            self.window = None
        
        self.is_visible = False