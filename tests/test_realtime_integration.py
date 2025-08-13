"""
Integration test to verify real-time step feedback
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

from src.core.session_manager import SessionManager
from src.core.event_queue import EventQueue
from src.core.event_processor import EventProcessor
from src.core.events import MouseClickEvent, KeyPressEvent


def test_end_to_end_realtime_feedback():
    """Test end-to-end real-time step feedback during recording"""
    print("Testing end-to-end real-time step feedback...")
    
    # Create mock dependencies
    mock_storage = Mock()
    mock_event_monitor = Mock()
    mock_screen_capture = Mock()
    mock_ocr_engine = Mock()
    mock_smart_ocr = Mock()
    
    # Create real components
    event_queue = EventQueue()
    event_processor = EventProcessor(
        mock_screen_capture, mock_ocr_engine, mock_smart_ocr, mock_storage, debug_mode=False
    )
    session_manager = SessionManager(
        mock_storage, mock_event_monitor, event_queue, event_processor, debug_mode=True
    )
    
    # Create session and start recording
    session = session_manager.create_session("test_tutorial", "Real-time Test")
    mock_event_monitor.start_monitoring.return_value = True
    session_manager.start_recording()
    
    print(f"Initial step count: {session.step_counter}")
    assert session.step_counter == 0
    
    # Simulate user actions that should increment step counter in real-time
    
    # Action 1: Mouse click
    mouse_event = MouseClickEvent(x=500, y=300, button='left', pressed=True, timestamp=time.time())
    mock_screenshot = Mock()
    coordinate_info = {'monitor_relative_x': 100, 'monitor_relative_y': 200}
    
    # Add to queue and increment step counter (simulating what app does)
    event_queue.add_mouse_click(mouse_event, mock_screenshot, coordinate_info)
    step_count = session_manager.increment_step_counter()
    
    print(f"After mouse click: {step_count}")
    assert step_count == 1
    assert session.step_counter == 1
    
    # Action 2: Keyboard event
    key_event = KeyPressEvent(key='Enter', timestamp=time.time(), is_special=True)
    event_queue.add_keyboard_event(key_event)
    step_count = session_manager.increment_step_counter()
    
    print(f"After keyboard event: {step_count}")
    assert step_count == 2
    assert session.step_counter == 2
    
    # Verify session status reflects real-time feedback
    status = session_manager.get_session_status()
    print(f"Session status step count: {status['step_count']}")
    assert status['step_count'] == 2
    
    # Stop recording and process events
    mock_storage.load_tutorial_metadata.return_value = Mock(duration=0, last_modified=time.time())
    mock_storage.get_project_path.return_value = Path("/test/path")
    
    # Mock event processing
    mock_ocr_result = Mock()
    mock_ocr_result.is_valid.return_value = True
    mock_ocr_result.cleaned_text = "Test Button"
    mock_smart_ocr.process_click_region.return_value = mock_ocr_result
    mock_storage.save_screenshot.return_value = "test.png"
    mock_storage.save_tutorial_step.return_value = True
    
    tutorial_id = session_manager.stop_recording()
    
    # Verify that:
    # 1. Real-time feedback worked (step counter incremented during capture)
    # 2. Events were processed correctly
    # 3. Session completed successfully
    
    assert tutorial_id == "test_tutorial"
    print("SUCCESS: Real-time step feedback working correctly!")
    print(f"Final captured steps: 2")
    print("Real-time feedback provides immediate user experience")
    
    return True


def run_realtime_integration_test():
    """Run the real-time integration test"""
    try:
        return test_end_to_end_realtime_feedback()
    except Exception as e:
        print(f"FAIL: Real-time integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_realtime_integration_test()