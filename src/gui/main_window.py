"""
Main GUI window for TutorialMaker
Provides the primary interface for managing tutorials and settings
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import webbrowser
from typing import Optional, Dict, Any
from datetime import datetime

from ..core.app import TutorialMakerApp
from ..core.session_manager import RecordingSession


class MainWindow:
    """Main application window"""
    
    def __init__(self, app: TutorialMakerApp):
        self.app = app
        self.root = tk.Tk()
        self.recording_window: Optional['RecordingControlWindow'] = None
        
        self._setup_window()
        self._create_widgets()
        self._setup_bindings()
        
    def _setup_window(self):
        """Configure main window properties"""
        self.root.title("TutorialMaker")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Configure DPI awareness for Windows
        try:
            # Try to enable DPI awareness on Windows
            import sys
            if sys.platform.startswith('win'):
                try:
                    from ctypes import windll
                    windll.shcore.SetProcessDpiAwareness(1)
                except:
                    pass  # Fail silently if not available
        except:
            pass
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Modern look
        
        # Configure Treeview row height for better readability
        # This fixes the "squished" appearance on Windows with different DPI settings
        row_height = self._calculate_optimal_row_height()
        self.style.configure('Treeview', rowheight=row_height)
        self.style.configure('Treeview.Heading', font=('Helvetica', 9, 'bold'))
        self.style.configure('Treeview', font=('Helvetica', 9))
        
        # Add some padding and styling improvements
        self.style.configure('Treeview', background='white', fieldbackground='white')
        self.style.map('Treeview', background=[('selected', '#0078d4')])
        self.style.configure('Treeview.Heading', background='#f0f0f0', relief='flat')
        
        # Configure colors
        self.root.configure(bg='#f8f9fa')
        
    def _create_widgets(self):
        """Create main window widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="TutorialMaker", 
                               font=('Helvetica', 24, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        version_label = ttk.Label(header_frame, text="v1.0", 
                                 font=('Helvetica', 10), foreground='gray')
        version_label.pack(side=tk.RIGHT, pady=(10, 0))
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Recording Controls", padding="15")
        control_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        # Recording status
        self.status_var = tk.StringVar(value="Ready to record")
        status_label = ttk.Label(control_frame, textvariable=self.status_var, 
                                font=('Helvetica', 12, 'bold'))
        status_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Tutorial name entry
        ttk.Label(control_frame, text="Tutorial Name:").grid(row=1, column=0, sticky="w")
        self.tutorial_name_var = tk.StringVar()
        tutorial_entry = ttk.Entry(control_frame, textvariable=self.tutorial_name_var, width=30)
        tutorial_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0))
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(15, 0))
        
        self.new_btn = ttk.Button(button_frame, text="New Tutorial", 
                                 command=self._new_tutorial, style='Accent.TButton')
        self.new_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.start_btn = ttk.Button(button_frame, text="Start Recording", 
                                   command=self._start_recording, state='disabled')
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop Recording", 
                                  command=self._stop_recording, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Keystroke filtering toggle
        filter_frame = ttk.Frame(control_frame)
        filter_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0), sticky="w")
        
        self.keystroke_filter_var = tk.BooleanVar()
        self.keystroke_filter_check = ttk.Checkbutton(
            filter_frame, 
            text="Filter keystrokes (clicks only)",
            variable=self.keystroke_filter_var,
            command=self._toggle_keystroke_filtering
        )
        self.keystroke_filter_check.pack(side=tk.LEFT)
        
        # Tutorials list
        list_frame = ttk.LabelFrame(main_frame, text="Your Tutorials", padding="15")
        list_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Treeview for tutorials
        columns = ('Name', 'Steps', 'Duration', 'Created', 'Status')
        self.tutorial_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        # Configure columns with better spacing and minimum widths
        self.tutorial_tree.heading('Name', text='Tutorial Name')
        self.tutorial_tree.heading('Steps', text='Steps')
        self.tutorial_tree.heading('Duration', text='Duration (s)')
        self.tutorial_tree.heading('Created', text='Created')
        self.tutorial_tree.heading('Status', text='Status')
        
        # Set column properties with minimum widths for better scaling
        self.tutorial_tree.column('Name', width=280, minwidth=200, stretch=True)
        self.tutorial_tree.column('Steps', width=80, minwidth=60, anchor='center', stretch=False)
        self.tutorial_tree.column('Duration', width=110, minwidth=90, anchor='center', stretch=False)
        self.tutorial_tree.column('Created', width=160, minwidth=120, stretch=False)
        self.tutorial_tree.column('Status', width=100, minwidth=80, anchor='center', stretch=False)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tutorial_tree.yview)
        self.tutorial_tree.configure(yscrollcommand=scrollbar.set)
        
        self.tutorial_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Context menu for tutorials
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Edit in Browser", command=self._edit_tutorial)
        self.context_menu.add_command(label="Export Tutorial", command=self._export_tutorial)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete Tutorial", command=self._delete_tutorial)
        
        # Bottom toolbar
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        
        ttk.Button(toolbar_frame, text="Refresh List", 
                  command=self._refresh_tutorials).pack(side=tk.LEFT)
        
        ttk.Button(toolbar_frame, text="Export All", 
                  command=self._export_all_tutorials).pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(toolbar_frame, text="Delete All", 
                  command=self._delete_all_tutorials).pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(toolbar_frame, text="Open Web Editor", 
                  command=self._open_web_editor).pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(toolbar_frame, text="Settings", 
                  command=self._open_settings).pack(side=tk.RIGHT)
        
        # Load initial data
        self._refresh_tutorials()
    
    def _calculate_optimal_row_height(self):
        """Calculate optimal row height based on system DPI and font size"""
        try:
            # Get the font metrics for the default font
            test_font = ('Helvetica', 9)
            
            # Create a temporary label to measure font height
            temp_label = tk.Label(self.root, font=test_font, text='Ag')
            temp_label.update_idletasks()
            font_height = temp_label.winfo_reqheight()
            temp_label.destroy()
            
            # Calculate row height with some padding
            # Use at least 25 pixels, but scale with font if needed
            row_height = max(25, font_height + 10)
            
            # On Windows with high DPI, might need extra height
            import sys
            if sys.platform.startswith('win'):
                try:
                    # Try to detect DPI scaling
                    import tkinter.font as tkfont
                    default_font = tkfont.nametofont("TkDefaultFont")
                    font_size = default_font['size']
                    if font_size > 9:  # Likely high DPI
                        row_height = max(row_height, int(font_size * 2.8))
                except:
                    pass
            
            return min(row_height, 40)  # Cap at 40 pixels
            
        except Exception:
            # Fallback to a safe default
            return 25
    
    def _on_window_configure(self, event):
        """Handle window configuration changes (including DPI changes)"""
        # Only respond to root window events, not child widgets
        if event.widget == self.root:
            # Check if we need to adjust row height due to DPI changes
            current_height = self.style.lookup('Treeview', 'rowheight')
            optimal_height = self._calculate_optimal_row_height()
            
            # Only update if there's a significant difference
            if abs(int(current_height or 25) - optimal_height) > 3:
                self.style.configure('Treeview', rowheight=optimal_height)
        
    def _setup_bindings(self):
        """Set up event bindings"""
        # Context menu for tutorial list
        self.tutorial_tree.bind("<Button-2>", self._show_context_menu)  # Right click on macOS
        self.tutorial_tree.bind("<Button-3>", self._show_context_menu)  # Right click on Windows/Linux
        
        # Double click to edit
        self.tutorial_tree.bind("<Double-1>", lambda e: self._edit_tutorial())
        
        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Bind to window configuration changes (helps with DPI changes)
        self.root.bind("<Configure>", self._on_window_configure)
        
    def _new_tutorial(self):
        """Create a new tutorial"""
        name = self.tutorial_name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a tutorial name")
            return
            
        try:
            tutorial_id = self.app.new_tutorial(name)
            self.status_var.set(f"Created: {name}")
            self.start_btn.config(state='normal')
            self.new_btn.config(state='disabled')
            self._refresh_tutorials()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create tutorial: {e}")
    
    def _start_recording(self):
        """Start recording the current tutorial"""
        try:
            success = self.app.start_recording()
            if success:
                self.status_var.set("🔴 Recording...")
                self.start_btn.config(state='disabled')
                self.stop_btn.config(state='normal')
                self.new_btn.config(state='disabled')
                
                # Show recording control window
                self._show_recording_controls()
            else:
                messagebox.showerror("Error", "Failed to start recording")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start recording: {e}")
    
    def _stop_recording(self):
        """Stop recording and finalize tutorial"""
        try:
            # Get recording stats before stopping (so we can show them)
            current_status = self.app.get_current_session_status()
            final_step_count = current_status.get('step_count', 0)
            tutorial_name = current_status.get('title', 'Unknown')
            
            tutorial_id = self.app.stop_recording()
            if tutorial_id:
                self.status_var.set(f"✅ Recording completed: {final_step_count} steps captured")
                self._reset_controls()
                self._refresh_tutorials()
                
                # Show final stats in recording controls before hiding
                if self.recording_window:
                    self.recording_window.show_completion_stats(final_step_count, tutorial_name)
                    # Delay hiding the window so user can see final stats
                    self.root.after(3000, self.recording_window.hide)  # Hide after 3 seconds
                    
                # Ask if user wants to edit
                if messagebox.askyesno("Recording Complete", 
                                     f"Tutorial '{tutorial_name}' recorded successfully!\n"
                                     f"Captured {final_step_count} steps.\n\n"
                                     "Would you like to edit it in the web browser?"):
                    self._open_tutorial_in_browser(tutorial_id)
            else:
                messagebox.showerror("Error", "Failed to stop recording")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop recording: {e}")
    
    def _reset_controls(self):
        """Reset controls to initial state"""
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='disabled')
        self.new_btn.config(state='normal')
        self.tutorial_name_var.set("")
    
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
    
    def _show_recording_controls(self):
        """Show floating recording control window"""
        try:
            if not self.recording_window:
                from .recording_controls import RecordingControlWindow
                self.recording_window = RecordingControlWindow(self.app, self)
            self.recording_window.show()
        except Exception as e:
            print(f"Warning: Could not show floating controls: {e}")
            print("Recording will continue normally, controls available in main window.")
    
    def _refresh_tutorials(self):
        """Refresh the tutorials list"""
        # Clear existing items
        for item in self.tutorial_tree.get_children():
            self.tutorial_tree.delete(item)
        
        # Load tutorials
        try:
            tutorials = self.app.list_tutorials()
            for tutorial in tutorials:
                created_date = datetime.fromtimestamp(tutorial.created_at).strftime('%Y-%m-%d %H:%M')
                self.tutorial_tree.insert('', 'end', values=(
                    tutorial.title,
                    tutorial.step_count,
                    f"{tutorial.duration:.1f}",
                    created_date,
                    tutorial.status.title()
                ), tags=(tutorial.tutorial_id,))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tutorials: {e}")
    
    def _show_context_menu(self, event):
        """Show context menu for tutorial list"""
        item = self.tutorial_tree.selection()[0] if self.tutorial_tree.selection() else None
        if item:
            self.context_menu.post(event.x_root, event.y_root)
    
    def _edit_tutorial(self):
        """Edit selected tutorial in browser"""
        selection = self.tutorial_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a tutorial to edit")
            return
        
        item = selection[0]
        tutorial_id = self.tutorial_tree.item(item, 'tags')[0]
        self._open_tutorial_in_browser(tutorial_id)
    
    def _export_tutorial(self):
        """Export selected tutorial"""
        selection = self.tutorial_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a tutorial to export")
            return
        
        item = selection[0]
        tutorial_id = self.tutorial_tree.item(item, 'tags')[0]
        
        try:
            results = self.app.export_tutorial(tutorial_id, ['html', 'word', 'pdf'])
            message = "Tutorial exported successfully:\\n"
            for format_name, path in results.items():
                if path and not path.startswith('Error:'):
                    message += f"• {format_name.upper()}: {path}\\n"
            messagebox.showinfo("Export Complete", message)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export tutorial: {e}")
    
    def _delete_tutorial(self):
        """Delete selected tutorial"""
        selection = self.tutorial_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a tutorial to delete")
            return
        
        item = selection[0]
        tutorial_id = self.tutorial_tree.item(item, 'tags')[0]
        tutorial_name = self.tutorial_tree.item(item, 'values')[0]
        
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete '{tutorial_name}'?\\n\\n"
                              "This action cannot be undone."):
            try:
                success = self.app.delete_tutorial(tutorial_id)
                if success:
                    self._refresh_tutorials()
                    messagebox.showinfo("Success", "Tutorial deleted successfully")
                else:
                    messagebox.showerror("Error", "Failed to delete tutorial")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete tutorial: {e}")
    
    def _open_web_editor(self):
        """Open web editor in browser"""
        try:
            url = self.app.start_web_server()
            if url:
                webbrowser.open(url)
            else:
                messagebox.showerror("Error", "Failed to start web server")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open web editor: {e}")
    
    def _open_tutorial_in_browser(self, tutorial_id: str):
        """Open specific tutorial in browser"""
        try:
            url = self.app.start_web_server()
            if url:
                tutorial_url = f"{url}/tutorial/{tutorial_id}"
                webbrowser.open(tutorial_url)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open tutorial: {e}")
    
    def _open_settings(self):
        """Open settings dialog"""
        try:
            from .settings_dialog import SettingsDialog
            dialog = SettingsDialog(self.root, self.app)
            dialog.show()
        except Exception as e:
            print(f"Warning: Could not open settings: {e}")
            messagebox.showwarning("Settings", "Settings dialog not available in this version.")
    
    def _export_all_tutorials(self):
        """Export all tutorials to multiple formats"""
        tutorials = self.app.list_tutorials()
        
        if not tutorials:
            messagebox.showinfo("No Tutorials", "No tutorials found to export.")
            return
        
        # Show format selection dialog
        from tkinter import simpledialog
        
        format_dialog = tk.Toplevel(self.root)
        format_dialog.title("Export All Tutorials")
        format_dialog.geometry("400x300")
        format_dialog.transient(self.root)
        format_dialog.grab_set()
        
        # Center the dialog
        format_dialog.update_idletasks()
        x = (format_dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (format_dialog.winfo_screenheight() // 2) - (300 // 2)
        format_dialog.geometry(f"400x300+{x}+{y}")
        
        # Dialog content
        tk.Label(format_dialog, text=f"Export {len(tutorials)} tutorial(s) to:", 
                font=('Arial', 12, 'bold')).pack(pady=20)
        
        # Format checkboxes
        format_vars = {}
        formats = [('HTML', 'html'), ('Word Document', 'word'), ('PDF', 'pdf'), ('Markdown', 'markdown')]
        
        for display_name, format_key in formats:
            var = tk.BooleanVar(value=format_key in ['html', 'word'])  # Default to HTML and Word
            format_vars[format_key] = var
            tk.Checkbutton(format_dialog, text=display_name, variable=var, 
                          font=('Arial', 10)).pack(pady=5)
        
        # Buttons
        button_frame = tk.Frame(format_dialog)
        button_frame.pack(pady=20)
        
        result = {'cancelled': True}
        
        def on_export():
            selected_formats = [k for k, v in format_vars.items() if v.get()]
            if not selected_formats:
                messagebox.showerror("No Formats", "Please select at least one export format.")
                return
            result['formats'] = selected_formats
            result['cancelled'] = False
            format_dialog.destroy()
        
        def on_cancel():
            format_dialog.destroy()
        
        tk.Button(button_frame, text="Export", command=on_export, bg='#28a745', 
                 fg='white', padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Cancel", command=on_cancel, padx=20, pady=5).pack(side=tk.LEFT)
        
        # Wait for dialog
        self.root.wait_window(format_dialog)
        
        if result['cancelled']:
            return
        
        # Perform export
        try:
            formats = result['formats']
            format_list = ', '.join(f.upper() for f in formats)
            
            # Show progress dialog
            progress = tk.Toplevel(self.root)
            progress.title("Exporting...")
            progress.geometry("350x150")
            progress.transient(self.root)
            progress.grab_set()
            progress.resizable(False, False)
            
            # Center progress dialog
            progress.update_idletasks()
            x = (progress.winfo_screenwidth() // 2) - (350 // 2)
            y = (progress.winfo_screenheight() // 2) - (150 // 2)
            progress.geometry(f"350x150+{x}+{y}")
            
            tk.Label(progress, text=f"Exporting {len(tutorials)} tutorials to {format_list}...", 
                    font=('Arial', 10)).pack(pady=20)
            tk.Label(progress, text="Please wait, this may take a while.", 
                    font=('Arial', 9, 'italic')).pack()
            
            progress.update()
            
            def export_thread():
                try:
                    results = self.app.export_all_tutorials(formats, max_workers=3)
                    
                    # Close progress dialog
                    progress.destroy()
                    
                    # Show results
                    successful = sum(1 for r in results.values() if isinstance(r, dict) and 'error' not in r)
                    total = len(results)
                    failed = total - successful
                    
                    message = f"Export completed:\n\n"
                    message += f"Total tutorials: {total}\n"
                    message += f"Successfully exported: {successful}\n"
                    message += f"Failed: {failed}\n\n"
                    message += f"Formats: {format_list}"
                    
                    messagebox.showinfo("Export Complete", message)
                    
                except Exception as e:
                    progress.destroy()
                    messagebox.showerror("Export Failed", f"Failed to export tutorials: {e}")
            
            # Run export in background thread
            threading.Thread(target=export_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start export: {e}")
    
    def _delete_all_tutorials(self):
        """Delete all tutorials with confirmation"""
        tutorials = self.app.list_tutorials()
        
        if not tutorials:
            messagebox.showinfo("No Tutorials", "No tutorials found to delete.")
            return
        
        # Double confirmation for safety
        if not messagebox.askyesno("Confirm Delete All", 
                                  f"Are you sure you want to delete ALL {len(tutorials)} tutorial(s)?\n\n"
                                  "This action cannot be undone and will permanently remove:\n"
                                  "• All tutorial data and metadata\n"
                                  "• All screenshots and recordings\n"
                                  "• All exported files (HTML, Word, PDF, etc.)\n\n"
                                  "This is a destructive operation!"):
            return
        
        # Final confirmation
        if not messagebox.askyesno("Final Warning", 
                                  "This is your FINAL warning.\n\n"
                                  f"ALL {len(tutorials)} tutorials will be permanently deleted.\n\n"
                                  "Are you absolutely certain you want to continue?"):
            return
        
        try:
            # Show progress
            progress = tk.Toplevel(self.root)
            progress.title("Deleting Tutorials...")
            progress.geometry("300x100")
            progress.transient(self.root)
            progress.grab_set()
            progress.resizable(False, False)
            
            # Center progress dialog
            progress.update_idletasks()
            x = (progress.winfo_screenwidth() // 2) - (300 // 2)
            y = (progress.winfo_screenheight() // 2) - (100 // 2)
            progress.geometry(f"300x100+{x}+{y}")
            
            tk.Label(progress, text=f"Deleting {len(tutorials)} tutorials...", 
                    font=('Arial', 10)).pack(pady=30)
            progress.update()
            
            # Delete all tutorials
            results = self.app.delete_all_tutorials()
            
            progress.destroy()
            
            # Show results
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            failed = total - successful
            
            message = f"Delete operation completed:\n\n"
            message += f"Total tutorials: {total}\n"
            message += f"Successfully deleted: {successful}\n"
            message += f"Failed: {failed}"
            
            # Refresh tutorial list
            self._refresh_tutorials()
            
            messagebox.showinfo("Delete Complete", message)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete tutorials: {e}")
    
    def _on_closing(self):
        """Handle window closing"""
        if self.app.current_session and self.app.current_session.is_recording():
            if messagebox.askyesno("Recording in Progress", 
                                 "A recording is in progress. Stop recording before closing?"):
                self._stop_recording()
            else:
                return
        
        # Hide recording controls
        if self.recording_window:
            self.recording_window.hide()
        
        self.root.destroy()
    
    def show(self):
        """Show the main window"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def hide(self):
        """Hide the main window"""
        self.root.withdraw()
    
    def run(self):
        """Run the main window event loop"""
        self.root.mainloop()