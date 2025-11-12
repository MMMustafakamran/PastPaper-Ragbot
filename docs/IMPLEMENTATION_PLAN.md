# Implementation Plan: OCR Integration & Format-Specific Parsers

## Overview
Implement Google Cloud Vision API for OCR folder PDFs, create format-specific parsers for NET/MDCAT/FAST papers, and enhance the dataset quality for RAG system.

## Phase 1: Google Cloud Vision API Integration

### 1.1 Update Dependencies
- **File**: `requirements.txt`
- **Action**: Add `google-cloud-vision==3.4.5`
- **Note**: Verify PyPDF2 is present (already in requirements)

### 1.2 Create OCR Extractor Module
- **File**: `src/ocr_extractor.py` (NEW)
- **Class**: `GoogleVisionOCR`
- **Methods**:
  - `__init__(credentials_path: str)` - Initialize with service account key
  - `extract_text_from_pdf(pdf_path: Path) -> Tuple[str, bool]` - Extract using Google Vision API
  - `_convert_pdf_to_images(pdf_path: Path) -> List[bytes]` - Convert PDF pages to image bytes
  - `_extract_text_from_image(image_bytes: bytes) -> str` - Extract text from single image
  - Handle API rate limits and errors
  - Progress logging for multi-page PDFs

### 1.3 Update keys.json
- **File**: `keys.json`
- **Action**: Add `GOOGLE_CLOUD_VISION_CREDENTIALS_PATH` pointing to service account JSON file
- **Alternative**: Use environment variable `GOOGLE_APPLICATION_CREDENTIALS`

## Phase 2: Enhanced PDF Extractor

### 2.1 Modify PDFExtractor Class
- **File**: `src/pdf_extractor.py`
- **Changes**:
  - Add import: `from src.ocr_extractor import GoogleVisionOCR`
  - Add method: `_should_use_ocr(pdf_path: Path) -> bool`
    - Check if "OCR" in path parts
    - Return True if PDF is in OCR subfolder
  - Modify `extract_text_from_pdf()`:
    ```python
    if self._should_use_ocr(pdf_path):
        ocr = GoogleVisionOCR(credentials_path)
        return ocr.extract_text_from_pdf(pdf_path)
    else:
        # Existing pdfplumber code
    ```
  - Update `extract_all()` stats to track:
    - `ocr_extracted`: count of OCR files
    - `text_extracted`: count of text files

### 2.2 Update Main Pipeline
- **File**: `main.py`
- **Function**: `extract_pdfs()`
- **Changes**:
  - Keep `input_dir="PastPapers/Solved_PastPapers"`
  - Extractor automatically detects OCR vs NO_OCR folders
  - Add logging: `"Using OCR for: {file}"` or `"Using text extraction for: {file}"`

## Phase 3: Format-Specific Parsers

### 3.1 Create Base Parser Interface
- **File**: `src/parsers/base_parser.py` (NEW)
- **Class**: `BasePaperParser` (abstract base class)
- **Methods**:
  - `parse_questions(text: str, source_file: str) -> List[Question]` (abstract)
  - `parse_answer_key(text: str) -> Dict[int, str]` (abstract)
  - `detect_format(text: str) -> bool` (abstract) - Check if parser matches format
  - `clean_text(text: str) -> str` - Common cleaning utilities

### 3.2 NET Paper Parser
- **File**: `src/parsers/net_parser.py` (NEW)
- **Format Analysis** (from extracted text):
  - Questions: `1)`, `2)`, `3)` (number with parenthesis)
  - Options: `A.`, `B.`, `C.`, `D.` (dot notation, each on separate line)
  - Answers: `(Correct)` marker after option text
  - Example: 
    ```
    1) Question text?
    A. Option 1
    B. Option 2 (Correct)
    C. Option 3
    D. Option 4
    ```
- **Implementation**:
  - `parse_questions()` - Extract questions with (Correct) markers
  - `extract_correct_answer(option_text: str) -> Tuple[str, Optional[str]]`
    - Find `(Correct)` marker
    - Return (cleaned_text, answer_label)
  - `clean_option_text()` - Remove (Correct) from option text
  - Handle multi-line questions and options
  - Extract year tags like `(NET 1 2015)` if present

### 3.3 MDCAT Paper Parser
- **File**: `src/parsers/mdcat_parser.py` (NEW)
- **Format Analysis** (from extracted text):
  - Questions: `Q.1`, `Q.2` (Q. prefix with dot)
  - Options: `A)`, `B)`, `C)`, `D)` (parenthesis notation)
  - **CRITICAL**: Options on same line: `A) text1. C) text2.` and `B) text3. D) text4.`
  - Answers: Usually in separate answer key section at end
  - Example:
    ```
    Q.1 Question text?
    A) Option 1. C) Option 3.
    B) Option 2. D) Option 4.
    ```
- **Implementation**:
  - `parse_questions()` - Handle inline options format
  - `parse_inline_options(line: str) -> List[Dict]`
    - Split "A) text1. C) text2." into:
      - `[{"label": "A", "text": "text1"}, {"label": "C", "text": "text2"}]`
    - Use regex: `r'([A-D])\)\s*([^A-D]+?)(?=\s+[A-D]\)|$)'`
  - `parse_answer_key_section(text: str) -> Dict[int, str]`
    - Find "ANSWER KEY" section
    - Extract patterns: `1. C`, `1) C`, `1: C`
    - Return `{question_number: answer_label}`
  - Handle answer keys in separate files if needed

### 3.4 FAST Paper Parser
- **File**: `src/parsers/fast_parser.py` (NEW)
- **Format Analysis**: (To be determined after OCR extraction)
  - First: Extract text from FAST OCR PDF
  - Analyze: Question numbering pattern, option format, answer format
  - Implement based on actual format found
- **Placeholder Implementation**:
  - Start with generic parser
  - Add format-specific logic after analysis

### 3.5 Parser Factory
- **File**: `src/parsers/parser_factory.py` (NEW)
- **Class**: `ParserFactory`
- **Method**: `get_parser(text: str, filename: str) -> BasePaperParser`
  - Try each parser's `detect_format()`:
    1. NET parser - check for `^\d+\)` and `\(Correct\)`
    2. MDCAT parser - check for `Q\.\d+` and inline options pattern
    3. FAST parser - check for FAST-specific patterns
  - Return first matching parser
  - Fallback: Return generic parser (existing QuestionParser logic)

### 3.6 Create Parsers Package
- **File**: `src/parsers/__init__.py` (NEW)
- **Exports**:
  ```python
  from .base_parser import BasePaperParser
  from .net_parser import NETPaperParser
  from .mdcat_parser import MDCATPaperParser
  from .fast_parser import FASTPaperParser
  from .parser_factory import ParserFactory
  ```

### 3.7 Update QuestionParser
- **File**: `src/question_parser.py`
- **Modify**: `parse_questions_from_text()`
  - Use `ParserFactory.get_parser()` to get appropriate parser
  - If format-specific parser found:
    - Delegate to format-specific parser
    - Merge results with existing metadata extraction
  - Else:
    - Use existing generic parsing logic as fallback

## Phase 4: Answer Key Extraction

### 4.1 Answer Key Matcher
- **File**: `src/answer_key_matcher.py` (NEW)
- **Class**: `AnswerKeyMatcher`
- **Methods**:
  - `match_answers_to_questions(questions: List[Question], answer_key: Dict[int, str]) -> List[Question]`
    - Match answer_key by question_number
    - Set `question.correct_answer = answer_key[question_number]`
    - Mark `opt['is_correct'] = True` for correct option
  - `validate_answers(questions: List[Question]) -> Dict[str, Any]`
    - Check answer labels match available options
    - Return stats: total, with_answers, invalid_answers list

### 4.2 Answer Key Patterns
- Support multiple formats:
  - **Inline**: `(Correct)` markers (NET format) - handled by parser
  - **End-of-paper**: 
    ```
    ANSWER KEY
    1. C    11. B    21. A
    2. D    12. C    22. D
    ```
  - **Separate file**: Look for `*_answers.pdf`, `*_key.pdf`, `*_solutions.pdf`
  - **Next to options**: Answers embedded in question text (rare)

### 4.3 Answer Key File Finder
- **File**: `src/answer_key_matcher.py` (add method)
- **Method**: `find_answer_key_file(question_file: Path) -> Optional[Path]`
  - Check same directory for answer key files
  - Patterns: `{base_name}_answers*`, `{base_name}_key*`
  - Return first match or None

## Phase 5: Enhanced Embedding Generation

### 5.1 Enhanced Embedding Generator
- **File**: `src/enhancers/embedding_generator.py` (NEW)
- **Class**: `EnhancedEmbeddingGenerator`
- **Method**: `generate_comprehensive_embedding(question: Question) -> str`
  - **Target**: 400+ characters with full context
  - **Format**:
    ```
    Subject: Physics | Topic: Modern Physics | Difficulty: Medium | 
    Question: When a helium atom loses an electron, it becomes: | 
    Options: A) An alpha particle | B) Proton | C) A positive helium ion | D) A negative helium ion | 
    Concepts: atomic structure, electron, ion, alpha particle | 
    Answer: C) A positive helium ion | 
    Source: MDCAT 2008
    ```
  - Include ALL options (not just question text)
  - Include answer if available
  - Include concepts/tags
  - Include source metadata

### 5.2 Create Enhancers Package
- **File**: `src/enhancers/__init__.py` (NEW)
- **Exports**: `from .embedding_generator import EnhancedEmbeddingGenerator`

### 5.3 Update SimpleEnhancer
- **File**: `src/enhance_simple.py`
- **Modify**: `enhance_question()` method
  - Import: `from src.enhancers import EnhancedEmbeddingGenerator`
  - Replace current `embedding_text` generation with:
    ```python
    generator = EnhancedEmbeddingGenerator()
    question['embedding_text'] = generator.generate_comprehensive_embedding(question)
    ```
  - Keep existing topic classification and difficulty scoring

## Phase 6: Pipeline Updates

### 6.1 Update Main Pipeline
- **File**: `main.py`
- **Function**: `extract_pdfs()`
  - Ensure processes both NO_OCR and OCR folders
  - Add progress indicators for OCR (slower processing)
  - Update statistics to show:
    - `ocr_files: X`
    - `text_files: Y`
    - `ocr_successful: X1`
    - `text_successful: Y1`

### 6.2 Error Handling
- **File**: `src/ocr_extractor.py`
- Add try-catch for:
  - Google Vision API rate limiting (429 errors)
  - Authentication errors (401, 403)
  - Invalid PDF format
  - Network errors
  - Large file size limits
- **Fallback**: Log error, return empty string, continue with other files

### 6.3 Logging Enhancements
- Add detailed logging:
  - `[OCR] Processing: {filename}`
  - `[TEXT] Processing: {filename}`
  - `[OCR] Page {n}/{total} extracted`
  - `[ERROR] OCR failed: {reason}`

## Phase 7: Testing & Validation

### 7.1 Test OCR Extraction
- **Test File 1**: `OCR/NET/497992392-NUST-NET-Solved-MCQs.pdf`
  - Verify text extraction quality
  - Check format matches expected NET format
  - Verify (Correct) markers are present
- **Test File 2**: `OCR/FAST/FAST ENTRY TEST PAST PAPERS PLSPOT_watermark.pdf`
  - Verify text extraction (should get actual questions, not just watermarks)
  - Analyze format for FAST parser implementation

### 7.2 Test Format Parsers
- **NET Parser**:
  - Test on extracted NET text
  - Verify (Correct) markers extracted
  - Verify correct_answer populated
  - Verify options cleaned (no (Correct) in text)
- **MDCAT Parser**:
  - Test on extracted MDCAT text
  - Verify inline options split correctly
  - Verify answer key extraction if present
  - Test malformed options fix

### 7.3 Validate Output Quality
- **Metrics to Check**:
  - ✅ 0% malformed options (no "A) text1. C) text2" in single option)
  - ✅ 90%+ questions with `correct_answer` populated
  - ✅ Average embedding text length > 400 characters
  - ✅ <30% questions labeled as "general" topic
  - ✅ All format-specific parsers working independently

### 7.4 Create Validation Script
- **File**: `tools/validate_dataset.py` (NEW)
- **Function**: Check output JSON quality
  - Count malformed options
  - Count missing answers
  - Calculate average embedding length
  - Generate quality report

## File Structure After Implementation

```
src/
├── pdf_extractor.py (MODIFIED - add OCR detection)
├── ocr_extractor.py (NEW - Google Vision API)
├── answer_key_matcher.py (NEW)
├── question_parser.py (MODIFIED - use parser factory)
├── enhance_simple.py (MODIFIED - use enhanced embeddings)
├── parsers/
│   ├── __init__.py (NEW)
│   ├── base_parser.py (NEW)
│   ├── net_parser.py (NEW)
│   ├── mdcat_parser.py (NEW)
│   ├── fast_parser.py (NEW)
│   └── parser_factory.py (NEW)
└── enhancers/
    ├── __init__.py (NEW)
    └── embedding_generator.py (NEW)

tools/
└── validate_dataset.py (NEW)

requirements.txt (MODIFIED - add google-cloud-vision)
keys.json (MODIFIED - add GOOGLE_CLOUD_VISION_CREDENTIALS_PATH)
main.py (MODIFIED - update extract_pdfs)
```

## Implementation Order

1. **Phase 1**: Google Cloud Vision API setup (OCR extractor)
2. **Phase 2**: Modify PDFExtractor to use OCR for OCR folder
3. **Phase 3.2**: Create NET parser (easiest - has inline answers)
4. **Phase 3.3**: Create MDCAT parser (fixes malformed options)
5. **Phase 3.4**: Analyze FAST format and create parser
6. **Phase 4**: Answer key matching
7. **Phase 5**: Enhanced embeddings
8. **Phase 6**: Pipeline integration
9. **Phase 7**: Testing and validation

## Success Criteria

1. ✅ OCR folder PDFs processed with Google Cloud Vision API
2. ✅ NO_OCR folder PDFs processed with pdfplumber (unchanged)
3. ✅ NET papers parsed with (Correct) markers extracted correctly
4. ✅ MDCAT papers parsed with inline options split correctly (0% malformed)
5. ✅ FAST papers parsed (format determined and implemented)
6. ✅ 90%+ questions with correct_answer populated
7. ✅ Average embedding text length > 400 characters
8. ✅ All format-specific parsers working independently
9. ✅ Answer keys matched from various sources (inline, end-of-paper, separate files)

## Notes

- **Google Cloud Vision API Setup**:
  - Requires service account JSON key file
  - Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable OR
  - Pass credentials path to `GoogleVisionOCR` constructor
  - Free tier: 1,000 pages/month, then $1.50 per 1,000 pages

- **OCR Processing**:
  - Slower than text extraction - add progress indicators
  - Test with small batch first to verify API setup
  - Handle rate limits gracefully

- **Format-Specific Parsers**:
  - Each parser is independent and extensible
  - Easy to add new formats in future
  - Factory pattern allows automatic format detection

- **Backward Compatibility**:
  - Keep existing pdfplumber extraction for NO_OCR folder
  - Existing QuestionParser logic as fallback
  - No breaking changes to current pipeline

