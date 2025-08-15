"""
Screen Selection Dialog
Allows users to select which monitor to record on, similar to Zoom's screen sharing dialog
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, List
from PIL import Image, ImageTk

from ..core.capture import ScreenCapture


class ScreenSelectorDialog:
    """Dialog for selecting which screen/monitor to record"""
    
    def __init__(self, parent: tk.Widget, screen_capture: ScreenCapture):
        self.parent = parent
        self.screen_capture = screen_capture
        self.selected_monitor = None
        self.dialog = None
        self.thumbnails = {}
        
    def show(self) -> Optional[int]:
        """
        Show the screen selection dialog
        Returns the selected monitor ID or None if cancelled
        """
        # Create modal dialog
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Select Screen to Record")
        # Initial size - will be adjusted after content loads
        self.dialog.geometry("600x400")
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Create widgets
        self._create_widgets()
        
        # Load screen previews
        self._load_screen_previews()
        
        # Wait for dialog to close
        self.dialog.wait_window()
        
        return self.selected_monitor
    
    def _center_dialog(self):
        """Center dialog on parent window"""
        self.dialog.update_idletasks()
        
        # Get parent window position and size
        if hasattr(self.parent, 'winfo_x'):
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
        else:
            # Fallback to screen center
            parent_x = self.dialog.winfo_screenwidth() // 4
            parent_y = self.dialog.winfo_screenheight() // 4
            parent_width = self.dialog.winfo_screenwidth() // 2
            parent_height = self.dialog.winfo_screenheight() // 2
        
        # Calculate center position
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_label = ttk.Label(main_frame, 
                                text="Choose which screen to record:",
                                font=('Helvetica', 12, 'bold'))
        header_label.pack(pady=(0, 20))
        
        # Screen selection frame
        self.screens_frame = ttk.Frame(main_frame)
        self.screens_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Buttons
        ttk.Button(button_frame, text="Cancel", 
                  command=self._on_cancel).pack(side=tk.RIGHT, padx=(10, 0))
        
        self.select_btn = ttk.Button(button_frame, text="Select", 
                                    command=self._on_select, state='disabled')
        self.select_btn.pack(side=tk.RIGHT)
        
        # Loading label
        self.loading_label = ttk.Label(self.screens_frame, 
                                      text="Loading screen previews...",
                                      font=('Helvetica', 10))
        self.loading_label.pack(expand=True)
    
    def _load_screen_previews(self):
        """Load screen preview thumbnails"""
        try:
            # Get screen info
            screen_info = self.screen_capture.get_screen_info()
            monitors = screen_info.get('monitors', [])
            
            if not monitors:
                self._show_no_screens_message()
                return
            
            # Generate thumbnails for each monitor
            thumbnails = {}
            for monitor in monitors:
                try:
                    # Capture monitor screenshot
                    screenshot = self.screen_capture.capture_full_screen(monitor_id=monitor['id'])
                    if screenshot:
                        # Create thumbnail (200x150 max)
                        thumbnail = self._create_thumbnail(screenshot, max_size=(200, 150))
                        thumbnails[monitor['id']] = {
                            'image': thumbnail,
                            'monitor': monitor,
                            'screenshot': screenshot
                        }
                except Exception as e:
                    print(f"Failed to capture monitor {monitor['id']}: {e}")
            
            # Update UI directly (no threading needed)
            self._display_screen_options(thumbnails)
            
        except Exception as e:
            print(f"Error loading screen previews: {e}")
            self._show_error_message()
    
    def _create_thumbnail(self, image: Image.Image, max_size: tuple) -> ImageTk.PhotoImage:
        """Create a thumbnail from an image"""
        # Calculate thumbnail size maintaining aspect ratio
        img_width, img_height = image.size
        max_width, max_height = max_size
        
        # Calculate scaling factor
        scale = min(max_width / img_width, max_height / img_height)
        
        # Calculate new size
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Resize image
        thumbnail = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        return ImageTk.PhotoImage(thumbnail)
    
    def _display_screen_options(self, thumbnails: Dict):
        """Display screen selection options"""
        # Clear loading message
        self.loading_label.destroy()
        
        if not thumbnails:
            self._show_no_screens_message()
            return
        
        # Store thumbnails to prevent garbage collection
        self.thumbnails = thumbnails
        
        # Create grid of screen options
        row = 0
        col = 0
        max_cols = 2
        
        self.screen_vars = {}
        
        for monitor_id, data in thumbnails.items():
            monitor = data['monitor']
            thumbnail = data['image']
            
            # Create frame for this screen option
            screen_frame = ttk.LabelFrame(self.screens_frame, 
                                         text=f"Monitor {monitor_id}", 
                                         padding="10")
            screen_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Configure grid weights
            self.screens_frame.columnconfigure(col, weight=1)
            self.screens_frame.rowconfigure(row, weight=1)
            
            # Radio button for selection
            var = tk.BooleanVar()
            self.screen_vars[monitor_id] = var
            
            radio = ttk.Radiobutton(screen_frame, 
                                   variable=var,
                                   value=True,
                                   command=lambda mid=monitor_id: self._on_screen_selected(mid))
            radio.pack(anchor=tk.W)
            
            # Thumbnail image
            img_label = ttk.Label(screen_frame, image=thumbnail)
            img_label.pack(pady=(5, 5))
            
            # Screen info
            info_text = f"{monitor['width']}x{monitor['height']}"
            if monitor.get('left', 0) != 0 or monitor.get('top', 0) != 0:
                info_text += f" at ({monitor['left']}, {monitor['top']})"
            
            info_label = ttk.Label(screen_frame, text=info_text, 
                                  font=('Helvetica', 9), foreground='gray')
            info_label.pack()
            
            # Make clicking on frame select this option
            for widget in [screen_frame, img_label, info_label]:
                widget.bind("<Button-1>", lambda e, mid=monitor_id: self._on_screen_clicked(mid))
            
            # Move to next position
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Select primary monitor by default
        if 1 in self.screen_vars:
            self._on_screen_selected(1)
        
        # Auto-size dialog to fit content
        self.dialog.after(100, self._auto_size_dialog)
    
    def _on_screen_clicked(self, monitor_id: int):
        """Handle clicking on a screen option"""
        self._on_screen_selected(monitor_id)
    
    def _on_screen_selected(self, monitor_id: int):
        """Handle screen selection"""
        # Clear other selections
        for mid, var in self.screen_vars.items():
            var.set(mid == monitor_id)
        
        self.selected_monitor = monitor_id
        self.select_btn.config(state='normal')
    
    def _show_no_screens_message(self):
        """Show message when no screens are available"""
        self.loading_label.config(text="No screens available for recording")
        
        # Auto-select primary monitor as fallback
        self.selected_monitor = 1
        self.select_btn.config(state='normal')
    
    def _show_error_message(self):
        """Show error message"""
        self.loading_label.config(text="Error loading screen previews")
        
        # Auto-select primary monitor as fallback
        self.selected_monitor = 1
        self.select_btn.config(state='normal')
    
    def _on_select(self):
        """Handle select button click"""
        self.dialog.destroy()
    
    def _auto_size_dialog(self):
        """Automatically size dialog to fit content"""
        if not self.dialog:
            return
        
        try:
            # Update to get accurate measurements
            self.dialog.update_idletasks()
            
            # Get required size from main frame
            main_frame = None
            for child in self.dialog.winfo_children():
                if isinstance(child, ttk.Frame):
                    main_frame = child
                    break
            
            if main_frame:
                main_frame.update_idletasks()
                
                # Calculate required size with padding
                req_width = main_frame.winfo_reqwidth() + 40
                req_height = main_frame.winfo_reqheight() + 80  # Extra for title bar and buttons
                
                # Set reasonable bounds
                min_width, max_width = 500, 1000
                min_height, max_height = 400, 800
                
                # Constrain to bounds
                final_width = max(min_width, min(max_width, req_width))
                final_height = max(min_height, min(max_height, req_height))
                
                # Apply new size
                self.dialog.geometry(f"{final_width}x{final_height}")
                
                # Re-center after sizing
                self.dialog.after(50, self._center_dialog)
                
        except Exception as e:
            print(f"Error auto-sizing screen selector: {e}")
    
    def _on_cancel(self):
        """Handle cancel button click"""
        self.selected_monitor = None
        self.dialog.destroy()


def show_screen_selector(parent: tk.Widget, screen_capture: ScreenCapture) -> Optional[int]:
    """
    Convenience function to show screen selector dialog
    Returns selected monitor ID or None if cancelled
    """
    dialog = ScreenSelectorDialog(parent, screen_capture)
    return dialog.show()