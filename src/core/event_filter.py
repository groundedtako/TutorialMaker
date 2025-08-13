"""
Event Filtering System
Provides configurable filtering for captured events including keystroke filtering,
recording control event exclusion, and post-stop/pause filtering.
"""

import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .events import MouseClickEvent, KeyPressEvent, EventType


@dataclass
class FilterSettings:
    """Configuration settings for event filtering"""
    filter_keystrokes: bool = False  # Default: disabled (as requested by user)


@dataclass
class FilterDecision:
    """Result of event filtering decision"""
    should_capture: bool
    reason: str


class EventFilter:
    """Event filtering system for tutorial recording - handles keystroke filtering only"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.settings = FilterSettings()
    
    def toggle_keystroke_filtering(self) -> bool:
        """Toggle keystroke filtering on/off"""
        self.settings.filter_keystrokes = not self.settings.filter_keystrokes
        
        if self.debug_mode:
            status = "enabled" if self.settings.filter_keystrokes else "disabled"
            print(f"EventFilter: Keystroke filtering {status}")
        
        return self.settings.filter_keystrokes
    
    def should_capture_event(self, event, session) -> FilterDecision:
        """
        Determine if an event should be captured based on current filter settings
        
        Args:
            event: MouseClickEvent or KeyPressEvent to evaluate
            session: Recording session object with state information
        
        Returns:
            FilterDecision indicating whether to capture the event and why
        """
        # Check session recording state first (highest priority)
        if not session.is_recording():
            return FilterDecision(should_capture=False, reason="session_not_recording")
        
        # Debouncing is handled later in EventProcessor during queue processing
        
        # Check keystroke filtering (only applies to keyboard events)
        if (self.settings.filter_keystrokes and 
            isinstance(event, KeyPressEvent)):
            return FilterDecision(should_capture=False, reason="keystroke_filtered")
        
        # Event passes all filters
        return FilterDecision(should_capture=True, reason="allowed")
    
    def get_filter_status(self) -> Dict[str, Any]:
        """Get current filter status for UI display"""
        return {
            'keystroke_filtering_enabled': self.settings.filter_keystrokes
        }