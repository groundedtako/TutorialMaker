"""
Smart OCR Processing with Region Detection and Context Analysis
Fully offline solution for improved OCR accuracy
"""

import time
import math
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

from .ocr import OCREngine, OCRResult


class SmartRegion:
    """Represents a detected UI element region"""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 element_type: str = "unknown", confidence: float = 0.0):
        self.x = x
        self.y = y 
        self.width = width
        self.height = height
        self.element_type = element_type
        self.confidence = confidence
    
    def contains_point(self, px: int, py: int) -> bool:
        """Check if point is inside this region"""
        return (self.x <= px <= self.x + self.width and 
                self.y <= py <= self.y + self.height)
    
    def get_bounds(self) -> Tuple[int, int, int, int]:
        """Get region bounds as (x1, y1, x2, y2)"""
        return (self.x, self.y, self.x + self.width, self.y + self.height)


class SmartOCRProcessor:
    """Advanced OCR processor with smart region detection"""
    
    def __init__(self):
        self.ocr_engine = OCREngine()
        self.min_confidence = 0.6  # Minimum confidence for valid text
        self.min_word_length = 2   # Minimum word length
        
        # Element detection settings
        self.button_min_size = (20, 15)    # Minimum button size
        self.button_max_size = (300, 60)   # Maximum button size  
        self.text_region_padding = 10      # Extra padding for text regions
    
    def process_click_region(self, screenshot: Image.Image, click_x: int, click_y: int, 
                           debug_mode: bool = False) -> OCRResult:
        """
        Process click region with smart element detection
        
        Args:
            screenshot: Full screenshot image
            click_x, click_y: Click coordinates
            debug_mode: Whether to save debug images
            
        Returns:
            OCRResult with improved accuracy
        """
        start_time = time.time()
        
        # Step 1: Detect UI elements around click point
        detected_regions = self._detect_ui_elements(screenshot, click_x, click_y)
        
        # Step 2: Find best region containing the click
        target_region = self._find_best_region_for_click(detected_regions, click_x, click_y)
        
        # Step 3: Extract and process the region
        if target_region:
            region_image = self._extract_region(screenshot, target_region)
            ocr_result = self._process_region_with_ocr(region_image, target_region)
        else:
            # Fallback to adaptive region sizing
            region_image = self._extract_adaptive_region(screenshot, click_x, click_y)
            ocr_result = self._process_region_with_ocr(region_image, None)
        
        # Step 4: Validate and filter results
        validated_result = self._validate_ocr_result(ocr_result, click_x, click_y)
        
        # Step 5: Generate fallback description if OCR failed
        if not validated_result.is_valid():
            validated_result = self._generate_context_description(
                screenshot, click_x, click_y, debug_mode
            )
        
        validated_result.processing_time = time.time() - start_time
        
        if debug_mode:
            self._save_debug_info(screenshot, click_x, click_y, target_region, validated_result)
        
        return validated_result
    
    def _detect_ui_elements(self, image: Image.Image, click_x: int, click_y: int) -> List[SmartRegion]:
        """
        Detect UI elements around click point using computer vision
        Fully offline using edge detection and contour analysis
        """
        regions = []
        
        if not OPENCV_AVAILABLE or not NUMPY_AVAILABLE:
            return regions
        
        try:
            # Convert PIL to OpenCV
            img_array = np.array(image)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Define search area around click (larger than old fixed region)
            search_radius = 150
            x1 = max(0, click_x - search_radius)
            y1 = max(0, click_y - search_radius)
            x2 = min(image.width, click_x + search_radius)
            y2 = min(image.height, click_y + search_radius)
            
            # Crop to search area
            search_region = gray[y1:y2, x1:x2]
            
            # Edge detection for UI elements
            edges = cv2.Canny(search_region, 50, 150)
            
            # Morphological operations to connect edges
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            
            # Find contours (potential UI elements)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Convert back to full image coordinates
                abs_x = x1 + x
                abs_y = y1 + y
                
                # Filter by size (likely UI elements)
                if (self.button_min_size[0] <= w <= self.button_max_size[0] and
                    self.button_min_size[1] <= h <= self.button_max_size[1]):
                    
                    # Calculate confidence based on contour properties
                    area = cv2.contourArea(contour)
                    rect_area = w * h
                    fill_ratio = area / rect_area if rect_area > 0 else 0
                    
                    # Higher confidence for rectangular shapes (typical buttons)
                    confidence = min(1.0, fill_ratio + 0.3)
                    
                    element_type = self._classify_element_type(w, h, fill_ratio)
                    
                    regions.append(SmartRegion(abs_x, abs_y, w, h, element_type, confidence))
            
        except Exception as e:
            print(f"Warning: Element detection failed: {e}")
        
        return regions
    
    def _classify_element_type(self, width: int, height: int, fill_ratio: float) -> str:
        """Classify UI element type based on dimensions"""
        aspect_ratio = width / height if height > 0 else 1
        
        if 1.5 <= aspect_ratio <= 6 and 15 <= height <= 40:
            return "button"
        elif aspect_ratio > 6 and height <= 30:
            return "text_field"
        elif aspect_ratio < 1.5 and 15 <= width <= 40:
            return "icon"
        else:
            return "unknown"
    
    def _find_best_region_for_click(self, regions: List[SmartRegion], 
                                   click_x: int, click_y: int) -> Optional[SmartRegion]:
        """Find the best region that contains or is closest to the click point"""
        
        # First, try to find regions that contain the click
        containing_regions = [r for r in regions if r.contains_point(click_x, click_y)]
        
        if containing_regions:
            # Return highest confidence region that contains the click
            return max(containing_regions, key=lambda r: r.confidence)
        
        # If no containing regions, find closest region
        if regions:
            def distance_to_click(region):
                center_x = region.x + region.width // 2
                center_y = region.y + region.height // 2
                return math.sqrt((click_x - center_x) ** 2 + (click_y - center_y) ** 2)
            
            closest_region = min(regions, key=distance_to_click)
            
            # Only use if reasonably close (within 50 pixels)
            if distance_to_click(closest_region) <= 50:
                return closest_region
        
        return None
    
    def _extract_region(self, image: Image.Image, region: SmartRegion) -> Image.Image:
        """Extract region with appropriate padding"""
        # Add padding based on element type
        if region.element_type == "button":
            padding = 5  # Small padding for buttons
        elif region.element_type == "text_field":
            padding = 3  # Minimal padding for text fields
        else:
            padding = self.text_region_padding
        
        x1 = max(0, region.x - padding)
        y1 = max(0, region.y - padding)
        x2 = min(image.width, region.x + region.width + padding)
        y2 = min(image.height, region.y + region.height + padding)
        
        return image.crop((x1, y1, x2, y2))
    
    def _extract_adaptive_region(self, image: Image.Image, click_x: int, click_y: int) -> Image.Image:
        """
        Fallback: Extract region with adaptive sizing based on local image analysis
        """
        # Analyze local area to determine appropriate region size
        base_size = 80  # Smaller than old fixed size
        
        # Simple adaptive sizing based on image complexity around click
        try:
            # Sample a small area to assess density
            sample_size = 40
            x1 = max(0, click_x - sample_size // 2)
            y1 = max(0, click_y - sample_size // 2)
            x2 = min(image.width, x1 + sample_size)
            y2 = min(image.height, y1 + sample_size)
            
            sample = image.crop((x1, y1, x2, y2))
            
            # Convert to grayscale and analyze variance
            if PIL_AVAILABLE:
                gray_sample = sample.convert('L')
                pixels = list(gray_sample.getdata())
                
                if pixels:
                    mean_brightness = sum(pixels) / len(pixels)
                    variance = sum((p - mean_brightness) ** 2 for p in pixels) / len(pixels)
                    
                    # Higher variance = more complex area = larger region needed
                    if variance > 2000:  # High complexity
                        region_width, region_height = 120, 60
                    elif variance > 1000:  # Medium complexity  
                        region_width, region_height = 100, 50
                    else:  # Low complexity
                        region_width, region_height = 80, 40
                else:
                    region_width, region_height = base_size, base_size // 2
            else:
                region_width, region_height = base_size, base_size // 2
                
        except Exception:
            region_width, region_height = base_size, base_size // 2
        
        # Extract the adaptive region
        x1 = max(0, click_x - region_width // 2)
        y1 = max(0, click_y - region_height // 2)
        x2 = min(image.width, x1 + region_width)
        y2 = min(image.height, y1 + region_height)
        
        return image.crop((x1, y1, x2, y2))
    
    def _process_region_with_ocr(self, region_image: Image.Image, 
                                region_info: Optional[SmartRegion]) -> OCRResult:
        """Process region with OCR, using region info to optimize"""
        
        # Choose preprocessing based on element type
        if region_info and region_info.element_type == "button":
            # Buttons often have contrasting text - use high contrast preprocessing
            return self.ocr_engine.extract_text(region_image, preprocessing=True)
        elif region_info and region_info.element_type == "text_field":
            # Text fields usually have clean text - minimal preprocessing
            return self.ocr_engine.extract_text(region_image, preprocessing=False)
        else:
            # Unknown elements - try both approaches and take best result
            result1 = self.ocr_engine.extract_text(region_image, preprocessing=False)
            result2 = self.ocr_engine.extract_text(region_image, preprocessing=True)
            
            return result1 if result1.confidence >= result2.confidence else result2
    
    def _validate_ocr_result(self, ocr_result: OCRResult, click_x: int, click_y: int) -> OCRResult:
        """Validate OCR result and filter out gibberish"""
        
        if not ocr_result.is_valid():
            return ocr_result
        
        text = ocr_result.cleaned_text.strip()
        
        # Filter out gibberish patterns
        if self._is_likely_gibberish(text):
            # Return invalid result
            return OCRResult("", 0.0, ocr_result.engine)
        
        # Check confidence threshold
        if ocr_result.confidence < self.min_confidence:
            return OCRResult("", 0.0, ocr_result.engine)
        
        # Check minimum word length (allow single meaningful characters like X, +, -)
        if len(text) < self.min_word_length and not self._is_meaningful_single_char(text):
            return OCRResult("", 0.0, ocr_result.engine)
        
        return ocr_result
    
    def _is_likely_gibberish(self, text: str) -> bool:
        """
        Detect if text is likely gibberish using offline heuristics
        """
        if not text:
            return True
        
        text = text.strip()
        
        # Too short or too long
        if len(text) < 1 or len(text) > 100:
            return True
        
        # Only punctuation or special characters
        if not any(c.isalnum() for c in text):
            return True
        
        # Too many consecutive non-alphabetic characters
        non_alpha_count = 0
        max_non_alpha = 0
        for char in text:
            if not char.isalpha():
                non_alpha_count += 1
                max_non_alpha = max(max_non_alpha, non_alpha_count)
            else:
                non_alpha_count = 0
        
        if max_non_alpha > 3:  # More than 3 consecutive non-letters
            return True
        
        # Check ratio of alphabetic characters
        alpha_chars = sum(1 for c in text if c.isalpha())
        alpha_ratio = alpha_chars / len(text)
        
        if alpha_ratio < 0.3:  # Less than 30% letters
            return True
        
        # Common gibberish patterns
        gibberish_patterns = [
            'ij', 'jj', 'qq', 'xx', 'zz',  # Unlikely letter combinations
            '|||', '...', '---', '___',     # Pattern repeats
        ]
        
        text_lower = text.lower()
        for pattern in gibberish_patterns:
            if pattern in text_lower:
                return True
        
        # Check for random letter sequences (no vowels in long text)
        if len(text) > 6:
            vowels = set('aeiou')
            has_vowels = any(c.lower() in vowels for c in text if c.isalpha())
            if not has_vowels and sum(1 for c in text if c.isalpha()) > 4:
                return True  # Likely gibberish if long text with no vowels
        
        return False
    
    def _is_meaningful_single_char(self, text: str) -> bool:
        """Check if a single character is meaningful (UI symbols, etc.)"""
        if len(text) != 1:
            return False
        
        # Common meaningful single characters in UI (ASCII only)
        meaningful_chars = {
            '+', '-', '*', '/', '=', '<', '>', '|', '\\', '&', '@', '#',
            'X', 'O', '?', '!', '%', '$', '^', '~', '_', '`', ':',
            'x'  # lowercase x often used as close button
        }
        
        return text in meaningful_chars or text.isalnum()
    
    def _generate_context_description(self, screenshot: Image.Image, click_x: int, click_y: int, 
                                    debug_mode: bool = False) -> OCRResult:
        """
        Generate contextual description when OCR fails
        Uses offline image analysis to provide better descriptions
        """
        
        # Try to determine what was clicked based on visual cues
        context_description = self._analyze_click_context(screenshot, click_x, click_y)
        
        if context_description:
            # Return as OCRResult with lower confidence to indicate it's inferred
            return OCRResult(context_description, 0.3, "context_analysis")
        
        # Final fallback - coordinate-based description
        return OCRResult("", 0.0, "context_analysis")
    
    def _analyze_click_context(self, image: Image.Image, click_x: int, click_y: int) -> Optional[str]:
        """
        Analyze visual context around click point to infer element type
        """
        
        if not OPENCV_AVAILABLE or not NUMPY_AVAILABLE:
            return None
        
        try:
            # Extract small region around click
            region_size = 60
            x1 = max(0, click_x - region_size // 2)
            y1 = max(0, click_y - region_size // 2)
            x2 = min(image.width, x1 + region_size)
            y2 = min(image.height, y1 + region_size)
            
            region = image.crop((x1, y1, x2, y2))
            img_array = np.array(region)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Analyze color distribution
            unique_colors = len(np.unique(img_array.reshape(-1, img_array.shape[-1]), axis=0))
            
            # Detect edges
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            
            # Brightness analysis
            mean_brightness = np.mean(gray)
            brightness_variance = np.var(gray)
            
            # Classify based on characteristics
            if edge_density > 0.1 and unique_colors < 10:
                return "button or interface element"
            elif edge_density < 0.05 and brightness_variance < 100:
                return "empty area"
            elif unique_colors > 50 and edge_density > 0.05:
                return "complex interface element"
            elif mean_brightness > 200:
                return "light interface element"
            elif mean_brightness < 100:
                return "dark interface element"
            
        except Exception as e:
            print(f"Context analysis failed: {e}")
        
        return None
    
    def _save_debug_info(self, screenshot: Image.Image, click_x: int, click_y: int, 
                        region: Optional[SmartRegion], result: OCRResult):
        """Save debug information for analysis"""
        try:
            debug_dir = Path("debug_ocr")
            debug_dir.mkdir(exist_ok=True)
            
            timestamp = int(time.time())
            
            # Save region with annotations
            debug_image = screenshot.copy()
            draw = ImageDraw.Draw(debug_image)
            
            # Mark click point
            draw.ellipse([click_x-5, click_y-5, click_x+5, click_y+5], fill='red', outline='darkred')
            
            # Mark detected region
            if region:
                x1, y1, x2, y2 = region.get_bounds()
                draw.rectangle([x1, y1, x2, y2], outline='blue', width=2)
                draw.text((x1, y1-15), f"{region.element_type} ({region.confidence:.2f})", fill='blue')
            
            debug_image.save(debug_dir / f"debug_{timestamp}.png")
            
            # Save text result
            with open(debug_dir / f"debug_{timestamp}.txt", "w") as f:
                f.write(f"Click: ({click_x}, {click_y})\n")
                f.write(f"Region: {region.element_type if region else 'None'}\n")
                f.write(f"OCR Result: '{result.cleaned_text}'\n")
                f.write(f"Confidence: {result.confidence}\n")
                f.write(f"Engine: {result.engine}\n")
                f.write(f"Valid: {result.is_valid()}\n")
            
        except Exception as e:
            print(f"Debug save failed: {e}")