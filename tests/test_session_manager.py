"""
Unit tests for SessionManager
"""

import sys
import os
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add project root and src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.core.session_manager import SessionManager, RecordingSession, SessionState
from src.core.event_queue import EventQueue
from src.core.events import MouseClickEvent


class TestRecordingSession:
    """Test RecordingSession class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.session = RecordingSession("test_tutorial_123", "Test Tutorial")
    
    def test_initial_state(self):
        """Test initial session state"""
        assert self.session.tutorial_id == "test_tutorial_123"
        assert self.session.title == "Test Tutorial"
        assert self.session.status == SessionState.STOPPED
        assert self.session.start_time is None
        assert self.session.step_counter == 0
        assert self.session.total_pause_duration == 0.0
        assert not self.session.is_recording()
    
    def test_start_recording(self):
        """Test starting recording session"""
        start_time = time.time()
        self.session.start()
        
        assert self.session.status == SessionState.RECORDING
        assert self.session.start_time is not None
        assert self.session.start_time >= start_time
        assert self.session.step_counter == 0
        assert self.session.total_pause_duration == 0.0
        assert self.session.is_recording()
    
    def test_pause_resume_cycle(self):
        """Test pause and resume functionality"""
        # Start recording
        self.session.start()
        initial_start_time = self.session.start_time
        
        # Wait a bit then pause
        time.sleep(0.01)
        pause_time = time.time()
        self.session.pause()
        
        assert self.session.status == SessionState.PAUSED
        assert self.session.pause_start_time is not None
        assert self.session.pause_start_time >= pause_time
        assert not self.session.is_recording()
        
        # Wait during pause
        time.sleep(0.01)
        
        # Resume
        resume_time = time.time()
        self.session.resume()
        
        assert self.session.status == SessionState.RECORDING
        assert self.session.pause_start_time is None
        assert self.session.total_pause_duration > 0
        assert self.session.start_time == initial_start_time  # Should not change
        assert self.session.is_recording()
    
    def test_stop_recording(self):
        """Test stopping recording session"""
        self.session.start()
        time.sleep(0.01)
        
        initial_step_count = 5
        self.session.step_counter = initial_step_count
        
        self.session.stop()
        
        assert self.session.status == SessionState.STOPPED
        assert self.session.step_counter == initial_step_count
        assert not self.session.is_recording()
    
    def test_duration_calculation(self):
        """Test duration calculation with pauses"""
        # No start time
        assert self.session.get_duration() == 0.0
        
        # Start recording
        self.session.start()
        time.sleep(0.02)  # 20ms
        
        # Duration should be positive
        duration1 = self.session.get_duration()
        assert duration1 > 0
        
        # Pause
        self.session.pause()
        time.sleep(0.02)  # 20ms pause
        
        # Duration during pause should not increase much
        duration2 = self.session.get_duration()
        assert abs(duration2 - duration1) < 0.01  # Should be similar
        
        # Resume
        self.session.resume()
        time.sleep(0.02)  # 20ms more recording
        
        # Duration should increase again
        duration3 = self.session.get_duration()
        assert duration3 > duration2


class TestSessionManager:
    """Test SessionManager class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock dependencies
        self.mock_storage = Mock()
        self.mock_event_monitor = Mock()
        self.mock_event_queue = Mock()
        self.mock_event_processor = Mock()
        
        # Create session manager
        self.session_manager = SessionManager(
            storage=self.mock_storage,
            event_monitor=self.mock_event_monitor,
            event_queue=self.mock_event_queue,
            event_processor=self.mock_event_processor,
            debug_mode=False
        )
    
    def test_no_current_session_initially(self):
        """Test that there's no current session initially"""
        assert self.session_manager.current_session is None
        assert not self.session_manager.has_active_session()
        
        status = self.session_manager.get_session_status()
        assert status['status'] == 'no_session'
    
    def test_create_new_session(self):
        """Test creating a new session"""
        tutorial_id = "test_tutorial_456"
        title = "New Test Tutorial"
        
        session = self.session_manager.create_session(tutorial_id, title)
        
        assert session is not None
        assert session.tutorial_id == tutorial_id
        assert session.title == title
        assert session.status == SessionState.STOPPED
        assert self.session_manager.current_session == session
        assert self.session_manager.has_active_session()
    
    def test_start_recording_success(self):
        """Test successfully starting recording"""
        # Create session first
        tutorial_id = "test_tutorial_789"
        session = self.session_manager.create_session(tutorial_id, "Test Tutorial")
        
        # Mock successful monitoring start
        self.mock_event_monitor.start_monitoring.return_value = True
        self.mock_event_queue.start_recording.return_value = None
        
        # Start recording
        result = self.session_manager.start_recording()
        
        assert result is True
        assert session.status == SessionState.RECORDING
        assert session.is_recording()
        
        # Verify dependencies were called
        self.mock_event_monitor.start_monitoring.assert_called_once()
        self.mock_event_queue.start_recording.assert_called_once()
        self.mock_storage.update_tutorial_status.assert_called_once_with(tutorial_id, "recording")
    
    def test_start_recording_no_session(self):
        """Test starting recording without a session"""
        result = self.session_manager.start_recording()
        
        assert result is False
        self.mock_event_monitor.start_monitoring.assert_not_called()
    
    def test_start_recording_monitoring_fails(self):
        """Test starting recording when event monitoring fails"""
        # Create session
        self.session_manager.create_session("test_tutorial", "Test")
        
        # Mock monitoring failure
        self.mock_event_monitor.start_monitoring.return_value = False
        
        # Should still succeed but with warning
        result = self.session_manager.start_recording()
        
        assert result is True  # Still returns True, just with limited functionality
        self.mock_event_monitor.start_monitoring.assert_called_once()
    
    def test_pause_resume_recording(self):
        """Test pause and resume functionality"""
        # Create and start session
        session = self.session_manager.create_session("test_tutorial", "Test")
        self.mock_event_monitor.start_monitoring.return_value = True
        self.session_manager.start_recording()
        
        # Pause
        self.session_manager.pause_recording()
        assert session.status == SessionState.PAUSED
        self.mock_storage.update_tutorial_status.assert_called_with("test_tutorial", "paused")
        
        # Resume
        self.session_manager.resume_recording()
        assert session.status == SessionState.RECORDING
        self.mock_storage.update_tutorial_status.assert_called_with("test_tutorial", "recording")
    
    def test_stop_recording_success(self):
        """Test successfully stopping recording"""
        # Create and start session
        tutorial_id = "test_tutorial_stop"
        session = self.session_manager.create_session(tutorial_id, "Stop Test")
        self.mock_event_monitor.start_monitoring.return_value = True
        self.session_manager.start_recording()
        
        # Mock event processing
        mock_events = [Mock()]
        self.mock_event_queue.get_events_for_processing.return_value = mock_events
        self.mock_event_processor.process_events_to_steps.return_value = 3
        self.mock_event_processor.save_raw_events.return_value = None
        
        # Mock storage operations
        mock_metadata = Mock()
        mock_metadata.duration = 0.0
        self.mock_storage.load_tutorial_metadata.return_value = mock_metadata
        self.mock_storage.get_project_path.return_value = Path("/fake/path")
        
        # Stop recording
        result = self.session_manager.stop_recording()
        
        assert result == tutorial_id
        assert session.status == SessionState.STOPPED
        assert self.session_manager.current_session is None  # Session should be cleared
        
        # Verify processing was called
        self.mock_event_queue.stop_recording.assert_called_once()
        self.mock_event_monitor.stop_monitoring.assert_called_once()
        self.mock_event_queue.get_events_for_processing.assert_called_once()
        self.mock_event_processor.process_events_to_steps.assert_called_once()
        self.mock_event_queue.complete_processing.assert_called_once()
        self.mock_storage.update_tutorial_status.assert_called_with(tutorial_id, "completed")
    
    def test_stop_recording_no_session(self):
        """Test stopping recording without a session"""
        result = self.session_manager.stop_recording()
        
        assert result is None
        self.mock_event_queue.stop_recording.assert_not_called()
    
    def test_replace_existing_session(self):
        """Test that creating a new session replaces the existing one"""
        # Create first session
        session1 = self.session_manager.create_session("tutorial1", "First")
        assert self.session_manager.current_session == session1
        
        # Create second session - should replace first
        session2 = self.session_manager.create_session("tutorial2", "Second")
        assert self.session_manager.current_session == session2
        assert self.session_manager.current_session != session1
    
    def test_get_session_status_with_session(self):
        """Test getting session status when session exists"""
        # Create and start session
        tutorial_id = "status_test"
        title = "Status Test Tutorial"
        session = self.session_manager.create_session(tutorial_id, title)
        session.step_counter = 5
        
        status = self.session_manager.get_session_status()
        
        assert status['status'] == SessionState.STOPPED.value
        assert status['title'] == title
        assert status['tutorial_id'] == tutorial_id
        assert status['step_count'] == 5
        assert status['is_recording'] == False
        assert 'duration' in status
    
    def test_increment_step_counter(self):
        """Test incrementing step counter"""
        session = self.session_manager.create_session("test", "Test")
        
        # Initial count
        assert session.step_counter == 0
        
        # Increment
        new_count = self.session_manager.increment_step_counter()
        assert new_count == 1
        assert session.step_counter == 1
        
        # Increment again
        new_count = self.session_manager.increment_step_counter()
        assert new_count == 2
        assert session.step_counter == 2
    
    def test_increment_step_counter_no_session(self):
        """Test incrementing step counter without session"""
        result = self.session_manager.increment_step_counter()
        assert result == 0


def run_session_manager_tests():
    """Run all session manager tests"""
    print("Running SessionManager tests...")
    
    # Test RecordingSession
    session_test = TestRecordingSession()
    session_test.setup_method()
    
    try:
        session_test.test_initial_state()
        print("  PASS RecordingSession initial state")
        
        session_test.test_start_recording()
        print("  PASS RecordingSession start recording")
        
        session_test.setup_method()  # Reset
        session_test.test_pause_resume_cycle()
        print("  PASS RecordingSession pause/resume")
        
        session_test.setup_method()  # Reset
        session_test.test_stop_recording()
        print("  PASS RecordingSession stop recording")
        
        session_test.setup_method()  # Reset
        session_test.test_duration_calculation()
        print("  PASS RecordingSession duration calculation")
        
    except Exception as e:
        print(f"  FAIL RecordingSession test failed: {e}")
        return False
    
    # Test SessionManager
    manager_test = TestSessionManager()
    manager_test.setup_method()
    
    try:
        manager_test.test_no_current_session_initially()
        print("  PASS SessionManager initial state")
        
        manager_test.test_create_new_session()
        print("  PASS SessionManager create session")
        
        manager_test.setup_method()  # Reset
        manager_test.test_start_recording_success()
        print("  PASS SessionManager start recording")
        
        manager_test.setup_method()  # Reset
        manager_test.test_start_recording_no_session()
        print("  PASS SessionManager start recording without session")
        
        manager_test.setup_method()  # Reset
        manager_test.test_pause_resume_recording()
        print("  PASS SessionManager pause/resume")
        
        manager_test.setup_method()  # Reset
        manager_test.test_stop_recording_success()
        print("  PASS SessionManager stop recording")
        
        manager_test.setup_method()  # Reset
        manager_test.test_stop_recording_no_session()
        print("  PASS SessionManager stop without session")
        
        manager_test.setup_method()  # Reset
        manager_test.test_get_session_status_with_session()
        print("  PASS SessionManager session status")
        
        manager_test.setup_method()  # Reset
        manager_test.test_increment_step_counter()
        print("  PASS SessionManager step counter")
        
        print("All SessionManager tests passed!")
        return True
        
    except Exception as e:
        print(f"  FAIL SessionManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_session_manager_tests()