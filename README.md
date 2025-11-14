# Past Papers Parsing Pipeline

A modular data extraction pipeline for converting exam past papers (PDFs) into structured JSON format for RAG (Retrieval Augmented Generation) applications.

## 🎯 Goal

Extract questions from past papers PDFs and prepare them for vector database storage and semantic search.

## 📁 Project Structure

```
past papers parsing/
├── main.py                    # Main pipeline entry point
├── README.md                  # This file
├── requirements.txt           # Python dependencies
│
├── config/                    # Configuration files
│   └── keys.json             # API keys and credentials
│
├── docs/                      # Documentation
│   ├── ANALYSIS_AND_RECOMMENDATIONS.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── ...
│
├── scripts/                   # Extraction scripts
│   ├── image_to_text.py      # OCR image to text converter
│   ├── extract_ocr.py         # OCR extraction workflow helper
│   └── extract_noocr.py      # NO_OCR extraction workflow
│
├── processors/                 # Processing modules
│   ├── mcq_processor.py      # Main MCQ processor
│   ├── fast_processor.py     # FAST-specific processor
│   └── test_processor.py     # Test suite
│
├── src/                       # Core modules
│   ├── pdf_extractor.py      # PDF text extraction (NO_OCR)
│   └── parsers/              # Format-specific parsers
│
└── data/                      # All data folders
    ├── input/                 # Input PDFs (Solved_PastPapers)
    │   ├── NO_OCR/           # PDFs with selectable text
    │   └── OCR/              # Scanned PDFs (with images/)
    ├── output/                # Temporary extraction output
    │   ├── NO_OCR/           # NO_OCR extracted text
    │   └── OCR/              # OCR extracted text
    ├── Standard_text/         # Final cleaned/formatted text (input for processing)
    └── processed_data/        # Final JSON output
```

## 📋 Pipeline Steps

1. **Extract** - PDF → Text (pdfplumber for NO_OCR, OpenAI Vision for OCR)
2. **Clean/Format** - Manual cleanup and formatting → `data/Standard_text/`
3. **Process** - Parse questions, classify topics, generate JSON

## 🚀 Usage

### Main Processing

```bash
# Process all files in Standard_text/
python main.py process

# Run tests
python main.py test
```

### Extraction Scripts

```bash
# Extract NO_OCR PDFs
python scripts/extract_noocr.py

# Extract OCR images
python scripts/image_to_text.py --filter NET
python scripts/image_to_text.py --filter FAST
```

## 📦 Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API keys:**
   - Create `config/config.json` for OpenAI API:
     ```json
     {
       "apiKey": "your-openai-api-key-here"
     }
     ```
   - Update `config/keys.json` if needed

3. **Organize PDFs:**
   - Place solved papers in `data/input/Solved_PastPapers/`
   - Organize by exam type:
     - `NO_OCR/` - PDFs with selectable text
     - `OCR/` - Scanned PDFs (will be converted to images)

## 🔄 Workflow

### Phase 1: Extraction

**NO_OCR PDFs:**
1. Run `python scripts/extract_noocr.py`
2. Review extracted text in `data/output/NO_OCR/`
3. Clean/format manually
4. Copy to `data/Standard_text/`

**OCR PDFs:**
1. Run `python scripts/image_to_text.py --filter NET` or `--filter FAST`
2. Review extracted text in `data/output/OCR/`
3. Clean/format manually
4. Copy to `data/Standard_text/`

### Phase 2: Processing

1. Run `python main.py process`
2. Processes all files in `data/Standard_text/`
3. Generates JSON files in `processed_data/`

## 📊 Output

Final JSON files are saved to `processed_data/` with:
- Questions with options
- Correct answers (when available)
- Topics and tags
- Difficulty scores
- Embedding text for RAG

## 📝 Notes

- MDCAT papers are automatically skipped (only NET and FAST processed)
- Format-specific parsers handle different exam formats
- Enhanced embeddings include full context for better RAG retrieval
