#!/usr/bin/env python3
"""
Past Papers Parsing Pipeline - Main Entry Point
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pdf_extractor import PDFExtractor
from src.question_parser import QuestionParser
from src.enhance_simple import SimpleEnhancer

# Note: TextCleaner removed - cleaning will be done in LLM preprocessor
# Note: OCR extraction handled separately via scripts/image_to_text.py


def setup_logging(verbose: bool = False):
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )


def extract_noocr():
    """Step 1: Extract text from NO_OCR PDFs"""
    print("="*60)
    print("STEP 1: NO_OCR PDF TEXT EXTRACTION")
    print("="*60)
    print()
    
    extractor = PDFExtractor(
        input_dir="data/input/Solved_PastPapers/NO_OCR",
        output_dir="data/output/NO_OCR"
    )
    
    stats = extractor.extract_all()
    extractor.print_summary(stats)
    
    return stats['successful'] > 0


def clean_text_llm():
    """Step 2: Clean text using LLM (GPT-5 Nano)"""
    print("="*60)
    print("STEP 2: LLM TEXT CLEANING")
    print("="*60)
    print()
    
    from src.text_cleaner_llm import LLMTextCleaner
    
    cleaner = LLMTextCleaner(
        input_dir="data/output",
        output_dir="data/cleaned"
    )
    
    stats = cleaner.clean_all()
    cleaner.print_summary(stats)
    
    return stats['successful'] > 0


def preprocess_llm():
    """Step 3: LLM Preprocessing - Convert text to JSON"""
    print("="*60)
    print("STEP 3: LLM PREPROCESSING")
    print("="*60)
    print()
    
    # TODO: Implement LLM preprocessor
    # This will use LLM to convert cleaned text to JSON
    # Input: data/cleaned/ (both NO_OCR and OCR)
    # Output: data/processed/
    
    print("[INFO] LLM preprocessing not yet implemented")
    print("       Will convert text files to structured JSON")
    print("       Input: data/cleaned/NO_OCR/ and data/cleaned/OCR/")
    print("       Output: data/processed/")
    return False


def enhance_metadata():
    """Step 4: Enhance metadata for quiz generation"""
    print("="*60)
    print("STEP 4: METADATA ENHANCEMENT")
    print("="*60)
    print()
    
    enhancer = SimpleEnhancer()
    stats = enhancer.enhance_all("data/processed")
    enhancer.print_summary(stats)
    
    return stats['successful'] > 0


def run_pipeline():
    """Run full pipeline"""
    print("\n" + "="*60)
    print("RUNNING FULL PIPELINE")
    print("="*60 + "\n")
    
    steps = [
        ("Extract NO_OCR PDFs", extract_noocr),
        ("Clean Text (LLM)", clean_text_llm),
        ("LLM Preprocessing", preprocess_llm),
        ("Enhance Metadata", enhance_metadata),
    ]
    
    for step_name, step_func in steps:
        print(f"\n[STARTING] {step_name}")
        success = step_func()
        
        if not success:
            print(f"[FAILED] Pipeline stopped at: {step_name}")
            return False
        
        print(f"[SUCCESS] Completed: {step_name}")
    
    print("\n[SUCCESS] Pipeline completed successfully!")
    return True


def print_help():
    """Print help information"""
    print("""
📚 Past Papers Parsing Pipeline

Usage: python main.py <command> [options]

Commands:
  extract-noocr    Extract text from NO_OCR PDFs (Step 1)
  clean-llm        Clean text using GPT-5 Nano (Step 2)
  preprocess-llm   LLM preprocessing: text → JSON (Step 3)
  enhance          Add metadata for quiz generation (Step 4)
  pipeline         Run full pipeline (all steps)
  help             Show this help message

OCR Extraction:
  OCR PDFs are processed separately:
  python scripts/image_to_text.py --filter "NET"
  python scripts/image_to_text.py --filter "FAST"

Options:
  -v, --verbose    Enable verbose logging

Examples:
  python main.py extract-noocr
  python main.py pipeline
  python main.py extract-noocr --verbose

Current Status:
  [READY] Step 1: NO_OCR PDF Extraction
  [READY] Step 2: LLM Text Cleaning (GPT-5 Nano)
  [TODO]  Step 3: LLM Preprocessing (text → JSON)
  [READY] Step 4: Metadata Enhancement
""")


def main():
    """Main entry point"""
    # Parse arguments
    args = sys.argv[1:]
    
    if not args:
        print_help()
        return
    
    command = args[0]
    verbose = '-v' in args or '--verbose' in args
    
    # Setup logging
    setup_logging(verbose)
    
    # Route commands
    if command == "extract-noocr":
        extract_noocr()
    elif command == "clean-llm":
        clean_text_llm()
    elif command == "preprocess-llm":
        preprocess_llm()
    elif command == "enhance":
        enhance_metadata()
    elif command == "pipeline":
        run_pipeline()
    elif command == "help" or command == "-h" or command == "--help":
        print_help()
    else:
        print(f"[ERROR] Unknown command: {command}")
        print("Run 'python main.py help' for usage information")


if __name__ == "__main__":
    main()

