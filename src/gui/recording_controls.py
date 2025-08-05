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
        self.window.geometry("320x140")
        self.window.resizable(False, False)
        
        # Make window stay on top
        self.window.attributes('-topmost', True)
        
        # Remove window decorations on some platforms
        try:
            self.window.attributes('-toolwindow', True)  # Windows
        except:
            pass
        
        # Position window in top-right corner
        self.window.geometry("+{}+{}".format(
            self.window.winfo_screenwidth() - 320,
            50
        ))
        
        self._create_widgets()
        self._setup_bindings()
        
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
        
        self.minimize_btn = ttk.Button(button_frame, text="—", 
                                      command=self._minimize, width=3)
        self.minimize_btn.pack(side=tk.RIGHT)
    
    def _setup_bindings(self):
        """Set up event bindings"""
        if not self.window:
            return
        
        # Double-click to minimize/restore
        self.window.bind("<Double-Button-1>", lambda e: self._minimize())
        
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
    
    def _minimize(self):
        """Minimize to a small indicator"""
        if self.window:
            self.window.geometry("100x30")
            # Hide all widgets except indicator and minimize button
            for widget in self.window.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if not isinstance(child, tk.Canvas) and child != self.minimize_btn:
                            child.pack_forget()
            
            self.minimize_btn.config(text="□", command=self._restore)
    
    def _restore(self):
        """Restore full control window"""
        if self.window:
            self.window.geometry("320x140")
            self._create_widgets()  # Recreate all widgets
            self.minimize_btn.config(text="—", command=self._minimize)
    
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
            self.status_var.set("✅ Completed")
            
            # Truncate tutorial name if too long
            if len(tutorial_name) > 25:
                tutorial_name = tutorial_name[:22] + "..."
            self.tutorial_name_var.set(tutorial_name)
            
            # Stop blinking indicator
            self._draw_indicator(recording=False)
            
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