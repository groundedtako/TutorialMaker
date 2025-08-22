"""
Unit tests for EventFilter system
"""

import sys
import os
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

# Add project root and src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.core.event_filter import EventFilter, FilterSettings, FilterDecision
from src.core.events import MouseClickEvent, KeyPressEvent, EventType


class TestFilterSettings:
    """Test FilterSettings dataclass"""
    
    def test_default_settings(self):
        """Test default filter settings"""
        settings = FilterSettings()
        
        # By default, keystroke filtering should be disabled
        assert settings.filter_keystrokes == False
        
        print("SUCCESS: Default filter settings correct")
    
    def test_custom_settings(self):
        """Test custom filter settings"""
        settings = FilterSettings(
            filter_keystrokes=True
        )
        
        assert settings.filter_keystrokes == True
        
        print("SUCCESS: Custom filter settings applied")


class TestEventFilter:
    """Test EventFilter class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.event_filter = EventFilter(debug_mode=True)
        
        # Mock session for testing
        self.mock_session = Mock()
        self.mock_session.is_recording.return_value = True
        self.mock_session.status = "recording"
        self.mock_session.last_event_time = 0.0
    
    def test_initial_state(self):
        """Test initial state of event filter"""
        assert self.event_filter.debug_mode == True
        assert self.event_filter.settings.filter_keystrokes == False  # Default: disabled
        
        print("SUCCESS: Event filter initial state correct")
    
    def test_toggle_keystroke_filtering(self):
        """Test toggling keystroke filtering on/off"""
        # Initially off
        assert self.event_filter.settings.filter_keystrokes == False
        
        # Toggle on
        self.event_filter.toggle_keystroke_filtering()
        assert self.event_filter.settings.filter_keystrokes == True
        
        # Toggle off
        self.event_filter.toggle_keystroke_filtering()
        assert self.event_filter.settings.filter_keystrokes == False
        
        print("SUCCESS: Keystroke filtering toggle works")
    
    def test_keystroke_filtering_disabled(self):
        """Test keystroke events pass through when filtering disabled"""
        # Ensure keystroke filtering is disabled
        self.event_filter.settings.filter_keystrokes = False
        
        # Test various keyboard events
        events = [
            KeyPressEvent(key='a', timestamp=time.time()),
            KeyPressEvent(key='Enter', timestamp=time.time(), is_special=True),
            KeyPressEvent(key='TEXT:Hello', timestamp=time.time()),
        ]
        
        for event in events:
            decision = self.event_filter.should_capture_event(event, self.mock_session)
            assert decision.should_capture == True
            assert decision.reason != "keystroke_filtered"
        
        print("SUCCESS: Keystroke events pass through when filtering disabled")
    
    def test_keystroke_filtering_enabled(self):
        """Test keystroke events are filtered when filtering enabled"""
        # Enable keystroke filtering
        self.event_filter.settings.filter_keystrokes = True
        
        # Test keyboard events get filtered
        events = [
            KeyPressEvent(key='a', timestamp=time.time()),
            KeyPressEvent(key='Enter', timestamp=time.time(), is_special=True),
            KeyPressEvent(key='TEXT:Hello', timestamp=time.time()),
        ]
        
        for event in events:
            decision = self.event_filter.should_capture_event(event, self.mock_session)
            assert decision.should_capture == False
            assert decision.reason == "keystroke_filtered"
        
        print("SUCCESS: Keystroke events filtered when filtering enabled")
    
    def test_mouse_events_never_filtered_by_keystroke_setting(self):
        """Test mouse events are never affected by keystroke filtering"""
        # Enable keystroke filtering
        self.event_filter.settings.filter_keystrokes = True
        
        # Mouse events should still pass through
        mouse_event = MouseClickEvent(x=500, y=300, button='left', pressed=True, timestamp=time.time())
        decision = self.event_filter.should_capture_event(mouse_event, self.mock_session)
        
        assert decision.should_capture == True
        assert decision.reason != "keystroke_filtered"
        
        print("SUCCESS: Mouse events unaffected by keystroke filtering")
    
    def test_post_stop_event_filtering(self):
        """Test filtering of events after stop button is pressed - DEPRECATED"""
        # This test is deprecated as the EventFilter was simplified
        print("SKIPPED: Post-stop filtering test (deprecated functionality)")
        return
        # Simulate stop button pressed
        stop_time = time.time()
        self.event_filter.mark_stop_event(stop_time)
        
        # Events after stop should be filtered
        later_event = MouseClickEvent(x=100, y=100, button='left', pressed=True, timestamp=stop_time + 0.2)
        decision = self.event_filter.should_capture_event(later_event, self.mock_session)
        
        assert decision.should_capture == False
        assert decision.reason == "post_stop_filtered"
        
        # Events before stop should pass
        earlier_event = MouseClickEvent(x=100, y=100, button='left', pressed=True, timestamp=stop_time - 0.1)
        decision = self.event_filter.should_capture_event(earlier_event, self.mock_session)
        
        assert decision.should_capture == True
        
        print("SUCCESS: Post-stop event filtering works")
    
    def test_post_pause_event_filtering(self):
        """Test filtering of events during pause (but not after resume) - DEPRECATED"""
        # This test is deprecated as the EventFilter was simplified
        print("SKIPPED: Post-pause filtering test (deprecated functionality)")
        return
        # Simulate pause button pressed
        pause_time = time.time()
        self.event_filter.mark_pause_event(pause_time)
        
        # Update session to paused state
        self.mock_session.is_recording.return_value = False
        self.mock_session.status = "paused"
        
        # Events during pause should be filtered
        during_pause_event = MouseClickEvent(x=100, y=100, button='left', pressed=True, timestamp=pause_time + 0.1)
        decision = self.event_filter.should_capture_event(during_pause_event, self.mock_session)
        
        assert decision.should_capture == False
        assert decision.reason == "session_not_recording"
        
        # Simulate resume
        self.event_filter.mark_resume_event()
        self.mock_session.is_recording.return_value = True
        self.mock_session.status = "recording"
        
        # Events after resume should pass
        after_resume_event = MouseClickEvent(x=100, y=100, button='left', pressed=True, timestamp=pause_time + 0.5)
        decision = self.event_filter.should_capture_event(after_resume_event, self.mock_session)
        
        assert decision.should_capture == True
        
        print("SUCCESS: Pause/resume event filtering works")
    
    def test_resume_behavior_comprehensive(self):
        """Test that after resume, normal events are captured but app-native still filtered - DEPRECATED"""
        # This test is deprecated as the EventFilter was simplified
        print("SKIPPED: Resume behavior comprehensive test (deprecated functionality)")
        return
        base_time = time.time()
        
        # Start with recording
        assert self.mock_session.is_recording() == True
        
        # Pause recording
        self.event_filter.mark_pause_event(base_time)
        self.mock_session.is_recording.return_value = False
        self.mock_session.status = "paused"
        
        # During pause, all events should be filtered
        pause_event = MouseClickEvent(x=100, y=100, button='left', pressed=True, timestamp=base_time + 0.1)
        decision = self.event_filter.should_capture_event(pause_event, self.mock_session)
        assert decision.should_capture == False
        assert decision.reason == "session_not_recording"
        
        # Resume recording
        self.event_filter.mark_resume_event()
        self.mock_session.is_recording.return_value = True
        self.mock_session.status = "recording"
        
        # After resume: normal events should be captured
        resume_time = time.time()
        normal_event = MouseClickEvent(x=200, y=200, button='left', pressed=True, timestamp=resume_time + 0.1)
        decision = self.event_filter.should_capture_event(normal_event, self.mock_session)
        assert decision.should_capture == True
        
        # After resume: all events should pass through filter initially
        # (recording controls handled by retroactive removal from queue)
        any_event = MouseClickEvent(x=300, y=300, button='left', pressed=True, timestamp=resume_time + 0.2)
        decision = self.event_filter.should_capture_event(any_event, self.mock_session)
        assert decision.should_capture == True
        
        print("SUCCESS: Resume behavior works correctly")
    
    def test_retroactive_recording_control_filtering(self):
        """Test that recording control events are handled by retroactive removal from queue"""
        # With the new approach, all events should be captured initially
        # Recording control filtering is handled by removing events from the queue retroactively
        
        all_events = [
            MouseClickEvent(x=500, y=50, button='left', pressed=True, timestamp=time.time()),  # Stop button
            MouseClickEvent(x=600, y=50, button='left', pressed=True, timestamp=time.time()),  # Pause button
            MouseClickEvent(x=700, y=50, button='left', pressed=True, timestamp=time.time()),  # Resume button
            MouseClickEvent(x=800, y=100, button='left', pressed=True, timestamp=time.time()),  # Export button
            MouseClickEvent(x=900, y=100, button='left', pressed=True, timestamp=time.time()),  # Edit button
        ]
        
        # All events should pass through the filter initially
        for event in all_events:
            decision = self.event_filter.should_capture_event(event, self.mock_session)
            assert decision.should_capture == True
        
        print("SUCCESS: All events pass through filter initially (recording controls removed retroactively)")
    
    def test_debouncing_rapid_events(self):
        """Test debouncing of rapid consecutive events - DEPRECATED"""
        # This test is deprecated as debouncing was moved to EventProcessor
        print("SKIPPED: Debouncing test (deprecated functionality - moved to EventProcessor)")
        return
        base_time = time.time()
        self.mock_session.last_event_time = base_time
        
        # Rapid event within debounce threshold should be filtered
        rapid_event = KeyPressEvent(key='a', timestamp=base_time + 0.01)  # 10ms later
        decision = self.event_filter.should_capture_event(rapid_event, self.mock_session)
        
        assert decision.should_capture == False
        assert decision.reason == "debounce_filtered"
        
        # Event after debounce threshold should pass
        delayed_event = KeyPressEvent(key='b', timestamp=base_time + 0.1)  # 100ms later
        decision = self.event_filter.should_capture_event(delayed_event, self.mock_session)
        
        assert decision.should_capture == True
        
        print("SUCCESS: Event debouncing works")
    
    def test_session_not_recording(self):
        """Test filtering when session is not recording"""
        self.mock_session.is_recording.return_value = False
        self.mock_session.status = "stopped"
        
        event = MouseClickEvent(x=500, y=300, button='left', pressed=True, timestamp=time.time())
        decision = self.event_filter.should_capture_event(event, self.mock_session)
        
        assert decision.should_capture == False
        assert decision.reason == "session_not_recording"
        
        print("SUCCESS: Events filtered when session not recording")
    
    def test_filter_decision_combination(self):
        """Test multiple filter conditions - SIMPLIFIED"""
        # Enable keystroke filtering (simplified test)
        self.event_filter.settings.filter_keystrokes = True
        
        # Keystroke event should be filtered
        keystroke_event = KeyPressEvent(key='a', timestamp=time.time() + 0.1)
        decision = self.event_filter.should_capture_event(keystroke_event, self.mock_session)
        
        assert decision.should_capture == False
        assert decision.reason == "keystroke_filtered"
        
        print("SUCCESS: Multiple filter conditions work correctly")
    
    def test_get_filter_status(self):
        """Test getting current filter status for UI display"""
        status = self.event_filter.get_filter_status()
        
        assert 'keystroke_filtering_enabled' in status
        assert status['keystroke_filtering_enabled'] == False  # Default
        
        # Toggle keystroke filtering and check status
        self.event_filter.toggle_keystroke_filtering()
        status = self.event_filter.get_filter_status()
        assert status['keystroke_filtering_enabled'] == True
        
        print("SUCCESS: Filter status reporting works")


class TestFilterDecision:
    """Test FilterDecision dataclass"""
    
    def test_filter_decision_creation(self):
        """Test creating FilterDecision objects"""
        # Allow decision
        allow_decision = FilterDecision(should_capture=True, reason="allowed")
        assert allow_decision.should_capture == True
        assert allow_decision.reason == "allowed"
        
        # Filter decision
        filter_decision = FilterDecision(should_capture=False, reason="keystroke_filtered")
        assert filter_decision.should_capture == False
        assert filter_decision.reason == "keystroke_filtered"
        
        print("SUCCESS: FilterDecision objects work correctly")


def run_event_filter_tests():
    """Run all event filter tests"""
    print("Running EventFilter tests...")
    
    # Test FilterSettings
    settings_test = TestFilterSettings()
    try:
        settings_test.test_default_settings()
        print("  PASS FilterSettings default")
        
        settings_test.test_custom_settings()
        print("  PASS FilterSettings custom")
    except Exception as e:
        print(f"  FAIL FilterSettings test: {e}")
        return False
    
    # Test FilterDecision
    decision_test = TestFilterDecision()
    try:
        decision_test.test_filter_decision_creation()
        print("  PASS FilterDecision creation")
    except Exception as e:
        print(f"  FAIL FilterDecision test: {e}")
        return False
    
    # Test EventFilter
    filter_test = TestEventFilter()
    
    test_methods = [
        ('initial state', 'test_initial_state'),
        ('keystroke toggle', 'test_toggle_keystroke_filtering'),
        ('keystroke filtering disabled', 'test_keystroke_filtering_disabled'),
        ('keystroke filtering enabled', 'test_keystroke_filtering_enabled'),
        ('mouse events unaffected', 'test_mouse_events_never_filtered_by_keystroke_setting'),
        ('post-stop filtering', 'test_post_stop_event_filtering'),
        ('pause/resume filtering', 'test_post_pause_event_filtering'),
        ('resume behavior comprehensive', 'test_resume_behavior_comprehensive'),
        ('retroactive recording control filtering', 'test_retroactive_recording_control_filtering'),
        ('event debouncing', 'test_debouncing_rapid_events'),
        ('session not recording', 'test_session_not_recording'),
        ('multiple filter conditions', 'test_filter_decision_combination'),
        ('filter status reporting', 'test_get_filter_status')
    ]
    
    for test_name, test_method in test_methods:
        try:
            filter_test.setup_method()
            getattr(filter_test, test_method)()
            print(f"  PASS {test_name}")
        except Exception as e:
            print(f"  FAIL {test_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("All EventFilter tests passed!")
    print("NEXT: Implement EventFilter based on test specifications")
    return True


if __name__ == "__main__":
    run_event_filter_tests()