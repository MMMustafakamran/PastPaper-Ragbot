#!/usr/bin/env python3
"""
NO_OCR Extraction Workflow
Extracts text from NO_OCR PDFs and prepares for Standard_text/
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pdf_extractor import PDFExtractor

def main():
    """Extract NO_OCR PDFs"""
    print("="*60)
    print("NO_OCR PDF EXTRACTION")
    print("="*60)
    print()
    
    extractor = PDFExtractor(
        input_dir="data/input/Solved_PastPapers/NO_OCR",
        output_dir="data/output/NO_OCR"
    )
    
    stats = extractor.extract_all()
    extractor.print_summary(stats)
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("1. Review extracted text in: data/output/NO_OCR/")
    print("2. Clean/format manually or with scripts")
    print("3. Copy final files to: data/Standard_text/")
    print("="*60)

if __name__ == "__main__":
    main()


