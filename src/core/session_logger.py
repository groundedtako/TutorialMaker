"""
Session Logging System
Provides detailed logging for tutorial recording sessions
"""

import json
import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

from .events import MouseClickEvent, KeyPressEvent, ManualCaptureEvent, EventType


@dataclass
class SessionLogEntry:
    """Individual log entry for session events"""
    timestamp: float
    event_type: str
    event_subtype: str
    message: str
    data: Dict[str, Any] = None
    level: str = "INFO"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        entry = asdict(self)
        entry['datetime'] = datetime.fromtimestamp(self.timestamp).isoformat()
        return entry


class SessionLogger:
    """Comprehensive session logging for tutorial recording"""
    
    def __init__(self, tutorial_id: str, storage_path: Path, debug_mode: bool = False):
        self.tutorial_id = tutorial_id
        self.storage_path = storage_path
        self.debug_mode = debug_mode
        self.session_start_time = time.time()
        
        # Log entries for the session
        self.log_entries: List[SessionLogEntry] = []
        
        # Event counters
        self.event_counters = {
            'mouse_clicks': 0,
            'manual_captures': 0,
            'keyboard_events': 0,
            'filtered_events': 0,
            'errors': 0
        }
        
        # Setup log file path
        self.log_file = storage_path / f"session_{tutorial_id[:8]}.log"
        
        # Initialize session log
        self._log_session_start()
    
    def log_event(self, event_type: str, event_subtype: str, message: str, 
                  data: Dict[str, Any] = None, level: str = "INFO"):
        """Log a session event"""
        entry = SessionLogEntry(
            timestamp=time.time(),
            event_type=event_type,
            event_subtype=event_subtype,
            message=message,
            data=data or {},
            level=level
        )
        
        self.log_entries.append(entry)
        
        # Also print to console if debug mode
        if self.debug_mode or level in ["WARNING", "ERROR"]:
            dt = datetime.fromtimestamp(entry.timestamp).strftime("%H:%M:%S.%f")[:-3]
            print(f"[{dt}] {level}: {event_type}.{event_subtype} - {message}")
    
    def log_mouse_click(self, event: MouseClickEvent, step_number: int = None):
        """Log mouse click event"""
        self.event_counters['mouse_clicks'] += 1
        
        data = {
            'coordinates': [event.x, event.y],
            'button': event.button,
            'step_number': step_number,
            'event_timestamp': event.timestamp
        }
        
        self.log_event(
            "capture", "mouse_click", 
            f"Mouse click at ({event.x}, {event.y}) - {event.button} button",
            data
        )
    
    def log_manual_capture(self, event: ManualCaptureEvent, step_number: int = None, 
                          trigger_method: str = "hotkey"):
        """Log manual capture event"""
        self.event_counters['manual_captures'] += 1
        
        data = {
            'coordinates': [event.x, event.y],
            'step_number': step_number,
            'trigger_method': trigger_method,
            'event_timestamp': event.timestamp
        }
        
        self.log_event(
            "capture", "manual_capture",
            f"Manual capture at ({event.x}, {event.y}) via {trigger_method}",
            data
        )
    
    def log_keyboard_event(self, event: KeyPressEvent, filtered: bool = False):
        """Log keyboard event"""
        if filtered:
            self.event_counters['filtered_events'] += 1
            event_type = "filtering"
            message = f"Filtered keyboard event: '{event.key}'"
        else:
            self.event_counters['keyboard_events'] += 1
            event_type = "capture"
            message = f"Keyboard event: '{event.key}'"
        
        data = {
            'key': event.key,
            'is_special': event.is_special,
            'filtered': filtered,
            'event_timestamp': event.timestamp
        }
        
        self.log_event(
            event_type, "keyboard", message, data
        )
    
    def log_hotkey_detection(self, hotkey: str, successful: bool = True):
        """Log hotkey detection events"""
        level = "INFO" if successful else "WARNING"
        message = f"Hotkey '{hotkey}' {'detected and processed' if successful else 'detected but failed to process'}"
        
        data = {
            'hotkey': hotkey,
            'successful': successful
        }
        
        self.log_event(
            "system", "hotkey", message, data, level
        )
    
    def log_session_state(self, state: str, details: str = ""):
        """Log session state changes"""
        data = {
            'state': state,
            'session_duration': time.time() - self.session_start_time
        }
        
        message = f"Session state: {state}"
        if details:
            message += f" - {details}"
        
        self.log_event(
            "session", "state_change", message, data
        )
    
    def log_error(self, component: str, error_message: str, exception: Exception = None):
        """Log error events"""
        self.event_counters['errors'] += 1
        
        data = {
            'component': component,
            'error_message': error_message
        }
        
        if exception:
            data['exception_type'] = type(exception).__name__
            data['exception_str'] = str(exception)
        
        self.log_event(
            "error", component, f"{component} error: {error_message}", data, "ERROR"
        )
    
    def log_ocr_result(self, coordinates: tuple, ocr_text: str, confidence: float, engine: str):
        """Log OCR processing results"""
        data = {
            'coordinates': coordinates,
            'ocr_text': ocr_text,
            'confidence': confidence,
            'engine': engine
        }
        
        message = f"OCR at {coordinates}: '{ocr_text}' (confidence: {confidence:.2f})"
        
        self.log_event(
            "processing", "ocr", message, data
        )
    
    def log_screenshot_capture(self, coordinates: tuple, monitor_id: int, success: bool):
        """Log screenshot capture events"""
        level = "INFO" if success else "WARNING"
        status = "successful" if success else "failed"
        
        data = {
            'coordinates': coordinates,
            'monitor_id': monitor_id,
            'success': success
        }
        
        message = f"Screenshot capture {status} at {coordinates} (monitor {monitor_id})"
        
        self.log_event(
            "processing", "screenshot", message, data, level
        )
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get session summary statistics"""
        session_duration = time.time() - self.session_start_time
        
        return {
            'tutorial_id': self.tutorial_id,
            'session_duration': session_duration,
            'total_log_entries': len(self.log_entries),
            'event_counters': self.event_counters.copy(),
            'session_start_time': self.session_start_time,
            'log_file': str(self.log_file)
        }
    
    def save_session_log(self):
        """Save session log to file"""
        try:
            # Prepare log data
            log_data = {
                'session_info': {
                    'tutorial_id': self.tutorial_id,
                    'session_start_time': self.session_start_time,
                    'session_start_datetime': datetime.fromtimestamp(self.session_start_time).isoformat(),
                    'session_duration': time.time() - self.session_start_time,
                    'total_entries': len(self.log_entries)
                },
                'event_counters': self.event_counters.copy(),
                'log_entries': [entry.to_dict() for entry in self.log_entries]
            }
            
            # Save to JSON file
            with open(self.log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            self.log_event(
                "system", "logging", 
                f"Session log saved to {self.log_file}"
            )
            
            return True
            
        except Exception as e:
            print(f"Error saving session log: {e}")
            return False
    
    def _log_session_start(self):
        """Log session start"""
        self.log_event(
            "session", "start", 
            f"Session started for tutorial {self.tutorial_id}",
            {'tutorial_id': self.tutorial_id}
        )


# Integration helpers for existing components
def create_session_logger(tutorial_id: str, storage_path: Path, debug_mode: bool = False) -> SessionLogger:
    """Factory function to create session logger"""
    return SessionLogger(tutorial_id, storage_path, debug_mode)