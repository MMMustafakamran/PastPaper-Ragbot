#!/usr/bin/env python3
"""
Test script for text extraction (OCR and NO_OCR)
Tests both extraction methods separately
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pdf_extractor import PDFExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

def test_extraction():
    """Test text extraction for both OCR and NO_OCR folders"""
    
    print("="*60)
    print("TESTING TEXT EXTRACTION")
    print("="*60)
    print()
    
    # Initialize extractor
    extractor = PDFExtractor(
        input_dir="PastPapers/Solved_PastPapers",
        output_dir="Extracted Text"
    )
    
    # Find all PDFs
    pdf_files = extractor.find_pdfs()
    
    if not pdf_files:
        print("[ERROR] No PDF files found in Solved_PastPapers")
        print("   Make sure PDFs are in:")
        print("   - PastPapers/Solved_PastPapers/NO_OCR/NET/")
        print("   - PastPapers/Solved_PastPapers/OCR/NET/")
        print("   - PastPapers/Solved_PastPapers/NO_OCR/FAST/")
        print("   - PastPapers/Solved_PastPapers/OCR/FAST/")
        return
    
    print(f"Found {len(pdf_files)} PDF files to test\n")
    
    # Separate OCR and NO_OCR files
    ocr_files = []
    text_files = []
    
    for pdf_path in pdf_files:
        if extractor._should_use_ocr(pdf_path):
            ocr_files.append(pdf_path)
        else:
            text_files.append(pdf_path)
    
    print(f"NO_OCR files: {len(text_files)}")
    print(f"OCR files: {len(ocr_files)}")
    print()
    
    # Test NO_OCR extraction
    if text_files:
        print("="*60)
        print("TESTING NO_OCR EXTRACTION (pdfplumber)")
        print("="*60)
        print()
        
        for pdf_path in text_files:
            print(f"Testing: {pdf_path.name}")
            print(f"  Path: {pdf_path.relative_to(extractor.input_dir)}")
            
            text, success, method = extractor.extract_text_from_pdf(pdf_path)
            
            if success:
                print(f"  [SUCCESS] Extracted {len(text)} characters")
                print(f"  Method: {method.upper()}")
                
                # Show first 200 chars
                preview = text[:200].replace('\n', ' ')
                print(f"  Preview: {preview}...")
                
                # Save to file
                output_path = extractor.get_output_path(pdf_path)
                if extractor.save_text(text, output_path):
                    print(f"  [SUCCESS] Saved to: {output_path}")
            else:
                print(f"  [FAILED] No text extracted")
            
            print()
    
    # Test OCR extraction
    if ocr_files:
        print("="*60)
        print("TESTING OCR EXTRACTION (Google Vision API)")
        print("="*60)
        print()
        
        if not extractor.ocr_extractor:
            print("  [WARNING] OCR extractor not available")
            print("  Make sure:")
            print("  1. google-cloud-vision is installed: pip install google-cloud-vision")
            print("  2. Google Cloud credentials are set in keys.json or GOOGLE_APPLICATION_CREDENTIALS env var")
            print()
        else:
            for pdf_path in ocr_files:
                print(f"Testing: {pdf_path.name}")
                print(f"  Path: {pdf_path.relative_to(extractor.input_dir)}")
                
                text, success, method = extractor.extract_text_from_pdf(pdf_path)
                
                if success:
                    print(f"  [SUCCESS] Extracted {len(text)} characters")
                    print(f"  Method: {method.upper()}")
                    
                    # Show first 200 chars
                    preview = text[:200].replace('\n', ' ')
                    print(f"  Preview: {preview}...")
                    
                    # Save to file
                    output_path = extractor.get_output_path(pdf_path)
                    if extractor.save_text(text, output_path):
                        print(f"  [SUCCESS] Saved to: {output_path}")
                else:
                    print(f"  [FAILED] No text extracted")
                
                print()
    
    # Summary
    print("="*60)
    print("EXTRACTION TEST SUMMARY")
    print("="*60)
    print(f"Total PDFs: {len(pdf_files)}")
    print(f"NO_OCR files: {len(text_files)}")
    print(f"OCR files: {len(ocr_files)}")
    print()
    print("Check 'Extracted Text' folder for output files")
    print("="*60)


if __name__ == "__main__":
    test_extraction()

