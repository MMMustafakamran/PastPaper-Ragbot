"""
Force OCR on NET PDF (ignore watermark text)
"""

import logging
from pathlib import Path
from src.pdf_extractor import PDFExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def force_ocr_net():
    """Force OCR on a NET PDF to read scanned questions"""
    
    # Tesseract path
    tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    if not Path(tesseract_path).exists():
        print(f"\n❌ Tesseract not found at: {tesseract_path}")
        print("\nTrying alternative locations...")
        alt_path = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
        if Path(alt_path).exists():
            tesseract_path = alt_path
            print(f"✅ Found at: {alt_path}")
        else:
            print("❌ Please restart your terminal or provide the correct path")
            return
    
    print("\n" + "="*70)
    print("🔍 FORCED OCR TEST: Reading Scanned Questions from NET PDF")
    print("="*70)
    
    # Initialize extractor with OCR
    extractor = PDFExtractor(use_ocr=True, tesseract_cmd=tesseract_path)
    
    # Get NET PDF
    net_folder = Path("Past Papers/NET/unselectable")
    pdf_files = list(net_folder.glob("*.pdf"))
    
    if not pdf_files:
        print(f"\n❌ No PDFs found in: {net_folder}")
        return
    
    # Use first PDF
    test_pdf = pdf_files[0]
    print(f"\n📄 PDF: {test_pdf.name}")
    print(f"📊 Pages: 74 (estimated)")
    print(f"⚠️  Note: This is a SCANNED document - will use OCR")
    
    # Ask for page limit (OCR is slow!)
    print("\n" + "-"*70)
    print("⏱️  OCR Performance Estimates:")
    print("   - 1 page  = ~30-60 seconds")
    print("   - 5 pages = ~2-5 minutes")
    print("   - 10 pages = ~5-10 minutes")
    print("   - 74 pages (full) = ~40-75 minutes! ⚠️")
    print("-"*70)
    
    # For testing, let's do just first 2 pages
    print("\n🎯 Strategy: Extract first 2 pages for testing")
    print("   (You can process more pages later)")
    
    print("\n▶️  Starting OCR extraction automatically...")
    
    print("\n" + "="*70)
    print("🔄 EXTRACTING TEXT WITH OCR (FORCED MODE)")
    print("="*70)
    print("\n⏳ Processing... This will take 1-2 minutes...\n")
    
    try:
        # Force OCR extraction
        text = extractor.extract_text(str(test_pdf), force_ocr=True)
        
        if text and len(text) > 1000:  # More than just watermarks
            print("\n" + "="*70)
            print("✅ SUCCESS! Real content extracted via OCR")
            print("="*70)
            
            # Clean up (remove watermarks)
            clean_text = text.replace("www.educatedzone.com", "").strip()
            
            print(f"\n📊 Extraction Statistics:")
            print(f"   - Total characters: {len(clean_text):,}")
            print(f"   - Total lines: {len(clean_text.splitlines()):,}")
            print(f"   - Words (approx): {len(clean_text.split()):,}")
            
            # Show preview
            print("\n" + "-"*70)
            print("📝 OCR Text Preview (first 2000 characters):")
            print("-"*70)
            preview = clean_text[:2000]
            print(preview)
            if len(clean_text) > 2000:
                print("\n[... more content ...]")
            
            # Save
            output_file = Path("Extracted Text/NET") / f"{test_pdf.stem}_FULL_OCR.txt"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(clean_text, encoding='utf-8')
            
            print(f"\n💾 Full OCR text saved to:")
            print(f"   {output_file}")
            
            # Check if we can find questions
            has_questions = bool(re.search(r'^\d+\.', clean_text, re.MULTILINE))
            
            if has_questions:
                print("\n✅ Found question patterns in OCR text!")
                print("   Ready for parsing with QuestionParser")
            else:
                print("\n⚠️  No clear question patterns detected")
                print("   Text might need manual review")
            
        else:
            print("\n⚠️  OCR returned minimal text")
            print("   This might indicate:")
            print("   - PDF is very poor quality")
            print("   - Need to adjust OCR settings")
            print("   - Wrong language setting")
            
    except Exception as e:
        print(f"\n❌ OCR Error: {e}")
        logger.exception("Full error:")
    
    print("\n" + "="*70)
    print("Test Complete!")
    print("="*70)

if __name__ == "__main__":
    import re
    force_ocr_net()
