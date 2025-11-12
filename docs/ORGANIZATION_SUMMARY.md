# Project Organization Summary

## ✅ Completed Organization

### Directory Structure

```
past papers parsing/
├── config/                    # Configuration files
│   ├── keys.json             # API keys
│   └── config.json.example   # OpenAI config template
│
├── docs/                      # Documentation
│   ├── DATA_STRUCTURE.md     # Data folder structure
│   └── ...
│
├── scripts/                   # Utility scripts
│   ├── image_to_text.py      # OpenAI Vision API converter
│   └── test_extraction.py    # Test extraction
│
├── src/                       # Source code
│   └── ...
│
└── data/                      # All data organized
    ├── input/                 # Source PDFs
    │   └── Solved_PastPapers/
    │       ├── NO_OCR/       # PDFs with selectable text
    │       └── OCR/          # Scanned PDFs
    │
    ├── images/                # PDF pages as images
    │   ├── NO_OCR/           # ✅ NO_OCR PDFs converted to images
    │   │   ├── FAST/
    │   │   └── NET/
    │   └── OCR/              # (Future: OCR PDFs as images)
    │
    ├── extracted/             # Text from PDFs (pdfplumber/Tesseract)
    │   ├── NO_OCR/
    │   └── OCR/
    │
    ├── output/                # Text from images (OpenAI Vision API)
    │   ├── NO_OCR/
    │   └── OCR/
    │
    ├── cleaned/               # Cleaned text
    └── processed/             # Final JSON files
```

## Key Points

### Images Organization ✅

- **`data/images/NO_OCR/`**: Contains images converted from NO_OCR PDFs
  - These are PDFs with selectable text that were converted to images
  - Used for OpenAI Vision API processing (often more accurate than pdfplumber)
  - Structure: `NO_OCR/[EXAM_TYPE]/[PDF_NAME]/page_XXX.png`

- **`data/images/OCR/`**: Reserved for future OCR PDF images
  - Will contain images from scanned PDFs

### Workflow Clarification

1. **NO_OCR PDFs** can be processed two ways:
   - **Direct**: PDF → pdfplumber → `data/extracted/NO_OCR/`
   - **Via Images**: PDF → Images → OpenAI Vision → `data/output/NO_OCR/`

2. **OCR PDFs** (scanned):
   - PDF → Images → OpenAI Vision → `data/output/OCR/`

### Script Usage

The `scripts/image_to_text.py` script:
- Searches recursively in `data/images/` for all PNG files
- Processes images from both `NO_OCR/` and `OCR/` folders
- Saves output text to `data/output/` maintaining the same structure

## Next Steps

1. Run image-to-text conversion:
   ```bash
   python scripts/image_to_text.py
   ```

2. The script will process images from `data/images/NO_OCR/` and save text to `data/output/NO_OCR/`

3. Continue with the pipeline:
   ```bash
   python main.py clean    # Clean the output text
   python main.py parse    # Parse questions
   python main.py enhance  # Add metadata
   ```

