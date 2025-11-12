"""
OCR Text Extractor using Google Cloud Vision API
Extracts text from scanned/image-based PDFs
"""

import logging
import os
from pathlib import Path
from typing import List, Tuple, Optional, TYPE_CHECKING
import json

if TYPE_CHECKING:
    from PIL import Image

try:
    from google.cloud import vision
    import fitz  # PyMuPDF
    from PIL import Image
    import io
except ImportError as e:
    logging.warning(f"OCR dependencies not installed: {e}")
    vision = None
    Image = None
    fitz = None

logger = logging.getLogger(__name__)


class GoogleVisionOCR:
    """Extract text from PDFs using Google Cloud Vision API"""
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Vision OCR client
        
        Args:
            credentials_path: Path to Google Cloud service account JSON key file
                           If None, uses GOOGLE_APPLICATION_CREDENTIALS env var
        """
        if vision is None:
            raise ImportError(
                "google-cloud-vision not installed. "
                "Install with: pip install google-cloud-vision pdf2image Pillow"
            )
        
        # Set credentials
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        elif 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
            # Try to load from keys.json
            keys_path = Path(__file__).parent.parent / "keys.json"
            if keys_path.exists():
                with open(keys_path, 'r') as f:
                    keys = json.load(f)
                    creds_path = keys.get('GOOGLE_CLOUD_VISION_CREDENTIALS_PATH', '')
                    if creds_path and Path(creds_path).exists():
                        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        
        # Initialize client
        try:
            self.client = vision.ImageAnnotatorClient()
            logger.info("Google Cloud Vision client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Vision client: {e}")
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
    
    def _extract_text_from_image(self, image_bytes: bytes) -> str:
        """
        Extract text from image using Google Vision API
        
        Args:
            image_bytes: Image bytes
            
        Returns:
            Extracted text
        """
        try:
            image = vision.Image(content=image_bytes)
            response = self.client.document_text_detection(image=image)
            
            if response.error.message:
                raise Exception(f"API Error: {response.error.message}")
            
            # Extract text from response
            if response.full_text_annotation:
                return response.full_text_annotation.text
            else:
                return ""
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
                
                # Convert image to bytes
                image_bytes = self._image_to_bytes(image)
                
                # Extract text
                page_text = self._extract_text_from_image(image_bytes)
                
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
        print("Usage: python ocr_extractor.py <pdf_path> [credentials_path]")
        return
    
    pdf_path = Path(sys.argv[1])
    creds_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        return
    
    try:
        ocr = GoogleVisionOCR(credentials_path=creds_path)
        text, success = ocr.extract_text_from_pdf(pdf_path)
        
        if success:
            print(f"\n✅ Successfully extracted {len(text)} characters")
            print(f"\nFirst 500 characters:")
            print(text[:500])
        else:
            print("\n❌ Failed to extract text")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()

