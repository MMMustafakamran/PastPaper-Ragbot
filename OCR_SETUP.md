# OCR Setup Guide

## 📋 Overview

This guide helps you install and configure OCR (Optical Character Recognition) capabilities for processing scanned PDFs.

## 🔧 Installation Steps

### **Step 1: Install Python Libraries**

```bash
pip install pytesseract==0.3.10
pip install Pillow==10.2.0
pip install pdf2image==1.17.0
```

Or install all at once:
```bash
pip install -r requirements.txt
```

### **Step 2: Install Tesseract OCR Engine**

#### **Windows** 🪟

1. Download Tesseract installer from:
   https://github.com/UB-Mannheim/tesseract/wiki

2. Run the installer (tesseract-ocr-w64-setup-v5.x.x.exe)

3. During installation, note the installation path (default: `C:\Program Files\Tesseract-OCR`)

4. **Option A:** Add to PATH
   - Open System Properties → Environment Variables
   - Add `C:\Program Files\Tesseract-OCR` to PATH
   - Restart terminal

5. **Option B:** Set path in code
   ```python
   from src.pdf_extractor import PDFExtractor
   
   extractor = PDFExtractor(
       use_ocr=True,
       tesseract_cmd=r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   )
   ```

6. Verify installation:
   ```bash
   tesseract --version
   ```

#### **macOS** 🍎

Using Homebrew:
```bash
brew install tesseract
```

Verify:
```bash
tesseract --version
```

#### **Linux** 🐧

Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev
```

CentOS/RHEL:
```bash
sudo yum install tesseract
```

Verify:
```bash
tesseract --version
```

### **Step 3: Install Poppler (for pdf2image)**

#### **Windows** 🪟

1. Download poppler for Windows:
   https://github.com/oschwartz10612/poppler-windows/releases/

2. Extract to a location (e.g., `C:\Program Files\poppler`)

3. Add `C:\Program Files\poppler\Library\bin` to PATH

Or use conda:
```bash
conda install -c conda-forge poppler
```

#### **macOS** 🍎

```bash
brew install poppler
```

#### **Linux** 🐧

Ubuntu/Debian:
```bash
sudo apt-get install poppler-utils
```

CentOS/RHEL:
```bash
sudo yum install poppler-utils
```

### **Step 4: Install Language Data (Optional)**

For better accuracy with Urdu or Arabic text:

#### **Windows**
1. Download language data from: https://github.com/tesseract-ocr/tessdata
2. Copy `.traineddata` files to: `C:\Program Files\Tesseract-OCR\tessdata\`

#### **Linux/macOS**
```bash
# Urdu
sudo apt-get install tesseract-ocr-urd

# Arabic
sudo apt-get install tesseract-ocr-ara
```

## ✅ Verify Installation

Run the test script:

```bash
python src/ocr_handler.py
```

You should see:
```
==================================================
OCR Dependencies Check
==================================================
✅ pytesseract: True
✅ pdf2image: True
✅ ready: True
```

## 🧪 Test OCR on a Scanned PDF

```bash
python src/ocr_handler.py "Past Papers/NET/unselectable/NUST NET Past Paper 1 PLS.pdf"
```

This will:
- Convert PDF pages to images
- Perform OCR on each page
- Show extracted text
- Offer to save results

## 🎯 Usage in Code

### **Basic Usage**

```python
from src.pdf_extractor import PDFExtractor

# Initialize with OCR enabled
extractor = PDFExtractor(use_ocr=True)

# Extract from scanned PDF (auto-detects and uses OCR)
text = extractor.extract_text("scanned_paper.pdf")
```

### **Force OCR**

```python
# Force OCR even if text is selectable
text = extractor.extract_text("paper.pdf", force_ocr=True)
```

### **Check if PDF needs OCR**

```python
# Get PDF info
info = extractor.get_pdf_info("paper.pdf")

print(f"Selectable: {info['is_selectable']}")
print(f"Method: {info['extraction_method']}")
print(f"OCR Available: {info['ocr_available']}")
```

### **Advanced OCR Settings**

```python
from src.ocr_handler import OCRHandler

# Initialize OCR handler
ocr = OCRHandler(tesseract_cmd=r'C:\Program Files\Tesseract-OCR\tesseract.exe')

# High-resolution OCR (slower but better quality)
text = ocr.ocr_pdf("scanned.pdf", dpi=600)

# OCR with Urdu language
text = ocr.ocr_pdf("urdu_paper.pdf", lang='urd')

# OCR with confidence scores
result = ocr.ocr_with_confidence(image)
print(f"Confidence: {result['avg_confidence']}%")
print(f"Text: {result['text']}")
```

## 📊 OCR Performance Tips

### **Quality vs Speed**

| DPI  | Quality      | Speed  | Use Case                |
|------|--------------|--------|-------------------------|
| 150  | Low          | Fast   | Quick preview           |
| 300  | Good         | Medium | Standard documents ✅   |
| 450  | Very Good    | Slow   | Important documents     |
| 600  | Excellent    | Slow   | Poor quality scans      |

**Default: 300 DPI** (good balance)

### **Improve OCR Accuracy**

1. **Higher DPI**: Use 450-600 for poor quality scans
2. **Preprocessing**: Images are automatically preprocessed
3. **Language**: Specify correct language for better results
4. **Clean Scans**: Original scan quality matters most

### **Common Issues**

#### ❌ "tesseract is not installed"
- Install Tesseract OCR engine (see Step 2 above)
- Add to PATH or specify path in code

#### ❌ "Unable to convert PDF"
- Install poppler (see Step 3 above)
- Verify poppler is in PATH

#### ❌ Low accuracy on Urdu/Arabic
- Install language data packages
- Use `lang='urd'` or `lang='ara'` parameter

#### ❌ Very slow processing
- Reduce DPI to 200-250
- Process fewer pages for testing
- Consider parallel processing for large batches

## 🔍 Debug OCR Issues

Save preprocessed images for inspection:

```python
from src.ocr_handler import OCRHandler

ocr = OCRHandler()
ocr.save_ocr_debug_images("problem.pdf", "debug_images/")
```

This helps identify:
- Image quality issues
- Text orientation problems
- Preprocessing effectiveness

## 📈 Expected Results

### **Selectable PDFs (No OCR)**
- ✅ 1-2 seconds per PDF
- ✅ 99%+ accuracy
- ✅ All formatting preserved

### **Scanned PDFs (With OCR)**
- ⏱️ 30-60 seconds per page (300 DPI)
- ✅ 85-95% accuracy (good quality scans)
- ⚠️ Some formatting may be lost
- ⚠️ Mathematical symbols may need correction

## 🎯 Integration with Pipeline

OCR is automatically used when needed:

```python
# Will automatically use OCR for scanned PDFs
pipeline = ExtractionPipeline(exam_type="NET")
results = pipeline.process_pdf("scanned_net_paper.pdf", "output/")
```

No manual intervention required! The system:
1. Checks if text is selectable
2. Uses pdfplumber/PyPDF2 for selectable PDFs
3. Automatically falls back to OCR for scanned PDFs
4. Post-processes OCR text to fix common errors

## 🆘 Support

If you encounter issues:
1. Verify installation: `python src/ocr_handler.py`
2. Check Tesseract: `tesseract --version`
3. Check poppler: `pdftoppm -v`
4. Review debug images: `ocr.save_ocr_debug_images()`

## 📚 Resources

- Tesseract Documentation: https://tesseract-ocr.github.io/
- Tesseract Language Data: https://github.com/tesseract-ocr/tessdata
- pdf2image: https://github.com/Belval/pdf2image
- pytesseract: https://github.com/madmaze/pytesseract
