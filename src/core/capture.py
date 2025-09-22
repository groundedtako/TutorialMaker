"""
Screenshot capture functionality
Cross-platform screen capture using mss library
"""

import time
import platform
from typing import Optional, Tuple, Dict, Any, Union
from pathlib import Path
from .logger import get_logger
try:
    import mss
    MSS_AVAILABLE = True
except (ImportError, ValueError, Exception):
    MSS_AVAILABLE = False
    # Note: Can't use logger here as it's module-level import
    print("Warning: mss not available. Screenshot capture disabled.")

try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except (ImportError, ValueError, Exception):
    PIL_AVAILABLE = False
    # Create minimal mock classes
    class Image:
        @staticmethod
        def new(*args, **kwargs):
            return None
        @staticmethod
        def frombytes(*args, **kwargs):
            return None
    class ImageDraw:
        @staticmethod
        def Draw(*args, **kwargs):
            return None
    # Note: Can't use logger here as it's module-level import
    print("Warning: PIL not available in capture module.")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except (ImportError, ValueError, Exception):
    NUMPY_AVAILABLE = False
    # Note: Can't use logger here as it's module-level import
    print("Warning: numpy not available in capture module.")

class ScreenCapture:
    """Cross-platform screenshot capture manager"""
    
    def __init__(self, debug_mode: bool = False):
        # Don't create MSS instance in __init__ to avoid threading issues
        self.system = platform.system().lower()
        self._last_screenshot = None
        self._last_screenshot_time = 0
        self.debug_mode = debug_mode
        self._thread_local_sct = None
        self._last_monitor_info = None
        self.logger = get_logger('core.capture')
        
    def _get_sct_instance(self):
        """Get thread-local MSS instance to avoid threading issues on Windows"""
        if not MSS_AVAILABLE:
            return None
        
        # Create a new MSS instance for each thread to avoid Windows threading issues
        try:
            return mss.mss()
        except Exception as e:
            self.logger.error(f"Error creating MSS instance: {e}")
            return None
    
    def get_monitor_from_point(self, x: int, y: int) -> int:
        """Determine which monitor contains the given point"""
        sct = self._get_sct_instance()
        if not sct:
            return 1  # Default to primary monitor
        
        try:
            if self.debug_mode:
                self.logger.debug(f"Detecting monitor for point ({x}, {y})")
                self.logger.debug(f"Available monitors: {len(sct.monitors) - 1}")
            
            # Check each monitor to see which contains the point
            for i, monitor in enumerate(sct.monitors[1:], 1):  # Skip index 0 (all monitors)
                left, top = monitor['left'], monitor['top']
                right, bottom = left + monitor['width'], top + monitor['height']
                
                if self.debug_mode:
                    self.logger.debug(f"Monitor {i}: ({left}, {top}) to ({right}, {bottom}) [{monitor['width']}x{monitor['height']}]")
                
                if (left <= x < right and top <= y < bottom):
                    if self.debug_mode:
                        self.logger.debug(f"Point ({x}, {y}) found in Monitor {i}")
                    return i
            
            # If point is not found in any monitor, return primary monitor
            if self.debug_mode:
                self.logger.debug(f"Point ({x}, {y}) not found in any monitor, defaulting to Monitor 1")
            return 1
        except Exception as e:
            self.logger.error(f"Error detecting monitor: {e}")
            return 1
        finally:
            if sct and hasattr(sct, 'close'):
                sct.close()
    
    def capture_full_screen(self, monitor_id: int = 1, click_point: tuple = None) -> Optional[Image.Image]:
        """
        Capture full screen screenshot
        
        Args:
            monitor_id: Monitor number (1 for primary, 0 for all monitors, -1 for auto-detect)
            click_point: Tuple (x, y) to auto-detect which monitor to capture from
            
        Returns:
            PIL Image of the screenshot, or None if capture not available
        """
        if not MSS_AVAILABLE:
            self.logger.warning("Screenshot capture not available")
            return None
        
        sct = self._get_sct_instance()
        if not sct:
            self.logger.error("Failed to create MSS instance")
            return None
            
        try:
            # Auto-detect monitor based on click point
            if click_point is not None:
                monitor_id = self.get_monitor_from_point(click_point[0], click_point[1])
                if self.debug_mode:
                    self.logger.debug(f"Auto-detected monitor {monitor_id} for click at {click_point}")
            
            # Get monitor information
            if monitor_id == 0:
                # Capture all monitors
                monitor = sct.monitors[0]  # All monitors combined
            else:
                # Capture specific monitor (default to primary)
                monitor = sct.monitors[min(monitor_id, len(sct.monitors) - 1)]
            
            if self.debug_mode:
                self.logger.debug(f"Capturing monitor {monitor_id}: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")
            
            # Capture screenshot
            screenshot = sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Cache the screenshot and monitor info
            self._last_screenshot = img
            self._last_screenshot_time = time.time()
            self._last_monitor_info = {
                'id': monitor_id,
                'left': monitor['left'],
                'top': monitor['top'],
                'width': monitor['width'],
                'height': monitor['height']
            }
            
            return img
            
        except Exception as e:
            self.logger.error(f"Error capturing screenshot: {e}")
            return None
        finally:
            # Always close the MSS instance to prevent threading issues
            if sct and hasattr(sct, 'close'):
                sct.close()
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> Optional[Image.Image]:
        """
        Capture a specific region of the screen
        
        Args:
            x, y: Top-left coordinates
            width, height: Region dimensions
            
        Returns:
            PIL Image of the region or None if failed
        """
        sct = self._get_sct_instance()
        if not sct:
            return None
            
        try:
            # Define region
            region = {
                "top": y,
                "left": x,
                "width": width,
                "height": height
            }
            
            # Capture region
            screenshot = sct.grab(region)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            return img
            
        except Exception as e:
            self.logger.error(f"Error capturing region: {e}")
            return None
        finally:
            if sct and hasattr(sct, 'close'):
                sct.close()
    
    def capture_click_region(self, click_x: int, click_y: int, 
                           base_width: int = 200, base_height: int = 100) -> Optional[Image.Image]:
        """
        Capture region around a click point for OCR analysis
        
        Args:
            click_x, click_y: Click coordinates
            base_width, base_height: Base region size
            
        Returns:
            PIL Image of the click region
        """
        # Calculate region bounds
        half_width = base_width // 2
        half_height = base_height // 2
        
        x = max(0, click_x - half_width)
        y = max(0, click_y - half_height)
        
        # Get screen bounds to avoid capturing outside screen
        screen_info = self.get_screen_info()
        max_x = screen_info['width'] - base_width
        max_y = screen_info['height'] - base_height
        
        x = min(x, max_x) if max_x > 0 else x
        y = min(y, max_y) if max_y > 0 else y
        
        return self.capture_region(x, y, base_width, base_height)
    
    def get_screen_info(self) -> Dict[str, Any]:
        """
        Get information about the screen/monitors
        
        Returns:
            Dictionary with screen information
        """
        sct = self._get_sct_instance()
        if not sct:
            return {'width': 1920, 'height': 1080, 'monitor_count': 1, 'system': self.system}
            
        try:
            primary_monitor = sct.monitors[1]  # Primary monitor
            all_monitors = sct.monitors[0]     # All monitors combined
            
            screen_info = {
                'primary_width': primary_monitor['width'],
                'primary_height': primary_monitor['height'],
                'width': all_monitors['width'],
                'height': all_monitors['height'],
                'monitor_count': len(sct.monitors) - 1,  # -1 because [0] is all monitors
                'system': self.system,
                'monitors': []
            }
            
            # Add detailed monitor information
            for i, monitor in enumerate(sct.monitors[1:], 1):
                # Check if monitor appears to be in portrait mode
                is_portrait = monitor['height'] > monitor['width']
                screen_info['monitors'].append({
                    'id': i,
                    'left': monitor['left'],
                    'top': monitor['top'],
                    'width': monitor['width'],
                    'height': monitor['height'],
                    'is_portrait': is_portrait,
                    'aspect_ratio': round(monitor['width'] / monitor['height'], 2)
                })
            
            return screen_info
            
        except Exception as e:
            self.logger.error(f"Error getting screen info: {e}")
            return {'width': 1920, 'height': 1080, 'monitor_count': 1, 'system': self.system}
        finally:
            if sct and hasattr(sct, 'close'):
                sct.close()
    
    def save_screenshot(self, image: Image.Image, filepath: Path) -> bool:
        """
        Save screenshot to file
        
        Args:
            image: PIL Image to save
            filepath: Path to save the image
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Save image
            image.save(filepath, "PNG")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving screenshot: {e}")
            return False
    
    def get_last_monitor_info(self) -> Optional[dict]:
        """Get information about the last captured monitor"""
        return self._last_monitor_info
    
    def adjust_coordinates_to_monitor(self, global_x: int, global_y: int) -> Tuple[int, int]:
        """
        Adjust global coordinates to be relative to the last captured monitor
        
        Args:
            global_x, global_y: Global screen coordinates
            
        Returns:
            Tuple of (monitor_relative_x, monitor_relative_y)
        """
        if not self._last_monitor_info:
            if self.debug_mode:
                self.logger.debug("No monitor info available, returning global coordinates")
            return global_x, global_y
        
        monitor = self._last_monitor_info
        relative_x = global_x - monitor['left']
        relative_y = global_y - monitor['top']
        
        if self.debug_mode:
            self.logger.debug(f"Adjusting coordinates ({global_x}, {global_y}) for monitor at ({monitor['left']}, {monitor['top']})")
            self.logger.debug(f"Monitor size: {monitor['width']}x{monitor['height']}")
            self.logger.debug(f"Raw relative: ({relative_x}, {relative_y})")
        
        # Ensure coordinates are within monitor bounds
        clamped_x = max(0, min(relative_x, monitor['width'] - 1))
        clamped_y = max(0, min(relative_y, monitor['height'] - 1))
        
        if self.debug_mode and (clamped_x != relative_x or clamped_y != relative_y):
            self.logger.debug(f"Coordinates clamped from ({relative_x}, {relative_y}) to ({clamped_x}, {clamped_y})")
        
        return clamped_x, clamped_y
    
    def get_cached_screenshot(self, max_age_seconds: float = 0.1) -> Optional[Image.Image]:
        """
        Get cached screenshot if it's recent enough
        
        Args:
            max_age_seconds: Maximum age of cached screenshot
            
        Returns:
            Cached screenshot or None if too old/doesn't exist
        """
        if (self._last_screenshot and 
            time.time() - self._last_screenshot_time <= max_age_seconds):
            return self._last_screenshot
        return None
    
    def extract_region_around_point(self, image: Image.Image, x: int, y: int, 
                                  expand_factor: float = 1.5) -> Image.Image:
        """
        Extract and expand region around a point using smart boundary detection
        
        Args:
            image: Source image
            x, y: Point coordinates relative to image
            expand_factor: How much to expand detected boundaries
            
        Returns:
            Cropped image region
        """
        try:
            # Convert to numpy for analysis
            img_array = np.array(image)
            
            # Basic region extraction (we'll enhance this later with edge detection)
            base_size = 100
            half_size = int(base_size * expand_factor) // 2
            
            x1 = max(0, x - half_size)
            y1 = max(0, y - half_size)
            x2 = min(img_array.shape[1], x + half_size)
            y2 = min(img_array.shape[0], y + half_size)
            
            # Crop the region
            region = image.crop((x1, y1, x2, y2))
            
            return region
            
        except Exception as e:
            self.logger.error(f"Error extracting region: {e}")
            # Return a default region around the point
            return image.crop((max(0, x-50), max(0, y-25), 
                             x+50, y+25))
    
    def add_debug_click_marker(self, image: Image.Image, x: int = None, y: int = None,
                              x_pct: float = None, y_pct: float = None,
                              marker_size: int = 6, color: str = "red") -> Image.Image:
        """
        Add a debug marker (red dot) at precise click location
        
        Args:
            image: PIL Image to mark
            x, y: Exact click coordinates (absolute pixels) - legacy support
            x_pct, y_pct: Click coordinates as percentages (0.0-1.0) - preferred
            marker_size: Size of the marker dot (radius)
            color: Color of the marker
            
        Returns:
            Image with debug marker added
        """
        if not self.debug_mode:
            return image
        
        try:
            # Convert percentage coordinates to pixel coordinates if provided
            if x_pct is not None and y_pct is not None:
                img_width, img_height = image.size
                pixel_x = int(x_pct * img_width)
                pixel_y = int(y_pct * img_height)
            elif x is not None and y is not None:
                # Use absolute coordinates (legacy support)
                pixel_x = x
                pixel_y = y
            else:
                self.logger.warning("No coordinates provided to add_debug_click_marker")
                return image
            
            # Create a copy to avoid modifying original
            marked_image = image.copy()
            draw = ImageDraw.Draw(marked_image)
            
            # Draw filled circle at exact click location
            left = pixel_x - marker_size
            top = pixel_y - marker_size
            right = pixel_x + marker_size
            bottom = pixel_y + marker_size
            
            # Draw the marker dot
            draw.ellipse([left, top, right, bottom], fill=color, outline="darkred", width=1)
            
            # Add crosshair for precise location
            crosshair_size = marker_size + 3
            draw.line([pixel_x - crosshair_size, pixel_y, pixel_x + crosshair_size, pixel_y], fill=color, width=1)
            draw.line([pixel_x, pixel_y - crosshair_size, pixel_x, pixel_y + crosshair_size], fill=color, width=1)
            
            return marked_image
            
        except Exception as e:
            self.logger.error(f"Error adding debug marker: {e}")
            return image
    
    def set_debug_mode(self, enabled: bool):
        """Enable or disable debug mode"""
        self.debug_mode = enabled
        if enabled:
            self.logger.info("Debug mode enabled - precise click locations will be marked with red dots")
        else:
            self.logger.info("Debug mode disabled")
    
    def close(self):
        """Clean up resources"""
        # No persistent MSS instance to close since we create thread-local instances
        pass