"""
OCR (Optical Character Recognition) functionality
Local-only text extraction from images
"""

import re
import time
from typing import Optional, Dict, List, Tuple
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import cv2

# OCR engines
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Warning: pytesseract not available. Install with: pip install pytesseract")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("Warning: easyocr not available. Install with: pip install easyocr")

class OCRResult:
    """Container for OCR results"""
    
    def __init__(self, text: str = "", confidence: float = 0.0, 
                 engine: str = "unknown", processing_time: float = 0.0):
        self.text = text.strip()
        self.confidence = confidence
        self.engine = engine
        self.processing_time = processing_time
        self.cleaned_text = self._clean_text(self.text)
    
    def _clean_text(self, text: str) -> str:
        """Clean OCR text of common artifacts"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common OCR artifacts
        cleaned = re.sub(r'[^\w\s\-_.,!?()@#$%&*+=<>\/\\:;"\']', '', cleaned)
        
        # Fix common OCR mistakes
        replacements = {
            'l': 'I',  # lowercase l often misread as I
            '0': 'O',  # zero often misread as O in UI text
            '1': 'l',  # 1 often misread as l
        }
        
        # Apply replacements only if the result makes more sense
        # (This is a simple heuristic - could be improved)
        for old, new in replacements.items():
            if old in cleaned and len(cleaned) < 20:  # Only for short text (likely UI elements)
                test_replacement = cleaned.replace(old, new)
                if self._looks_like_ui_text(test_replacement):
                    cleaned = test_replacement
        
        return cleaned
    
    def _looks_like_ui_text(self, text: str) -> bool:
        """Simple heuristic to determine if text looks like UI text"""
        if not text:
            return False
        
        # Common UI words and patterns
        ui_patterns = [
            r'\b(save|open|close|cancel|ok|yes|no|submit|send|login|logout)\b',
            r'\b(file|edit|view|help|settings|preferences|options)\b',
            r'\b(new|create|delete|remove|add|insert|update)\b',
            r'\b(home|back|next|previous|continue|finish)\b',
        ]
        
        text_lower = text.lower()
        for pattern in ui_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def is_valid(self) -> bool:
        """Check if OCR result is likely valid"""
        return (len(self.cleaned_text) > 0 and 
                self.confidence > 0.3 and 
                len(self.cleaned_text) < 100)  # UI text is usually short

class OCREngine:
    """Local OCR processing engine"""
    
    def __init__(self):
        self.tesseract_available = TESSERACT_AVAILABLE
        self.easyocr_available = EASYOCR_AVAILABLE
        self.easyocr_reader = None
        self.ocr_cache = {}  # Cache results to avoid reprocessing
        
        # Initialize EasyOCR if available
        if self.easyocr_available:
            try:
                self.easyocr_reader = easyocr.Reader(['en'], gpu=False)
                print("EasyOCR initialized")
            except Exception as e:
                print(f"Failed to initialize EasyOCR: {e}")
                self.easyocr_available = False
        
        if not self.tesseract_available and not self.easyocr_available:
            print("Warning: No OCR engines available. Please install pytesseract or easyocr")
    
    def extract_text(self, image: Image.Image, preprocessing: bool = True) -> OCRResult:
        """
        Extract text from image using available OCR engines
        
        Args:
            image: PIL Image to process
            preprocessing: Whether to apply image preprocessing
            
        Returns:
            OCRResult with extracted text and metadata
        """
        if not image:
            return OCRResult()
        
        # Check cache first
        image_hash = self._hash_image(image)
        if image_hash in self.ocr_cache:
            return self.ocr_cache[image_hash]
        
        start_time = time.time()
        best_result = OCRResult()
        
        # Preprocess image if requested
        if preprocessing:
            processed_image = self._preprocess_image(image)
        else:
            processed_image = image
        
        # Try Tesseract first (usually faster)
        if self.tesseract_available:
            tesseract_result = self._extract_with_tesseract(processed_image)
            if tesseract_result.is_valid():
                best_result = tesseract_result
        
        # Try EasyOCR if Tesseract failed or we don't have it
        if (not best_result.is_valid() and self.easyocr_available):
            easyocr_result = self._extract_with_easyocr(processed_image)
            if easyocr_result.is_valid():
                if (not best_result.is_valid() or 
                    easyocr_result.confidence > best_result.confidence):
                    best_result = easyocr_result
        
        # If still no good result, try with different preprocessing
        if not best_result.is_valid() and preprocessing:
            # Try with different preprocessing approaches
            for preprocess_func in [self._preprocess_for_buttons, self._preprocess_high_contrast]:
                alt_processed = preprocess_func(image)
                if self.tesseract_available:
                    alt_result = self._extract_with_tesseract(alt_processed)
                    if alt_result.is_valid() and alt_result.confidence > best_result.confidence:
                        best_result = alt_result
                        break
        
        best_result.processing_time = time.time() - start_time
        
        # Cache the result
        if best_result.is_valid():
            self.ocr_cache[image_hash] = best_result
        
        return best_result
    
    def _extract_with_tesseract(self, image: Image.Image) -> OCRResult:
        """Extract text using Tesseract"""
        try:
            # Configure Tesseract for UI text
            config = '--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,!?()-_'
            
            # Extract text
            text = pytesseract.image_to_string(image, config=config)
            
            # Get confidence (if available)
            try:
                data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                confidence = avg_confidence / 100.0  # Convert to 0-1 scale
            except:
                confidence = 0.5  # Default confidence
            
            return OCRResult(text, confidence, "tesseract")
            
        except Exception as e:
            print(f"Tesseract OCR failed: {e}")
            return OCRResult()
    
    def _extract_with_easyocr(self, image: Image.Image) -> OCRResult:
        """Extract text using EasyOCR"""
        try:
            # Convert PIL to numpy array
            img_array = np.array(image)
            
            # Extract text
            results = self.easyocr_reader.readtext(img_array)
            
            if results:
                # Combine all detected text
                texts = []
                confidences = []
                
                for (bbox, text, conf) in results:
                    if conf > 0.3:  # Only include high-confidence results
                        texts.append(text)
                        confidences.append(conf)
                
                if texts:
                    combined_text = ' '.join(texts)
                    avg_confidence = sum(confidences) / len(confidences)
                    return OCRResult(combined_text, avg_confidence, "easyocr")
            
            return OCRResult()
            
        except Exception as e:
            print(f"EasyOCR failed: {e}")
            return OCRResult()
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Apply standard preprocessing to improve OCR accuracy"""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)
            
            # Resize if too small (OCR works better on larger images)
            width, height = image.size
            if width < 100 or height < 50:
                scale_factor = max(100 / width, 50 / height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            print(f"Image preprocessing failed: {e}")
            return image
    
    def _preprocess_for_buttons(self, image: Image.Image) -> Image.Image:
        """Preprocessing specifically for button text"""
        try:
            # Convert to numpy for OpenCV processing
            img_array = np.array(image.convert('L'))
            
            # Apply threshold to create binary image
            _, binary = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Morphological operations to clean up
            kernel = np.ones((2, 2), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # Convert back to PIL
            return Image.fromarray(binary)
            
        except Exception as e:
            print(f"Button preprocessing failed: {e}")
            return self._preprocess_image(image)
    
    def _preprocess_high_contrast(self, image: Image.Image) -> Image.Image:
        """High contrast preprocessing for difficult text"""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Extreme contrast enhancement
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(3.0)
            
            # Apply threshold
            img_array = np.array(image)
            _, binary = cv2.threshold(img_array, 127, 255, cv2.THRESH_BINARY)
            
            return Image.fromarray(binary)
            
        except Exception as e:
            print(f"High contrast preprocessing failed: {e}")
            return image
    
    def _hash_image(self, image: Image.Image) -> str:
        """Create a hash of the image for caching"""
        try:
            # Simple hash based on image data
            img_array = np.array(image.resize((32, 32), Image.Resampling.LANCZOS))
            return str(hash(img_array.tobytes()))
        except:
            return str(time.time())  # Fallback to timestamp
    
    def clear_cache(self):
        """Clear the OCR cache"""
        self.ocr_cache.clear()
    
    def get_stats(self) -> Dict:
        """Get OCR engine statistics"""
        return {
            'tesseract_available': self.tesseract_available,
            'easyocr_available': self.easyocr_available,
            'cache_size': len(self.ocr_cache),
            'engines_working': (self.tesseract_available or self.easyocr_available)
        }