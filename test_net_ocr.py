"""
Test OCR on unselectable NET PDF
"""

import logging
from pathlib import Path
from src.pdf_extractor import PDFExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_net_ocr():
    """Test OCR on a scanned NET PDF"""
    
    # Tesseract path (adjust if different)
    tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    # Check if tesseract exists
    if not Path(tesseract_path).exists():
        print("\n❌ Tesseract not found at:", tesseract_path)
        print("\nPlease provide the correct path to tesseract.exe")
        print("Common locations:")
        print("  - C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
        print("  - C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe")
        
        # Try to find it
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                tesseract_path = path
                print(f"\n✅ Found Tesseract at: {path}")
                break
        else:
            print("\n⚠️  Could not auto-detect Tesseract installation")
            return
    
    print("\n" + "="*70)
    print("🔍 OCR TEST: Processing Scanned NET PDF")
    print("="*70)
    
    # Initialize extractor with OCR
    extractor = PDFExtractor(use_ocr=True, tesseract_cmd=tesseract_path)
    
    # List available unselectable NET PDFs
    net_folder = Path("Past Papers/NET/unselectable")
    
    if not net_folder.exists():
        print(f"\n❌ Folder not found: {net_folder}")
        return
    
    pdf_files = list(net_folder.glob("*.pdf"))
    
    if not pdf_files:
        print(f"\n❌ No PDF files found in: {net_folder}")
        return
    
    print(f"\n📁 Found {len(pdf_files)} scanned NET PDFs:")
    for i, pdf in enumerate(pdf_files, 1):
        print(f"   {i}. {pdf.name}")
    
    # Select first PDF for testing
    test_pdf = pdf_files[0]
    print(f"\n🎯 Testing with: {test_pdf.name}")
    
    # Get PDF info
    print("\n" + "-"*70)
    print("📊 PDF Information")
    print("-"*70)
    
    info = extractor.get_pdf_info(str(test_pdf))
    print(f"Filename: {info['filename']}")
    print(f"Pages: {info['num_pages']}")
    print(f"Size: {info['size_bytes'] / 1024:.1f} KB")
    print(f"Selectable Text: {info['is_selectable']}")
    print(f"Extraction Method: {info['extraction_method']}")
    print(f"OCR Available: {info['ocr_available']}")
    
    # Perform OCR
    print("\n" + "-"*70)
    print("🔄 Starting OCR Extraction...")
    print("⏱️  This may take 30-60 seconds per page...")
    print("-"*70 + "\n")
    
    try:
        text = extractor.extract_text(str(test_pdf), method='auto')
        
        if text:
            print("\n" + "="*70)
            print("✅ OCR EXTRACTION SUCCESSFUL!")
            print("="*70)
            print(f"\nExtracted Text Statistics:")
            print(f"  - Total characters: {len(text):,}")
            print(f"  - Total lines: {len(text.splitlines()):,}")
            print(f"  - Total words (approx): {len(text.split()):,}")
            
            # Show preview
            print("\n" + "-"*70)
            print("📝 Text Preview (first 1000 characters):")
            print("-"*70)
            print(text[:1000])
            print("\n[... truncated ...]")
            
            # Save to file
            output_file = Path("Extracted Text/NET") / f"{test_pdf.stem}_ocr.txt"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(text, encoding='utf-8')
            
            print(f"\n💾 Full text saved to: {output_file}")
            
            # Ask if user wants to parse questions
            print("\n" + "="*70)
            print("🎯 Next Step: Parse Questions?")
            print("="*70)
            print("\nWould you like to:")
            print("  1. Parse questions from this OCR text")
            print("  2. Just view the raw OCR text")
            
        else:
            print("\n❌ OCR extraction failed - no text extracted")
            print("This might be due to:")
            print("  - Very poor scan quality")
            print("  - Non-text content (images only)")
            print("  - OCR configuration issues")
            
    except Exception as e:
        print(f"\n❌ Error during OCR: {e}")
        logger.exception("OCR failed")
    
    print("\n" + "="*70)
    print("Test Complete!")
    print("="*70)

if __name__ == "__main__":
    test_net_ocr()
