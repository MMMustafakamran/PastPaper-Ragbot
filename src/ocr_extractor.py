"""
OCR Text Extractor using Tesseract OCR
Extracts text from scanned/image-based PDFs
"""

import logging
import os
from pathlib import Path
from typing import List, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image

try:
    import pytesseract
    import fitz  # PyMuPDF
    from PIL import Image
    import io
except ImportError as e:
    logging.warning(f"OCR dependencies not installed: {e}")
    pytesseract = None
    Image = None
    fitz = None

logger = logging.getLogger(__name__)


class TesseractOCR:
    """Extract text from PDFs using Tesseract OCR"""
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize Tesseract OCR
        
        Args:
            tesseract_cmd: Path to tesseract executable (if not in PATH)
                          On Windows, usually: 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
        """
        if pytesseract is None:
            raise ImportError(
                "pytesseract not installed. "
                "Install with: pip install pytesseract"
            )
        
        # Set tesseract command path if provided
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        else:
            # Try to find tesseract in common Windows locations
            if os.name == 'nt':  # Windows
                common_paths = [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        logger.info(f"Found Tesseract at: {path}")
                        break
        
        # Test Tesseract installation
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract OCR initialized successfully (version: {version})")
        except Exception as e:
            logger.error(f"Tesseract not found or not working: {e}")
            logger.error("Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")
            raise
    
    def _convert_pdf_to_images(self, pdf_path: Path) -> List:
        """
        Convert PDF pages to PIL Images using PyMuPDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of PIL Image objects (one per page)
        """
        try:
            if fitz is None:
                raise ImportError("PyMuPDF (fitz) not installed")
            
            logger.info(f"Converting PDF to images: {pdf_path.name}")
            
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(str(pdf_path))
            images = []
            
            # Convert each page to image
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Render page to image (300 DPI for better OCR)
                mat = fitz.Matrix(300/72, 300/72)  # 300 DPI scaling
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)
                
                logger.debug(f"  Converted page {page_num + 1}/{len(pdf_document)}")
            
            pdf_document.close()
            logger.info(f"Converted {len(images)} pages to images")
            return images
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {e}")
            raise
    
    def _image_to_bytes(self, image) -> bytes:
        """
        Convert PIL Image to bytes
        
        Args:
            image: PIL Image object
            
        Returns:
            Image bytes
        """
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    
    def _extract_text_from_image(self, image: Image.Image) -> str:
        """
        Extract text from image using Tesseract OCR
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text
        """
        try:
            if pytesseract is None:
                raise ImportError("pytesseract not installed")
            
            # Use Tesseract to extract text
            # PSM 6: Assume a single uniform block of text
            # PSM 11: Sparse text (for documents with multiple columns)
            text = pytesseract.image_to_string(
                image,
                lang='eng',  # English language
                config='--psm 6'  # Page segmentation mode
            )
            
            return text.strip()
        except Exception as e:
            logger.error(f"Failed to extract text from image: {e}")
            raise
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Tuple[str, bool]:
        """
        Extract text from PDF using OCR
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, success)
        """
        try:
            # Convert PDF to images
            images = self._convert_pdf_to_images(pdf_path)
            
            if not images:
                logger.warning(f"No images extracted from {pdf_path.name}")
                return "", False
            
            # Extract text from each page
            text_content = []
            total_pages = len(images)
            
            logger.info(f"Processing {total_pages} pages with OCR...")
            
            for page_num, image in enumerate(images, 1):
                logger.info(f"  OCR Page {page_num}/{total_pages}...")
                
                # Extract text directly from PIL Image
                page_text = self._extract_text_from_image(image)
                
                if page_text:
                    text_content.append(page_text)
                    logger.debug(f"    Extracted {len(page_text)} characters")
                else:
                    logger.warning(f"    No text found on page {page_num}")
            
            # Combine all pages
            full_text = "\n\n".join(text_content)
            
            if not full_text.strip():
                logger.warning(f"No text extracted from {pdf_path.name}")
                return "", False
            
            logger.info(f"Successfully extracted {len(full_text)} characters from {pdf_path.name}")
            return full_text, True
            
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path.name}: {e}")
            return "", False


def main():
    """Main function for testing"""
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python ocr_extractor.py <pdf_path> [tesseract_path]")
        return
    
    pdf_path = Path(sys.argv[1])
    tesseract_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        return
    
    try:
        ocr = TesseractOCR(tesseract_cmd=tesseract_path)
        text, success = ocr.extract_text_from_pdf(pdf_path)
        
        if success:
            print(f"\n[SUCCESS] Successfully extracted {len(text)} characters")
            print(f"\nFirst 500 characters:")
            print(text[:500])
        else:
            print("\n[FAILED] Failed to extract text")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")


if __name__ == "__main__":
    main()

