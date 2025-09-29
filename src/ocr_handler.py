"""
OCR Handler Module
Performs Optical Character Recognition on scanned PDFs and images
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from PIL import Image as PILImage
else:
    PILImage = Any

try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    Image = None

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

logger = logging.getLogger(__name__)


class OCRHandler:
    """Handle OCR operations for scanned PDFs and images"""
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize OCR handler
        
        Args:
            tesseract_cmd: Path to tesseract executable (optional)
                          Windows: r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
                          Linux/Mac: Usually in PATH
        """
        self.pytesseract_available = PYTESSERACT_AVAILABLE
        self.pdf2image_available = PDF2IMAGE_AVAILABLE
        
        if not self.pytesseract_available:
            logger.warning("pytesseract not available. Install with: pip install pytesseract")
            logger.warning("Also install Tesseract-OCR: https://github.com/tesseract-ocr/tesseract")
        
        if not self.pdf2image_available:
            logger.warning("pdf2image not available. Install with: pip install pdf2image")
        
        # Set tesseract command path if provided
        if tesseract_cmd and PYTESSERACT_AVAILABLE:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Check if all OCR dependencies are available"""
        return {
            'pytesseract': self.pytesseract_available,
            'pdf2image': self.pdf2image_available,
            'ready': self.pytesseract_available and self.pdf2image_available
        }
    
    def pdf_to_images(self, pdf_path: str, dpi: int = 300) -> List[Any]:
        """
        Convert PDF pages to images
        
        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for conversion (higher = better quality, slower)
            
        Returns:
            List of PIL Image objects, one per page
        """
        if not self.pdf2image_available:
            raise ImportError("pdf2image not installed. Run: pip install pdf2image")
        
        try:
            logger.info(f"Converting PDF to images (DPI: {dpi})...")
            images = convert_from_path(pdf_path, dpi=dpi)
            logger.info(f"Converted {len(images)} pages to images")
            return images
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {e}")
            return []
    
    def preprocess_image(self, image: Any) -> Any:
        """
        Preprocess image for better OCR results
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        # Convert to grayscale
        image = image.convert('L')
        
        # Optional: Apply threshold for better text detection
        # This can be enhanced based on paper quality
        # from PIL import ImageEnhance
        # enhancer = ImageEnhance.Contrast(image)
        # image = enhancer.enhance(2.0)
        
        return image
    
    def ocr_image(self, image: Any, lang: str = 'eng') -> str:
        """
        Perform OCR on a single image
        
        Args:
            image: PIL Image object
            lang: Language for OCR (eng, ara, urd, etc.)
            
        Returns:
            Extracted text
        """
        if not self.pytesseract_available:
            raise ImportError("pytesseract not installed. Run: pip install pytesseract")
        
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Perform OCR with custom config for better results
            custom_config = r'--oem 3 --psm 6'  # OEM 3: Default, PSM 6: Assume uniform block of text
            text = pytesseract.image_to_string(processed_image, lang=lang, config=custom_config)
            
            return text
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""
    
    def ocr_pdf(self, pdf_path: str, lang: str = 'eng', dpi: int = 300) -> str:
        """
        Perform OCR on entire PDF
        
        Args:
            pdf_path: Path to PDF file
            lang: Language for OCR
            dpi: Resolution for conversion
            
        Returns:
            Extracted text from all pages
        """
        pdf_path = str(Path(pdf_path).resolve())
        
        if not Path(pdf_path).exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return ""
        
        logger.info(f"Starting OCR on: {Path(pdf_path).name}")
        
        # Convert PDF to images
        images = self.pdf_to_images(pdf_path, dpi=dpi)
        
        if not images:
            logger.error("No images generated from PDF")
            return ""
        
        # Perform OCR on each page
        all_text = []
        for page_num, image in enumerate(images, 1):
            logger.info(f"OCR processing page {page_num}/{len(images)}...")
            
            text = self.ocr_image(image, lang=lang)
            
            if text.strip():
                all_text.append(f"\n--- Page {page_num} ---\n")
                all_text.append(text)
            
            logger.info(f"Page {page_num}: Extracted {len(text)} characters")
        
        full_text = "\n".join(all_text)
        logger.info(f"OCR complete: {len(full_text)} total characters extracted")
        
        return full_text
    
    def post_process_ocr_text(self, text: str) -> str:
        """
        Clean up common OCR errors
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned text
        """
        # Fix common OCR mistakes
        replacements = {
            # Number/letter confusion
            r'\b0\b': 'O',  # Zero to letter O in words
            r'\b1\b(?=[a-zA-Z])': 'I',  # 1 to I before letters
            r'\bS\b(?=\d)': '5',  # S to 5 before numbers
            
            # Common OCR artifacts
            r'\|': 'l',  # Pipe to lowercase L
            r'¢': 'c',
            r'©': 'c',
            
            # Multiple spaces
            r' {2,}': ' ',
            
            # Fix line breaks in middle of words
            r'(\w+)-\n(\w+)': r'\1\2',
        }
        
        cleaned = text
        for pattern, replacement in replacements.items():
            cleaned = re.sub(pattern, replacement, cleaned)
        
        return cleaned
    
    def ocr_with_confidence(self, image: Any, lang: str = 'eng') -> Dict[str, Any]:
        """
        Perform OCR and return text with confidence scores
        
        Args:
            image: PIL Image object
            lang: Language for OCR
            
        Returns:
            Dictionary with text and confidence information
        """
        if not self.pytesseract_available:
            raise ImportError("pytesseract not installed")
        
        try:
            processed_image = self.preprocess_image(image)
            
            # Get detailed OCR data
            data = pytesseract.image_to_data(processed_image, lang=lang, output_type=pytesseract.Output.DICT)
            
            # Extract text and confidence
            text_parts = []
            confidences = []
            
            for i, word in enumerate(data['text']):
                if word.strip():
                    text_parts.append(word)
                    conf = int(data['conf'][i])
                    if conf > 0:  # -1 means no confidence
                        confidences.append(conf)
            
            text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'text': text,
                'avg_confidence': avg_confidence,
                'word_count': len(text_parts),
                'low_confidence_words': sum(1 for c in confidences if c < 60)
            }
        except Exception as e:
            logger.error(f"OCR with confidence failed: {e}")
            return {
                'text': '',
                'avg_confidence': 0,
                'word_count': 0,
                'low_confidence_words': 0
            }
    
    def save_ocr_debug_images(self, pdf_path: str, output_dir: str):
        """
        Save preprocessed images for debugging OCR issues
        
        Args:
            pdf_path: Path to PDF
            output_dir: Directory to save images
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        images = self.pdf_to_images(pdf_path)
        
        for i, image in enumerate(images, 1):
            processed = self.preprocess_image(image)
            output_file = output_path / f"page_{i:03d}_processed.png"
            processed.save(output_file)
            logger.info(f"Saved debug image: {output_file}")


def test_ocr():
    """Test OCR functionality"""
    import sys
    
    handler = OCRHandler()
    
    # Check dependencies
    deps = handler.check_dependencies()
    print("\n" + "="*50)
    print("OCR Dependencies Check")
    print("="*50)
    for dep, available in deps.items():
        status = "✅" if available else "❌"
        print(f"{status} {dep}: {available}")
    
    if not deps['ready']:
        print("\n⚠️  OCR not ready. Install missing dependencies:")
        if not deps['pytesseract']:
            print("   pip install pytesseract")
            print("   Download Tesseract: https://github.com/tesseract-ocr/tesseract")
        if not deps['pdf2image']:
            print("   pip install pdf2image")
        return
    
    if len(sys.argv) < 2:
        print("\n" + "="*50)
        print("Usage")
        print("="*50)
        print("python ocr_handler.py <path_to_scanned_pdf>")
        return
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"❌ File not found: {pdf_path}")
        return
    
    print("\n" + "="*50)
    print(f"Processing: {Path(pdf_path).name}")
    print("="*50)
    
    # Perform OCR
    text = handler.ocr_pdf(pdf_path)
    
    print(f"\n✅ Extracted {len(text)} characters")
    print(f"Lines: {len(text.split(chr(10)))}")
    
    # Show preview
    print("\n" + "="*50)
    print("Preview (first 500 characters)")
    print("="*50)
    print(text[:500])
    
    # Save option
    save = input("\nSave to file? (y/n): ")
    if save.lower() == 'y':
        output_path = Path(pdf_path).stem + "_ocr_extracted.txt"
        Path(output_path).write_text(text, encoding='utf-8')
        print(f"✅ Saved to: {output_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_ocr()
