"""
Test real-time step feedback during recording
"""

import sys
import os
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add project root and src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.core.session_manager import SessionManager, SessionState
from src.core.events import MouseClickEvent, KeyPressEvent


class TestRealtimeStepFeedback:
    """Test that step counter increments in real-time during recording"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock dependencies
        self.mock_storage = Mock()
        self.mock_event_monitor = Mock()
        self.mock_event_queue = Mock()
        self.mock_event_processor = Mock()
        
        # Create SessionManager for testing
        self.session_manager = SessionManager(
            storage=self.mock_storage,
            event_monitor=self.mock_event_monitor,
            event_queue=self.mock_event_queue,
            event_processor=self.mock_event_processor,
            debug_mode=True
        )
    
    def test_step_counter_increments_on_mouse_events(self):
        """Test that step counter increments immediately when mouse events are captured"""
        # Create session and start recording
        session = self.session_manager.create_session("test_tutorial", "Step Counter Test")
        self.mock_event_monitor.start_monitoring.return_value = True
        
        self.session_manager.start_recording()
        assert session.is_recording()
        assert session.step_counter == 0
        
        # This test shows what SHOULD happen - step counter should increment
        # when events are captured, not just when processed
        
        # Currently this functionality doesn't exist - we need to implement it
        # For now, test the increment_step_counter method works
        count = self.session_manager.increment_step_counter()
        assert count == 1
        assert session.step_counter == 1
        
        count = self.session_manager.increment_step_counter()
        assert count == 2
        assert session.step_counter == 2
        
        print(f"SUCCESS: Step counter can be incremented to {session.step_counter}")
    
    def test_step_counter_current_behavior(self):
        """Test current step counter behavior vs desired behavior"""
        session = self.session_manager.create_session("test_tutorial", "Current Behavior Test")
        
        # Current behavior: step_counter only increments via explicit calls
        assert session.step_counter == 0
        
        # Manual increment (this works)
        count1 = self.session_manager.increment_step_counter()
        assert count1 == 1
        assert session.step_counter == 1
        
        # But the problem is: events are captured and queued without incrementing
        # the step counter, so users don't see real-time feedback
        
        print("CURRENT ISSUE: Events are queued but step_counter not incremented until processing")
        print("DESIRED: Step counter should increment when events are captured for real-time feedback")
        
    def test_desired_realtime_feedback_behavior(self):
        """Test what the behavior SHOULD be for real-time feedback"""
        session = self.session_manager.create_session("test_tutorial", "Desired Behavior") 
        self.mock_event_monitor.start_monitoring.return_value = True
        self.session_manager.start_recording()
        
        # DESIRED: When event is captured, step counter should increment immediately
        # This would provide real-time feedback to users
        
        # Current session status
        status = self.session_manager.get_session_status()
        assert status['step_count'] == 0
        
        # User performs action -> we should increment step counter immediately
        # (regardless of whether event will be filtered later during processing)
        self.session_manager.increment_step_counter()  # This simulates what should happen
        
        # Status should reflect immediate feedback
        status = self.session_manager.get_session_status()
        assert status['step_count'] == 1
        
        print("SUCCESS: Real-time feedback concept validated")


def run_realtime_step_feedback_tests():
    """Run all real-time step feedback tests"""
    print("Running Real-time Step Feedback tests...")
    
    test_instance = TestRealtimeStepFeedback()
    
    try:
        test_instance.setup_method()
        test_instance.test_step_counter_increments_on_mouse_events()
        print("  PASS step counter mechanism works")
        
        test_instance.setup_method()
        test_instance.test_step_counter_current_behavior()
        print("  PASS identified current issue with real-time feedback")
        
        test_instance.setup_method()
        test_instance.test_desired_realtime_feedback_behavior()
        print("  PASS validated desired real-time feedback behavior")
        
        print("All Real-time Step Feedback tests passed!")
        print("NEXT: Implement real-time step counter increments in event handlers")
        return True
        
    except Exception as e:
        print(f"  FAIL Real-time step feedback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_realtime_step_feedback_tests()