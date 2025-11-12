# main.py Context

## Purpose
Main entry point for past papers parsing pipeline. Converts PDFs → JSON for RAG system.

## Pipeline Flow
1. **Extract** - PDF → Text (pdfplumber for NO_OCR, Google Vision for OCR)
2. **Clean** - Remove promotional content, URLs, headers
3. **Parse** - Extract questions, options, metadata → JSON
4. **Enhance** - Add topics, tags, difficulty, embeddings

## Key Functions
- `extract_pdfs()` - Step 1: Extract text from PDFs in `PastPapers/Solved_PastPapers`
- `clean_text()` - Step 2: Clean extracted text
- `parse_questions()` - Step 3: Parse questions into JSON
- `enhance_metadata()` - Step 4: Add metadata for quiz generation
- `run_pipeline()` - Execute all steps sequentially

## Usage
```bash
python main.py extract    # Step 1 only
python main.py clean       # Step 2 only
python main.py parse       # Step 3 only
python main.py enhance     # Step 4 only
python main.py pipeline    # All steps
```

## Input/Output
- **Input**: `PastPapers/Solved_PastPapers/` (NO_OCR/ and OCR/ subfolders)
- **Output**: 
  - `Extracted Text/` - Raw text files
  - `Cleaned Text/` - Cleaned text files
  - `Processed Data/` - Final JSON files

## Dependencies
- `src.pdf_extractor` - PDF text extraction
- `src.text_cleaner` - Text cleaning
- `src.question_parser` - Question parsing
- `src.enhance_simple` - Metadata enhancement

