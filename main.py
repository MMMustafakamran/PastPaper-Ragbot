#!/usr/bin/env python3
"""
Past Papers Processing Pipeline - Main Entry Point
Simplified workflow: Process files in Standard_text/
"""

import sys
import logging
from pathlib import Path

# Add processors to path
sys.path.insert(0, str(Path(__file__).parent))

from processors.mcq_processor import BatchProcessor
from processors.fast_processor import process_fast_papers

def setup_logging(verbose: bool = False):
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )

def process_all():
    """Process all files in Standard_text/"""
    print("="*60)
    print("PROCESSING STANDARD_TEXT FILES")
    print("="*60)
    print()
    
    # Process FAST papers first (if needed)
    print("[1/2] Processing FAST papers...")
    try:
        process_fast_papers()
        print("✓ FAST papers processed")
    except Exception as e:
        print(f"⚠ FAST processing error: {e}")
    
    print()
    
    # Process all MCQs
    print("[2/2] Processing all MCQ files...")
    processor = BatchProcessor(
        topics_file="Topics_net",
        output_dir="processed_data"
    )
    processor.process_directory("data/Standard_text")
    
    print("\n" + "="*60)
    print("✅ Processing complete!")
    print("="*60)

def print_help():
    """Print help information"""
    print("""
📚 Past Papers Processing Pipeline

Usage: python main.py [command]

Commands:
  process       Process all files in data/Standard_text/ (default)
  test          Run test processor
  help          Show this help message

Workflow:
  1. Extract OCR/NO_OCR → data/Standard_text/ (manual/scripts)
  2. Process Standard_text → processed_data/ (this script)

Examples:
  python main.py process
  python main.py test
""")

def main():
    """Main entry point"""
    args = sys.argv[1:]
    
    if not args or args[0] in ['-h', '--help', 'help']:
        print_help()
        return
    
    command = args[0]
    verbose = '-v' in args or '--verbose' in args
    
    setup_logging(verbose)
    
    if command == "process":
        process_all()
    elif command == "test":
        from processors.test_processor import main as test_main
        test_main()
    else:
        print(f"[ERROR] Unknown command: {command}")
        print_help()

if __name__ == "__main__":
    main()
