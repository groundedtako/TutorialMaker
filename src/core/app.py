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
from .storage import TutorialStorage, TutorialStep, TutorialMetadata
from .exporters import TutorialExporter

class RecordingSession:
    """Manages a single recording session"""
    
    def __init__(self, tutorial_id: str, title: str = ""):
        self.tutorial_id = tutorial_id
        self.title = title
        self.status = "stopped"  # stopped, recording, paused
        self.start_time = None
        self.pause_start_time = None
        self.total_pause_duration = 0.0
        self.step_counter = 0
        self.last_event_time = 0.0
        
    def start(self):
        """Start recording"""
        self.status = "recording"
        self.start_time = time.time()
        self.step_counter = 0
        self.total_pause_duration = 0.0
        print(f"Recording started for: {self.title}")
    
    def pause(self):
        """Pause recording"""
        if self.status == "recording":
            self.status = "paused"
            self.pause_start_time = time.time()
            print("Recording paused")
    
    def resume(self):
        """Resume recording"""
        if self.status == "paused":
            self.status = "recording"
            if self.pause_start_time:
                self.total_pause_duration += time.time() - self.pause_start_time
                self.pause_start_time = None
            print("Recording resumed")
    
    def stop(self):
        """Stop recording"""
        self.status = "stopped"
        if self.pause_start_time:
            self.total_pause_duration += time.time() - self.pause_start_time
        print(f"Recording stopped. Total steps: {self.step_counter}")
    
    def is_recording(self) -> bool:
        """Check if currently recording (not paused or stopped)"""
        return self.status == "recording"
    
    def get_duration(self) -> float:
        """Get total recording duration excluding pauses"""
        if not self.start_time:
            return 0.0
        
        current_time = time.time()
        total_time = current_time - self.start_time
        
        # Subtract pause time
        pause_time = self.total_pause_duration
        if self.status == "paused" and self.pause_start_time:
            pause_time += current_time - self.pause_start_time
        
        return max(0.0, total_time - pause_time)

class TutorialMakerApp:
    """Main application class"""
    
    def __init__(self, debug_mode: bool = False):
        # Initialize components
        self.screen_capture = ScreenCapture(debug_mode=debug_mode)
        self.event_monitor = EventMonitor()
        self.ocr_engine = OCREngine()
        self.storage = TutorialStorage()
        self.exporter = TutorialExporter(self.storage)
        self.debug_mode = debug_mode
        
        # Current session
        self.current_session: Optional[RecordingSession] = None
        
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
        # Stop any current session
        if self.current_session:
            self.stop_recording()
        
        # Create new tutorial project
        tutorial_id = self.storage.create_tutorial_project(title, description)
        
        # Create new session
        self.current_session = RecordingSession(tutorial_id, title or f"Tutorial {tutorial_id[:8]}")
        
        print(f"New tutorial created: {self.current_session.title}")
        return tutorial_id
    
    def start_recording(self) -> bool:
        """
        Start recording the current tutorial
        
        Returns:
            True if recording started successfully
        """
        if not self.current_session:
            print("No tutorial session. Create a new tutorial first.")
            return False
        
        # Start event monitoring
        if not self.event_monitor.start_monitoring():
            print("Failed to start event monitoring. Limited functionality available.")
            # Continue anyway - user can still do manual capture
        
        # Start session
        self.current_session.start()
        
        # Update storage status
        self.storage.update_tutorial_status(self.current_session.tutorial_id, "recording")
        
        return True
    
    def pause_recording(self):
        """Pause the current recording"""
        if self.current_session and self.current_session.is_recording():
            self.current_session.pause()
            self.storage.update_tutorial_status(self.current_session.tutorial_id, "paused")
    
    def resume_recording(self):
        """Resume the current recording"""
        if self.current_session and self.current_session.status == "paused":
            self.current_session.resume()
            self.storage.update_tutorial_status(self.current_session.tutorial_id, "recording")
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop recording and finalize the tutorial
        
        Returns:
            Tutorial ID if successful, None otherwise
        """
        if not self.current_session:
            return None
        
        tutorial_id = self.current_session.tutorial_id
        
        # Stop session
        self.current_session.stop()
        
        # Stop event monitoring
        self.event_monitor.stop_monitoring()
        
        # Update storage
        self.storage.update_tutorial_status(tutorial_id, "completed")
        
        # Update metadata with final stats
        metadata = self.storage.load_tutorial_metadata(tutorial_id)
        if metadata:
            metadata.duration = self.current_session.get_duration()
            metadata.last_modified = time.time()
            # Save updated metadata
            project_path = self.storage.get_project_path(tutorial_id)
            if project_path:
                self.storage._save_metadata(project_path, metadata)
        
        print(f"Tutorial completed: {self.current_session.title}")
        print(f"Duration: {self.current_session.get_duration():.1f} seconds")
        print(f"Steps captured: {self.current_session.step_counter}")
        
        # Clear current session
        self.current_session = None
        
        return tutorial_id
    
    def _on_mouse_click(self, event: MouseClickEvent):
        """Handle mouse click events"""
        if not self.current_session or not self.current_session.is_recording():
            return
        
        try:
            # Get screen dimensions at the time of click
            screen_info = self.screen_capture.get_screen_info()
            screen_width = screen_info['width']
            screen_height = screen_info['height']
            
            # Calculate percentage coordinates
            x_pct = event.x / screen_width
            y_pct = event.y / screen_height
            
            # Capture screenshot immediately
            screenshot = self.screen_capture.capture_full_screen()
            if not screenshot:
                print("Failed to capture screenshot")
                return
            
            # Extract region around click for OCR
            click_region = self.screen_capture.capture_click_region(event.x, event.y)
            
            # Perform OCR on the clicked region
            ocr_result = OCRResult()
            if click_region:
                ocr_result = self.ocr_engine.extract_text(click_region)
            
            # Add debug marker to screenshot if in debug mode using percentage coordinates
            if self.debug_mode:
                screenshot = self.screen_capture.add_debug_click_marker(
                    screenshot, x_pct=x_pct, y_pct=y_pct
                )
            
            # Generate step description
            description = self._generate_click_description(event, ocr_result)
            
            # Create tutorial step
            self.current_session.step_counter += 1
            step_number = self.current_session.step_counter
            
            # Save screenshot (with debug marker if enabled)
            screenshot_path = self.storage.save_screenshot(
                self.current_session.tutorial_id, 
                screenshot, 
                step_number
            )
            
            # Create step
            step = TutorialStep(
                step_id=f"step_{step_number}",
                timestamp=event.timestamp,
                step_number=step_number,
                description=description,
                screenshot_path=screenshot_path,
                event_data={'x': event.x, 'y': event.y, 'button': event.button},
                ocr_text=ocr_result.cleaned_text if ocr_result.is_valid() else None,
                ocr_confidence=ocr_result.confidence if ocr_result.is_valid() else 0.0,
                coordinates=(event.x, event.y),
                coordinates_pct=(x_pct, y_pct),  # Store percentage coordinates
                screen_dimensions=(screen_width, screen_height),  # Store screen dimensions at capture time
                step_type="click"
            )
            
            # Save step
            self.storage.save_tutorial_step(self.current_session.tutorial_id, step)
            
            print(f"Step {step_number}: {description}")
            
        except Exception as e:
            print(f"Error processing mouse click: {e}")
    
    def _on_keyboard_event(self, event: KeyPressEvent):
        """Handle keyboard events"""
        if not self.current_session or not self.current_session.is_recording():
            return
        
        try:
            # Skip very rapid consecutive events (debouncing)
            if (event.timestamp - self.current_session.last_event_time) < 0.05:
                return
            self.current_session.last_event_time = event.timestamp
            
            # Handle different types of keyboard events
            if event.event_type == EventType.TEXT_INPUT:
                # This is a text input session
                description = f'Type "{event.key.replace("TEXT:", "")}"'
                step_type = "type"
            elif event.is_special:
                # Special key
                description = f'Press {event.key}'
                step_type = "key"
            else:
                # Regular character - might be part of larger text input
                # For now, treat single characters as individual keystrokes
                description = f'Type "{event.key}"'
                step_type = "type"
            
            # Create tutorial step for significant keyboard events
            if event.is_special or event.event_type == EventType.TEXT_INPUT:
                # Take screenshot for special keys and text input sessions
                screenshot = self.screen_capture.capture_full_screen()
                
                self.current_session.step_counter += 1
                step_number = self.current_session.step_counter
                
                # Save screenshot
                screenshot_path = None
                if screenshot:
                    screenshot_path = self.storage.save_screenshot(
                        self.current_session.tutorial_id, 
                        screenshot, 
                        step_number
                    )
                
                # Create step
                step = TutorialStep(
                    step_id=f"step_{step_number}",
                    timestamp=event.timestamp,
                    step_number=step_number,
                    description=description,
                    screenshot_path=screenshot_path,
                    event_data={'key': event.key, 'is_special': event.is_special},
                    step_type=step_type
                )
                
                # Save step
                self.storage.save_tutorial_step(self.current_session.tutorial_id, step)
                
                print(f"Step {step_number}: {description}")
            
        except Exception as e:
            print(f"Error processing keyboard event: {e}")
    
    def _generate_click_description(self, event: MouseClickEvent, ocr_result: OCRResult) -> str:
        """Generate a human-readable description for a click event"""
        if ocr_result.is_valid() and ocr_result.cleaned_text:
            # We have OCR text - use it
            return f'Click on "{ocr_result.cleaned_text}"'
        else:
            # No OCR text - use coordinates
            return f'Click at position ({event.x}, {event.y})'
    
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
        return self.debug_mode
    
    def get_current_session_status(self) -> Dict[str, Any]:
        """Get status of current recording session"""
        if not self.current_session:
            return {
                'status': 'no_session',
                'debug_mode': self.debug_mode
            }
        
        return {
            'status': self.current_session.status,
            'title': self.current_session.title,
            'tutorial_id': self.current_session.tutorial_id,
            'duration': self.current_session.get_duration(),
            'step_count': self.current_session.step_counter,
            'is_recording': self.current_session.is_recording(),
            'debug_mode': self.debug_mode
        }
    
    def run(self):
        """Run the main application loop"""
        self.running = True
        
        print("\nTutorialMaker is ready!")
        print("Commands:")
        print("  new <title>     - Create new tutorial")
        print("  start          - Start recording")
        print("  pause          - Pause recording")
        print("  resume         - Resume recording") 
        print("  stop           - Stop recording")
        print("  list           - List tutorials")
        print("  status         - Show current status")
        print("  debug          - Toggle debug mode (shows precise click locations)")
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
        if self.current_session:
            self.stop_recording()
        
        # Stop event monitoring
        self.event_monitor.stop_monitoring()
        
        # Clean up resources
        self.screen_capture.close()
        self.ocr_engine.clear_cache()
        
        self.running = False
        print("Shutdown complete")