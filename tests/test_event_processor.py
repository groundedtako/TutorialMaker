"""
Unit tests for EventProcessor
"""

import sys
import os
import pytest
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add project root and src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.core.event_processor import EventProcessor
from src.core.event_queue import QueuedEvent
from src.core.events import MouseClickEvent, KeyPressEvent, EventType
from src.core.storage import TutorialStep


class TestEventProcessor:
    """Test suite for EventProcessor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Set up test-friendly environment
        self.test_mode = os.environ.get('TUTORIALMAKER_TEST_MODE', 'false') == 'true'
        self.test_dir = Path(os.environ.get('TUTORIALMAKER_TEST_DIR', '/tmp'))
        
        # Mock dependencies
        self.mock_screen_capture = Mock()
        self.mock_ocr_engine = Mock()
        self.mock_smart_ocr = Mock()
        self.mock_storage = Mock()
        
        # Create EventProcessor instance
        self.processor = EventProcessor(
            screen_capture=self.mock_screen_capture,
            ocr_engine=self.mock_ocr_engine,
            smart_ocr=self.mock_smart_ocr,
            storage=self.mock_storage,
            debug_mode=False
        )
        
        # Mock session
        self.mock_session = Mock()
        self.mock_session.step_counter = 0
        self.mock_session.last_event_time = 0
    
    def test_process_mouse_click_with_coordinate_info(self):
        """Test processing mouse click with pre-calculated coordinate info"""
        # Create test event
        event = MouseClickEvent(x=500, y=300, button='left', pressed=True, timestamp=time.time())
        
        # Create mock screenshot
        mock_screenshot = Mock()
        mock_screenshot.size = (800, 600)
        
        # Create coordinate info
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
        
        # Create queued event
        queued_event = QueuedEvent(
            event_type='mouse_click',
            timestamp=event.timestamp,
            event_object=event,
            event_data={'x': event.x, 'y': event.y, 'button': event.button, 'timestamp': event.timestamp},
            screenshot=mock_screenshot,
            coordinate_info=coordinate_info
        )
        
        # Mock OCR result
        mock_ocr_result = Mock()
        mock_ocr_result.is_valid.return_value = True
        mock_ocr_result.cleaned_text = "Submit"
        mock_ocr_result.confidence = 0.95
        mock_ocr_result.engine = "tesseract"
        
        self.mock_smart_ocr.process_click_region.return_value = mock_ocr_result
        self.mock_storage.save_screenshot.return_value = "screenshots/test.png"
        self.mock_storage.save_tutorial_step.return_value = True
        
        # Process the event
        result = self.processor._process_mouse_click_event(queued_event, "test_tutorial", self.mock_session, 1)
        
        # Verify result
        assert result is True
        # Note: session.step_counter is no longer incremented by processor
        # It's incremented during event capture for real-time feedback
        
        # Verify OCR was called with correct coordinates
        self.mock_smart_ocr.process_click_region.assert_called_once_with(
            mock_screenshot, 200, 150, False
        )
        
        # Verify storage calls
        self.mock_storage.save_screenshot.assert_called_once()
        self.mock_storage.save_tutorial_step.assert_called_once()
        
        # Verify step creation
        step_call = self.mock_storage.save_tutorial_step.call_args[0][1]
        assert isinstance(step_call, TutorialStep)
        assert step_call.step_number == 1
        assert step_call.description == 'Click on "Submit"'
        assert step_call.coordinates == (500, 300)
        assert abs(step_call.coordinates_pct[0] - 0.25) < 0.001  # 200/800 = 0.25
        assert abs(step_call.coordinates_pct[1] - 0.25) < 0.001  # 150/600 = 0.25
    
    def test_process_mouse_click_without_coordinate_info(self):
        """Test processing mouse click without coordinate info (fallback)"""
        # Reset session counter and mocks for this test
        self.mock_session.step_counter = 0
        self.mock_smart_ocr.reset_mock()
        self.mock_storage.reset_mock()
        
        # Create test event
        event = MouseClickEvent(x=500, y=300, button='left', pressed=True, timestamp=time.time())
        
        # Create mock screenshot
        mock_screenshot = Mock()
        mock_screenshot.size = (1920, 1080)
        
        # Create queued event without coordinate info
        queued_event = QueuedEvent(
            event_type='mouse_click',
            timestamp=event.timestamp,
            event_object=event,
            event_data={'x': event.x, 'y': event.y, 'button': event.button, 'timestamp': event.timestamp},
            screenshot=mock_screenshot,
            coordinate_info=None  # No coordinate info
        )
        
        # Mock dependencies
        self.mock_screen_capture.get_screen_info.return_value = {'width': 1920, 'height': 1080}
        
        mock_ocr_result = Mock()
        mock_ocr_result.is_valid.return_value = False
        mock_ocr_result.cleaned_text = ""
        
        self.mock_smart_ocr.process_click_region.return_value = mock_ocr_result
        self.mock_storage.save_screenshot.return_value = "screenshots/test.png"
        self.mock_storage.save_tutorial_step.return_value = True
        
        # Process the event
        result = self.processor._process_mouse_click_event(queued_event, "test_tutorial", self.mock_session, 1)
        
        # Verify result
        assert result is True
        # Note: session.step_counter is no longer incremented by processor
        
        # Verify fallback coordinates were used
        expected_x = int((500 / 1920) * 1920)  # Should be 500
        expected_y = int((300 / 1080) * 1080)  # Should be 300
        
        self.mock_smart_ocr.process_click_region.assert_called_once_with(
            mock_screenshot, expected_x, expected_y, False
        )
    
    def test_process_keyboard_event_special_key(self):
        """Test processing special keyboard event"""
        # Reset session counter and mocks for this test
        self.mock_session.step_counter = 0
        self.mock_storage.reset_mock()
        self.mock_screen_capture.reset_mock()
        
        # Create test event
        event = KeyPressEvent(
            key='Enter',
            is_special=True,
            timestamp=time.time(),
            event_type=EventType.KEY_PRESS
        )
        
        # Create queued event
        queued_event = QueuedEvent(
            event_type='keyboard_event',
            timestamp=event.timestamp,
            event_object=event,
            event_data={'key': event.key, 'is_special': event.is_special, 'timestamp': event.timestamp}
        )
        
        # Mock dependencies
        mock_screenshot = Mock()
        self.mock_screen_capture.capture_full_screen.return_value = mock_screenshot
        self.mock_storage.save_screenshot.return_value = "screenshots/test.png"
        self.mock_storage.save_tutorial_step.return_value = True
        
        # Process the event
        result = self.processor._process_keyboard_event(queued_event, "test_tutorial", self.mock_session, 1)
        
        # Verify result
        assert result is True
        # Note: session.step_counter is no longer incremented by processor
        
        # Verify storage calls
        self.mock_storage.save_tutorial_step.assert_called_once()
        
        # Verify step creation
        step_call = self.mock_storage.save_tutorial_step.call_args[0][1]
        assert isinstance(step_call, TutorialStep)
        assert step_call.description == 'Press Enter'
        assert step_call.step_type == 'key'
    
    def test_process_events_to_steps_integration(self):
        """Test the main processing method with multiple events"""
        # Reset session counter and mocks for this test
        self.mock_session.step_counter = 0
        self.mock_storage.reset_mock()
        self.mock_screen_capture.reset_mock()
        self.mock_smart_ocr.reset_mock()
        
        # Create test events
        mouse_event = MouseClickEvent(x=500, y=300, button='left', pressed=True, timestamp=time.time())
        keyboard_event = KeyPressEvent(
            key='Enter',
            is_special=True,
            timestamp=time.time() + 1,
            event_type=EventType.KEY_PRESS
        )
        
        # Create queued events
        events = [
            QueuedEvent(
                event_type='mouse_click',
                timestamp=mouse_event.timestamp,
                event_object=mouse_event,
                event_data={'x': mouse_event.x, 'y': mouse_event.y, 'button': mouse_event.button, 'timestamp': mouse_event.timestamp},
                screenshot=Mock(),
                coordinate_info={
                    'screen_width': 1920,
                    'screen_height': 1080,
                    'monitor_relative_x': 200,
                    'monitor_relative_y': 150,
                    'monitor_info': {'id': 1, 'width': 800, 'height': 600, 'left': 300, 'top': 150}
                }
            ),
            QueuedEvent(
                event_type='keyboard_event',
                timestamp=keyboard_event.timestamp,
                event_object=keyboard_event,
                event_data={'key': keyboard_event.key, 'is_special': keyboard_event.is_special, 'timestamp': keyboard_event.timestamp}
            )
        ]
        
        # Mock dependencies
        mock_ocr_result = Mock()
        mock_ocr_result.is_valid.return_value = True
        mock_ocr_result.cleaned_text = "Button"
        mock_ocr_result.confidence = 0.9
        
        self.mock_smart_ocr.process_click_region.return_value = mock_ocr_result
        self.mock_screen_capture.capture_full_screen.return_value = Mock()
        self.mock_storage.save_screenshot.return_value = "screenshots/test.png"
        self.mock_storage.save_tutorial_step.return_value = True
        
        # Process events
        steps_created = self.processor.process_events_to_steps(events, "test_tutorial", self.mock_session)
        
        # Verify results
        assert steps_created == 2
        # Note: session.step_counter is no longer incremented by processor
        assert self.mock_storage.save_tutorial_step.call_count == 2
    
    def test_save_raw_events(self):
        """Test saving raw events to JSON"""
        # Create test events
        events = [
            QueuedEvent(
                event_type='mouse_click',
                timestamp=time.time(),
                event_object=Mock(),
                event_data={'x': 100, 'y': 200, 'button': 'left', 'timestamp': time.time()}
            )
        ]
        
        # Mock dependencies
        self.mock_storage.get_project_path.return_value = Path("/mock/path")
        self.mock_storage._save_events.return_value = True
        
        # Save events
        result = self.processor.save_raw_events(events, "test_tutorial")
        
        # Verify result
        assert result is True
        self.mock_storage.get_project_path.assert_called_once_with("test_tutorial")
        self.mock_storage._save_events.assert_called_once()


if __name__ == "__main__":
    # Run tests
    test_processor = TestEventProcessor()
    test_processor.setup_method()
    
    try:
        test_processor.test_process_mouse_click_with_coordinate_info()
        print("SUCCESS: test_process_mouse_click_with_coordinate_info")
        
        test_processor.test_process_mouse_click_without_coordinate_info()
        print("SUCCESS: test_process_mouse_click_without_coordinate_info")
        
        test_processor.test_process_keyboard_event_special_key()
        print("SUCCESS: test_process_keyboard_event_special_key")
        
        test_processor.test_process_events_to_steps_integration()
        print("SUCCESS: test_process_events_to_steps_integration")
        
        test_processor.test_save_raw_events()
        print("SUCCESS: test_save_raw_events")
        
        print("\nAll EventProcessor tests passed!")
        
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()