"""
Unit tests for CoordinateSystemHandler
"""

import sys
import os
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional

# Add project root and src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.core.coordinate_handler import CoordinateSystemHandler, MonitorInfo, CoordinateInfo


@dataclass 
class MockMonitor:
    """Mock monitor for testing"""
    id: int
    left: int
    top: int
    width: int
    height: int
    is_primary: bool = False


class TestMonitorInfo:
    """Test MonitorInfo dataclass"""
    
    def test_monitor_info_creation(self):
        """Test creating MonitorInfo with all fields"""
        monitor = MonitorInfo(
            id=1,
            left=0,
            top=0,
            width=1920,
            height=1080,
            is_primary=True
        )
        
        assert monitor.id == 1
        assert monitor.left == 0
        assert monitor.top == 0 
        assert monitor.width == 1920
        assert monitor.height == 1080
        assert monitor.is_primary == True
        
    def test_monitor_info_secondary(self):
        """Test creating secondary monitor"""
        monitor = MonitorInfo(
            id=2,
            left=1920,
            top=0,
            width=1440,
            height=900,
            is_primary=False
        )
        
        assert monitor.id == 2
        assert monitor.left == 1920
        assert monitor.width == 1440
        assert monitor.is_primary == False


class TestCoordinateInfo:
    """Test CoordinateInfo dataclass"""
    
    def test_coordinate_info_creation(self):
        """Test creating CoordinateInfo with all transformations"""
        monitor = MonitorInfo(id=1, left=0, top=0, width=1920, height=1080, is_primary=True)
        
        coord_info = CoordinateInfo(
            global_x=500,
            global_y=300,
            monitor_relative_x=500,
            monitor_relative_y=300,
            percentage_x=0.26,
            percentage_y=0.28,
            monitor=monitor
        )
        
        assert coord_info.global_x == 500
        assert coord_info.global_y == 300
        assert coord_info.monitor_relative_x == 500
        assert coord_info.monitor_relative_y == 300
        assert abs(coord_info.percentage_x - 0.26) < 0.01
        assert abs(coord_info.percentage_y - 0.28) < 0.01
        assert coord_info.monitor.id == 1


class TestCoordinateSystemHandler:
    """Test CoordinateSystemHandler class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock screen capture component
        self.mock_screen_capture = Mock()
        
        # Create coordinate handler
        self.coordinate_handler = CoordinateSystemHandler(debug_mode=True)
    
    def test_initial_state(self):
        """Test initial state of coordinate handler"""
        assert self.coordinate_handler.debug_mode == True
        assert self.coordinate_handler._monitors == []
        assert self.coordinate_handler._primary_monitor is None
        assert self.coordinate_handler._last_capture_monitor is None
    
    def test_update_monitor_info(self):
        """Test updating monitor information"""
        # Mock monitor data
        mock_monitors = [
            {'id': 1, 'left': 0, 'top': 0, 'width': 1920, 'height': 1080, 'primary': True},
            {'id': 2, 'left': 1920, 'top': 0, 'width': 1440, 'height': 900, 'primary': False}
        ]
        
        self.coordinate_handler.update_monitor_info(mock_monitors)
        
        # Verify monitors were parsed correctly
        assert len(self.coordinate_handler._monitors) == 2
        
        # Check primary monitor
        primary = self.coordinate_handler._primary_monitor
        assert primary is not None
        assert primary.id == 1
        assert primary.width == 1920
        assert primary.height == 1080
        assert primary.is_primary == True
        
        # Check secondary monitor
        secondary = [m for m in self.coordinate_handler._monitors if m.id == 2][0]
        assert secondary.id == 2
        assert secondary.left == 1920
        assert secondary.width == 1440
        assert secondary.is_primary == False
        
        print("SUCCESS: Monitor info updated correctly")
    
    def test_get_monitor_from_point_primary(self):
        """Test getting monitor from point on primary display"""
        # Set up monitors
        mock_monitors = [
            {'id': 1, 'left': 0, 'top': 0, 'width': 1920, 'height': 1080, 'primary': True},
            {'id': 2, 'left': 1920, 'top': 0, 'width': 1440, 'height': 900, 'primary': False}
        ]
        self.coordinate_handler.update_monitor_info(mock_monitors)
        
        # Test point on primary monitor
        monitor = self.coordinate_handler.get_monitor_from_point(500, 300)
        assert monitor is not None
        assert monitor.id == 1
        assert monitor.is_primary == True
        
        print("SUCCESS: Primary monitor detection")
    
    def test_get_monitor_from_point_secondary(self):
        """Test getting monitor from point on secondary display"""
        # Set up monitors
        mock_monitors = [
            {'id': 1, 'left': 0, 'top': 0, 'width': 1920, 'height': 1080, 'primary': True},
            {'id': 2, 'left': 1920, 'top': 0, 'width': 1440, 'height': 900, 'primary': False}
        ]
        self.coordinate_handler.update_monitor_info(mock_monitors)
        
        # Test point on secondary monitor
        monitor = self.coordinate_handler.get_monitor_from_point(2200, 300)
        assert monitor is not None
        assert monitor.id == 2
        assert monitor.is_primary == False
        
        print("SUCCESS: Secondary monitor detection")
    
    def test_get_monitor_from_point_not_found(self):
        """Test getting monitor from point outside all displays"""
        # Set up monitors
        mock_monitors = [
            {'id': 1, 'left': 0, 'top': 0, 'width': 1920, 'height': 1080, 'primary': True}
        ]
        self.coordinate_handler.update_monitor_info(mock_monitors)
        
        # Test point outside all monitors
        monitor = self.coordinate_handler.get_monitor_from_point(-500, -500)
        # Should return primary monitor as fallback
        assert monitor is not None
        assert monitor.id == 1
        assert monitor.is_primary == True
        
        print("SUCCESS: Fallback to primary monitor")
    
    def test_transform_coordinates_single_monitor(self):
        """Test coordinate transformation on single monitor setup"""
        # Set up single monitor
        mock_monitors = [
            {'id': 1, 'left': 0, 'top': 0, 'width': 1920, 'height': 1080, 'primary': True}
        ]
        self.coordinate_handler.update_monitor_info(mock_monitors)
        
        # Transform coordinates
        coord_info = self.coordinate_handler.transform_coordinates(500, 300)
        
        assert coord_info.global_x == 500
        assert coord_info.global_y == 300
        assert coord_info.monitor_relative_x == 500  # Same as global on single monitor at origin
        assert coord_info.monitor_relative_y == 300
        assert abs(coord_info.percentage_x - (500/1920)) < 0.01
        assert abs(coord_info.percentage_y - (300/1080)) < 0.01
        assert coord_info.monitor.id == 1
        
        print(f"SUCCESS: Single monitor transformation - percentages: ({coord_info.percentage_x:.3f}, {coord_info.percentage_y:.3f})")
    
    def test_transform_coordinates_multi_monitor(self):
        """Test coordinate transformation on multi-monitor setup"""
        # Set up multi-monitor
        mock_monitors = [
            {'id': 1, 'left': 0, 'top': 0, 'width': 1920, 'height': 1080, 'primary': True},
            {'id': 2, 'left': 1920, 'top': 0, 'width': 1440, 'height': 900, 'primary': False}
        ]
        self.coordinate_handler.update_monitor_info(mock_monitors)
        
        # Transform coordinates on secondary monitor
        coord_info = self.coordinate_handler.transform_coordinates(2200, 300)
        
        assert coord_info.global_x == 2200
        assert coord_info.global_y == 300
        assert coord_info.monitor_relative_x == 280  # 2200 - 1920
        assert coord_info.monitor_relative_y == 300
        assert abs(coord_info.percentage_x - (280/1440)) < 0.01
        assert abs(coord_info.percentage_y - (300/900)) < 0.01
        assert coord_info.monitor.id == 2
        
        print(f"SUCCESS: Multi-monitor transformation - relative: ({coord_info.monitor_relative_x}, {coord_info.monitor_relative_y})")
    
    def test_calculate_pixel_coordinates(self):
        """Test calculating pixel coordinates from percentage"""
        # Set up monitor
        mock_monitors = [
            {'id': 1, 'left': 0, 'top': 0, 'width': 1920, 'height': 1080, 'primary': True}
        ]
        self.coordinate_handler.update_monitor_info(mock_monitors)
        
        # Create coordinate info
        monitor = self.coordinate_handler._primary_monitor
        coord_info = CoordinateInfo(
            global_x=500, global_y=300,
            monitor_relative_x=500, monitor_relative_y=300,
            percentage_x=0.5, percentage_y=0.5,  # Center
            monitor=monitor
        )
        
        # Calculate pixel coordinates for different image sizes
        pixel_x, pixel_y = self.coordinate_handler.calculate_pixel_coordinates(coord_info, 800, 600)
        
        assert pixel_x == 400  # 0.5 * 800
        assert pixel_y == 300  # 0.5 * 600
        
        print(f"SUCCESS: Pixel calculation - ({pixel_x}, {pixel_y}) for 800x600 image")
    
    def test_coordinate_clamping(self):
        """Test coordinate clamping within monitor bounds"""
        # Set up monitor
        mock_monitors = [
            {'id': 1, 'left': 0, 'top': 0, 'width': 1920, 'height': 1080, 'primary': True}
        ]
        self.coordinate_handler.update_monitor_info(mock_monitors)
        
        # Test coordinates outside monitor bounds
        coord_info = self.coordinate_handler.transform_coordinates(-100, -50)  # Negative coordinates
        
        # Should be clamped to monitor bounds
        assert coord_info.monitor_relative_x >= 0
        assert coord_info.monitor_relative_y >= 0
        assert coord_info.percentage_x >= 0.0
        assert coord_info.percentage_y >= 0.0
        
        # Test coordinates too large
        coord_info = self.coordinate_handler.transform_coordinates(3000, 2000)  # Outside bounds
        
        # Should be clamped to monitor maximum
        assert coord_info.monitor_relative_x < 1920
        assert coord_info.monitor_relative_y < 1080
        assert coord_info.percentage_x <= 1.0
        assert coord_info.percentage_y <= 1.0
        
        print("SUCCESS: Coordinate clamping works correctly")
    
    def test_capture_monitor_tracking(self):
        """Test tracking of last captured monitor"""
        # Set up monitors
        mock_monitors = [
            {'id': 1, 'left': 0, 'top': 0, 'width': 1920, 'height': 1080, 'primary': True},
            {'id': 2, 'left': 1920, 'top': 0, 'width': 1440, 'height': 900, 'primary': False}
        ]
        self.coordinate_handler.update_monitor_info(mock_monitors)
        
        # Simulate capture on monitor 2
        coord_info = self.coordinate_handler.transform_coordinates(2200, 300)
        self.coordinate_handler.set_last_capture_monitor(coord_info.monitor)
        
        # Verify last capture monitor is tracked
        last_monitor = self.coordinate_handler.get_last_capture_monitor()
        assert last_monitor is not None
        assert last_monitor.id == 2
        
        print("SUCCESS: Capture monitor tracking")
    
    def test_coordinate_validation(self):
        """Test coordinate validation and error handling"""
        # Test with no monitors configured
        coord_info = self.coordinate_handler.transform_coordinates(500, 300)
        
        # Should return basic coordinate info with fallback behavior
        assert coord_info.global_x == 500
        assert coord_info.global_y == 300
        
        print("SUCCESS: Coordinate validation with no monitors")


def run_coordinate_system_handler_tests():
    """Run all coordinate system handler tests"""
    print("Running CoordinateSystemHandler tests...")
    
    # Test MonitorInfo
    monitor_info_test = TestMonitorInfo()
    try:
        monitor_info_test.test_monitor_info_creation()
        print("  PASS MonitorInfo creation")
        
        monitor_info_test.test_monitor_info_secondary()
        print("  PASS MonitorInfo secondary monitor")
    except Exception as e:
        print(f"  FAIL MonitorInfo test: {e}")
        return False
    
    # Test CoordinateInfo
    coord_info_test = TestCoordinateInfo()
    try:
        coord_info_test.test_coordinate_info_creation()
        print("  PASS CoordinateInfo creation")
    except Exception as e:
        print(f"  FAIL CoordinateInfo test: {e}")
        return False
    
    # Test CoordinateSystemHandler
    handler_test = TestCoordinateSystemHandler()
    
    test_methods = [
        ('initial state', 'test_initial_state'),
        ('monitor info update', 'test_update_monitor_info'),
        ('primary monitor detection', 'test_get_monitor_from_point_primary'),
        ('secondary monitor detection', 'test_get_monitor_from_point_secondary'),
        ('monitor fallback', 'test_get_monitor_from_point_not_found'),
        ('single monitor transform', 'test_transform_coordinates_single_monitor'),
        ('multi monitor transform', 'test_transform_coordinates_multi_monitor'),
        ('pixel coordinate calculation', 'test_calculate_pixel_coordinates'),
        ('coordinate clamping', 'test_coordinate_clamping'),
        ('capture monitor tracking', 'test_capture_monitor_tracking'),
        ('coordinate validation', 'test_coordinate_validation')
    ]
    
    for test_name, test_method in test_methods:
        try:
            handler_test.setup_method()
            getattr(handler_test, test_method)()
            print(f"  PASS {test_name}")
        except Exception as e:
            print(f"  FAIL {test_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("All CoordinateSystemHandler tests passed!")
    print("NEXT: Implement CoordinateSystemHandler based on test specifications")
    return True


if __name__ == "__main__":
    run_coordinate_system_handler_tests()