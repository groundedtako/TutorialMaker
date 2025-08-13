"""
Integration tests for the complete event processing pipeline
"""

import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.app import TutorialMakerApp
from src.core.events import MouseClickEvent
from src.core.event_queue import EventQueue, QueueState


class TestEventProcessingIntegration:
    """Integration tests for the complete event processing flow"""
    
    def test_end_to_end_click_processing(self):
        """Test the complete flow from click event to tutorial step"""
        # Create app with mocked dependencies
        with patch('src.core.app.ScreenCapture') as mock_screen_capture_class, \
             patch('src.core.app.EventMonitor') as mock_event_monitor_class, \
             patch('src.core.app.OCREngine') as mock_ocr_class, \
             patch('src.core.app.SmartOCRProcessor') as mock_smart_ocr_class, \
             patch('src.core.app.TutorialStorage') as mock_storage_class:
            
            # Set up mocks
            mock_screen_capture = Mock()
            mock_screen_capture_class.return_value = mock_screen_capture
            
            mock_event_monitor = Mock()
            mock_event_monitor_class.return_value = mock_event_monitor
            
            mock_storage = Mock()
            mock_storage_class.return_value = mock_storage
            
            # Create app
            app = TutorialMakerApp(debug_mode=False)
            
            # Create new tutorial
            mock_storage.create_tutorial_project.return_value = "test_tutorial_123"
            mock_storage.load_tutorial_metadata.return_value = Mock(title="Test Tutorial")
            
            tutorial_id = app.new_tutorial("Test Tutorial")
            assert tutorial_id == "test_tutorial_123"
            
            # Start recording
            mock_event_monitor.start_monitoring.return_value = True
            result = app.start_recording()
            assert result is True
            assert app.event_queue.is_recording()
            
            # Simulate a mouse click event
            mock_screenshot = Mock()
            mock_screenshot.size = (800, 600)
            mock_screen_capture.capture_full_screen.return_value = mock_screenshot
            mock_screen_capture.get_screen_info.return_value = {'width': 1920, 'height': 1080}
            mock_screen_capture.adjust_coordinates_to_monitor.return_value = (200, 150)
            mock_screen_capture.get_last_monitor_info.return_value = {
                'id': 1, 'width': 800, 'height': 600, 'left': 300, 'top': 150
            }
            
            # Create and process click event
            click_event = MouseClickEvent(
                x=500, y=300, button='left', pressed=True, timestamp=time.time()
            )
            
            app._on_mouse_click(click_event)
            
            # Verify event was queued
            assert len(app.event_queue.events) == 1
            queued_event = app.event_queue.events[0]
            assert queued_event.event_type == 'mouse_click'
            assert queued_event.screenshot is not None
            assert queued_event.coordinate_info is not None
            
            # Stop recording and process events
            mock_storage.save_screenshot.return_value = "screenshots/test.png"
            mock_storage.save_tutorial_step.return_value = True
            mock_storage.get_project_path.return_value = Path("/mock/path")
            mock_storage._save_events.return_value = True
            
            # Mock OCR result
            mock_ocr_result = Mock()
            mock_ocr_result.is_valid.return_value = True
            mock_ocr_result.cleaned_text = "Submit Button"
            mock_ocr_result.confidence = 0.95
            app.event_processor.smart_ocr.process_click_region.return_value = mock_ocr_result
            
            # Stop recording (this triggers event processing)
            result_tutorial_id = app.stop_recording()
            
            # Verify processing happened
            assert result_tutorial_id == tutorial_id
            assert app.event_queue.state == QueueState.IDLE
            assert app.current_session.step_counter > 0
            
            # Verify storage calls
            mock_storage.save_tutorial_step.assert_called_once()
            mock_storage._save_events.assert_called_once()
            
            print("SUCCESS: End-to-end click processing test passed")
    
    def test_coordinate_info_preservation(self):
        """Test that coordinate information is preserved through the pipeline"""
        # Create event queue
        queue = EventQueue()
        
        # Start recording
        queue.start_recording()
        
        # Create test event with coordinate info
        event = MouseClickEvent(x=500, y=300, button='left', pressed=True, timestamp=time.time())
        screenshot = Mock()
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
        queue.add_mouse_click(event, screenshot, coordinate_info)
        
        # Stop recording and get events
        queue.stop_recording()
        events = queue.get_events_for_processing()
        
        # Verify coordinate info preservation
        assert len(events) == 1
        queued_event = events[0]
        assert queued_event.coordinate_info is not None
        assert queued_event.coordinate_info['monitor_relative_x'] == 200
        assert queued_event.coordinate_info['monitor_relative_y'] == 150
        assert queued_event.coordinate_info['monitor_info']['width'] == 800
        
        # Calculate percentage coordinates (should match expected values)
        coord_info = queued_event.coordinate_info
        monitor_info = coord_info['monitor_info']
        x_pct = coord_info['monitor_relative_x'] / monitor_info['width']
        y_pct = coord_info['monitor_relative_y'] / monitor_info['height']
        
        assert abs(x_pct - 0.25) < 0.001  # 200/800 = 0.25
        assert abs(y_pct - 0.25) < 0.001  # 150/600 = 0.25
        
        print("SUCCESS: Coordinate info preservation test passed")


def run_integration_tests():
    """Run all integration tests"""
    test_suite = TestEventProcessingIntegration()
    
    try:
        test_suite.test_end_to_end_click_processing()
        test_suite.test_coordinate_info_preservation()
        print("\nAll integration tests passed!")
        return True
    except Exception as e:
        print(f"Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_integration_tests()