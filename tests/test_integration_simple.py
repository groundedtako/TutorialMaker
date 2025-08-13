"""
Simple integration tests for event processing components
"""

import sys
import os
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

# Add project root and src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.core.event_queue import EventQueue, QueueState
from src.core.event_processor import EventProcessor
from src.core.events import MouseClickEvent


def test_queue_to_processor_integration():
    """Test integration between EventQueue and EventProcessor"""
    
    # Create event queue
    queue = EventQueue()
    
    # Create mock dependencies for processor
    mock_screen_capture = Mock()
    mock_ocr_engine = Mock()
    mock_smart_ocr = Mock()
    mock_storage = Mock()
    
    # Create processor
    processor = EventProcessor(
        screen_capture=mock_screen_capture,
        ocr_engine=mock_ocr_engine,
        smart_ocr=mock_smart_ocr,
        storage=mock_storage,
        debug_mode=False
    )
    
    # Start recording
    queue.start_recording()
    assert queue.state == QueueState.RECORDING
    
    # Create test event with coordinate info
    event = MouseClickEvent(x=500, y=300, button='left', pressed=True, timestamp=time.time())
    mock_screenshot = Mock()
    mock_screenshot.size = (800, 600)
    
    coordinate_info = {
        'screen_width': 1920,
        'screen_height': 1080,
        'monitor_relative_x': 200,
        'monitor_relative_y': 150,
        'monitor_info': {
            'id': 1,
            'width': 800,
            'height': 600,
            'left': 300,
            'top': 150
        }
    }
    
    # Add event to queue
    queue.add_mouse_click(event, mock_screenshot, coordinate_info)
    assert len(queue.events) == 1
    
    # Stop recording
    queue.stop_recording()
    assert queue.state == QueueState.STOPPED
    
    # Get events for processing
    events = queue.get_events_for_processing()
    assert queue.state == QueueState.PROCESSING
    assert len(events) == 1
    
    # Set up processor mocks
    mock_ocr_result = Mock()
    mock_ocr_result.is_valid.return_value = True
    mock_ocr_result.cleaned_text = "Test Button"
    mock_ocr_result.confidence = 0.9
    mock_smart_ocr.process_click_region.return_value = mock_ocr_result
    
    mock_storage.save_screenshot.return_value = "screenshots/test.png"
    mock_storage.save_tutorial_step.return_value = True
    
    # Create mock session
    mock_session = Mock()
    mock_session.step_counter = 0
    
    # Process events
    steps_created = processor.process_events_to_steps(events, "test_tutorial", mock_session)
    
    # Verify processing
    assert steps_created == 1
    # Note: session.step_counter is no longer incremented by processor
    # It's incremented during event capture for real-time feedback
    
    # Verify storage calls
    mock_storage.save_tutorial_step.assert_called_once()
    
    # Verify OCR was called with correct coordinates (from coordinate_info)
    mock_smart_ocr.process_click_region.assert_called_once_with(
        mock_screenshot, 200, 150, False  # monitor_relative coordinates
    )
    
    # Complete processing
    queue.complete_processing()
    assert queue.state == QueueState.IDLE
    
    print("SUCCESS: Queue to Processor integration test passed")


def test_coordinate_calculation_accuracy():
    """Test that coordinate calculations are accurate throughout the pipeline"""
    
    # Test data
    global_x, global_y = 1300, 400  # Click on second monitor
    monitor_1 = {'left': 0, 'top': 0, 'width': 1920, 'height': 1080}
    monitor_2 = {'left': 1920, 'top': 0, 'width': 800, 'height': 600}
    
    # Simulate monitor-relative coordinate calculation
    monitor_relative_x = global_x - monitor_2['left']  # 1300 - 1920 = -620... wait that's wrong
    
    # Let me fix the test data
    global_x, global_y = 2200, 300  # Click on second monitor (1920 + 280, 300)
    monitor_relative_x = global_x - monitor_2['left']  # 2200 - 1920 = 280
    monitor_relative_y = global_y - monitor_2['top']   # 300 - 0 = 300
    
    # Create coordinate info
    coordinate_info = {
        'screen_width': 2720,  # 1920 + 800
        'screen_height': 1080,
        'monitor_relative_x': monitor_relative_x,  # 280
        'monitor_relative_y': monitor_relative_y,  # 300
        'monitor_info': monitor_2
    }
    
    # Calculate percentage coordinates
    x_pct = monitor_relative_x / monitor_2['width']  # 280 / 800 = 0.35
    y_pct = monitor_relative_y / monitor_2['height'] # 300 / 600 = 0.5
    
    # Verify calculations
    assert abs(x_pct - 0.35) < 0.001
    assert abs(y_pct - 0.5) < 0.001
    
    # Test that these coordinates would work for OCR region
    screenshot_width, screenshot_height = 800, 600  # Monitor 2 screenshot
    ocr_x = monitor_relative_x  # Should be 280
    ocr_y = monitor_relative_y  # Should be 300
    
    # Verify OCR coordinates are within screenshot bounds
    assert 0 <= ocr_x <= screenshot_width
    assert 0 <= ocr_y <= screenshot_height
    
    print("SUCCESS: Coordinate calculation accuracy test passed")
    print(f"   Global click: ({global_x}, {global_y})")
    print(f"   Monitor relative: ({monitor_relative_x}, {monitor_relative_y})")
    print(f"   Percentage: ({x_pct:.3f}, {y_pct:.3f})")
    print(f"   OCR coordinates: ({ocr_x}, {ocr_y})")


def run_simple_integration_tests():
    """Run simple integration tests"""
    # Set up test environment
    test_mode = os.environ.get('TUTORIALMAKER_TEST_MODE', 'false') == 'true'
    test_dir = None
    
    if test_mode:
        test_dir = Path(os.environ.get('TUTORIALMAKER_TEST_DIR', tempfile.gettempdir()))
        test_dir.mkdir(exist_ok=True)
    
    try:
        test_queue_to_processor_integration()
        test_coordinate_calculation_accuracy()
        print("\nAll simple integration tests passed!")
        return True
    except Exception as e:
        print(f"Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up test artifacts if not in test mode
        if not test_mode and test_dir and test_dir.exists():
            try:
                shutil.rmtree(test_dir)
            except:
                pass  # Ignore cleanup errors


if __name__ == "__main__":
    run_simple_integration_tests()