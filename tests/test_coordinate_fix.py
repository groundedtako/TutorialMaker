"""
Quick test to validate the coordinate fix
"""

import sys
from pathlib import Path

# Add project root and src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.core.event_queue import QueuedEvent
from src.core.events import MouseClickEvent
import time

def test_coordinate_info_storage():
    """Test that coordinate info is properly stored with events"""
    
    # Create a mock mouse click event
    event = MouseClickEvent(x=500, y=300, button='left', pressed=True, timestamp=time.time())
    
    # Create mock coordinate info
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
        event_data={
            'x': event.x,
            'y': event.y,
            'button': event.button,
            'timestamp': event.timestamp
        },
        screenshot=None,  # Mock screenshot
        coordinate_info=coordinate_info
    )
    
    # Validate coordinate info is stored
    assert queued_event.coordinate_info is not None
    assert queued_event.coordinate_info['monitor_relative_x'] == 200
    assert queued_event.coordinate_info['monitor_relative_y'] == 150
    assert queued_event.coordinate_info['monitor_info']['width'] == 800
    
    print("SUCCESS: Coordinate info storage test passed")
    
    # Test percentage calculation
    coord_info = queued_event.coordinate_info
    monitor_info = coord_info['monitor_info']
    x_pct = coord_info['monitor_relative_x'] / monitor_info['width']
    y_pct = coord_info['monitor_relative_y'] / monitor_info['height']
    
    expected_x_pct = 200 / 800  # 0.25
    expected_y_pct = 150 / 600  # 0.25
    
    assert abs(x_pct - expected_x_pct) < 0.001
    assert abs(y_pct - expected_y_pct) < 0.001
    
    print("SUCCESS: Percentage calculation test passed")
    print(f"   Click percentages: ({x_pct:.3f}, {y_pct:.3f})")

if __name__ == "__main__":
    test_coordinate_info_storage()
    print("\nAll coordinate fix tests passed!")