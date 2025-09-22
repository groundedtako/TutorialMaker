"""
Session Manager for TutorialMaker
Manages recording sessions and their lifecycle
"""

import time
from enum import Enum
from typing import Optional, Dict, Any
from pathlib import Path

from .events import EventMonitor
from .event_queue import EventQueue
from .event_processor import EventProcessor
from .storage import TutorialStorage
from .session_logger import SessionLogger
from .logger import get_logger

class SessionState(Enum):
    """Recording session states"""
    STOPPED = "stopped"
    RECORDING = "recording"
    PAUSED = "paused"


class RecordingSession:
    """Manages a single recording session"""
    
    def __init__(self, tutorial_id: str, title: str = "", selected_monitor: Optional[int] = None, 
                 logger: Optional[SessionLogger] = None):
        self.tutorial_id = tutorial_id
        self.title = title
        self.status = SessionState.STOPPED
        self.start_time = None
        self.pause_start_time = None
        self.total_pause_duration = 0.0
        self.step_counter = 0
        self.last_event_time = 0.0
        self.selected_monitor = selected_monitor  # Monitor to record on
        self.logger = logger  # Session logger for detailed logging
    
    @property
    def monitor_id(self) -> Optional[int]:
        """Get the monitor ID for this session"""
        return self.selected_monitor
        
    def start(self):
        """Start recording"""
        self.status = SessionState.RECORDING
        self.start_time = time.time()
        self.step_counter = 0
        self.total_pause_duration = 0.0
        if self.logger:
            self.logger.log_session_state("recording_started", f"Started recording '{self.title}'")
        # Note: RecordingSession doesn't have logger access, using session logger instead
    
    def pause(self):
        """Pause recording"""
        if self.status == SessionState.RECORDING:
            self.status = SessionState.PAUSED
            self.pause_start_time = time.time()
            if self.logger:
                self.logger.log_session_state("recording_paused", "Recording paused by user")
            # Note: Using session logger instead of print
    
    def resume(self):
        """Resume recording"""
        if self.status == SessionState.PAUSED:
            self.status = SessionState.RECORDING
            if self.pause_start_time:
                pause_duration = time.time() - self.pause_start_time
                self.total_pause_duration += pause_duration
                self.pause_start_time = None
                if self.logger:
                    self.logger.log_session_state("recording_resumed", f"Resumed after {pause_duration:.1f}s pause")
            # Note: Using session logger instead of print
    
    def stop(self):
        """Stop recording"""
        self.status = SessionState.STOPPED
        if self.pause_start_time:
            self.total_pause_duration += time.time() - self.pause_start_time
        if self.logger:
            self.logger.log_session_state("recording_stopped", f"Recording stopped. {self.step_counter} steps captured")
        # Note: Using session logger instead of print
    
    def is_recording(self) -> bool:
        """Check if currently recording (not paused or stopped)"""
        return self.status == SessionState.RECORDING
    
    def get_duration(self) -> float:
        """Get total recording duration excluding pauses"""
        if not self.start_time:
            return 0.0
        
        current_time = time.time()
        total_time = current_time - self.start_time
        
        # Subtract pause time
        pause_time = self.total_pause_duration
        if self.status == SessionState.PAUSED and self.pause_start_time:
            pause_time += current_time - self.pause_start_time
        
        return max(0.0, total_time - pause_time)
    
    def is_event_on_selected_monitor(self, x: int, y: int, monitor_info: list) -> bool:
        """
        Check if an event at (x, y) is on the selected monitor
        
        Args:
            x, y: Global coordinates of the event
            monitor_info: List of monitor information dicts
            
        Returns:
            True if event is on selected monitor or no monitor selected
        """
        if self.selected_monitor is None:
            return True  # No monitor selected, accept all events
        
        # Find the monitor that contains this point
        for monitor in monitor_info:
            if monitor['id'] == self.selected_monitor:
                left = monitor['left']
                top = monitor['top']
                right = left + monitor['width']
                bottom = top + monitor['height']
                
                return left <= x < right and top <= y < bottom
        
        return False  # Selected monitor not found, reject event


class SessionManager:
    """Manages recording sessions and their lifecycle"""
    
    def __init__(self, storage: TutorialStorage, event_monitor: EventMonitor, 
                 event_queue: EventQueue, event_processor: EventProcessor, 
                 debug_mode: bool = False):
        self.storage = storage
        self.event_monitor = event_monitor
        self.event_queue = event_queue
        self.event_processor = event_processor
        self.debug_mode = debug_mode
        self.logger = get_logger('core.session_manager')
        
        # Current session
        self.current_session: Optional[RecordingSession] = None
    
    def create_session(self, tutorial_id: str, title: str = "", selected_monitor: Optional[int] = None) -> RecordingSession:
        """
        Create a new recording session
        
        Args:
            tutorial_id: Unique identifier for the tutorial
            title: Tutorial title
            selected_monitor: Monitor ID to record on (None = auto-detect)
            
        Returns:
            RecordingSession instance
        """
        # Stop any existing session
        if self.current_session:
            if self.current_session.is_recording():
                self.logger.info("Stopping current session to start new one...")
                self.stop_recording()
        
        # Create session logger
        project_path = self.storage.get_project_path(tutorial_id)
        if project_path:
            session_logger = SessionLogger(tutorial_id, project_path, self.debug_mode)
        else:
            session_logger = None
            self.logger.warning("Could not create session logger - project path not found")
        
        # Create new session with logger
        self.current_session = RecordingSession(tutorial_id, title, selected_monitor, session_logger)
        
        if self.debug_mode:
            monitor_text = f" (Monitor {selected_monitor})" if selected_monitor else " (Auto-detect monitor)"
            self.logger.debug(f"Created new session for tutorial '{title}' (ID: {tutorial_id}){monitor_text}")
        
        return self.current_session
    
    def has_active_session(self) -> bool:
        """Check if there's an active session"""
        return self.current_session is not None
    
    def start_recording(self) -> bool:
        """
        Start recording the current session
        
        Returns:
            True if recording started successfully
        """
        if not self.current_session:
            self.logger.error("No tutorial session. Create a new tutorial first.")
            return False
        
        # Start event monitoring
        if not self.event_monitor.start_monitoring():
            self.logger.warning("Failed to start event monitoring. Limited functionality available.")
            # Continue anyway - user can still do manual capture
        
        # Start session
        self.current_session.start()
        
        # Start event queue
        self.event_queue.start_recording()
        
        # Update storage status
        self.storage.update_tutorial_status(self.current_session.tutorial_id, "recording")
        
        if self.debug_mode:
            self.logger.debug(f"Started recording for session '{self.current_session.title}'")
        
        return True
    
    def pause_recording(self):
        """Pause the current recording"""
        if self.current_session and self.current_session.is_recording():
            self.current_session.pause()
            self.storage.update_tutorial_status(self.current_session.tutorial_id, "paused")
            
            if self.debug_mode:
                self.logger.debug(f"Paused recording for session '{self.current_session.title}'")
    
    def resume_recording(self):
        """Resume the current recording"""
        if self.current_session and self.current_session.status == SessionState.PAUSED:
            self.current_session.resume()
            self.storage.update_tutorial_status(self.current_session.tutorial_id, "recording")
            
            if self.debug_mode:
                self.logger.debug(f"Resumed recording for session '{self.current_session.title}'")
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop recording, finalize the tutorial, and process events
        
        Returns:
            Tutorial ID if successful, None otherwise
        """
        if not self.current_session:
            if self.debug_mode:
                self.logger.debug("No active session to stop")
            return None
        
        tutorial_id = self.current_session.tutorial_id
        tutorial_title = self.current_session.title
        
        # Stop event queue and monitoring immediately
        self.event_queue.stop_recording()
        self.event_monitor.stop_monitoring()
        
        # Set session status to stopped to prevent any more event processing
        self.current_session.status = SessionState.STOPPED
        
        # Process all queued events into tutorial steps
        self.logger.info(f"Processing events for tutorial: {tutorial_title}")
        self._process_queued_events()
        
        # Finalize session data
        self.current_session.stop()
        
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
        
        # Store final stats before clearing session
        final_step_count = self.current_session.step_counter
        final_duration = self.current_session.get_duration()
        
        # Save session log before clearing session
        if self.current_session.logger:
            try:
                summary = self.current_session.logger.get_session_summary()
                self.current_session.logger.log_session_state("session_completed", 
                    f"Session completed with {final_step_count} steps in {final_duration:.1f}s")
                self.current_session.logger.save_session_log()
                self.logger.info(f"Session log saved: {summary['log_file']}")
            except Exception as e:
                self.logger.warning(f"Could not save session log: {e}")
        
        self.logger.info(f"Tutorial completed: {tutorial_title}")
        self.logger.info(f"Duration: {final_duration:.1f} seconds")
        self.logger.info(f"Steps captured: {final_step_count}")
        
        # Get project path for user reference
        project_path = self.storage.get_project_path(tutorial_id)
        if project_path:
            self.logger.info(f"Tutorial saved to: {project_path}")
            self.logger.info(f"Edit in browser: http://localhost:5001/tutorial/{tutorial_id}")
            self.logger.info("Use 'export' command or web interface to export to HTML/Word/PDF")
        
        # Clear current session
        self.current_session = None
        
        if self.debug_mode:
            self.logger.debug(f"Completed session for tutorial '{tutorial_title}' ({tutorial_id})")
        
        return tutorial_id
    
    def _process_queued_events(self):
        """Process all queued events into tutorial steps using EventProcessor"""
        if not self.current_session:
            return
        
        # Get events from queue
        events = self.event_queue.get_events_for_processing()
        
        if not events:
            self.logger.info("No events to process")
            self.event_queue.complete_processing()
            return
        
        # Use EventProcessor to convert events to tutorial steps
        steps_created = self.event_processor.process_events_to_steps(
            events, 
            self.current_session.tutorial_id, 
            self.current_session
        )
        
        # Save raw events to events.json
        self.event_processor.save_raw_events(events, self.current_session.tutorial_id)
        
        # Complete processing
        self.event_queue.complete_processing()
        self.logger.info(f"Tutorial processing complete. Created {steps_created} tutorial steps")
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get status of current recording session"""
        if not self.current_session:
            return {
                'status': 'no_session',
                'debug_mode': self.debug_mode
            }
        
        return {
            'status': self.current_session.status.value,
            'title': self.current_session.title,
            'tutorial_id': self.current_session.tutorial_id,
            'duration': self.current_session.get_duration(),
            'step_count': self.current_session.step_counter,
            'is_recording': self.current_session.is_recording(),
            'debug_mode': self.debug_mode
        }
    
    def increment_step_counter(self) -> int:
        """
        Increment the step counter for the current session
        
        Returns:
            New step count, or 0 if no active session
        """
        if not self.current_session:
            return 0
        
        self.current_session.step_counter += 1
        
        if self.debug_mode:
            self.logger.debug(f"Incremented step counter to {self.current_session.step_counter}")
        
        return self.current_session.step_counter
    
    def set_debug_mode(self, debug_mode: bool):
        """Enable or disable debug mode"""
        self.debug_mode = debug_mode
        # Also update event processor debug mode
        if hasattr(self.event_processor, 'debug_mode'):
            self.event_processor.debug_mode = debug_mode