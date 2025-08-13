"""
Integration tests for CoordinateSystemHandler with existing components
"""

import sys
import os
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add project root and src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.core.coordinate_handler import CoordinateSystemHandler, MonitorInfo, CoordinateInfo
from src.core.events import MouseClickEvent


class TestCoordinateHandlerIntegration:
    """Integration tests for CoordinateSystemHandler with existing system"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.coordinate_handler = CoordinateSystemHandler(debug_mode=True)
        
        # Set up typical dual-monitor configuration
        self.monitor_data = [
            {'id': 1, 'left': 0, 'top': 0, 'width': 1920, 'height': 1080, 'primary': True},
            {'id': 2, 'left': 1920, 'top': 0, 'width': 1440, 'height': 900, 'primary': False}
        ]
        self.coordinate_handler.update_monitor_info(self.monitor_data)
    
    def test_replace_screen_capture_coordinate_logic(self):
        """Test that CoordinateHandler can replace ScreenCapture coordinate logic"""
        # Simulate what ScreenCapture.adjust_coordinates_to_monitor() currently does
        
        # Test case: Click on secondary monitor
        global_x, global_y = 2200, 300
        
        # Current approach (what we want to replace):
        # 1. Screen capture determines monitor
        # 2. Adjusts coordinates manually
        # 3. Stores separate monitor info
        
        # New approach using CoordinateHandler:
        coord_info = self.coordinate_handler.transform_coordinates(global_x, global_y)
        
        # Verify we get the same results but with better structure
        assert coord_info.global_x == 2200
        assert coord_info.global_y == 300
        assert coord_info.monitor_relative_x == 280  # 2200 - 1920
        assert coord_info.monitor_relative_y == 300
        assert coord_info.monitor.id == 2
        assert coord_info.monitor.width == 1440
        assert coord_info.monitor.height == 900
        
        # Legacy format compatibility
        legacy_dict = coord_info.to_legacy_dict()
        assert legacy_dict['monitor_relative_x'] == 280
        assert legacy_dict['monitor_relative_y'] == 300
        assert legacy_dict['monitor_info']['id'] == 2
        
        print("SUCCESS: CoordinateHandler can replace ScreenCapture coordinate logic")
    
    def test_event_processor_integration(self):
        """Test integration with EventProcessor coordinate usage"""
        # Simulate how EventProcessor currently uses coordinate_info
        
        # Create coordinate info using new handler
        coord_info = self.coordinate_handler.transform_coordinates(500, 300)
        
        # Test percentage coordinate calculation (what EventProcessor does)
        assert abs(coord_info.percentage_x - 0.260) < 0.01  # 500/1920
        assert abs(coord_info.percentage_y - 0.278) < 0.01  # 300/1080
        
        # Test pixel coordinate calculation for screenshot marking
        screenshot_width, screenshot_height = 800, 600
        pixel_x, pixel_y = self.coordinate_handler.calculate_pixel_coordinates(
            coord_info, screenshot_width, screenshot_height
        )
        
        expected_x = int(coord_info.percentage_x * screenshot_width)  # Should be ~208
        expected_y = int(coord_info.percentage_y * screenshot_height)  # Should be ~167
        
        assert pixel_x == expected_x
        assert pixel_y == expected_y
        
        print(f"SUCCESS: EventProcessor integration - pixel coords ({pixel_x}, {pixel_y})")
    
    def test_multi_monitor_workflow(self):
        """Test complete multi-monitor workflow"""
        # Simulate user clicking on different monitors during recording
        
        clicks = [
            (500, 300),    # Primary monitor
            (2200, 400),   # Secondary monitor 
            (100, 100),    # Primary monitor again
            (3000, 500)    # Secondary monitor
        ]
        
        results = []
        
        for global_x, global_y in clicks:
            coord_info = self.coordinate_handler.transform_coordinates(global_x, global_y)
            
            # Simulate screenshot capture on detected monitor
            self.coordinate_handler.set_last_capture_monitor(coord_info.monitor)
            
            results.append({
                'global': (coord_info.global_x, coord_info.global_y),
                'monitor_id': coord_info.monitor.id,
                'relative': (coord_info.monitor_relative_x, coord_info.monitor_relative_y),
                'percentage': (coord_info.percentage_x, coord_info.percentage_y),
                'monitor_size': (coord_info.monitor.width, coord_info.monitor.height)
            })
        
        # Verify results
        assert results[0]['monitor_id'] == 1  # Primary
        assert results[1]['monitor_id'] == 2  # Secondary 
        assert results[2]['monitor_id'] == 1  # Primary again
        assert results[3]['monitor_id'] == 2  # Secondary again
        
        # Verify relative coordinates are correct
        assert results[1]['relative'] == (280, 400)  # 2200-1920, 400-0
        assert results[3]['relative'] == (1080, 500)  # 3000-1920, 500-0
        
        # Verify last capture monitor tracking
        last_monitor = self.coordinate_handler.get_last_capture_monitor()
        assert last_monitor.id == 2  # Should be last click's monitor
        
        print("SUCCESS: Multi-monitor workflow with monitor switching")
    
    def test_backward_compatibility(self):
        """Test that new handler maintains backward compatibility"""
        # Test that we can create legacy coordinate_info dicts
        coord_info = self.coordinate_handler.transform_coordinates(1000, 500)
        legacy_dict = coord_info.to_legacy_dict()
        
        # Verify legacy format has expected keys
        required_keys = ['screen_width', 'screen_height', 'monitor_relative_x', 
                        'monitor_relative_y', 'monitor_info']
        for key in required_keys:
            assert key in legacy_dict, f"Missing legacy key: {key}"
        
        # Test screen info format compatibility
        screen_info = self.coordinate_handler.get_screen_info()
        assert 'width' in screen_info
        assert 'height' in screen_info
        assert 'monitor_count' in screen_info
        assert 'monitors' in screen_info
        assert screen_info['monitor_count'] == 2
        
        print("SUCCESS: Backward compatibility maintained")
    
    def test_coordinate_accuracy_preservation(self):
        """Test that coordinate accuracy is preserved through transformations"""
        # Test various coordinate scenarios
        test_cases = [
            # (global_x, global_y, expected_monitor_id)
            (0, 0, 1),           # Top-left of primary
            (1919, 1079, 1),     # Bottom-right of primary
            (1920, 0, 2),        # Top-left of secondary
            (3359, 899, 2),      # Bottom-right of secondary
            (960, 540, 1),       # Center of primary
            (2640, 450, 2),      # Center of secondary
        ]
        
        for global_x, global_y, expected_monitor in test_cases:
            coord_info = self.coordinate_handler.transform_coordinates(global_x, global_y)
            
            assert coord_info.monitor.id == expected_monitor, \
                f"Point ({global_x}, {global_y}) should be on monitor {expected_monitor}, got {coord_info.monitor.id}"
            
            # Verify round-trip accuracy for percentage coordinates
            pixel_x, pixel_y = self.coordinate_handler.calculate_pixel_coordinates(
                coord_info, coord_info.monitor.width, coord_info.monitor.height
            )
            
            # Should be very close to original monitor-relative coordinates
            assert abs(pixel_x - coord_info.monitor_relative_x) <= 1
            assert abs(pixel_y - coord_info.monitor_relative_y) <= 1
        
        print("SUCCESS: Coordinate accuracy preserved through transformations")
    
    def test_error_handling_and_edge_cases(self):
        """Test error handling for edge cases"""
        # Test with no monitors
        empty_handler = CoordinateSystemHandler(debug_mode=False)
        coord_info = empty_handler.transform_coordinates(500, 300)
        
        # Should create fallback monitor
        assert coord_info.monitor.id == 1
        assert coord_info.monitor.width == 1920
        assert coord_info.monitor.height == 1080
        
        # Test with single monitor
        single_monitor_handler = CoordinateSystemHandler(debug_mode=False)
        single_monitor_handler.update_monitor_info([
            {'id': 1, 'left': 0, 'top': 0, 'width': 1366, 'height': 768, 'primary': True}
        ])
        
        coord_info = single_monitor_handler.transform_coordinates(683, 384)  # Center
        assert abs(coord_info.percentage_x - 0.5) < 0.01
        assert abs(coord_info.percentage_y - 0.5) < 0.01
        
        # Test coordinate clamping
        coord_info = single_monitor_handler.transform_coordinates(-100, -100)
        assert coord_info.monitor_relative_x >= 0
        assert coord_info.monitor_relative_y >= 0
        assert coord_info.percentage_x >= 0.0
        assert coord_info.percentage_y >= 0.0
        
        print("SUCCESS: Error handling and edge cases work correctly")


def run_coordinate_handler_integration_tests():
    """Run all coordinate handler integration tests"""
    print("Running CoordinateHandler integration tests...")
    
    test_instance = TestCoordinateHandlerIntegration()
    
    test_methods = [
        ('screen capture replacement', 'test_replace_screen_capture_coordinate_logic'),
        ('event processor integration', 'test_event_processor_integration'),
        ('multi-monitor workflow', 'test_multi_monitor_workflow'),
        ('backward compatibility', 'test_backward_compatibility'),
        ('coordinate accuracy', 'test_coordinate_accuracy_preservation'),
        ('error handling', 'test_error_handling_and_edge_cases')
    ]
    
    for test_name, test_method in test_methods:
        try:
            test_instance.setup_method()
            getattr(test_instance, test_method)()
            print(f"  PASS {test_name}")
        except Exception as e:
            print(f"  FAIL {test_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("All CoordinateHandler integration tests passed!")
    print("READY: CoordinateHandler can be integrated into existing components")
    return True


if __name__ == "__main__":
    run_coordinate_handler_integration_tests()