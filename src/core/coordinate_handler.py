"""
Coordinate System Handler for TutorialMaker
Centralizes multi-monitor coordinate mapping and transformations
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
from .logger import get_logger

@dataclass
class MonitorInfo:
    """Information about a monitor/display"""
    id: int
    left: int
    top: int
    width: int
    height: int
    is_primary: bool = False
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if the point is within this monitor's bounds"""
        return (self.left <= x < self.left + self.width and 
                self.top <= y < self.top + self.height)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for compatibility"""
        return {
            'id': self.id,
            'left': self.left,
            'top': self.top, 
            'width': self.width,
            'height': self.height,
            'primary': self.is_primary
        }


@dataclass 
class CoordinateInfo:
    """Complete coordinate information for a point"""
    global_x: int
    global_y: int
    monitor_relative_x: int
    monitor_relative_y: int
    percentage_x: float
    percentage_y: float
    monitor: MonitorInfo
    
    def to_legacy_dict(self) -> Dict[str, Any]:
        """Convert to legacy coordinate_info format for compatibility"""
        return {
            'screen_width': self.monitor.width,  # For compatibility, use monitor width
            'screen_height': self.monitor.height,
            'monitor_relative_x': self.monitor_relative_x,
            'monitor_relative_y': self.monitor_relative_y,
            'monitor_info': self.monitor.to_dict()
        }


class CoordinateSystemHandler:
    """Centralized handler for multi-monitor coordinate transformations"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self._monitors: List[MonitorInfo] = []
        self._primary_monitor: Optional[MonitorInfo] = None
        self._last_capture_monitor: Optional[MonitorInfo] = None
        self.logger = get_logger('core.coordinate_handler')
        
        if self.debug_mode:
            self.logger.debug("CoordinateSystemHandler initialized")
    
    def update_monitor_info(self, monitor_data: List[Dict[str, Any]]):
        """
        Update monitor information from screen capture data
        
        Args:
            monitor_data: List of monitor dictionaries with keys:
                         id, left, top, width, height, primary
        """
        self._monitors = []
        self._primary_monitor = None
        
        for monitor_dict in monitor_data:
            monitor = MonitorInfo(
                id=monitor_dict['id'],
                left=monitor_dict['left'],
                top=monitor_dict['top'],
                width=monitor_dict['width'],
                height=monitor_dict['height'],
                is_primary=monitor_dict.get('primary', False)
            )
            
            self._monitors.append(monitor)
            
            if monitor.is_primary:
                self._primary_monitor = monitor
        
        # Fallback: if no primary monitor found, use first monitor
        if not self._primary_monitor and self._monitors:
            self._primary_monitor = self._monitors[0]
            self._primary_monitor.is_primary = True
        
        if self.debug_mode:
            self.logger.debug(f"Updated monitor info - {len(self._monitors)} monitors")
            for monitor in self._monitors:
                primary_str = " (PRIMARY)" if monitor.is_primary else ""
                self.logger.debug(f"  Monitor {monitor.id}: {monitor.width}x{monitor.height} at ({monitor.left}, {monitor.top}){primary_str}")
    
    def get_monitor_from_point(self, x: int, y: int) -> Optional[MonitorInfo]:
        """
        Determine which monitor contains the given point
        
        Args:
            x, y: Global screen coordinates
            
        Returns:
            MonitorInfo for the monitor containing the point, or primary monitor as fallback
        """
        # Check each monitor
        for monitor in self._monitors:
            if monitor.contains_point(x, y):
                if self.debug_mode:
                    self.logger.debug(f"Point ({x}, {y}) found on monitor {monitor.id}")
                return monitor
        
        # Fallback to primary monitor
        if self.debug_mode:
            self.logger.debug(f"Point ({x}, {y}) not found on any monitor, using primary")
        return self._primary_monitor
    
    def transform_coordinates(self, global_x: int, global_y: int) -> CoordinateInfo:
        """
        Transform global coordinates to all coordinate systems
        
        Args:
            global_x, global_y: Global screen coordinates
            
        Returns:
            CoordinateInfo with all coordinate transformations
        """
        # Get the monitor containing this point
        monitor = self.get_monitor_from_point(global_x, global_y)
        
        if not monitor:
            if self.debug_mode:
                self.logger.debug(f"No monitor info available for ({global_x}, {global_y})")
            # Create fallback monitor
            monitor = MonitorInfo(
                id=1, left=0, top=0, width=1920, height=1080, is_primary=True
            )
        
        # Calculate monitor-relative coordinates
        relative_x = global_x - monitor.left
        relative_y = global_y - monitor.top
        
        # Clamp coordinates to monitor bounds
        clamped_x = max(0, min(relative_x, monitor.width - 1))
        clamped_y = max(0, min(relative_y, monitor.height - 1))
        
        # Calculate percentage coordinates (0.0 to 1.0)
        percentage_x = clamped_x / monitor.width if monitor.width > 0 else 0.0
        percentage_y = clamped_y / monitor.height if monitor.height > 0 else 0.0
        
        if self.debug_mode:
            if clamped_x != relative_x or clamped_y != relative_y:
                self.logger.debug(f"Coordinates clamped from ({relative_x}, {relative_y}) to ({clamped_x}, {clamped_y})")
            self.logger.debug(f"Global ({global_x}, {global_y}) -> Relative ({clamped_x}, {clamped_y}) -> Percentage ({percentage_x:.3f}, {percentage_y:.3f})")
        
        return CoordinateInfo(
            global_x=global_x,
            global_y=global_y,
            monitor_relative_x=clamped_x,
            monitor_relative_y=clamped_y,
            percentage_x=percentage_x,
            percentage_y=percentage_y,
            monitor=monitor
        )
    
    def calculate_pixel_coordinates(self, coord_info: CoordinateInfo, image_width: int, image_height: int) -> Tuple[int, int]:
        """
        Calculate pixel coordinates within an image using percentage coordinates
        
        Args:
            coord_info: CoordinateInfo with percentage coordinates
            image_width, image_height: Dimensions of target image
            
        Returns:
            Tuple of (pixel_x, pixel_y) within the image
        """
        pixel_x = int(coord_info.percentage_x * image_width)
        pixel_y = int(coord_info.percentage_y * image_height)
        
        # Ensure coordinates are within image bounds
        pixel_x = max(0, min(pixel_x, image_width - 1))
        pixel_y = max(0, min(pixel_y, image_height - 1))
        
        if self.debug_mode:
            self.logger.debug(f"Percentage ({coord_info.percentage_x:.3f}, {coord_info.percentage_y:.3f}) -> Pixel ({pixel_x}, {pixel_y}) in {image_width}x{image_height}")
        
        return pixel_x, pixel_y
    
    def set_last_capture_monitor(self, monitor: MonitorInfo):
        """Set the monitor that was last used for capture"""
        self._last_capture_monitor = monitor
        if self.debug_mode:
            self.logger.debug(f"Set last capture monitor to {monitor.id}")
    
    def get_last_capture_monitor(self) -> Optional[MonitorInfo]:
        """Get the monitor that was last used for capture"""
        return self._last_capture_monitor
    
    def get_primary_monitor(self) -> Optional[MonitorInfo]:
        """Get the primary monitor"""
        return self._primary_monitor
    
    def get_all_monitors(self) -> List[MonitorInfo]:
        """Get all available monitors"""
        return self._monitors.copy()
    
    def get_screen_info(self) -> Dict[str, Any]:
        """
        Get comprehensive screen information for compatibility
        
        Returns:
            Dictionary with screen information compatible with existing code
        """
        if not self._monitors:
            return {
                'width': 1920,
                'height': 1080,
                'monitor_count': 1,
                'monitors': []
            }
        
        # Calculate total screen dimensions
        if len(self._monitors) == 1:
            # Single monitor
            primary = self._primary_monitor or self._monitors[0]
            total_width = primary.width
            total_height = primary.height
        else:
            # Multi-monitor - calculate bounding box
            min_left = min(m.left for m in self._monitors)
            max_right = max(m.left + m.width for m in self._monitors)
            min_top = min(m.top for m in self._monitors)
            max_bottom = max(m.top + m.height for m in self._monitors)
            
            total_width = max_right - min_left
            total_height = max_bottom - min_top
        
        return {
            'width': total_width,
            'height': total_height,
            'monitor_count': len(self._monitors),
            'monitors': [m.to_dict() for m in self._monitors]
        }
    
    def is_multi_monitor(self) -> bool:
        """Check if this is a multi-monitor setup"""
        return len(self._monitors) > 1
    
    def debug_coordinate_info(self, coord_info: CoordinateInfo):
        """Print detailed coordinate information for debugging"""
        if not self.debug_mode:
            return
            
        print(f"DEBUG: === Coordinate Info ===")
        print(f"DEBUG: Global: ({coord_info.global_x}, {coord_info.global_y})")
        print(f"DEBUG: Monitor Relative: ({coord_info.monitor_relative_x}, {coord_info.monitor_relative_y})")
        print(f"DEBUG: Percentage: ({coord_info.percentage_x:.3f}, {coord_info.percentage_y:.3f})")
        print(f"DEBUG: Monitor: {coord_info.monitor.id} ({coord_info.monitor.width}x{coord_info.monitor.height})")
        print(f"DEBUG: Monitor Position: ({coord_info.monitor.left}, {coord_info.monitor.top})")
        print(f"DEBUG: ========================")