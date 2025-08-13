"""
Simple event queue for recording sessions
Provides clean separation between event collection and processing
"""

import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .events import MouseClickEvent, KeyPressEvent


class QueueState(Enum):
    """Event queue states"""
    IDLE = "idle"
    RECORDING = "recording"
    STOPPED = "stopped"
    PROCESSING = "processing"


@dataclass
class QueuedEvent:
    """Container for queued events with metadata"""
    event_type: str  # 'mouse_click' or 'keyboard_event'
    timestamp: float
    event_object: Any  # The original event object
    
    # Event-specific data for JSON serialization
    event_data: Dict[str, Any]
    
    # Screenshot captured at the time of the event (for mouse clicks)
    screenshot: Any = None  # PIL Image
    
    # Pre-calculated coordinate information (for mouse clicks)
    coordinate_info: Optional[Dict[str, Any]] = None


class EventQueue:
    """Simple event queue with clear state management"""
    
    def __init__(self):
        self.state = QueueState.IDLE
        self.events: List[QueuedEvent] = []
        self.recording_start_time: Optional[float] = None
        self.recording_stop_time: Optional[float] = None
    
    def start_recording(self):
        """Start recording events"""
        self.state = QueueState.RECORDING
        self.events.clear()
        self.recording_start_time = time.time()
        self.recording_stop_time = None
        print(f"EventQueue: Started recording")
    
    def stop_recording(self):
        """Stop recording events and prepare for processing"""
        if self.state != QueueState.RECORDING:
            return
        
        self.state = QueueState.STOPPED
        self.recording_stop_time = time.time()
        print(f"EventQueue: Stopped recording. Collected {len(self.events)} events")
    
    def add_mouse_click(self, event: MouseClickEvent, screenshot=None, coordinate_info=None):
        """Add mouse click event to queue with optional screenshot and coordinate info"""
        if self.state != QueueState.RECORDING:
            return
        
        queued_event = QueuedEvent(
            event_type='mouse_click',
            timestamp=event.timestamp,
            event_object=event,
            event_data={
                'x': event.x,
                'y': event.y,
                'button': event.button,
                'timestamp': event.timestamp
            },
            screenshot=screenshot,
            coordinate_info=coordinate_info
        )
        
        self.events.append(queued_event)
    
    def add_keyboard_event(self, event: KeyPressEvent):
        """Add keyboard event to queue"""
        if self.state != QueueState.RECORDING:
            return
        
        queued_event = QueuedEvent(
            event_type='keyboard_event',
            timestamp=event.timestamp,
            event_object=event,
            event_data={
                'key': event.key,
                'is_special': event.is_special,
                'event_type': str(event.event_type),
                'timestamp': event.timestamp
            }
        )
        
        self.events.append(queued_event)
    
    def get_events_for_processing(self) -> List[QueuedEvent]:
        """Get events ready for processing into tutorial steps"""
        if self.state != QueueState.STOPPED:
            return []
        
        self.state = QueueState.PROCESSING
        print(f"EventQueue: Processing {len(self.events)} events")
        
        # Return copy of events for processing
        return self.events.copy()
    
    def complete_processing(self):
        """Mark processing as complete and reset queue"""
        self.state = QueueState.IDLE
        processed_count = len(self.events)
        self.events.clear()
        self.recording_start_time = None
        self.recording_stop_time = None
        print(f"EventQueue: Processing complete. Processed {processed_count} events")
    
    def get_events_for_json(self) -> List[Dict[str, Any]]:
        """Get events in JSON-serializable format"""
        return [event.event_data for event in self.events]
    
    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self.state == QueueState.RECORDING
    
    def is_ready_for_processing(self) -> bool:
        """Check if ready for processing"""
        return self.state == QueueState.STOPPED
    
    def get_status(self) -> Dict[str, Any]:
        """Get queue status information"""
        return {
            'state': self.state.value,
            'event_count': len(self.events),
            'recording_start_time': self.recording_start_time,
            'recording_stop_time': self.recording_stop_time
        }