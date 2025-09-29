"""
Extraction Pipeline
Orchestrates PDF extraction, noise removal, and question parsing
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import re

from .pdf_extractor import PDFExtractor
from .noise_remover import NoiseRemover
from .parser import QuestionParser, Question

logger = logging.getLogger(__name__)


class ExtractionPipeline:
    """Complete pipeline for extracting questions from PDF past papers"""
    
    def __init__(self, exam_type: str, use_ocr: bool = False):
        """
        Initialize extraction pipeline
        
        Args:
            exam_type: Type of exam (MDCAT, NET, NUST, etc.)
            use_ocr: Enable OCR for scanned PDFs
        """
        self.exam_type = exam_type
        
        # Initialize all components
        self.pdf_extractor = PDFExtractor(use_ocr=use_ocr)
        self.noise_remover = NoiseRemover()
        self.parser = QuestionParser()
        
        logger.info(f"Pipeline initialized for {exam_type} (OCR: {use_ocr})")
    
    def _extract_year_from_filename(self, filename: str) -> Optional[int]:
        """
        Try to extract year from filename
        
        Args:
            filename: PDF filename
            
        Returns:
            Year if found, None otherwise
        """
        # Look for 4-digit year (2000-2099)
        year_match = re.search(r'20\d{2}', filename)
        if year_match:
            return int(year_match.group())
        
        # Look for 2-digit year (00-99)
        year_match = re.search(r'\b(\d{2})\b', filename)
        if year_match:
            year = int(year_match.group())
            # Assume 00-30 is 2000-2030, 31-99 is 1931-1999
            if year <= 30:
                return 2000 + year
            else:
                return 1900 + year
        
        return None
    
    def process_pdf(self, pdf_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single PDF through the complete pipeline
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory for output files (optional)
            
        Returns:
            Dictionary with results and statistics
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        logger.info("="*70)
        logger.info(f"Processing: {pdf_path.name}")
        logger.info("="*70)
        
        result = {
            'status': 'success',
            'source_file': pdf_path.name,
            'exam_type': self.exam_type,
            'total_questions': 0,
            'valid_questions': 0,
            'errors': []
        }
        
        try:
            # Step 1: Get PDF info
            logger.info("Step 1/6: Analyzing PDF...")
            pdf_info = self.pdf_extractor.get_pdf_info(str(pdf_path))
            result['pdf_info'] = pdf_info
            
            logger.info(f"  - Pages: {pdf_info['num_pages']}")
            logger.info(f"  - Selectable: {pdf_info['is_selectable']}")
            logger.info(f"  - Method: {pdf_info['extraction_method']}")
            
            # Step 2: Extract text
            logger.info("Step 2/6: Extracting text from PDF...")
            raw_text = self.pdf_extractor.extract_text(str(pdf_path))
            
            if not raw_text:
                result['status'] = 'failed'
                result['errors'].append("No text extracted from PDF")
                logger.error("  ✗ No text extracted")
                return result
            
            logger.info(f"  ✓ Extracted {len(raw_text):,} characters")
            result['raw_text_length'] = len(raw_text)
            
            # Step 3: Remove noise
            logger.info("Step 3/6: Cleaning text (removing noise)...")
            clean_text = self.noise_remover.clean_text(raw_text)
            stats = self.noise_remover.get_noise_statistics(raw_text, clean_text)
            
            logger.info(f"  ✓ Removed {stats['removal_percentage']:.1f}% noise")
            logger.info(f"  ✓ {stats['cleaned_length']:,} characters remaining")
            result['noise_stats'] = stats
            
            # Step 4: Parse questions
            logger.info("Step 4/6: Parsing questions...")
            questions = self.parser.extract_questions_from_text(clean_text)
            result['total_questions'] = len(questions)
            
            logger.info(f"  ✓ Found {len(questions)} questions")
            
            # Step 5: Enrich and validate
            logger.info("Step 5/6: Enriching metadata and validating...")
            
            # Extract year from filename
            paper_year = self._extract_year_from_filename(pdf_path.name)
            
            # Set source and exam type for all questions
            for q in questions:
                q.source = pdf_path.name
                q.exam_type = self.exam_type
                q.paper_year = paper_year
            
            # Validate questions
            valid_questions = [q for q in questions if self.parser.validate_question(q)]
            result['valid_questions'] = len(valid_questions)
            
            validation_rate = (len(valid_questions) / len(questions) * 100) if questions else 0
            logger.info(f"  ✓ {len(valid_questions)} valid ({validation_rate:.1f}%)")
            
            if len(valid_questions) == 0:
                result['status'] = 'warning'
                result['errors'].append("No valid questions found")
                logger.warning("  ⚠ No valid questions found")
                return result
            
            # Step 6: Generate summary
            logger.info("Step 6/6: Generating statistics...")
            summary = self.parser.generate_comprehensive_summary(valid_questions)
            result['summary'] = summary
            
            # Log subject distribution
            logger.info("  Subject breakdown:")
            for subject, count in summary['subject_distribution'].items():
                percentage = (count / len(valid_questions) * 100)
                logger.info(f"    - {subject}: {count} ({percentage:.1f}%)")
            
            # Save output if directory provided
            if output_dir:
                self._save_results(valid_questions, summary, pdf_path, output_dir)
            
            result['questions'] = valid_questions
            
            logger.info("="*70)
            logger.info(f"✓ Processing complete: {len(valid_questions)} questions extracted")
            logger.info("="*70)
            
        except Exception as e:
            result['status'] = 'failed'
            result['errors'].append(str(e))
            logger.error(f"Pipeline failed: {e}")
            logger.exception("Full error:")
        
        return result
    
    def _save_results(self, questions: List[Question], summary: Dict[str, Any], 
                     source_pdf: Path, output_dir: str):
        """
        Save extraction results to JSON file
        
        Args:
            questions: List of Question objects
            summary: Summary statistics
            source_pdf: Source PDF path
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create output filename
        output_file = output_path / f"{source_pdf.stem}_questions.json"
        
        # Prepare data
        from dataclasses import asdict
        
        data = {
            'source': {
                'filename': source_pdf.name,
                'exam_type': self.exam_type,
                'extraction_timestamp': datetime.now().isoformat(),
                'parser_version': '4.0'
            },
            'summary': summary,
            'questions': [asdict(q) for q in questions]
        }
        
        # Save to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"  ✓ Saved to: {output_file}")
    
    def get_statistics(self, result: Dict[str, Any]) -> str:
        """
        Get formatted statistics string
        
        Args:
            result: Pipeline result dictionary
            
        Returns:
            Formatted statistics string
        """
        if result['status'] != 'success':
            return f"Status: {result['status']}\nErrors: {', '.join(result['errors'])}"
        
        stats = []
        stats.append(f"Source: {result['source_file']}")
        stats.append(f"Exam Type: {result['exam_type']}")
        stats.append(f"Total Questions Found: {result['total_questions']}")
        stats.append(f"Valid Questions: {result['valid_questions']}")
        
        if 'summary' in result:
            summary = result['summary']
            stats.append(f"\nSubject Distribution:")
            for subject, count in summary['subject_distribution'].items():
                stats.append(f"  - {subject}: {count}")
        
        return "\n".join(stats)


def test_pipeline():
    """Test the pipeline on a sample PDF"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python -m src.pipeline <exam_type> <pdf_path>")
        print("\nExample:")
        print('  python -m src.pipeline MDCAT "Past Papers/MDCAT/selectable/PMC MDCAT PAPER 2020.pdf"')
        return
    
    exam_type = sys.argv[1]
    pdf_path = sys.argv[2]
    
    # Initialize pipeline
    pipeline = ExtractionPipeline(exam_type=exam_type, use_ocr=False)
    
    # Process PDF
    result = pipeline.process_pdf(pdf_path, output_dir=f"Processed Data/{exam_type}")
    
    # Print statistics
    print("\n" + "="*70)
    print("EXTRACTION RESULTS")
    print("="*70)
    print(pipeline.get_statistics(result))
    print("="*70)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    test_pipeline()
