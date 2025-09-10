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
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')  # Modern look
        
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
        
        # Configure columns
        self.tutorial_tree.heading('Name', text='Tutorial Name')
        self.tutorial_tree.heading('Steps', text='Steps')
        self.tutorial_tree.heading('Duration', text='Duration (s)')
        self.tutorial_tree.heading('Created', text='Created')
        self.tutorial_tree.heading('Status', text='Status')
        
        self.tutorial_tree.column('Name', width=250)
        self.tutorial_tree.column('Steps', width=80, anchor='center')
        self.tutorial_tree.column('Duration', width=100, anchor='center')
        self.tutorial_tree.column('Created', width=150)
        self.tutorial_tree.column('Status', width=100, anchor='center')
        
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
        
        ttk.Button(toolbar_frame, text="Open Web Editor", 
                  command=self._open_web_editor).pack(side=tk.LEFT, padx=(10, 0))
        
        # Add Delete All button with danger styling
        delete_all_btn = ttk.Button(toolbar_frame, text="Delete All Tutorials", 
                                   command=self._delete_all_tutorials)
        delete_all_btn.pack(side=tk.LEFT, padx=(20, 0))
        
        # Style the delete button as dangerous
        style = ttk.Style()
        style.configure("Danger.TButton", foreground="red")
        delete_all_btn.configure(style="Danger.TButton")
        
        ttk.Button(toolbar_frame, text="Settings", 
                  command=self._open_settings).pack(side=tk.RIGHT)
        
        # Load initial data
        self._refresh_tutorials()
        
    def _setup_bindings(self):
        """Set up event bindings"""
        # Context menu for tutorial list
        self.tutorial_tree.bind("<Button-2>", self._show_context_menu)  # Right click on macOS
        self.tutorial_tree.bind("<Button-3>", self._show_context_menu)  # Right click on Windows/Linux
        
        # Double click to edit
        self.tutorial_tree.bind("<Double-1>", lambda e: self._edit_tutorial())
        
        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
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
    
    def _delete_all_tutorials(self):
        """Delete all tutorials with safety confirmations"""
        # Get list of all tutorials
        tutorials = self.app.storage.list_tutorials()
        tutorial_count = len(tutorials)
        
        if tutorial_count == 0:
            messagebox.showinfo("No Tutorials", "No tutorials to delete")
            return
        
        # First confirmation - show count and warning
        if not messagebox.askyesno("Delete All Tutorials", 
                                  f"Are you sure you want to DELETE ALL {tutorial_count} tutorials?\n\n"
                                  "This action cannot be undone. All tutorial data, screenshots, "
                                  "and exported files will be permanently removed.\n\n"
                                  "Click YES to continue with confirmation, NO to cancel."):
            return
        
        # Second confirmation - require typing DELETE ALL
        from tkinter import simpledialog
        confirm_text = simpledialog.askstring(
            "Confirm Deletion", 
            f"This will permanently delete ALL {tutorial_count} tutorials.\n\n"
            "To confirm, please type: DELETE ALL",
            show='*' if tutorial_count > 5 else None  # Hide text for large deletions
        )
        
        if confirm_text != 'DELETE ALL':
            if confirm_text is not None:  # User didn't cancel
                messagebox.showinfo("Cancelled", "Deletion cancelled - confirmation text did not match")
            return
        
        # Show progress dialog
        progress_window = self._create_progress_dialog("Deleting Tutorials", f"Deleting {tutorial_count} tutorials...")
        
        # Perform deletion with progress tracking
        deleted_count = 0
        failed_count = 0
        failures = []
        
        try:
            for i, tutorial in enumerate(tutorials):
                # Update progress
                progress = (i + 1) / tutorial_count * 100
                self._update_progress_dialog(progress_window, f"Deleting: {tutorial.title[:30]}...", progress)
                
                try:
                    success = self.app.storage.delete_tutorial(tutorial.tutorial_id)
                    if success:
                        deleted_count += 1
                    else:
                        failed_count += 1
                        failures.append(f"• {tutorial.title}: Delete operation failed")
                except Exception as e:
                    failed_count += 1
                    failures.append(f"• {tutorial.title}: {str(e)}")
                
                # Allow GUI to update
                self.root.update()
            
            # Close progress dialog
            progress_window.destroy()
            
            # Show results
            if failed_count == 0:
                messagebox.showinfo("Success", f"Successfully deleted all {deleted_count} tutorials")
            else:
                failure_text = "\n".join(failures[:5])  # Show first 5 failures
                if len(failures) > 5:
                    failure_text += f"\n... and {len(failures) - 5} more"
                
                messagebox.showwarning("Partial Success", 
                                     f"Deleted {deleted_count} tutorials successfully.\n"
                                     f"{failed_count} tutorials could not be deleted:\n\n{failure_text}")
            
            # Refresh the tutorial list
            self._refresh_tutorials()
            
        except Exception as e:
            progress_window.destroy()
            messagebox.showerror("Error", f"Delete operation failed: {str(e)}")
    
    def _create_progress_dialog(self, title, message):
        """Create a progress dialog window"""
        progress_window = tk.Toplevel(self.root)
        progress_window.title(title)
        progress_window.geometry("400x120")
        progress_window.resizable(False, False)
        progress_window.grab_set()  # Make it modal
        
        # Center on parent
        progress_window.transient(self.root)
        progress_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        # Progress label
        progress_window.label = ttk.Label(progress_window, text=message)
        progress_window.label.pack(pady=20)
        
        # Progress bar
        progress_window.progress = ttk.Progressbar(progress_window, length=300, mode='determinate')
        progress_window.progress.pack(pady=10)
        
        return progress_window
    
    def _update_progress_dialog(self, progress_window, message, percentage):
        """Update progress dialog"""
        if progress_window and progress_window.winfo_exists():
            progress_window.label.config(text=message)
            progress_window.progress['value'] = percentage
            progress_window.update()
    
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