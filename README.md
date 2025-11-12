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
├── scripts/                   # Utility scripts
│   ├── image_to_text.py      # OpenAI vision API converter
│   └── test_extraction.py    # Test extraction script
│
├── src/                       # Source code (main pipeline)
│   ├── pdf_extractor.py      # PDF text extraction
│   ├── ocr_extractor.py      # Tesseract OCR (legacy)
│   ├── text_cleaner.py       # Text cleaning
│   ├── question_parser.py    # Question parsing
│   ├── enhance_simple.py     # Metadata enhancement
│   ├── parsers/              # Format-specific parsers
│   └── enhancers/            # Embedding generators
│
└── data/                      # All data folders
    ├── input/                 # Input PDFs (Solved_PastPapers)
    │   ├── NO_OCR/           # PDFs with selectable text
    │   └── OCR/              # Scanned PDFs
    ├── extracted/             # Extracted text
    ├── cleaned/               # Cleaned text
    ├── images/                # PDF pages converted to images
    │   ├── NO_OCR/           # NO_OCR PDFs converted to images (for OpenAI Vision)
    │   └── OCR/              # OCR PDFs converted to images (future)
    ├── output/                # OpenAI vision API output (text from images)
    └── processed/             # Final JSON files
```

## 📋 Pipeline Steps

1. **Extract** - PDF → Text (pdfplumber for NO_OCR, OpenAI Vision for OCR)
2. **Clean** - Remove promotional content, URLs, and noise
3. **Parse** - Extract questions, options, and metadata
4. **Enhance** - Add topics, tags, difficulty, embeddings

## 🚀 Usage

### Main Pipeline

```bash
# Run full pipeline
python main.py pipeline

# Or run steps individually
python main.py extract    # Extract text from PDFs
python main.py clean      # Clean extracted text
python main.py parse      # Parse questions into JSON
python main.py enhance    # Add metadata for quiz generation
```

### Utility Scripts

```bash
# Test text extraction (NO_OCR and OCR)
python scripts/test_extraction.py

# Convert images to text using OpenAI Vision API
python scripts/image_to_text.py

# Process limited images (testing)
python scripts/image_to_text.py --limit 5
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

### For NO_OCR PDFs:
1. PDF → Text extraction (pdfplumber)
2. Clean text
3. Parse questions
4. Enhance metadata

### For OCR PDFs (scanned):
1. PDF → Images (PyMuPDF)
2. Images → Text (OpenAI Vision API via `scripts/image_to_text.py`)
3. Clean text
4. Parse questions
5. Enhance metadata

### For NO_OCR PDFs (when using OpenAI Vision):
1. PDF → Images (PyMuPDF) - saved to `data/images/NO_OCR/`
2. Images → Text (OpenAI Vision API via `scripts/image_to_text.py`)
3. Clean text
4. Parse questions
5. Enhance metadata

## 📊 Output

Final JSON files are saved to `data/processed/` with:
- Questions with options
- Correct answers (when available)
- Topics and tags
- Difficulty scores
- Enhanced embeddings (400+ chars)

## 📝 Notes

- MDCAT papers are automatically skipped (only NET and FAST processed)
- Format-specific parsers handle different exam formats
- Enhanced embeddings include full context for better RAG retrieval
