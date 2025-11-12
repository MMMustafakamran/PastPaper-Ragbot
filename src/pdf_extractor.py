"""
PDF Text Extractor
Extracts text from PDF files and saves to text files
Supports both text extraction (pdfplumber) and OCR (Google Vision API)
"""

import logging
from pathlib import Path
from typing import List, Tuple, Optional
import pdfplumber

# Try to import OCR extractor (optional)
try:
    from src.ocr_extractor import GoogleVisionOCR
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("OCR extractor not available. Install google-cloud-vision for OCR support.")

if OCR_AVAILABLE:
    logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text from PDF files"""
    
    def __init__(self, input_dir: str = "Past Papers", output_dir: str = "Extracted Text", 
                 credentials_path: Optional[str] = None):
        """
        Initialize PDF extractor
        
        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory to save extracted text
            credentials_path: Path to Google Cloud Vision credentials (for OCR)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.credentials_path = credentials_path
        
        # Initialize OCR extractor if available
        self.ocr_extractor = None
        if OCR_AVAILABLE:
            try:
                self.ocr_extractor = GoogleVisionOCR(credentials_path=credentials_path)
            except Exception as e:
                logger.warning(f"OCR extractor initialization failed: {e}. OCR will be skipped.")
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def find_pdfs(self) -> List[Path]:
        """
        Find all PDF files in input directory recursively
        Excludes MDCAT papers (only process solved papers: NET and FAST)
            
        Returns:
            List of PDF file paths
        """
        if not self.input_dir.exists():
            logger.error(f"Input directory not found: {self.input_dir}")
            return []
        
        pdf_files = list(self.input_dir.rglob("*.pdf"))
        
        # Filter out MDCAT papers (only process NET and FAST)
        filtered_files = []
        for pdf_path in pdf_files:
            path_str = str(pdf_path).upper()
            # Skip MDCAT papers
            if 'MDCAT' in path_str:
                logger.debug(f"Skipping MDCAT paper: {pdf_path.name}")
                continue
            filtered_files.append(pdf_path)
        
        logger.info(f"Found {len(filtered_files)} PDF files (excluded {len(pdf_files) - len(filtered_files)} MDCAT files)")
        return filtered_files
    
    def _should_use_ocr(self, pdf_path: Path) -> bool:
        """
        Determine if OCR should be used for this PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if PDF is in OCR folder, False otherwise
        """
        # Check if "OCR" is in the path parts
        path_parts = pdf_path.parts
        return "OCR" in path_parts
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Tuple[str, bool, str]:
        """
        Extract text from a single PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, success, method_used)
            method_used: "ocr" or "text"
        """
        # Check if OCR should be used
        if self._should_use_ocr(pdf_path):
            if self.ocr_extractor:
                logger.info(f"[OCR] Processing {pdf_path.name}")
                text, success = self.ocr_extractor.extract_text_from_pdf(pdf_path)
                return text, success, "ocr"
            else:
                logger.warning(f"[OCR] OCR requested but not available for {pdf_path.name}")
                logger.warning(f"      Falling back to text extraction...")
                # Fall through to text extraction
        
        # Use text extraction (pdfplumber)
        logger.info(f"[TEXT] Processing {pdf_path.name}")
        try:
            text_content = []
            
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"  Pages: {total_pages}")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    
                    if page_text:
                        text_content.append(page_text)
                        logger.debug(f"  Page {page_num}/{total_pages} - {len(page_text)} chars")
                    else:
                        logger.warning(f"  Page {page_num}/{total_pages} - No text found")
            
            full_text = "\n\n".join(text_content)
            
            if not full_text.strip():
                logger.warning(f"No text extracted from {pdf_path.name}")
                return "", False, "text"
            
            logger.info(f"Successfully extracted {len(full_text)} characters from {pdf_path.name}")
            return full_text, True, "text"
            
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path.name}: {e}")
            return "", False, "text"
    
    def get_output_path(self, pdf_path: Path) -> Path:
        """
        Generate output path for extracted text file
        Maintains directory structure from input
        
        Args:
            pdf_path: Original PDF file path
            
        Returns:
            Path for output text file
        """
        # Get relative path from input directory
        try:
            relative_path = pdf_path.relative_to(self.input_dir)
        except ValueError:
            # If pdf_path is not relative to input_dir, just use the filename
            relative_path = pdf_path.name
        
        # Change extension to .txt
        output_path = self.output_dir / relative_path.parent / f"{pdf_path.stem}.txt"
        
        # Create parent directories
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        return output_path
    
    def save_text(self, text: str, output_path: Path) -> bool:
        """
        Save extracted text to file
        
        Args:
            text: Text content to save
            output_path: Path to save text file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            logger.info(f"Saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save text to {output_path}: {e}")
            return False
    
    def extract_all(self) -> dict:
        """
        Extract text from all PDFs in input directory
            
        Returns:
            Dictionary with extraction statistics
        """
        pdf_files = self.find_pdfs()
        
        if not pdf_files:
            logger.warning("No PDF files found")
            return {
                'total_pdfs': 0,
                'successful': 0,
                'failed': 0,
                'files': []
            }
        
        stats = {
            'total_pdfs': len(pdf_files),
            'successful': 0,
            'failed': 0,
            'ocr_files': 0,
            'text_files': 0,
            'ocr_successful': 0,
            'text_successful': 0,
            'files': []
        }
        
        for pdf_path in pdf_files:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {pdf_path.relative_to(self.input_dir)}")
            logger.info(f"{'='*60}")
            
            # Extract text
            text, success, method = self.extract_text_from_pdf(pdf_path)
            
            # Update method counts
            if method == "ocr":
                stats['ocr_files'] += 1
            else:
                stats['text_files'] += 1
            
            if success and text:
                # Get output path
                output_path = self.get_output_path(pdf_path)
                
                # Save text
                if self.save_text(text, output_path):
                    stats['successful'] += 1
                    if method == "ocr":
                        stats['ocr_successful'] += 1
                    else:
                        stats['text_successful'] += 1
                    
                    stats['files'].append({
                        'pdf': str(pdf_path),
                        'output': str(output_path),
                        'status': 'success',
                        'method': method,
                        'chars': len(text)
                    })
                else:
                    stats['failed'] += 1
                    stats['files'].append({
                        'pdf': str(pdf_path),
                        'status': 'failed_to_save',
                        'method': method
                    })
            else:
                stats['failed'] += 1
                stats['files'].append({
                    'pdf': str(pdf_path),
                    'status': 'failed_to_extract',
                    'method': method
                })
        
        return stats
    
    def print_summary(self, stats: dict) -> None:
        """Print extraction summary"""
        print("\n" + "="*60)
        print("EXTRACTION SUMMARY")
        print("="*60)
        print(f"Total PDFs found: {stats['total_pdfs']}")
        print(f"Successfully extracted: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        
        if stats.get('ocr_files', 0) > 0 or stats.get('text_files', 0) > 0:
            print(f"\nExtraction Methods:")
            print(f"  OCR files: {stats.get('ocr_files', 0)} ({stats.get('ocr_successful', 0)} successful)")
            print(f"  Text files: {stats.get('text_files', 0)} ({stats.get('text_successful', 0)} successful)")
        
        if stats['successful'] > 0:
            print(f"\n[SUCCESS] Extracted text saved to: {self.output_dir}")
            print("\nSuccessfully processed files:")
            for file_info in stats['files']:
                if file_info['status'] == 'success':
                    pdf_name = Path(file_info['pdf']).name
                    chars = file_info['chars']
                    method = file_info.get('method', 'unknown')
                    print(f"  [+] {pdf_name} ({chars:,} chars, {method.upper()})")
        
        if stats['failed'] > 0:
            print("\n[FAILED] Failed files:")
            for file_info in stats['files']:
                if file_info['status'] != 'success':
                    pdf_name = Path(file_info['pdf']).name
                    status = file_info['status']
                    method = file_info.get('method', 'unknown')
                    print(f"  [-] {pdf_name} ({status}, {method.upper()})")


def main():
    """Main function for testing"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    # Create extractor
    extractor = PDFExtractor()
    
    # Extract all PDFs
    stats = extractor.extract_all()
    
    # Print summary
    extractor.print_summary(stats)


if __name__ == "__main__":
    main()

