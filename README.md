# Past Papers Parsing Pipeline

A modular data extraction pipeline for converting exam past papers (PDFs) into structured JSON format for RAG (Retrieval Augmented Generation) applications.

## 🎯 Goal

Extract questions from past papers PDFs and prepare them for vector database storage and semantic search.

## 📋 Pipeline Steps

1. **Extract** - Extract text from PDFs in `Past Papers/` folder
2. **Clean** - Remove promotional content, URLs, and noise
3. **Parse** - Extract questions, options, and metadata
4. **Export** - Save as JSON with rich metadata for RAG

## 📁 Directory Structure

```
Past Papers/          # Input PDFs organized by exam type
Extracted Text/       # Raw extracted text files
Processed Data/       # Final JSON outputs with metadata
```

## 🚀 Usage

```bash
# Step 1: Extract text from PDFs
python main.py extract

# Step 2: Clean extracted text
python main.py clean

# Step 3: Parse questions into JSON
python main.py parse

# Or run full pipeline
python main.py pipeline
```

## 📦 Requirements

- Python 3.7+
- pdfplumber for PDF extraction
- No OCR required (only selectable text PDFs)
