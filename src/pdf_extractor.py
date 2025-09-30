"""
PDF Text Extractor
Extracts text from PDF files and saves to text files
"""

import logging
from pathlib import Path
from typing import List, Tuple, Optional
import pdfplumber

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text from PDF files"""
    
    def __init__(self, input_dir: str = "Past Papers", output_dir: str = "Extracted Text"):
        """
        Initialize PDF extractor
        
        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory to save extracted text
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def find_pdfs(self) -> List[Path]:
        """
        Find all PDF files in input directory recursively
        
        Returns:
            List of PDF file paths
        """
        if not self.input_dir.exists():
            logger.error(f"Input directory not found: {self.input_dir}")
            return []
        
        pdf_files = list(self.input_dir.rglob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files")
        return pdf_files
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Tuple[str, bool]:
        """
        Extract text from a single PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, success)
        """
        try:
            text_content = []
            
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"Processing {pdf_path.name} ({total_pages} pages)")
                
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
                return "", False
            
            logger.info(f"Successfully extracted {len(full_text)} characters from {pdf_path.name}")
            return full_text, True
            
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path.name}: {e}")
            return "", False
    
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
            'files': []
        }
        
        for pdf_path in pdf_files:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {pdf_path.relative_to(self.input_dir)}")
            logger.info(f"{'='*60}")
            
            # Extract text
            text, success = self.extract_text_from_pdf(pdf_path)
            
            if success and text:
                # Get output path
                output_path = self.get_output_path(pdf_path)
                
                # Save text
                if self.save_text(text, output_path):
                    stats['successful'] += 1
                    stats['files'].append({
                        'pdf': str(pdf_path),
                        'output': str(output_path),
                        'status': 'success',
                        'chars': len(text)
                    })
                else:
                    stats['failed'] += 1
                    stats['files'].append({
                        'pdf': str(pdf_path),
                        'status': 'failed_to_save'
                    })
            else:
                stats['failed'] += 1
                stats['files'].append({
                    'pdf': str(pdf_path),
                    'status': 'failed_to_extract'
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
        
        if stats['successful'] > 0:
            print(f"\n✅ Extracted text saved to: {self.output_dir}")
            print("\nSuccessfully processed files:")
            for file_info in stats['files']:
                if file_info['status'] == 'success':
                    pdf_name = Path(file_info['pdf']).name
                    chars = file_info['chars']
                    print(f"  ✓ {pdf_name} ({chars:,} characters)")
        
        if stats['failed'] > 0:
            print("\n❌ Failed files:")
            for file_info in stats['files']:
                if file_info['status'] != 'success':
                    pdf_name = Path(file_info['pdf']).name
                    status = file_info['status']
                    print(f"  ✗ {pdf_name} ({status})")


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

