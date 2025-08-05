"""
Event monitoring and processing
Cross-platform mouse and keyboard event monitoring
"""

import time
import threading
import platform
from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
import json

try:
    from pynput import mouse, keyboard
    from pynput.mouse import Button
    from pynput.keyboard import Key
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("Warning: pynput not available. Event monitoring will be limited.")

class EventType(Enum):
    """Types of events we can capture"""
    MOUSE_CLICK = "mouse_click"
    KEY_PRESS = "key_press"
    TEXT_INPUT = "text_input"
    SPECIAL_KEY = "special_key"

@dataclass
class MouseClickEvent:
    """Mouse click event data"""
    timestamp: float
    x: int
    y: int
    button: str  # 'left', 'right', 'middle'
    pressed: bool  # True for press, False for release
    event_type: EventType = EventType.MOUSE_CLICK
    is_drag: bool = False  # New field for future drag support

@dataclass
class KeyPressEvent:
    """Keyboard event data"""
    timestamp: float
    key: str
    key_code: Optional[int] = None
    modifiers: List[str] = None
    is_special: bool = False
    event_type: EventType = EventType.KEY_PRESS

@dataclass
class TextInputEvent:
    """Text input session data"""
    timestamp: float
    text: str
    duration: float
    field_context: Optional[Dict] = None
    event_type: EventType = EventType.TEXT_INPUT

class EventMonitor:
    """Cross-platform event monitoring manager"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.is_monitoring = False
        self.mouse_listener = None
        self.keyboard_listener = None
        # Event callbacks
        self.mouse_click_callback: Optional[Callable] = None
        self.key_press_callback: Optional[Callable] = None
        # Text input tracking
        self.current_text_session = []
        self.last_key_time = 0
        self.text_session_timeout = 2.0  # seconds
        # Permission tracking
        self.has_mouse_access = False
        self.has_keyboard_access = False
        # Mouse click/drag tracking
        self._mouse_pressed = False
        self._press_pos = None
        self._press_time = None
        self._dragged = False
        self._drag_threshold = 5  # pixels
        if not PYNPUT_AVAILABLE:
            print("pynput not available. Please install: pip install pynput")
    
    def set_mouse_callback(self, callback: Callable[[MouseClickEvent], None]):
        """Set callback for mouse click events"""
        self.mouse_click_callback = callback
    
    def set_keyboard_callback(self, callback: Callable[[KeyPressEvent], None]):
        """Set callback for keyboard events"""
        self.key_press_callback = callback
    
    def start_monitoring(self) -> bool:
        """
        Start monitoring mouse and keyboard events
        
        Returns:
            True if monitoring started successfully, False otherwise
        """
        if not PYNPUT_AVAILABLE:
            print("Cannot start monitoring: pynput not available")
            return False
        
        if self.is_monitoring:
            print("Already monitoring")
            return True
        
        try:
            # Start mouse listener
            if self._start_mouse_listener():
                self.has_mouse_access = True
                print("Mouse monitoring started")
            else:
                print("Failed to start mouse monitoring (permissions?)")
            
            # Start keyboard listener
            if self._start_keyboard_listener():
                self.has_keyboard_access = True
                print("Keyboard monitoring started")
            else:
                print("Failed to start keyboard monitoring (permissions?)")
            
            if self.has_mouse_access or self.has_keyboard_access:
                self.is_monitoring = True
                return True
            else:
                print("Failed to start any monitoring")
                return False
                
        except Exception as e:
            print(f"Error starting monitoring: {e}")
            return False
    
    def stop_monitoring(self):
        """Stop all event monitoring"""
        self.is_monitoring = False
        
        if self.mouse_listener:
            try:
                self.mouse_listener.stop()
            except:
                pass
            self.mouse_listener = None
        
        if self.keyboard_listener:
            try:
                self.keyboard_listener.stop()
            except:
                pass
            self.keyboard_listener = None
        
        self.has_mouse_access = False
        self.has_keyboard_access = False
        
        print("Event monitoring stopped")
    
    def _start_mouse_listener(self) -> bool:
        """Start mouse event listener"""
        try:
            self.mouse_listener = mouse.Listener(
                on_click=self._on_mouse_click,
                on_move=self._on_mouse_move,
                suppress=False  # Don't suppress events
            )
            self.mouse_listener.start()
            return True
        except Exception as e:
            print(f"Failed to start mouse listener: {e}")
            return False
    
    def _start_keyboard_listener(self) -> bool:
        """Start keyboard event listener"""
        try:
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release,
                suppress=False  # Don't suppress events
            )
            self.keyboard_listener.start()
            return True
        except Exception as e:
            print(f"Failed to start keyboard listener: {e}")
            return False
    
    def _on_mouse_click(self, x: int, y: int, button: Button, pressed: bool):
        """Handle mouse click events (only emit for simple clicks, not drags)"""
        if not self.is_monitoring:
            return
        if pressed:
            # Mouse button pressed: record state
            self._mouse_pressed = True
            self._press_pos = (x, y)
            self._press_time = time.time()
            self._dragged = False
        else:
            # Mouse button released
            if not self._mouse_pressed:
                return
            self._mouse_pressed = False
            if self._press_pos is None:
                return
            dx = x - self._press_pos[0]
            dy = y - self._press_pos[1]
            dist_sq = dx*dx + dy*dy
            if dist_sq <= self._drag_threshold * self._drag_threshold and not self._dragged:
                # Simple click: emit event
                button_name = "unknown"
                if button == Button.left:
                    button_name = "left"
                elif button == Button.right:
                    button_name = "right"
                elif button == Button.middle:
                    button_name = "middle"
                event = MouseClickEvent(
                    timestamp=time.time(),
                    x=self._press_pos[0],  # Use press position instead of release
                    y=self._press_pos[1],  # Use press position instead of release
                    button=button_name,
                    pressed=False,
                    is_drag=False
                )
                if self.mouse_click_callback:
                    try:
                        self.mouse_click_callback(event)
                    except Exception as e:
                        print(f"Error in mouse callback: {e}")
            else:
                # Drag detected (logic ready for future use)
                # Example for future:
                # button_name = ... (as above)
                # event = MouseClickEvent(
                #     timestamp=time.time(),
                #     x=x,
                #     y=y,
                #     button=button_name,
                #     pressed=False,
                #     is_drag=True
                # )
                # if self.mouse_click_callback:
                #     try:
                #         self.mouse_click_callback(event)
                #     except Exception as e:
                #         print(f"Error in mouse callback: {e}")
                pass
            self._press_pos = None
            self._press_time = None
            self._dragged = False
    
    def _on_mouse_move(self, x: int, y: int):
        """Track if mouse is dragged while pressed"""
        if self._mouse_pressed and self._press_pos is not None:
            dx = x - self._press_pos[0]
            dy = y - self._press_pos[1]
            dist_sq = dx*dx + dy*dy
            if dist_sq > self._drag_threshold * self._drag_threshold:
                self._dragged = True

    def _on_key_press(self, key):
        """Handle key press events"""
        if not self.is_monitoring:
            return
        
        current_time = time.time()
        
        # Convert key to string and determine if it's special
        key_str, is_special, key_code = self._process_key(key)
        
        # Create key event
        event = KeyPressEvent(
            timestamp=current_time,
            key=key_str,
            key_code=key_code,
            is_special=is_special
        )
        
        # Handle text input sessions
        if not is_special and key_str and len(key_str) == 1:
            # This is a printable character
            self._handle_text_input(key_str, current_time)
        else:
            # Special key - finalize any ongoing text session
            self._finalize_text_session()
        
        # Call callback if set
        if self.key_press_callback:
            try:
                self.key_press_callback(event)
            except Exception as e:
                print(f"Error in keyboard callback: {e}")
    
    def _on_key_release(self, key):
        """Handle key release events (currently unused)"""
        pass
    
    def _process_key(self, key) -> tuple[str, bool, Optional[int]]:
        """
        Process a key object into string representation
        
        Returns:
            (key_string, is_special, key_code)
        """
        is_special = False
        key_code = None
        
        try:
            if hasattr(key, 'char') and key.char:
                # Regular character
                return key.char, False, None
            elif hasattr(key, 'name'):
                # Special key with name
                return key.name, True, None
            else:
                # Try to get string representation
                key_str = str(key)
                if key_str.startswith('Key.'):
                    # pynput special key
                    return key_str[4:], True, None
                else:
                    # Unknown key type
                    return key_str, True, None
                    
        except Exception as e:
            print(f"Error processing key: {e}")
            return "unknown", True, None
    
    def _handle_text_input(self, char: str, timestamp: float):
        """Handle text input character"""
        # Check if this continues the current text session
        if (self.current_text_session and 
            timestamp - self.last_key_time <= self.text_session_timeout):
            # Continue current session
            self.current_text_session.append(char)
        else:
            # Start new session (finalize old one first)
            self._finalize_text_session()
            self.current_text_session = [char]
        
        self.last_key_time = timestamp
    
    def _finalize_text_session(self):
        """Finalize current text input session"""
        if not self.current_text_session:
            return
        
        # Create text input event
        text = ''.join(self.current_text_session)
        if text.strip():  # Only create event if there's actual text
            duration = self.last_key_time - (self.last_key_time - len(self.current_text_session) * 0.1)
            
            event = TextInputEvent(
                timestamp=self.last_key_time,
                text=text,
                duration=duration
            )
            
            # For now, we'll handle text events the same as key events
            # In the future, we might want a separate callback
            if self.key_press_callback:
                try:
                    # Convert to KeyPressEvent for compatibility
                    key_event = KeyPressEvent(
                        timestamp=event.timestamp,
                        key=f'TEXT:{event.text}',
                        is_special=False,
                        event_type=EventType.TEXT_INPUT
                    )
                    self.key_press_callback(key_event)
                except Exception as e:
                    print(f"Error in text input callback: {e}")
        
        # Clear session
        self.current_text_session = []
    
    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            'is_monitoring': self.is_monitoring,
            'has_mouse_access': self.has_mouse_access,
            'has_keyboard_access': self.has_keyboard_access,
            'system': self.system,
            'pynput_available': PYNPUT_AVAILABLE
        }


def serialize_event(event) -> str:
    """Serialize an event to JSON string"""
    try:
        if hasattr(event, '__dict__'):
            event_dict = asdict(event)
        else:
            event_dict = dict(event)
        
        # Convert enum to string
        if 'event_type' in event_dict and hasattr(event_dict['event_type'], 'value'):
            event_dict['event_type'] = event_dict['event_type'].value
        
        return json.dumps(event_dict)
    except Exception as e:
        print(f"Error serializing event: {e}")
        return "{}"

def deserialize_event(event_json: str) -> Optional[Dict]:
    """Deserialize an event from JSON string"""
    try:
        return json.loads(event_json)
    except Exception as e:
        print(f"Error deserializing event: {e}")
        return None