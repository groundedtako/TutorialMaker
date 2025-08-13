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
    
    def new_tutorial(self, title: str = None, description: str = "") -> str:
        """
        Create a new tutorial
        
        Args:
            title: Optional title for the tutorial
            description: Optional description
            
        Returns:
            Tutorial ID
        """
        # Create new tutorial project
        tutorial_id = self.storage.create_tutorial_project(title, description)
        
        # Get the actual title that was saved (in case it was auto-generated)
        metadata = self.storage.load_tutorial_metadata(tutorial_id)
        actual_title = metadata.title if metadata else (title or f"Tutorial {tutorial_id[:8]}")
        
        # Create new session using SessionManager
        session = self.session_manager.create_session(tutorial_id, actual_title)
        
        print(f"New tutorial created: {session.title}")
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
        self.session_manager.pause_recording()
    
    def resume_recording(self):
        """Resume the current recording"""
        self.session_manager.resume_recording()
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop recording, finalize the tutorial, and automatically export
        
        Returns:
            Tutorial ID if successful, None otherwise
        """
        return self.session_manager.stop_recording()
    
    def _on_mouse_click(self, event: MouseClickEvent):
        """Handle mouse click events - capture screenshot and calculate coordinates, then add to queue during recording"""
        # Check if we have an active recording session
        if not self.session_manager.has_active_session():
            return
        
        session = self.session_manager.current_session
        if not session or not session.is_recording():
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
    
    def export_all_tutorials(self, formats: List[str] = None) -> Dict[str, Dict[str, str]]:
        """
        Export all tutorials to specified formats
        
        Args:
            formats: List of formats to export
            
        Returns:
            Dictionary mapping tutorial IDs to export results
        """
        return self.exporter.export_all_tutorials(formats)
    
    def toggle_debug_mode(self) -> bool:
        """Toggle debug mode on/off"""
        self.debug_mode = not self.debug_mode
        self.screen_capture.set_debug_mode(self.debug_mode)
        self.event_processor.debug_mode = self.debug_mode
        self.session_manager.set_debug_mode(self.debug_mode)
        self.coordinate_handler.debug_mode = self.debug_mode
        return self.debug_mode
    
    def start_web_server(self) -> str:
        """Start the web server for editing tutorials"""
        try:
            url = self.web_server.start(open_browser=True)
            print(f"✅ Web server started at {url}")
            print("You can now edit and manage your tutorials in the browser.")
            return url
        except Exception as e:
            print(f"⚠️  Failed to start web server: {e}")
            return ""
    
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