"""
Settings dialog for TutorialMaker
Configure application preferences and recording options
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any, TYPE_CHECKING
import json
from pathlib import Path

if TYPE_CHECKING:
    from ..core.app import TutorialMakerApp


class SettingsDialog:
    """Settings configuration dialog"""
    
    def __init__(self, parent: tk.Widget, app: 'TutorialMakerApp'):
        self.parent = parent
        self.app = app
        self.dialog: tk.Toplevel = None
        
        # Settings data
        self.settings = self._load_settings()
        
        # UI variables
        self.vars = {}
        
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        settings_file = Path.home() / "TutorialMaker" / "settings.json"
        
        # Default settings
        defaults = {
            'recording': {
                'auto_export': True,
                'export_formats': ['html', 'word'],
                'debug_mode': False,
                'pause_on_inactivity': False,
                'inactivity_timeout': 30,
            },
            'ui': {
                'start_minimized': False,
                'show_notifications': True,
                'floating_controls': True,
                'always_on_top': True,
            },
            'hotkeys': {
                'start_stop_recording': 'cmd+shift+r',
                'pause_resume': 'cmd+shift+p',
                'new_tutorial': 'cmd+shift+n',
            },
            'storage': {
                'base_path': str(Path.home() / "TutorialMaker"),
                'auto_cleanup_days': 30,
                'max_storage_gb': 5.0,
            }
        }
        
        try:
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    # Merge with defaults
                    for category, options in defaults.items():
                        if category in saved_settings:
                            options.update(saved_settings[category])
                        defaults[category] = options
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        return defaults
    
    def _save_settings(self):
        """Save settings to file"""
        settings_file = Path.home() / "TutorialMaker" / "settings.json"
        settings_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
            return False
    
    def _create_dialog(self):
        """Create settings dialog window"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("TutorialMaker Settings")
        self.dialog.geometry("500x600")
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center on parent
        self.dialog.geometry("+{}+{}".format(
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        self._create_widgets()
        self._load_values()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook for different categories
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Recording settings tab
        self._create_recording_tab(notebook)
        
        # UI settings tab
        self._create_ui_tab(notebook)
        
        # Hotkeys tab
        self._create_hotkeys_tab(notebook)
        
        # Storage tab
        self._create_storage_tab(notebook)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Restore Defaults", 
                  command=self._restore_defaults).pack(side=tk.LEFT)
        
        ttk.Button(button_frame, text="Cancel", 
                  command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(button_frame, text="Apply", 
                  command=self._apply).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(button_frame, text="OK", 
                  command=self._ok).pack(side=tk.RIGHT, padx=(5, 0))
    
    def _create_recording_tab(self, notebook: ttk.Notebook):
        """Create recording settings tab"""
        frame = ttk.Frame(notebook, padding="15")
        notebook.add(frame, text="Recording")
        
        # Export settings
        export_frame = ttk.LabelFrame(frame, text="Export Settings", padding="10")
        export_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.vars['auto_export'] = tk.BooleanVar()
        ttk.Checkbutton(export_frame, text="Auto-export when recording stops", 
                       variable=self.vars['auto_export']).pack(anchor=tk.W)
        
        # Export formats
        formats_frame = ttk.Frame(export_frame)
        formats_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(formats_frame, text="Export formats:").pack(anchor=tk.W)
        
        format_checkboxes = ttk.Frame(formats_frame)
        format_checkboxes.pack(fill=tk.X, pady=(5, 0))
        
        self.vars['export_html'] = tk.BooleanVar()
        self.vars['export_word'] = tk.BooleanVar()
        self.vars['export_pdf'] = tk.BooleanVar()
        
        ttk.Checkbutton(format_checkboxes, text="HTML", 
                       variable=self.vars['export_html']).pack(side=tk.LEFT, padx=(20, 15))
        ttk.Checkbutton(format_checkboxes, text="Word", 
                       variable=self.vars['export_word']).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Checkbutton(format_checkboxes, text="PDF", 
                       variable=self.vars['export_pdf']).pack(side=tk.LEFT)
        
        # Advanced settings
        advanced_frame = ttk.LabelFrame(frame, text="Advanced", padding="10")
        advanced_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.vars['debug_mode'] = tk.BooleanVar()
        ttk.Checkbutton(advanced_frame, text="Debug mode (show click markers on screenshots)", 
                       variable=self.vars['debug_mode']).pack(anchor=tk.W)
        
        self.vars['pause_on_inactivity'] = tk.BooleanVar()
        ttk.Checkbutton(advanced_frame, text="Auto-pause on inactivity", 
                       variable=self.vars['pause_on_inactivity']).pack(anchor=tk.W, pady=(5, 0))
        
        timeout_frame = ttk.Frame(advanced_frame)
        timeout_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(timeout_frame, text="Inactivity timeout:").pack(side=tk.LEFT, padx=(20, 5))
        self.vars['inactivity_timeout'] = tk.StringVar()
        ttk.Entry(timeout_frame, textvariable=self.vars['inactivity_timeout'], 
                 width=5).pack(side=tk.LEFT)
        ttk.Label(timeout_frame, text="seconds").pack(side=tk.LEFT, padx=(5, 0))
    
    def _create_ui_tab(self, notebook: ttk.Notebook):
        """Create UI settings tab"""
        frame = ttk.Frame(notebook, padding="15")
        notebook.add(frame, text="Interface")
        
        # Window behavior
        window_frame = ttk.LabelFrame(frame, text="Window Behavior", padding="10")
        window_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.vars['start_minimized'] = tk.BooleanVar()
        ttk.Checkbutton(window_frame, text="Start minimized to system tray", 
                       variable=self.vars['start_minimized']).pack(anchor=tk.W)
        
        self.vars['show_notifications'] = tk.BooleanVar()
        ttk.Checkbutton(window_frame, text="Show system notifications", 
                       variable=self.vars['show_notifications']).pack(anchor=tk.W, pady=(5, 0))
        
        # Recording controls
        controls_frame = ttk.LabelFrame(frame, text="Recording Controls", padding="10")
        controls_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.vars['floating_controls'] = tk.BooleanVar()
        ttk.Checkbutton(controls_frame, text="Show floating controls during recording", 
                       variable=self.vars['floating_controls']).pack(anchor=tk.W)
        
        self.vars['always_on_top'] = tk.BooleanVar()
        ttk.Checkbutton(controls_frame, text="Keep controls always on top", 
                       variable=self.vars['always_on_top']).pack(anchor=tk.W, pady=(5, 0))
    
    def _create_hotkeys_tab(self, notebook: ttk.Notebook):
        """Create hotkeys settings tab"""
        frame = ttk.Frame(notebook, padding="15")
        notebook.add(frame, text="Hotkeys")
        
        # Hotkey settings
        hotkeys_frame = ttk.LabelFrame(frame, text="Global Hotkeys", padding="10")
        hotkeys_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Start/Stop recording
        row1 = ttk.Frame(hotkeys_frame)
        row1.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(row1, text="Start/Stop Recording:", width=20).pack(side=tk.LEFT)
        self.vars['start_stop_recording'] = tk.StringVar()
        ttk.Entry(row1, textvariable=self.vars['start_stop_recording'], width=20).pack(side=tk.LEFT, padx=(10, 0))
        
        # Pause/Resume
        row2 = ttk.Frame(hotkeys_frame)
        row2.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(row2, text="Pause/Resume:", width=20).pack(side=tk.LEFT)
        self.vars['pause_resume'] = tk.StringVar()
        ttk.Entry(row2, textvariable=self.vars['pause_resume'], width=20).pack(side=tk.LEFT, padx=(10, 0))
        
        # New tutorial
        row3 = ttk.Frame(hotkeys_frame)
        row3.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(row3, text="New Tutorial:", width=20).pack(side=tk.LEFT)
        self.vars['new_tutorial'] = tk.StringVar()
        ttk.Entry(row3, textvariable=self.vars['new_tutorial'], width=20).pack(side=tk.LEFT, padx=(10, 0))
        
        # Help text
        help_text = ttk.Label(hotkeys_frame, 
                             text="Format: cmd+shift+r, ctrl+alt+s, etc.\\nLeave empty to disable hotkey.",
                             foreground='gray', font=('Helvetica', 9))
        help_text.pack(anchor=tk.W, pady=(10, 0))
    
    def _create_storage_tab(self, notebook: ttk.Notebook):
        """Create storage settings tab"""
        frame = ttk.Frame(notebook, padding="15")
        notebook.add(frame, text="Storage")
        
        # Storage location
        location_frame = ttk.LabelFrame(frame, text="Storage Location", padding="10")
        location_frame.pack(fill=tk.X, pady=(0, 15))
        
        path_frame = ttk.Frame(location_frame)
        path_frame.pack(fill=tk.X)
        
        ttk.Label(path_frame, text="Base folder:").pack(anchor=tk.W)
        
        path_entry_frame = ttk.Frame(path_frame)
        path_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.vars['base_path'] = tk.StringVar()
        ttk.Entry(path_entry_frame, textvariable=self.vars['base_path']).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_entry_frame, text="Browse...", 
                  command=self._browse_storage_path).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Cleanup settings
        cleanup_frame = ttk.LabelFrame(frame, text="Cleanup", padding="10")
        cleanup_frame.pack(fill=tk.X, pady=(0, 15))
        
        cleanup_row1 = ttk.Frame(cleanup_frame)
        cleanup_row1.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(cleanup_row1, text="Auto-cleanup tutorials older than:").pack(side=tk.LEFT)
        self.vars['auto_cleanup_days'] = tk.StringVar()
        ttk.Entry(cleanup_row1, textvariable=self.vars['auto_cleanup_days'], width=5).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Label(cleanup_row1, text="days (0 = disabled)").pack(side=tk.LEFT)
        
        cleanup_row2 = ttk.Frame(cleanup_frame)
        cleanup_row2.pack(fill=tk.X)
        ttk.Label(cleanup_row2, text="Maximum storage usage:").pack(side=tk.LEFT)
        self.vars['max_storage_gb'] = tk.StringVar()
        ttk.Entry(cleanup_row2, textvariable=self.vars['max_storage_gb'], width=5).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Label(cleanup_row2, text="GB").pack(side=tk.LEFT)
        
        # Storage info
        info_frame = ttk.LabelFrame(frame, text="Current Usage", padding="10")
        info_frame.pack(fill=tk.X)
        
        try:
            stats = self.app.storage.get_storage_stats()
            info_text = f"Tutorials: {stats['total_tutorials']}\\nStorage used: {stats['total_size_mb']} MB"
        except:
            info_text = "Storage information unavailable"
        
        ttk.Label(info_frame, text=info_text).pack(anchor=tk.W)
    
    def _browse_storage_path(self):
        """Browse for storage path"""
        current_path = self.vars['base_path'].get()
        new_path = filedialog.askdirectory(initialdir=current_path, title="Select storage folder")
        if new_path:
            self.vars['base_path'].set(new_path)
    
    def _load_values(self):
        """Load current settings into UI"""
        # Recording settings
        recording = self.settings['recording']
        self.vars['auto_export'].set(recording.get('auto_export', True))
        self.vars['debug_mode'].set(recording.get('debug_mode', False))
        self.vars['pause_on_inactivity'].set(recording.get('pause_on_inactivity', False))
        self.vars['inactivity_timeout'].set(str(recording.get('inactivity_timeout', 30)))
        
        # Export formats
        formats = recording.get('export_formats', ['html', 'word'])
        self.vars['export_html'].set('html' in formats)
        self.vars['export_word'].set('word' in formats)
        self.vars['export_pdf'].set('pdf' in formats)
        
        # UI settings
        ui = self.settings['ui']
        self.vars['start_minimized'].set(ui.get('start_minimized', False))
        self.vars['show_notifications'].set(ui.get('show_notifications', True))
        self.vars['floating_controls'].set(ui.get('floating_controls', True))
        self.vars['always_on_top'].set(ui.get('always_on_top', True))
        
        # Hotkeys
        hotkeys = self.settings['hotkeys']
        self.vars['start_stop_recording'].set(hotkeys.get('start_stop_recording', 'cmd+shift+r'))
        self.vars['pause_resume'].set(hotkeys.get('pause_resume', 'cmd+shift+p'))
        self.vars['new_tutorial'].set(hotkeys.get('new_tutorial', 'cmd+shift+n'))
        
        # Storage
        storage = self.settings['storage']
        self.vars['base_path'].set(storage.get('base_path', str(Path.home() / "TutorialMaker")))
        self.vars['auto_cleanup_days'].set(str(storage.get('auto_cleanup_days', 30)))
        self.vars['max_storage_gb'].set(str(storage.get('max_storage_gb', 5.0)))
    
    def _save_values(self):
        """Save UI values to settings"""
        # Recording settings
        recording = self.settings['recording']
        recording['auto_export'] = self.vars['auto_export'].get()
        recording['debug_mode'] = self.vars['debug_mode'].get()
        recording['pause_on_inactivity'] = self.vars['pause_on_inactivity'].get()
        
        try:
            recording['inactivity_timeout'] = int(self.vars['inactivity_timeout'].get())
        except ValueError:
            recording['inactivity_timeout'] = 30
        
        # Export formats
        formats = []
        if self.vars['export_html'].get():
            formats.append('html')
        if self.vars['export_word'].get():
            formats.append('word')
        if self.vars['export_pdf'].get():
            formats.append('pdf')
        recording['export_formats'] = formats
        
        # UI settings
        ui = self.settings['ui']
        ui['start_minimized'] = self.vars['start_minimized'].get()
        ui['show_notifications'] = self.vars['show_notifications'].get()
        ui['floating_controls'] = self.vars['floating_controls'].get()
        ui['always_on_top'] = self.vars['always_on_top'].get()
        
        # Hotkeys
        hotkeys = self.settings['hotkeys']
        hotkeys['start_stop_recording'] = self.vars['start_stop_recording'].get()
        hotkeys['pause_resume'] = self.vars['pause_resume'].get()
        hotkeys['new_tutorial'] = self.vars['new_tutorial'].get()
        
        # Storage
        storage = self.settings['storage']
        storage['base_path'] = self.vars['base_path'].get()
        
        try:
            storage['auto_cleanup_days'] = int(self.vars['auto_cleanup_days'].get())
        except ValueError:
            storage['auto_cleanup_days'] = 30
        
        try:
            storage['max_storage_gb'] = float(self.vars['max_storage_gb'].get())
        except ValueError:
            storage['max_storage_gb'] = 5.0
    
    def _restore_defaults(self):
        """Restore default settings"""
        if messagebox.askyesno("Restore Defaults", 
                              "Are you sure you want to restore all settings to their default values?"):
            self.settings = self._load_settings()  # This loads defaults
            self._load_values()
    
    def _apply(self):
        """Apply settings"""
        self._save_values()
        if self._save_settings():
            # Apply settings to running app
            self._apply_to_app()
            messagebox.showinfo("Settings", "Settings applied successfully")
    
    def _apply_to_app(self):
        """Apply settings to the running application"""
        # Apply debug mode
        debug_mode = self.settings['recording']['debug_mode']
        self.app.screen_capture.set_debug_mode(debug_mode)
        
        # Other settings would be applied here as the app supports them
    
    def _ok(self):
        """OK button - apply and close"""
        self._apply()
        self._close()
    
    def _cancel(self):
        """Cancel button - close without saving"""
        self._close()
    
    def _close(self):
        """Close dialog"""
        if self.dialog:
            self.dialog.destroy()
    
    def show(self):
        """Show the settings dialog"""
        if not self.dialog:
            self._create_dialog()
        
        self.dialog.focus_set()
        self.dialog.wait_window()