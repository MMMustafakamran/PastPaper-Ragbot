"""
PDF Extractor Module
Extracts text from PDF files using pdfplumber, PyPDF2, and OCR
"""

import pdfplumber
from pathlib import Path
from typing import Optional, Dict, Any
import logging

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    from .ocr_handler import OCRHandler
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    OCRHandler = None

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text from PDF files"""
    
    def __init__(self, use_ocr: bool = True, tesseract_cmd: Optional[str] = None):
        """
        Initialize PDF extractor
        
        Args:
            use_ocr: Enable OCR for scanned PDFs
            tesseract_cmd: Path to tesseract executable (optional)
        """
        self.pdfplumber_available = True
        self.pypdf2_available = PYPDF2_AVAILABLE
        self.ocr_available = OCR_AVAILABLE and use_ocr
        
        # Initialize OCR handler if available
        if self.ocr_available:
            self.ocr_handler = OCRHandler(tesseract_cmd=tesseract_cmd)
            logger.info("OCR handler initialized")
        else:
            self.ocr_handler = None
            if use_ocr:
                logger.warning("OCR requested but not available")
    
    def is_text_selectable(self, pdf_path: str) -> bool:
        """
        Check if PDF has selectable text (not scanned)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if text is selectable, False if scanned/image-based
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    return False
                
                # Check first few pages
                pages_to_check = min(3, len(pdf.pages))
                text_found = False
                
                for i in range(pages_to_check):
                    text = pdf.pages[i].extract_text()
                    if text and len(text.strip()) > 100:  # At least 100 chars
                        text_found = True
                        break
                
                return text_found
        except Exception as e:
            logger.error(f"Error checking PDF selectability: {e}")
            return False
    
    def extract_text_pdfplumber(self, pdf_path: str) -> str:
        """
        Extract text using pdfplumber (primary method)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n{page_text}\n"
                    
                    logger.debug(f"Extracted page {page_num}/{len(pdf.pages)}")
            
            return text.strip()
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            return ""
    
    def extract_text_pypdf2(self, pdf_path: str) -> str:
        """
        Extract text using PyPDF2 (fallback method)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        if not self.pypdf2_available:
            logger.warning("PyPDF2 not available")
            return ""
        
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n{page_text}\n"
                    
                    logger.debug(f"Extracted page {page_num + 1}/{num_pages}")
            
            return text.strip()
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            return ""
    
    def extract_text_ocr(self, pdf_path: str, lang: str = 'eng', dpi: int = 300) -> str:
        """
        Extract text using OCR (for scanned PDFs)
        
        Args:
            pdf_path: Path to PDF file
            lang: Language for OCR (eng, ara, urd)
            dpi: Resolution for image conversion
            
        Returns:
            Extracted text
        """
        if not self.ocr_available:
            logger.error("OCR not available")
            return ""
        
        try:
            logger.info(f"Starting OCR extraction (this may take a while)...")
            text = self.ocr_handler.ocr_pdf(pdf_path, lang=lang, dpi=dpi)
            
            # Post-process OCR text
            if text:
                text = self.ocr_handler.post_process_ocr_text(text)
            
            return text
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""
    
    def extract_text(self, pdf_path: str, method: str = 'auto', force_ocr: bool = False) -> str:
        """
        Extract text from PDF using best available method
        
        Args:
            pdf_path: Path to PDF file
            method: 'auto', 'pdfplumber', 'pypdf2', or 'ocr'
            force_ocr: Force OCR even if text is selectable
            
        Returns:
            Extracted text
        """
        pdf_path = str(Path(pdf_path).resolve())
        
        if not Path(pdf_path).exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return ""
        
        logger.info(f"Extracting text from: {Path(pdf_path).name}")
        
        # Force OCR if requested
        if force_ocr or method == 'ocr':
            return self.extract_text_ocr(pdf_path)
        
        text = ""
        
        # Try standard methods first
        if method == 'pdfplumber' or method == 'auto':
            text = self.extract_text_pdfplumber(pdf_path)
            if text:
                logger.info(f"Successfully extracted {len(text)} characters using pdfplumber")
                return text
        
        if method == 'pypdf2' or (method == 'auto' and not text):
            if self.pypdf2_available:
                text = self.extract_text_pypdf2(pdf_path)
                if text:
                    logger.info(f"Successfully extracted {len(text)} characters using PyPDF2")
                    return text
        
        # If auto mode and no text extracted, try OCR as fallback
        if method == 'auto' and not text and self.ocr_available:
            logger.info("No selectable text found. Attempting OCR...")
            text = self.extract_text_ocr(pdf_path)
            if text:
                logger.info(f"Successfully extracted {len(text)} characters using OCR")
                return text
        
        if not text:
            logger.warning(f"No text extracted from {Path(pdf_path).name}")
        
        return text
    
    def extract_and_save(self, pdf_path: str, output_path: str, method: str = 'auto') -> bool:
        """
        Extract text from PDF and save to file
        
        Args:
            pdf_path: Path to input PDF file
            output_path: Path to output text file
            method: Extraction method
            
        Returns:
            True if successful, False otherwise
        """
        text = self.extract_text(pdf_path, method)
        
        if not text:
            logger.error(f"Failed to extract text from {pdf_path}")
            return False
        
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            logger.info(f"Text saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving text file: {e}")
            return False
    
    def get_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """
        Get information about PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with PDF information
        """
        info = {
            'path': str(pdf_path),
            'filename': Path(pdf_path).name,
            'exists': Path(pdf_path).exists(),
            'size_bytes': 0,
            'num_pages': 0,
            'is_selectable': False,
            'extraction_method': 'unknown',
            'ocr_available': self.ocr_available
        }
        
        if not info['exists']:
            return info
        
        info['size_bytes'] = Path(pdf_path).stat().st_size
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                info['num_pages'] = len(pdf.pages)
                info['is_selectable'] = self.is_text_selectable(pdf_path)
                
                if info['is_selectable']:
                    info['extraction_method'] = 'pdfplumber'
                elif self.ocr_available:
                    info['extraction_method'] = 'ocr'
                else:
                    info['extraction_method'] = 'ocr_required_but_unavailable'
        except Exception as e:
            logger.error(f"Error getting PDF info: {e}")
        
        return info


def test_extractor():
    """Test the PDF extractor"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py <path_to_pdf>")
        return
    
    pdf_path = sys.argv[1]
    extractor = PDFExtractor()
    
    # Get PDF info
    print("\n" + "="*50)
    print("PDF Information")
    print("="*50)
    info = extractor.get_pdf_info(pdf_path)
    for key, value in info.items():
        print(f"{key}: {value}")
    
    # Extract text
    print("\n" + "="*50)
    print("Extracting Text")
    print("="*50)
    text = extractor.extract_text(pdf_path)
    
    print(f"\nExtracted {len(text)} characters")
    print(f"Number of lines: {len(text.split(chr(10)))}")
    
    # Show preview
    print("\n" + "="*50)
    print("Preview (first 500 characters)")
    print("="*50)
    print(text[:500])
    
    # Save option
    save = input("\nSave to file? (y/n): ")
    if save.lower() == 'y':
        output_path = Path(pdf_path).stem + "_extracted.txt"
        if extractor.extract_and_save(pdf_path, output_path):
            print(f"Saved to: {output_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_extractor()
