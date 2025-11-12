# Data Structure Documentation

## Overview

This document explains the data folder structure and workflow.

## Directory Structure

```
data/
├── input/                     # Source PDF files
│   └── Solved_PastPapers/
│       ├── NO_OCR/           # PDFs with selectable text
│       │   ├── FAST/
│       │   └── NET/
│       └── OCR/              # Scanned PDFs (image-based)
│           ├── FAST/
│           └── NET/
│
├── images/                    # PDF pages converted to PNG images
│   ├── NO_OCR/               # Images from NO_OCR PDFs
│   │   ├── FAST/
│   │   │   └── [PDF_NAME]/
│   │   │       ├── page_001.png
│   │   │       ├── page_002.png
│   │   │       └── ...
│   │   └── NET/
│   │       └── [PDF_NAME]/
│   │           ├── page_001.png
│   │           └── ...
│   └── OCR/                  # Images from OCR PDFs (future)
│       ├── FAST/
│       └── NET/
│
├── extracted/                 # Text extracted from PDFs
│   ├── NO_OCR/               # Text from NO_OCR PDFs (pdfplumber)
│   │   ├── FAST/
│   │   └── NET/
│   └── OCR/                  # Text from OCR PDFs (Tesseract/OpenAI Vision)
│       ├── FAST/
│       └── NET/
│
├── output/                    # Text extracted from images via OpenAI Vision
│   ├── NO_OCR/               # Text from NO_OCR images
│   │   ├── FAST/
│   │   │   └── [PDF_NAME].txt
│   │   └── NET/
│   │       └── [PDF_NAME].txt
│   └── OCR/                  # Text from OCR images
│       ├── FAST/
│       └── NET/
│
├── cleaned/                   # Cleaned text (removed noise, URLs, etc.)
│   ├── FAST/
│   └── NET/
│
└── processed/                 # Final structured JSON files
    ├── FAST/
    └── NET/
```

## Workflow

### Option 1: Direct Text Extraction (NO_OCR PDFs)
```
PDF (NO_OCR) → pdfplumber → Extracted Text → Clean → Parse → JSON
```

### Option 2: Image-based Extraction (NO_OCR or OCR PDFs)
```
PDF → Images → OpenAI Vision API → Output Text → Clean → Parse → JSON
```

## Notes

- **NO_OCR images**: These are PDFs with selectable text that have been converted to images for processing with OpenAI Vision API (often more accurate than pdfplumber)
- **OCR images**: These are scanned PDFs that need OCR processing
- The `output/` folder contains text extracted from images using OpenAI Vision API
- The `extracted/` folder contains text extracted directly from PDFs using pdfplumber or Tesseract

