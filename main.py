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
from src.text_cleaner import TextCleaner
from src.question_parser import QuestionParser
from src.enhance_simple import SimpleEnhancer


def setup_logging(verbose: bool = False):
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )


def extract_pdfs():
    """Step 1: Extract text from PDFs"""
    print("="*60)
    print("STEP 1: PDF TEXT EXTRACTION")
    print("="*60)
    print()
    
    extractor = PDFExtractor(
        input_dir="Past Papers",
        output_dir="Extracted Text"
    )
    
    stats = extractor.extract_all()
    extractor.print_summary(stats)
    
    return stats['successful'] > 0


def clean_text():
    """Step 2: Clean extracted text"""
    print("="*60)
    print("STEP 2: TEXT CLEANING")
    print("="*60)
    print()
    
    cleaner = TextCleaner(
        input_dir="Extracted Text",
        output_dir="Cleaned Text"
    )
    
    stats = cleaner.clean_all()
    cleaner.print_summary(stats)
    
    return stats['successful'] > 0


def parse_questions():
    """Step 3: Parse questions into JSON"""
    print("="*60)
    print("STEP 3: QUESTION PARSING")
    print("="*60)
    print()
    
    from pathlib import Path
    
    parser = QuestionParser()
    cleaned_dir = Path("Cleaned Text")
    output_dir = Path("Processed Data")
    
    if not cleaned_dir.exists():
        print(f"❌ Cleaned text directory not found: {cleaned_dir}")
        print("   Run 'python main.py clean' first")
        return False
    
    # Find all cleaned text files
    text_files = list(cleaned_dir.rglob("*.txt"))
    
    if not text_files:
        print(f"❌ No text files found in {cleaned_dir}")
        return False
    
    print(f"Found {len(text_files)} text files to parse\n")
    
    total_questions = 0
    successful = 0
    failed = 0
    
    for text_file in text_files:
        print(f"{'='*60}")
        print(f"Parsing: {text_file.relative_to(cleaned_dir)}")
        print(f"{'='*60}")
        
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            questions = parser.parse_questions_from_text(text, text_file.name)
            
            if questions:
                relative_path = text_file.relative_to(cleaned_dir)
                output_path = output_dir / relative_path.parent / f"{text_file.stem}.json"
                
                if parser.save_to_json(questions, output_path):
                    print(f"✅ Extracted {len(questions)} questions")
                    print(f"   Saved to: {output_path}")
                    
                    summary = parser.generate_summary(questions)
                    print(f"   Subjects: {summary['by_subject']}")
                    print(f"   With answers: {summary['with_answers']}/{len(questions)}")
                    print(f"   With solutions: {summary['with_solutions']}/{len(questions)}")
                    
                    total_questions += len(questions)
                    successful += 1
                else:
                    print(f"❌ Failed to save JSON")
                    failed += 1
            else:
                print(f"⚠️  No questions found")
                failed += 1
        except Exception as e:
            print(f"❌ Error: {e}")
            failed += 1
        
        print()
    
    print("="*60)
    print("PARSING SUMMARY")
    print("="*60)
    print(f"Files processed: {len(text_files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total questions extracted: {total_questions}")
    print(f"\n✅ JSON files saved to: {output_dir}")
    
    return successful > 0


def enhance_metadata():
    """Step 4: Enhance metadata for quiz generation"""
    print("="*60)
    print("STEP 4: METADATA ENHANCEMENT")
    print("="*60)
    print()
    
    enhancer = SimpleEnhancer()
    stats = enhancer.enhance_all("Processed Data")
    enhancer.print_summary(stats)
    
    return stats['successful'] > 0


def run_pipeline():
    """Run full pipeline"""
    print("\n" + "="*60)
    print("RUNNING FULL PIPELINE")
    print("="*60 + "\n")
    
    steps = [
        ("Extract PDFs", extract_pdfs),
        ("Clean Text", clean_text),
        ("Parse Questions", parse_questions),
        ("Enhance Metadata", enhance_metadata),
    ]
    
    for step_name, step_func in steps:
        print(f"\n▶ Starting: {step_name}")
        success = step_func()
        
        if not success:
            print(f"❌ Pipeline stopped at: {step_name}")
            return False
        
        print(f"✅ Completed: {step_name}")
    
    print("\n🎉 Pipeline completed successfully!")
    return True


def print_help():
    """Print help information"""
    print("""
📚 Past Papers Parsing Pipeline

Usage: python main.py <command> [options]

Commands:
  extract     Extract text from PDFs (Step 1)
  clean       Clean extracted text (Step 2)
  parse       Parse questions into JSON (Step 3)
  enhance     Add metadata for quiz generation (Step 4)
  pipeline    Run full pipeline (all steps)
  help        Show this help message

Options:
  -v, --verbose    Enable verbose logging

Examples:
  python main.py extract
  python main.py pipeline
  python main.py extract --verbose

Current Status:
  ✅ Step 1: PDF Extraction - READY
  ✅ Step 2: Text Cleaning - READY
  ✅ Step 3: Question Parsing - READY
  ✅ Step 4: Metadata Enhancement - READY
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
    if command == "extract":
        extract_pdfs()
    elif command == "clean":
        clean_text()
    elif command == "parse":
        parse_questions()
    elif command == "enhance":
        enhance_metadata()
    elif command == "pipeline":
        run_pipeline()
    elif command == "help" or command == "-h" or command == "--help":
        print_help()
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python main.py help' for usage information")


if __name__ == "__main__":
    main()

