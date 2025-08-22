"""
Main TutorialMaker application
Coordinates all components and manages recording sessions
"""

import time
import threading
from typing import Optional, Dict, Any, List
from pathlib import Path

from .capture import ScreenCapture
from .events import EventMonitor, MouseClickEvent, KeyPressEvent, EventType
from .ocr import OCREngine, OCRResult
from .smart_ocr import SmartOCRProcessor
from .storage import TutorialStorage, TutorialStep, TutorialMetadata
from .exporters import TutorialExporter
from .event_queue import EventQueue
from .event_processor import EventProcessor
from .session_manager import SessionManager
from .coordinate_handler import CoordinateSystemHandler
from .event_filter import EventFilter
from ..web.server import TutorialWebServer


class TutorialMakerApp:
    """Main application class"""
    
    def __init__(self, debug_mode: bool = False):
        # Initialize components
        self.screen_capture = ScreenCapture(debug_mode=debug_mode)
        self.event_monitor = EventMonitor()
        self.ocr_engine = OCREngine()
        self.smart_ocr = SmartOCRProcessor()
        self.storage = TutorialStorage()
        self.exporter = TutorialExporter(self.storage)
        self.web_server = TutorialWebServer(self.storage)
        self.web_server.set_app_instance(self)  # Allow web server to access session status
        self.debug_mode = debug_mode
        
        # Event queue for clean event processing
        self.event_queue = EventQueue()
        # Event processor for converting events to tutorial steps
        self.event_processor = EventProcessor(
            self.screen_capture, 
            self.ocr_engine, 
            self.smart_ocr, 
            self.storage, 
            debug_mode
        )
        # Coordinate system handler for multi-monitor coordinate transformations
        self.coordinate_handler = CoordinateSystemHandler(debug_mode)
        # Event filter for filtering app-native events and keystrokes
        self.event_filter = EventFilter(debug_mode)
        # Session manager for handling recording sessions
        self.session_manager = SessionManager(
            self.storage,
            self.event_monitor,
            self.event_queue,
            self.event_processor,
            debug_mode
        )
        
        # Set up event callbacks
        self.event_monitor.set_mouse_callback(self._on_mouse_click)
        self.event_monitor.set_keyboard_callback(self._on_keyboard_event)
        
        # Processing thread
        self.processing_thread = None
        self.running = False
        
        # Selected monitor for recording (used by web interface)
        self.selected_monitor_id: Optional[int] = None
        # Flag to indicate if we're in web mode (to avoid GUI dialogs)
        self.web_mode: bool = False
        
        print("TutorialMaker initialized successfully")
        self._print_status()
    
    def _print_status(self):
        """Print current system status"""
        screen_info = self.screen_capture.get_screen_info()
        event_status = self.event_monitor.get_status()
        ocr_stats = self.ocr_engine.get_stats()
        storage_stats = self.storage.get_storage_stats()
        
        # Initialize coordinate handler with monitor info
        if 'monitors' in screen_info:
            self.coordinate_handler.update_monitor_info(screen_info['monitors'])
        
        print("\nSystem Status:")
        print(f"  Screen: {screen_info['width']}x{screen_info['height']} ({screen_info['monitor_count']} monitors)")
        print(f"  Events: Mouse={event_status['has_mouse_access']}, Keyboard={event_status['has_keyboard_access']}")
        print(f"  OCR: Tesseract={ocr_stats['tesseract_available']}, EasyOCR={ocr_stats['easyocr_available']}")
        print(f"  Storage: {storage_stats['total_tutorials']} tutorials, {storage_stats['total_size_mb']}MB")
    
    def select_recording_monitor(self) -> Optional[int]:
        """
        Show screen selection dialog for choosing recording monitor
        Returns selected monitor ID or None if cancelled
        """
        try:
            # Try to import GUI components
            from ..gui.screen_selector import show_screen_selector
            import tkinter as tk
            
            # Check if we're in a GUI-capable environment
            if not hasattr(tk, '_default_root') and not tk._default_root:
                # Try to create a root window to test GUI availability
                try:
                    test_root = tk.Tk()
                    test_root.withdraw()
                    test_root.destroy()
                except tk.TclError:
                    # No display available - we're in headless mode
                    raise Exception("No display available (headless environment)")
            
            # Create temporary root if none exists
            root = tk._default_root
            if root is None:
                root = tk.Tk()
                root.withdraw()
                created_root = True
            else:
                created_root = False
            
            # Show screen selector
            selected_monitor = show_screen_selector(root, self.screen_capture)
            
            # Clean up temporary root
            if created_root:
                root.destroy()
            
            return selected_monitor
            
        except (ImportError, tk.TclError, Exception) as e:
            # GUI not available or error occurred
            print(f"Screen selector not available: {e}")
            return 1  # Default to primary monitor
    
    def new_tutorial(self, title: str = None, description: str = "", selected_monitor: Optional[int] = None) -> str:
        """
        Create a new tutorial
        
        Args:
            title: Optional title for the tutorial
            description: Optional description
            selected_monitor: Monitor ID to record on (None = prompt user)
            
        Returns:
            Tutorial ID
        """
        print(f"DEBUG: new_tutorial called with title='{title}', selected_monitor={selected_monitor}")
        
        # Create new tutorial project
        tutorial_id = self.storage.create_tutorial_project(title, description)
        print(f"DEBUG: Created tutorial project with ID: {tutorial_id}")
        
        # Get the actual title that was saved (in case it was auto-generated)
        metadata = self.storage.load_tutorial_metadata(tutorial_id)
        actual_title = metadata.title if metadata else (title or f"Tutorial {tutorial_id[:8]}")
        
        # If no monitor selected, check if one was set via web interface or show selector
        if selected_monitor is None:
            print(f"DEBUG: No monitor selected, checking options...")
            # Check if monitor was pre-selected (e.g., via web interface)
            if self.selected_monitor_id is not None:
                selected_monitor = self.selected_monitor_id
                print(f"DEBUG: Using pre-selected monitor {selected_monitor}")
            else:
                print(f"DEBUG: No pre-selected monitor, checking if GUI is available...")
                
                # Check if we're in web mode (avoid GUI dialogs)
                if self.web_mode:
                    print(f"DEBUG: Web mode detected, defaulting to primary monitor")
                    selected_monitor = 1
                else:
                    print(f"DEBUG: Desktop environment, checking screen count...")
                    # Try to show screen selector if GUI is available
                    try:
                        screen_info = self.screen_capture.get_screen_info()
                        monitor_count = screen_info.get('monitor_count', 1)
                        print(f"DEBUG: Found {monitor_count} monitors")
                        
                        if monitor_count > 1:
                            # Multiple monitors - try to show selector, but handle gracefully if it fails
                            print(f"DEBUG: Multiple monitors detected, trying to show selector...")
                            try:
                                selected_monitor = self.select_recording_monitor()
                                if selected_monitor is None:
                                    print("DEBUG: Screen selection cancelled, using primary monitor")
                                    selected_monitor = 1
                                else:
                                    print(f"DEBUG: User selected monitor {selected_monitor}")
                            except Exception as selector_error:
                                print(f"DEBUG: Screen selector failed: {selector_error}, using primary monitor")
                                selected_monitor = 1
                        else:
                            # Single monitor - use primary
                            print(f"DEBUG: Single monitor setup, using primary")
                            selected_monitor = 1
                    except Exception as e:
                        print(f"DEBUG: Screen info failed: {e}, using primary monitor")
                        selected_monitor = 1
        
        # Create new session using SessionManager
        print(f"DEBUG: Creating session with monitor {selected_monitor}")
        session = self.session_manager.create_session(tutorial_id, actual_title, selected_monitor)
        print(f"DEBUG: Session created successfully")
        
        monitor_text = f" (Monitor {selected_monitor})" if selected_monitor else ""
        print(f"New tutorial created: {session.title}{monitor_text}")
        print(f"DEBUG: new_tutorial returning tutorial_id: {tutorial_id}")
        return tutorial_id
    
    def start_recording(self) -> bool:
        """
        Start recording the current tutorial
        
        Returns:
            True if recording started successfully
        """
        return self.session_manager.start_recording()
    
    def pause_recording(self):
        """Pause the current recording"""
        # Remove last event from queue (likely the pause button click)
        if hasattr(self, 'event_queue'):
            self.event_queue.remove_last_event()
        
        self.session_manager.pause_recording()
    
    def resume_recording(self):
        """Resume the current recording"""
        # No need to remove last event - resume button clicks aren't captured during pause
        # because session.is_recording() returns False when paused
        
        self.session_manager.resume_recording()
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop recording, finalize the tutorial, and automatically export
        
        Returns:
            Tutorial ID if successful, None otherwise
        """
        # Only remove last event if it's a recent mouse click (likely the stop button click)
        if (hasattr(self, 'event_queue') and 
            self.event_queue.events and 
            self.event_queue.is_recording()):
            
            last_event = self.event_queue.events[-1]
            # Only remove if it's a very recent mouse click (within last 2 seconds)
            import time
            if (last_event.event_type == 'mouse_click' and 
                time.time() - last_event.timestamp < 2.0):
                self.event_queue.remove_last_event()
                if self.debug_mode:
                    print("DEBUG: Removed stop button click from event queue")
            elif self.debug_mode:
                print(f"DEBUG: Keeping last event in queue ({last_event.event_type}, {time.time() - last_event.timestamp:.1f}s ago)")
        
        return self.session_manager.stop_recording()
    
    def _on_mouse_click(self, event: MouseClickEvent):
        """Handle mouse click events - capture screenshot and calculate coordinates, then add to queue during recording"""
        # Check if we have an active recording session
        if not self.session_manager.has_active_session():
            return
        
        session = self.session_manager.current_session
        if not session or not session.is_recording():
            return
        
        # Check if event is on the selected monitor (ignore events on other monitors)
        if session.selected_monitor is not None:
            screen_info = self.screen_capture.get_screen_info()
            monitors = screen_info.get('monitors', [])
            
            if not session.is_event_on_selected_monitor(event.x, event.y, monitors):
                if self.debug_mode:
                    print(f"DEBUG: Ignoring click at ({event.x}, {event.y}) - not on selected monitor {session.selected_monitor}")
                return
        
        # Apply filtering (mainly for keystroke filtering and post-stop/pause filtering)
        if hasattr(self, 'event_filter'):
            filter_decision = self.event_filter.should_capture_event(event, session)
            if not filter_decision.should_capture:
                if self.debug_mode:
                    print(f"DEBUG: Filtered {event} - Reason: {filter_decision.reason}")
                return
        
        # Transform coordinates using centralized coordinate handler
        coord_info = self.coordinate_handler.transform_coordinates(event.x, event.y)
        
        # Capture screenshot immediately at the time of click
        screenshot = self.screen_capture.capture_full_screen(click_point=(event.x, event.y))
        
        # Track which monitor was captured
        if screenshot:
            self.coordinate_handler.set_last_capture_monitor(coord_info.monitor)
        
        # Convert to legacy format for compatibility with existing EventProcessor
        coordinate_info = coord_info.to_legacy_dict() if coord_info else None
        
        # Add to event queue with captured screenshot and coordinate info
        self.event_queue.add_mouse_click(event, screenshot, coordinate_info)
        
        # Increment step counter for real-time user feedback
        step_count = self.session_manager.increment_step_counter()
        
        if self.debug_mode:
            print(f"DEBUG: Queued mouse click at ({event.x}, {event.y}) - Step {step_count}")
    
    def _on_keyboard_event(self, event: KeyPressEvent):
        """Handle keyboard events - add to queue during recording"""
        # Check if we have an active recording session
        if not self.session_manager.has_active_session():
            return
        
        session = self.session_manager.current_session
        if not session or not session.is_recording():
            return
        
        # Apply filtering (including keystroke filtering if enabled)
        if hasattr(self, 'event_filter'):
            filter_decision = self.event_filter.should_capture_event(event, session)
            if not filter_decision.should_capture:
                if self.debug_mode:
                    print(f"DEBUG: Filtered keyboard event '{event.key}' - Reason: {filter_decision.reason}")
                return
        
        # Add to event queue
        self.event_queue.add_keyboard_event(event)
        
        # Increment step counter for significant keyboard events (real-time feedback)
        should_increment = False
        if hasattr(event, 'is_special') and event.is_special:
            # Special keys like Enter, Tab, etc.
            should_increment = True
        elif hasattr(event, 'event_type') and event.event_type == "text_input":
            # Text input sessions
            should_increment = True
        
        if should_increment:
            step_count = self.session_manager.increment_step_counter()
            if self.debug_mode:
                print(f"DEBUG: Queued keyboard event '{event.key}' - Step {step_count}")
        else:
            if self.debug_mode:
                print(f"DEBUG: Queued keyboard event '{event.key}' (no step increment)")
    
    
    def list_tutorials(self) -> List[TutorialMetadata]:
        """List all available tutorials"""
        return self.storage.list_tutorials()
    
    def delete_tutorial(self, tutorial_id: str) -> bool:
        """Delete a tutorial"""
        return self.storage.delete_tutorial(tutorial_id)
    
    def delete_all_tutorials(self) -> Dict[str, bool]:
        """Delete all tutorials"""
        return self.storage.delete_all_tutorials()
    
    def get_tutorial_data(self, tutorial_id: str) -> Optional[Dict]:
        """Get complete tutorial data"""
        return self.storage.export_tutorial_data(tutorial_id)
    
    def export_tutorial(self, tutorial_id: str, formats: List[str] = None) -> Dict[str, str]:
        """
        Export tutorial to specified formats
        
        Args:
            tutorial_id: Tutorial ID to export
            formats: List of formats ('html', 'word', 'pdf'). If None, exports all.
            
        Returns:
            Dictionary mapping format names to output file paths
        """
        return self.exporter.export_tutorial(tutorial_id, formats)
    
    def export_all_tutorials(self, formats: List[str] = None, max_workers: int = 3) -> Dict[str, Dict[str, str]]:
        """
        Export all tutorials to specified formats with concurrent processing
        
        Args:
            formats: List of formats to export
            max_workers: Maximum number of concurrent export operations
            
        Returns:
            Dictionary mapping tutorial IDs to export results
        """
        return self.exporter.export_all_tutorials(formats, max_workers)
    
    def toggle_debug_mode(self) -> bool:
        """Toggle debug mode on/off"""
        self.debug_mode = not self.debug_mode
        self.screen_capture.set_debug_mode(self.debug_mode)
        self.event_processor.debug_mode = self.debug_mode
        self.session_manager.set_debug_mode(self.debug_mode)
        self.coordinate_handler.debug_mode = self.debug_mode
        self.event_filter.debug_mode = self.debug_mode
        return self.debug_mode
    
    def toggle_keystroke_filtering(self) -> bool:
        """Toggle keystroke filtering on/off"""
        # Only remove last event if it's a recent mouse click (likely the toggle button click)
        # This prevents accidentally removing important user events
        if (hasattr(self, 'event_queue') and 
            self.event_queue.events and 
            self.event_queue.is_recording()):
            
            last_event = self.event_queue.events[-1]
            # Only remove if it's a very recent mouse click (within last 2 seconds)
            import time
            if (last_event.event_type == 'mouse_click' and 
                time.time() - last_event.timestamp < 2.0):
                self.event_queue.remove_last_event()
                if self.debug_mode:
                    print("DEBUG: Removed toggle button click from event queue")
            elif self.debug_mode:
                print(f"DEBUG: Keeping last event in queue ({last_event.event_type}, {time.time() - last_event.timestamp:.1f}s ago)")
        
        enabled = self.event_filter.toggle_keystroke_filtering()
        return enabled
    
    def start_web_server(self) -> str:
        """Start the web server for editing tutorials"""
        try:
            # Set web mode to avoid GUI dialogs when called from web interface
            self.web_mode = True
            url = self.web_server.start(open_browser=True)
            print(f"✅ Web server started at {url}")
            print("You can now edit and manage your tutorials in the browser.")
            return url
        except Exception as e:
            print(f"⚠️  Failed to start web server: {e}")
            return ""
    
    @property
    def current_session(self):
        """Access current session for backward compatibility"""
        return self.session_manager.current_session
    
    def get_current_session_status(self) -> Dict[str, Any]:
        """Get status of current recording session"""
        return self.session_manager.get_session_status()
    
    def run(self):
        """Run the main application loop"""
        self.running = True
        
        print("\nTutorialMaker is ready!")
        print("Commands:")
        print("  new <title>     - Create new tutorial")
        print("  start          - Start recording")
        print("  pause          - Pause recording")
        print("  resume         - Resume recording") 
        print("  stop           - Stop recording and auto-export to HTML/Word/PDF")
        print("  list           - List tutorials")
        print("  status         - Show current status")
        print("  debug          - Toggle debug mode (shows precise click locations)")
        print("  filter         - Toggle keystroke filtering on/off")
        print("  web            - Start web server for editing (http://localhost:5000)")
        print("  quit           - Exit application")
        
        try:
            while self.running:
                try:
                    command = input("\n> ").strip().lower().split()
                    if not command:
                        continue
                    
                    cmd = command[0]
                    
                    if cmd == "quit" or cmd == "exit":
                        break
                    elif cmd == "new":
                        title = " ".join(command[1:]) if len(command) > 1 else None
                        tutorial_id = self.new_tutorial(title)
                        print(f"Created tutorial: {tutorial_id}")
                    elif cmd == "start":
                        self.start_recording()
                    elif cmd == "pause":
                        self.pause_recording()
                    elif cmd == "resume":
                        self.resume_recording()
                    elif cmd == "stop":
                        tutorial_id = self.stop_recording()
                        if tutorial_id:
                            print(f"Tutorial saved: {tutorial_id}")
                    elif cmd == "list":
                        tutorials = self.list_tutorials()
                        if tutorials:
                            print(f"\nFound {len(tutorials)} tutorials:")
                            for t in tutorials:
                                print(f"  {t.title} ({t.tutorial_id[:8]}) - {t.step_count} steps")
                        else:
                            print("No tutorials found")
                    elif cmd == "status":
                        status = self.get_current_session_status()
                        print(f"Current session: {status}")
                    elif cmd == "debug":
                        debug_enabled = self.toggle_debug_mode()
                        status = "enabled" if debug_enabled else "disabled"
                        print(f"Debug mode {status}")
                    elif cmd == "filter":
                        filter_enabled = self.toggle_keystroke_filtering()
                        status = "enabled" if filter_enabled else "disabled"
                        print(f"Keystroke filtering {status}")
                    elif cmd == "web":
                        self.start_web_server()
                    else:
                        print(f"Unknown command: {cmd}")
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error: {e}")
        
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown of the application"""
        print("\nShutting down...")
        
        # Stop any recording
        if self.session_manager.has_active_session():
            self.stop_recording()
        
        # Stop event monitoring
        self.event_monitor.stop_monitoring()
        
        # Stop web server
        self.web_server.stop()
        
        # Clean up resources
        self.screen_capture.close()
        self.ocr_engine.clear_cache()
        
        self.running = False
        print("Shutdown complete")