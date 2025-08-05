"""
Screenshot capture functionality
Cross-platform screen capture using mss library
"""

import time
import platform
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import mss
from PIL import Image, ImageDraw
import numpy as np

class ScreenCapture:
    """Cross-platform screenshot capture manager"""
    
    def __init__(self, debug_mode: bool = False):
        self.sct = mss.mss()
        self.system = platform.system().lower()
        self._last_screenshot = None
        self._last_screenshot_time = 0
        self.debug_mode = debug_mode
        
    def capture_full_screen(self, monitor_id: int = 1) -> Image.Image:
        """
        Capture full screen screenshot
        
        Args:
            monitor_id: Monitor number (1 for primary, 0 for all monitors)
            
        Returns:
            PIL Image of the screenshot
        """
        try:
            # Get monitor information
            if monitor_id == 0:
                # Capture all monitors
                monitor = self.sct.monitors[0]  # All monitors combined
            else:
                # Capture specific monitor (default to primary)
                monitor = self.sct.monitors[min(monitor_id, len(self.sct.monitors) - 1)]
            
            # Capture screenshot
            screenshot = self.sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Cache the screenshot
            self._last_screenshot = img
            self._last_screenshot_time = time.time()
            
            return img
            
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return None
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> Optional[Image.Image]:
        """
        Capture a specific region of the screen
        
        Args:
            x, y: Top-left coordinates
            width, height: Region dimensions
            
        Returns:
            PIL Image of the region or None if failed
        """
        try:
            # Define region
            region = {
                "top": y,
                "left": x,
                "width": width,
                "height": height
            }
            
            # Capture region
            screenshot = self.sct.grab(region)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            return img
            
        except Exception as e:
            print(f"Error capturing region: {e}")
            return None
    
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
        try:
            primary_monitor = self.sct.monitors[1]  # Primary monitor
            all_monitors = self.sct.monitors[0]     # All monitors combined
            
            return {
                'primary_width': primary_monitor['width'],
                'primary_height': primary_monitor['height'],
                'width': all_monitors['width'],
                'height': all_monitors['height'],
                'monitor_count': len(self.sct.monitors) - 1,  # -1 because [0] is all monitors
                'system': self.system
            }
            
        except Exception as e:
            print(f"Error getting screen info: {e}")
            return {'width': 1920, 'height': 1080, 'monitor_count': 1, 'system': self.system}
    
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
            print(f"Error saving screenshot: {e}")
            return False
    
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
            print(f"Error extracting region: {e}")
            # Return a default region around the point
            return image.crop((max(0, x-50), max(0, y-25), 
                             x+50, y+25))
    
    def add_debug_click_marker(self, image: Image.Image, x: int, y: int, 
                              marker_size: int = 6, color: str = "red") -> Image.Image:
        """
        Add a debug marker (red dot) at precise click location
        
        Args:
            image: PIL Image to mark
            x, y: Exact click coordinates
            marker_size: Size of the marker dot (radius)
            color: Color of the marker
            
        Returns:
            Image with debug marker added
        """
        if not self.debug_mode:
            return image
        
        try:
            # Create a copy to avoid modifying original
            marked_image = image.copy()
            draw = ImageDraw.Draw(marked_image)
            
            # Draw filled circle at exact click location
            left = x - marker_size
            top = y - marker_size
            right = x + marker_size
            bottom = y + marker_size
            
            # Draw the marker dot
            draw.ellipse([left, top, right, bottom], fill=color, outline="darkred", width=1)
            
            # Add crosshair for precise location
            crosshair_size = marker_size + 3
            draw.line([x - crosshair_size, y, x + crosshair_size, y], fill=color, width=1)
            draw.line([x, y - crosshair_size, x, y + crosshair_size], fill=color, width=1)
            
            return marked_image
            
        except Exception as e:
            print(f"Error adding debug marker: {e}")
            return image
    
    def set_debug_mode(self, enabled: bool):
        """Enable or disable debug mode"""
        self.debug_mode = enabled
        if enabled:
            print("Debug mode enabled - precise click locations will be marked with red dots")
        else:
            print("Debug mode disabled")
    
    def close(self):
        """Clean up resources"""
        if hasattr(self.sct, 'close'):
            self.sct.close()