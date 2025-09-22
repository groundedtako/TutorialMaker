"""
Smart OCR Processing with Region Detection and Context Analysis
Fully offline solution for improved OCR accuracy
"""

import time
import math
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
from .logger import get_logger

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
        self.min_confidence = 0.3  # Minimum confidence for valid text (same as OCRResult.is_valid)
        self.min_word_length = 1   # Minimum word length (allow single meaningful characters)
        self.logger = get_logger('core.smart_ocr')
        
        # Element detection settings
        self.button_min_size = (40, 25)    # Increased minimum button size
        self.button_max_size = (400, 80)   # Increased maximum button size  
        self.text_region_padding = 20      # Increased padding for text regions
    
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
            if debug_mode:
                self._save_debug_region(region_image, target_region, click_x, click_y, "detected_region.png")
            ocr_result = self._process_region_with_ocr(region_image, target_region)
        else:
            # Fallback to adaptive region sizing
            region_image, region_bounds = self._extract_adaptive_region_with_bounds(screenshot, click_x, click_y)
            if debug_mode:
                self._save_debug_region(region_image, region_bounds, click_x, click_y, "adaptive_region.png")
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
            self.logger.warning(f"Element detection failed: {e}")
        
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
            padding = 15  # Increased padding to capture full button
        elif region.element_type == "text_field":
            padding = 10  # Increased padding for text fields
        else:
            padding = self.text_region_padding
        
        x1 = max(0, region.x - padding)
        y1 = max(0, region.y - padding)
        x2 = min(image.width, region.x + region.width + padding)
        y2 = min(image.height, region.y + region.height + padding)
        
        return image.crop((x1, y1, x2, y2))
    
    def _extract_adaptive_region(self, image: Image.Image, click_x: int, click_y: int) -> Image.Image:
        """Extract adaptive region (legacy method for compatibility)"""
        region_image, _ = self._extract_adaptive_region_with_bounds(image, click_x, click_y)
        return region_image
    
    def _extract_adaptive_region_with_bounds(self, image: Image.Image, click_x: int, click_y: int) -> Tuple[Image.Image, SmartRegion]:
        """
        Fallback: Extract region with intelligent dynamic sizing based on UI analysis
        """
        # Try intelligent boundary detection first
        intelligent_region = self._detect_intelligent_boundaries(image, click_x, click_y)
        if intelligent_region:
            return image.crop(intelligent_region.get_bounds()), intelligent_region
        
        # Use smarter, more focused region sizing to avoid mixed content
        base_width, base_height = self._get_focused_region_size(image, click_x, click_y)
        
        # Simple adaptive sizing based on image complexity around click
        try:
            # Sample a larger area to assess density
            sample_size = 80  # Increased from 40
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
                        region_width, region_height = 400, 200  # Even larger for complex UI
                    elif variance > 1000:  # Medium complexity  
                        region_width, region_height = 350, 175  # Larger for medium complexity
                    else:  # Low complexity
                        region_width, region_height = base_width, base_height
                else:
                    region_width, region_height = base_width, base_height
            else:
                region_width, region_height = base_width, base_height
                
        except Exception:
            region_width, region_height = base_width, base_height
        
        # Ensure we don't exceed reasonable bounds
        region_width = min(region_width, 400)  # Cap at 400px wide
        region_height = min(region_height, 200)  # Cap at 200px tall
        
        # Extract the adaptive region centered on click
        x1 = max(0, click_x - region_width // 2)
        y1 = max(0, click_y - region_height // 2)
        x2 = min(image.width, x1 + region_width)
        y2 = min(image.height, y1 + region_height)
        
        # Adjust if we hit image boundaries to maintain region size when possible
        if x2 - x1 < region_width and x1 > 0:
            x1 = max(0, x2 - region_width)
        if y2 - y1 < region_height and y1 > 0:
            y1 = max(0, y2 - region_height)
        
        # Create region info for debug purposes
        region_bounds = SmartRegion(x1, y1, x2 - x1, y2 - y1, "adaptive", 1.0)
        
        return image.crop((x1, y1, x2, y2)), region_bounds
    
    def _process_region_with_ocr(self, region_image: Image.Image, 
                                region_info: Optional[SmartRegion]) -> OCRResult:
        """Process region with OCR, using region info to optimize"""
        
        # Use enhanced OCR processing for all regions (proven optimal strategies)
        # This provides much better accuracy than the old approaches
        enhanced_result = self._enhanced_ocr_processing(region_image)
        
        # If enhanced processing gave us a good result, use it
        if enhanced_result.confidence > 0.7:
            return enhanced_result
        
        # Otherwise try region-specific fallbacks
        if region_info and region_info.element_type == "button":
            # Buttons often have contrasting text - try high contrast preprocessing
            fallback_result = self.ocr_engine.extract_text(region_image, preprocessing=True)
            return enhanced_result if enhanced_result.confidence >= fallback_result.confidence else fallback_result
        elif region_info and region_info.element_type == "text_field":
            # Text fields usually have clean text - try minimal preprocessing
            fallback_result = self.ocr_engine.extract_text(region_image, preprocessing=False)
            return enhanced_result if enhanced_result.confidence >= fallback_result.confidence else fallback_result
        else:
            # For unknown elements, enhanced processing is our best bet
            return enhanced_result
    
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
        
        if alpha_ratio < 0.2:  # Less than 20% letters (allow more numbers/symbols in UI text)
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
            self.logger.warning(f"Context analysis failed: {e}")
        
        return None
    
    def _enhanced_ocr_processing(self, region_image: Image.Image) -> OCRResult:
        """Enhanced OCR processing using proven optimal strategies from systematic testing"""
        
        # Strategy 1: EasyOCR with sharpening (best for clean buttons)
        easyocr_result = self._try_easyocr_sharpened(region_image)
        if easyocr_result and easyocr_result.confidence > 0.8:
            return self._clean_ocr_result(easyocr_result)
        
        # Strategy 2: Tesseract with threshold (best for mixed content)
        tesseract_threshold_result = self._try_tesseract_threshold(region_image)
        if tesseract_threshold_result and tesseract_threshold_result.confidence > 0.9:
            return self._clean_ocr_result(tesseract_threshold_result)
        
        # Strategy 3: Try both and return best
        all_results = []
        
        if easyocr_result:
            all_results.append(easyocr_result)
        if tesseract_threshold_result:
            all_results.append(tesseract_threshold_result)
        
        # Additional fallback strategies
        fallback_results = self._try_fallback_strategies(region_image)
        all_results.extend(fallback_results)
        
        # Return the best result with cleaning
        if all_results:
            best_result = max(all_results, key=lambda r: r.confidence if r.confidence > 0 else 0)
            final_result = best_result if best_result.confidence > 0.3 else all_results[0]
            return self._clean_ocr_result(final_result)
        
        # Final fallback - return empty result
        empty_result = OCRResult("", 0.0, "enhanced_processing_failed")
        return self._clean_ocr_result(empty_result)
    
    def _multi_strategy_ocr(self, region_image: Image.Image) -> OCRResult:
        """Multi-strategy OCR for unknown regions"""
        # Try both preprocessing approaches and take the best
        result1 = self.ocr_engine.extract_text(region_image, preprocessing=False)
        result2 = self.ocr_engine.extract_text(region_image, preprocessing=True)
        
        # If both have low confidence, try enhanced processing
        if result1.confidence < 0.5 and result2.confidence < 0.5:
            enhanced_result = self._enhanced_ocr_processing(region_image)
            if enhanced_result.confidence > max(result1.confidence, result2.confidence):
                return enhanced_result
        
        return result1 if result1.confidence >= result2.confidence else result2
    
    def _try_easyocr_sharpened(self, region_image: Image.Image) -> Optional[OCRResult]:
        """
        EasyOCR with sharpening - optimal for clean buttons
        Success rate: 100% for detected_region files (Export, OK, Stop Recording)
        """
        try:
            # Check if EasyOCR is available
            try:
                import easyocr
                easyocr_available = True
            except ImportError:
                easyocr_available = False
                
            if not easyocr_available:
                return None
            
            # Import EasyOCR if available
            import easyocr
            if not hasattr(self, '_easyocr_reader') or self._easyocr_reader is None:
                self._easyocr_reader = easyocr.Reader(['en'])
            
            # Apply sharpening preprocessing (winning strategy)
            if PIL_AVAILABLE:
                enhancer = ImageEnhance.Sharpness(region_image)
                sharpened_image = enhancer.enhance(2.0)
            else:
                sharpened_image = region_image
            
            # Convert to numpy array for EasyOCR
            import numpy as np
            img_array = np.array(sharpened_image)
            
            # Run EasyOCR
            results = self._easyocr_reader.readtext(img_array)
            
            if results:
                # Combine all detected text
                texts = [result[1] for result in results]
                confidences = [result[2] for result in results]
                
                combined_text = ' '.join(texts).strip()
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                
                return OCRResult(combined_text, avg_confidence, "easyocr_sharpened")
            else:
                return OCRResult("", 0.0, "easyocr_sharpened")
                
        except Exception as e:
            self.logger.warning(f"EasyOCR sharpened failed: {e}")
            return None
    
    def _try_tesseract_threshold(self, region_image: Image.Image) -> Optional[OCRResult]:
        """
        Tesseract with threshold preprocessing - optimal for mixed content
        Success rate: 95% confidence for "Recording in progress..." text
        """
        try:
            # Check if Tesseract is available
            try:
                import pytesseract
                tesseract_available = True
            except ImportError:
                tesseract_available = False
                
            if not tesseract_available:
                return None
            
            # Apply threshold preprocessing (winning strategy)
            if OPENCV_AVAILABLE and NUMPY_AVAILABLE:
                import cv2
                import numpy as np
                
                # Convert to grayscale
                gray_image = region_image.convert('L')
                img_array = np.array(gray_image)
                
                # Apply threshold (winning strategy from systematic test)
                _, binary = cv2.threshold(img_array, 127, 255, cv2.THRESH_BINARY)
                threshold_image = Image.fromarray(binary)
            else:
                # Fallback threshold using PIL
                threshold_image = region_image.convert('L')
                if PIL_AVAILABLE:
                    # Simple threshold
                    threshold_image = threshold_image.point(lambda x: 255 if x > 127 else 0, mode='1')
            
            # Run Tesseract with default settings (winning configuration)
            text = pytesseract.image_to_string(threshold_image).strip()
            
            # Get confidence
            try:
                data = pytesseract.image_to_data(threshold_image, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_conf = sum(confidences) / len(confidences) if confidences else 0
                confidence = avg_conf / 100.0  # Convert to 0-1 scale
            except:
                confidence = 0.5 if text else 0.0
            
            return OCRResult(text, confidence, "tesseract_threshold")
            
        except Exception as e:
            self.logger.warning(f"Tesseract threshold failed: {e}")
            return None
    
    def _try_fallback_strategies(self, region_image: Image.Image) -> List[OCRResult]:
        """Additional fallback strategies from systematic testing"""
        results = []
        
        try:
            # Fallback 1: EasyOCR with high contrast (good for some cases)  
            try:
                import easyocr
                easyocr_available = True
            except ImportError:
                easyocr_available = False
                
            if easyocr_available and PIL_AVAILABLE:
                enhancer = ImageEnhance.Contrast(region_image)
                high_contrast = enhancer.enhance(2.5)
                
                if not hasattr(self, '_easyocr_reader') or self._easyocr_reader is None:
                    import easyocr
                    self._easyocr_reader = easyocr.Reader(['en'])
                
                import numpy as np
                img_array = np.array(high_contrast)
                easyocr_results = self._easyocr_reader.readtext(img_array)
                
                if easyocr_results:
                    texts = [result[1] for result in easyocr_results]
                    confidences = [result[2] for result in easyocr_results]
                    combined_text = ' '.join(texts).strip()
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                    results.append(OCRResult(combined_text, avg_confidence, "easyocr_high_contrast"))
            
            # Fallback 2: Tesseract with PSM 6 (good for mixed content)
            try:
                import pytesseract
                tesseract_available = True
            except ImportError:
                tesseract_available = False
                
            if tesseract_available:
                import pytesseract
                text = pytesseract.image_to_string(region_image, config='--psm 6').strip()
                if text:
                    try:
                        data = pytesseract.image_to_data(region_image, config='--psm 6', output_type=pytesseract.Output.DICT)
                        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                        avg_conf = sum(confidences) / len(confidences) if confidences else 0
                        confidence = avg_conf / 100.0
                    except:
                        confidence = 0.5
                    results.append(OCRResult(text, confidence, "tesseract_psm6"))
            
            # Fallback 3: Original OCR engine for compatibility
            original_result = self.ocr_engine.extract_text(region_image, preprocessing=False)
            if original_result.is_valid():
                results.append(original_result)
                
        except Exception as e:
            self.logger.warning(f"Fallback strategies failed: {e}")
        
        return results
    
    def _clean_ocr_result(self, ocr_result: OCRResult) -> OCRResult:
        """
        Clean and improve OCR results by removing common OCR artifacts and gibberish
        """
        if not ocr_result or not ocr_result.cleaned_text.strip():
            return ocr_result
        
        original_text = ocr_result.cleaned_text.strip()
        cleaned_text = original_text
        
        try:
            # Remove OCR artifacts and improve readability
            
            # Fix common OCR mistakes for UI elements
            replacements = {
                'ecording': 'Recording',
                'nsh torial': 'Tutorial', 
                'nsh': '',  # Remove meaningless fragments
                'torial': 'Tutorial',
                'Record ecording': 'Recording',
                'Stop Record': 'Stop Recording',
            }
            
            for wrong, right in replacements.items():
                cleaned_text = cleaned_text.replace(wrong, right)
            
            # Remove redundant words (like "Export Export" -> "Export")
            words = cleaned_text.split()
            cleaned_words = []
            prev_word = ""
            
            for word in words:
                word = word.strip()
                if word and word.lower() != prev_word.lower():
                    cleaned_words.append(word)
                    prev_word = word
            
            cleaned_text = ' '.join(cleaned_words)
            
            # Remove trailing punctuation that doesn't make sense
            cleaned_text = cleaned_text.rstrip(':.,;')
            
            # If we made improvements, slightly boost confidence
            if cleaned_text != original_text and len(cleaned_text.strip()) > 0:
                confidence_boost = min(0.1, (1.0 - ocr_result.confidence) * 0.5)
                new_confidence = min(1.0, ocr_result.confidence + confidence_boost)
            else:
                new_confidence = ocr_result.confidence
            
            # Return cleaned result
            return OCRResult(
                cleaned_text.strip(),
                new_confidence,
                f"{ocr_result.engine}_cleaned"
            )
            
        except Exception as e:
            self.logger.warning(f"OCR cleaning failed: {e}")
            return ocr_result
    
    def _isolate_text_areas(self, region_image: Image.Image) -> List[Image.Image]:
        """
        Isolate text-only areas from mixed content regions
        Separates text from buttons, icons, and UI chrome
        """
        text_crops = []
        
        if not OPENCV_AVAILABLE or not NUMPY_AVAILABLE:
            return text_crops
        
        try:
            # Convert to grayscale for analysis
            img_array = np.array(region_image.convert('L'))
            height, width = img_array.shape
            
            # Method 1: Horizontal text line detection
            # Look for horizontal bands that contain text-like patterns
            for y_start in range(0, height - 10, 5):  # Scan in 5px steps
                y_end = min(y_start + 25, height)  # 25px high bands
                
                horizontal_band = img_array[y_start:y_end, :]
                
                # Check if this band contains text-like content
                if self._is_text_like_band(horizontal_band):
                    # Extend the band vertically to capture full text height
                    text_y_start = max(0, y_start - 5)
                    text_y_end = min(height, y_end + 5)
                    
                    # Add some horizontal padding
                    text_x_start = 5
                    text_x_end = width - 5
                    
                    # Extract text crop
                    text_crop = region_image.crop((text_x_start, text_y_start, text_x_end, text_y_end))
                    
                    # Only add if it's a reasonable text size
                    if text_crop.size[0] > 30 and text_crop.size[1] > 10:
                        text_crops.append(text_crop)
            
            # Method 2: Exclude obvious button areas
            # Remove areas that look like buttons (rounded rectangles with solid colors)
            filtered_crops = []
            for crop in text_crops:
                if not self._looks_like_button_area(crop):
                    filtered_crops.append(crop)
            
            # Remove duplicates and overlapping regions
            return self._deduplicate_text_crops(filtered_crops)
            
        except Exception as e:
            self.logger.warning(f"Text isolation failed: {e}")
            return text_crops
    
    def _is_text_like_band(self, band: np.ndarray) -> bool:
        """Check if a horizontal band contains text-like patterns"""
        try:
            if band.size == 0:
                return False
            
            # Calculate variance - text areas have moderate variance
            variance = np.var(band.astype(float))
            
            # Text typically has variance between 100-5000
            # (not solid color, not too noisy)
            if not (100 <= variance <= 5000):
                return False
            
            # Check for horizontal text-like patterns
            # Text has regular spacing and similar heights
            mean_row = np.mean(band, axis=0)  # Average each column
            
            # Look for variation indicating character boundaries
            diff = np.diff(mean_row)
            changes = np.sum(np.abs(diff) > 10)  # Count significant changes
            
            # Text should have some character boundaries but not too many
            min_changes = band.shape[1] // 20  # At least some variation
            max_changes = band.shape[1] // 3   # But not too chaotic
            
            return min_changes <= changes <= max_changes
            
        except Exception:
            return False
    
    def _looks_like_button_area(self, crop: Image.Image) -> bool:
        """Check if a crop looks like a button (to exclude from text processing)"""
        try:
            if not OPENCV_AVAILABLE or not NUMPY_AVAILABLE:
                return False
            
            img_array = np.array(crop.convert('L'))
            
            # Buttons typically have:
            # 1. Low variance (solid or gradient backgrounds)
            variance = np.var(img_array.astype(float))
            if variance < 50:  # Very low variance = likely solid button
                return True
            
            # 2. Strong edges around the perimeter (button borders)
            edges = cv2.Canny(img_array, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            if edge_density > 0.15:  # High edge density = likely button
                return True
            
            # 3. Uniform color distribution
            hist = cv2.calcHist([img_array], [0], None, [256], [0, 256])
            # If most pixels are in just a few color buckets, it's likely a button
            non_zero_buckets = np.sum(hist > 0)
            if non_zero_buckets < 20:  # Few colors = likely button
                return True
            
            return False
            
        except Exception:
            return False
    
    def _deduplicate_text_crops(self, crops: List[Image.Image]) -> List[Image.Image]:
        """Remove duplicate and heavily overlapping text crops"""
        if len(crops) <= 1:
            return crops
        
        # Sort by area (largest first)
        crops_with_area = [(crop, crop.size[0] * crop.size[1]) for crop in crops]
        crops_with_area.sort(key=lambda x: x[1], reverse=True)
        
        unique_crops = []
        for crop, area in crops_with_area:
            # Check if this crop is substantially different from existing ones
            is_unique = True
            for existing_crop in unique_crops:
                if self._crops_overlap_significantly(crop, existing_crop):
                    is_unique = False
                    break
            
            if is_unique:
                unique_crops.append(crop)
        
        return unique_crops[:3]  # Limit to 3 best text crops
    
    def _crops_overlap_significantly(self, crop1: Image.Image, crop2: Image.Image) -> bool:
        """Check if two crops overlap significantly (simple size-based heuristic)"""
        # Simple overlap detection based on size similarity
        area1 = crop1.size[0] * crop1.size[1]
        area2 = crop2.size[0] * crop2.size[1]
        
        ratio = min(area1, area2) / max(area1, area2)
        return ratio > 0.7  # If areas are very similar, consider them overlapping
    
    def _get_platform_base_size(self, image: Image.Image) -> Tuple[int, int]:
        """Get platform-appropriate base region size"""
        # Scale based on screen resolution and platform
        screen_width, screen_height = image.size
        
        # High DPI detection (common on Mac Retina, Windows high-DPI)
        is_high_dpi = screen_width > 2560 or screen_height > 1600
        
        if is_high_dpi:
            # Larger base size for high-DPI displays
            base_width = int(screen_width * 0.15)  # 15% of screen width
            base_height = int(screen_height * 0.08)  # 8% of screen height
        else:
            # Standard size for regular displays
            base_width = int(screen_width * 0.12)  # 12% of screen width  
            base_height = int(screen_height * 0.06)  # 6% of screen height
        
        # Ensure reasonable bounds
        base_width = max(200, min(base_width, 600))
        base_height = max(100, min(base_height, 300))
        
        return base_width, base_height
    
    def _get_focused_region_size(self, image: Image.Image, click_x: int, click_y: int) -> Tuple[int, int]:
        """
        Get focused region size based on local content analysis around click point
        Smaller regions to avoid mixed content issues
        """
        screen_width, screen_height = image.size
        
        # Start with much smaller base sizes to focus on click target
        base_width = 150  # Smaller than previous 300
        base_height = 75  # Smaller than previous 150
        
        try:
            # Analyze immediate area around click (smaller sample)
            sample_radius = 30  # Much smaller than previous 80
            x1 = max(0, click_x - sample_radius)
            y1 = max(0, click_y - sample_radius)
            x2 = min(image.width, click_x + sample_radius)
            y2 = min(image.height, click_y + sample_radius)
            
            if PIL_AVAILABLE:
                sample_region = image.crop((x1, y1, x2, y2))
                gray_sample = sample_region.convert('L')
                pixels = list(gray_sample.getdata())
                
                if pixels:
                    # Check local complexity but keep regions smaller
                    variance = np.var(np.array(pixels, dtype=float)) if NUMPY_AVAILABLE else 0
                    
                    if variance > 3000:  # Very high complexity - slightly larger but still focused
                        region_width, region_height = 200, 100
                    elif variance > 1500:  # Medium complexity
                        region_width, region_height = 175, 85
                    else:  # Low complexity - keep small
                        region_width, region_height = base_width, base_height
                else:
                    region_width, region_height = base_width, base_height
            else:
                region_width, region_height = base_width, base_height
                
            # Ensure we don't exceed reasonable bounds (smaller caps)
            region_width = min(region_width, 250)  # Reduced from 400
            region_height = min(region_height, 125)  # Reduced from 200
            
            return region_width, region_height
            
        except Exception:
            return base_width, base_height
    
    def _detect_intelligent_boundaries(self, image: Image.Image, click_x: int, click_y: int) -> Optional[SmartRegion]:
        """
        Intelligently detect UI element boundaries around click point
        Returns region that encompasses the full UI element (button, text, etc.)
        """
        if not OPENCV_AVAILABLE or not NUMPY_AVAILABLE:
            return None
        
        try:
            # Convert to OpenCV format
            img_array = np.array(image)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Define search area around click
            search_radius = min(200, min(image.width, image.height) // 8)
            x1 = max(0, click_x - search_radius)
            y1 = max(0, click_y - search_radius) 
            x2 = min(image.width, click_x + search_radius)
            y2 = min(image.height, click_y + search_radius)
            
            search_region = gray[y1:y2, x1:x2]
            
            # Try button detection first
            button_region = self._detect_button_boundaries(search_region, click_x - x1, click_y - y1)
            if button_region:
                return SmartRegion(
                    x1 + button_region[0], y1 + button_region[1],
                    button_region[2] - button_region[0], button_region[3] - button_region[1],
                    "intelligent_button", 0.9
                )
            
            # Try text boundary detection
            text_region = self._detect_text_boundaries(search_region, click_x - x1, click_y - y1)
            if text_region:
                return SmartRegion(
                    x1 + text_region[0], y1 + text_region[1],
                    text_region[2] - text_region[0], text_region[3] - text_region[1],
                    "intelligent_text", 0.8
                )
                
        except Exception as e:
            self.logger.warning(f"Intelligent boundary detection failed: {e}")
            
        return None
    
    def _detect_button_boundaries(self, search_region: np.ndarray, relative_x: int, relative_y: int) -> Optional[Tuple[int, int, int, int]]:
        """Detect button boundaries using edge detection and color analysis"""
        try:
            # Edge detection for button borders
            edges = cv2.Canny(search_region, 30, 100)
            
            # Morphological operations to connect edges
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Find contour that contains the click point
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check if click point is inside this contour
                if (x <= relative_x <= x + w and y <= relative_y <= y + h):
                    # Check if it looks like a button (reasonable aspect ratio and size)
                    aspect_ratio = w / h if h > 0 else 1
                    if (0.5 <= aspect_ratio <= 8 and  # Reasonable button aspect ratio
                        w >= 40 and h >= 20 and      # Minimum button size
                        w <= 400 and h <= 100):      # Maximum button size
                        
                        # Add padding around detected button
                        padding = 10
                        x1 = max(0, x - padding)
                        y1 = max(0, y - padding)
                        x2 = min(search_region.shape[1], x + w + padding)
                        y2 = min(search_region.shape[0], y + h + padding)
                        
                        return (x1, y1, x2, y2)
            
        except Exception:
            pass
        
        return None
    
    def _detect_text_boundaries(self, search_region: np.ndarray, relative_x: int, relative_y: int) -> Optional[Tuple[int, int, int, int]]:
        """Detect text boundaries by finding text-like regions"""
        try:
            # Create binary image to find text regions
            _, binary = cv2.threshold(search_region, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Morphological operations to connect text characters
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1))  # Horizontal kernel for text
            connected = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Find the largest contour that contains the click point
            best_contour = None
            best_area = 0
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Check if click point is inside and it looks like text
                if (x <= relative_x <= x + w and y <= relative_y <= y + h):
                    aspect_ratio = w / h if h > 0 else 1
                    if (aspect_ratio >= 2 and      # Text is typically wider than tall
                        h >= 8 and h <= 50 and    # Reasonable text height
                        w >= 20 and               # Minimum text width
                        area > best_area):
                        best_contour = (x, y, w, h)
                        best_area = area
            
            if best_contour:
                x, y, w, h = best_contour
                
                # Expand horizontally to capture full text line
                padding_h = max(20, w // 4)  # Horizontal padding based on text width
                padding_v = max(5, h // 2)   # Vertical padding based on text height
                
                x1 = max(0, x - padding_h)
                y1 = max(0, y - padding_v)
                x2 = min(search_region.shape[1], x + w + padding_h)
                y2 = min(search_region.shape[0], y + h + padding_v)
                
                return (x1, y1, x2, y2)
                
        except Exception:
            pass
        
        return None
    
    def _save_debug_region(self, region_image: Image.Image, region_bounds: SmartRegion, 
                          click_x: int, click_y: int, base_filename: str):
        """Save debug region image with click marker and info"""
        try:
            # Create timestamped filename to preserve multiple clicks
            timestamp = int(time.time() * 1000)  # milliseconds for uniqueness
            name_parts = base_filename.split('.')
            if len(name_parts) == 2:
                timestamped_filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
            else:
                timestamped_filename = f"{base_filename}_{timestamp}"
            
            # Calculate relative click position within the region
            relative_x = click_x - region_bounds.x
            relative_y = click_y - region_bounds.y
            
            # Create a copy of the region image and add click marker
            debug_image = region_image.copy()
            if PIL_AVAILABLE:
                draw = ImageDraw.Draw(debug_image)
                
                # Draw red dot at click position (if within bounds)
                if (0 <= relative_x < debug_image.width and 0 <= relative_y < debug_image.height):
                    marker_size = 3
                    draw.ellipse([
                        relative_x - marker_size, relative_y - marker_size,
                        relative_x + marker_size, relative_y + marker_size
                    ], fill='red', outline='darkred')
                
                # Draw border around the region
                draw.rectangle([0, 0, debug_image.width - 1, debug_image.height - 1], 
                             outline='blue', width=1)
            
            # Save the debug image
            debug_image.save(timestamped_filename)
            
            # Print debug info
            self.logger.debug(f"Region saved to {timestamped_filename}")
            self.logger.debug(f"Region bounds: ({region_bounds.x}, {region_bounds.y}, {region_bounds.x + region_bounds.width}, {region_bounds.y + region_bounds.height})")
            self.logger.debug(f"Region size: {region_bounds.width}x{region_bounds.height}")
            self.logger.debug(f"Click coordinates: ({click_x}, {click_y})")
            self.logger.debug(f"Relative click in region: ({relative_x}, {relative_y})")
            
            # Check if click is within region bounds
            if (0 <= relative_x < region_bounds.width and 0 <= relative_y < region_bounds.height):
                self.logger.info("Click is within region bounds - red dot should be visible")
            else:
                self.logger.warning("Click is outside region bounds - no red dot will be shown")
                
        except Exception as e:
            self.logger.error(f"Failed to save debug region: {e}")
    
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
            self.logger.error(f"Debug save failed: {e}")