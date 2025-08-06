"""
Screenshot processing with click highlighting
Adds visual indicators to show where clicks occurred
"""

from PIL import Image, ImageDraw
from typing import Tuple, Optional
import math

class ClickHighlighter:
    """Add click indicators to screenshots"""
    
    def __init__(self):
        self.highlight_color = (59, 130, 246, 100)  # Blue with transparency (rgba)
        self.border_color = (59, 130, 246, 180)     # Darker blue border
        self.radius = 20
        self.border_width = 2
    
    def add_click_indicator(self, image: Image.Image, click_x: float, click_y: float) -> Image.Image:
        """
        Add a click indicator circle to the screenshot
        
        Args:
            image: PIL Image to modify
            click_x: X coordinate of click
            click_y: Y coordinate of click
            
        Returns:
            Modified PIL Image with click indicator
        """
        # Convert to RGBA if not already
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Create a transparent overlay
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Calculate circle bounds
        left = click_x - self.radius
        top = click_y - self.radius
        right = click_x + self.radius
        bottom = click_y + self.radius
        
        # Draw filled circle (main highlight)
        draw.ellipse([left, top, right, bottom], fill=self.highlight_color)
        
        # Draw border circle
        border_left = click_x - self.radius - self.border_width//2
        border_top = click_y - self.radius - self.border_width//2
        border_right = click_x + self.radius + self.border_width//2
        border_bottom = click_y + self.radius + self.border_width//2
        
        draw.ellipse([border_left, border_top, border_right, border_bottom], 
                    outline=self.border_color, width=self.border_width)
        
        # Composite the overlay onto the original image
        result = Image.alpha_composite(image, overlay)
        
        # Convert back to RGB if original was RGB
        if image.mode == 'RGB':
            result = result.convert('RGB')
        
        return result
    
    def add_animated_click_indicator_html(self, click_x: float, click_y: float, 
                                        screenshot_width: int, screenshot_height: int) -> str:
        """
        Generate HTML/CSS for animated click indicator
        
        Args:
            click_x: X coordinate of click
            click_y: Y coordinate of click
            screenshot_width: Width of screenshot for scaling
            screenshot_height: Height of screenshot for scaling
            
        Returns:
            HTML string with click indicator
        """
        # Calculate position as percentage for responsive design
        x_percent = (click_x / screenshot_width) * 100
        y_percent = (click_y / screenshot_height) * 100
        
        return f"""
        <div class="click-indicator" style="left: calc({x_percent}% - 20px); top: calc({y_percent}% - 20px);">
            <div class="click-circle"></div>
        </div>
        """
    
    def get_click_indicator_css(self) -> str:
        """Get CSS for animated click indicators"""
        return """
        .screenshot-container {
            position: relative;
            display: inline-block;
        }
        
        .click-indicator {
            position: absolute;
            width: 40px;
            height: 40px;
            pointer-events: none;
            z-index: 10;
        }
        
        .click-circle {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: rgba(59, 130, 246, 0.3);
            border: 2px solid rgba(59, 130, 246, 0.7);
            animation: clickPulse 2s ease-out infinite;
            opacity: 0;
        }
        
        /* Animation that triggers when step comes into view */
        .step-visible .click-circle {
            animation: clickContract 1.5s ease-out;
        }
        
        @keyframes clickContract {
            0% {
                transform: scale(3);
                opacity: 0.8;
            }
            50% {
                transform: scale(1.2);
                opacity: 0.6;
            }
            100% {
                transform: scale(1);
                opacity: 0.4;
            }
        }
        
        @keyframes clickPulse {
            0% {
                transform: scale(1);
                opacity: 0.4;
            }
            50% {
                transform: scale(1.1);
                opacity: 0.6;
            }
            100% {
                transform: scale(1);
                opacity: 0.4;
            }
        }
        
        /* Hover effect to make indicator more visible */
        .tutorial-step:hover .click-circle {
            opacity: 0.8 !important;
            transform: scale(1.1);
        }
        """

def process_screenshot_with_click(image: Image.Image, click_x: float, click_y: float) -> Image.Image:
    """
    Convenience function to add click highlighting to a screenshot
    
    Args:
        image: PIL Image to process
        click_x: X coordinate of click
        click_y: Y coordinate of click
        
    Returns:
        Processed image with click indicator
    """
    highlighter = ClickHighlighter()
    return highlighter.add_click_indicator(image, click_x, click_y)