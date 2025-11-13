"""
LLM Text Cleaner using GPT-5 Nano
Cleans extracted text files by removing noise while preserving question structure
"""

import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


def load_config() -> str:
    """Load API key from config.json"""
    config_path = Path(__file__).parent.parent / "config" / "config.json"
    if not config_path.exists():
        config_path = Path(__file__).parent.parent / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"config.json not found. Expected at: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    api_key = config.get("apiKey")
    if not api_key or api_key == "your-openai-api-key-here":
        raise ValueError("Please set your OpenAI API key in config.json")
    
    return api_key


class LLMTextCleaner:
    """Clean text files using GPT-5 Nano"""
    
    def __init__(self, input_dir: str = "data/output", output_dir: str = "data/cleaned",
                 model: str = "gpt-5-nano"):
        """
        Initialize LLM text cleaner
        
        Args:
            input_dir: Directory containing text files to clean
            output_dir: Directory to save cleaned text
            model: OpenAI model to use (default: gpt-5-nano)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.model = model
        
        # Load API key and initialize client
        try:
            api_key = load_config()
            self.client = OpenAI(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def clean_text_with_llm(self, text: str, source_file: str = "") -> Tuple[str, Dict]:
        """
        Clean text using GPT-5 Nano
        
        Args:
            text: Raw text to clean
            source_file: Source filename for context
            
        Returns:
            Tuple of (cleaned_text, stats)
        """
        if not text.strip():
            return "", {'tokens_used': 0, 'processing_time': 0}
        
        start_time = time.time()
        
        # System prompt for cleaning
        system_prompt = """You are an expert at cleaning educational exam paper text while preserving question structure.

Your task is to clean the text by:
1. REMOVING noise:
   - URLs (https://, www., etc.)
   - Promotional content ("Download app", "Visit website", etc.)
   - Headers/footers ("Page X of Y", "Total MCQs", etc.)
   - Contact information (phone numbers, emails)
   - Watermarks and copyright notices
   - Instructions that are not part of questions ("Each question has four possible answers...")

2. PRESERVING important structure:
   - Question numbers (1), 2), Q.1, Q.2, etc.)
   - Option labels (A., B., C., D. or A), B), C), D))
   - Answer markers ((Correct), ✓, √)
   - Question text and option text
   - Mathematical notation and formulas
   - Answer key sections

3. NORMALIZING:
   - Remove excessive whitespace (keep single spaces)
   - Remove empty lines (keep one blank line between questions)
   - Preserve line breaks between questions and options

Return ONLY the cleaned text. No explanations or markdown formatting."""

        # User prompt with text
        user_prompt = f"""Clean this exam paper text:

{text}

Remove all noise (URLs, promotional content, headers, footers) while preserving:
- Question numbers and text
- Option labels and text
- Answer markers if present
- Mathematical notation
- Answer keys

Return the cleaned text only."""

        try:
            # GPT-5 Nano doesn't support custom temperature, only default (1)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_completion_tokens=8192,
                timeout=60.0
            )
            
            processing_time = time.time() - start_time
            
            # Extract cleaned text
            cleaned_text = response.choices[0].message.content.strip()
            
            # Get token usage
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
            
            stats = {
                'tokens_used': tokens_used,
                'processing_time': processing_time,
                'original_length': len(text),
                'cleaned_length': len(cleaned_text),
                'reduction_percentage': round((len(text) - len(cleaned_text)) / len(text) * 100, 2) if len(text) > 0 else 0
            }
            
            return cleaned_text, stats
            
        except Exception as e:
            logger.error(f"Failed to clean text with LLM: {e}")
            # Return original text if cleaning fails
            return text, {'tokens_used': 0, 'processing_time': 0, 'error': str(e)}
    
    def clean_text_file(self, text_path: Path) -> Tuple[bool, Dict]:
        """
        Clean a single text file
        
        Args:
            text_path: Path to text file
            
        Returns:
            Tuple of (success, stats)
        """
        logger.info(f"Cleaning: {text_path.relative_to(self.input_dir)}")
        
        try:
            # Read text file
            with open(text_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()
            
            if not raw_text.strip():
                logger.warning(f"Empty file: {text_path.name}")
                return False, {'error': 'empty_file'}
            
            # Clean text with LLM
            cleaned_text, clean_stats = self.clean_text_with_llm(raw_text, text_path.name)
            
            if not cleaned_text.strip():
                logger.warning(f"Cleaned text is empty: {text_path.name}")
                return False, {'error': 'cleaned_empty'}
            
            # Get output path
            output_path = self.get_output_path(text_path)
            
            # Save cleaned text
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
            
            logger.info(f"  ✓ Saved to: {output_path.relative_to(self.output_dir)}")
            logger.info(f"  ✓ Reduced by {clean_stats.get('reduction_percentage', 0):.1f}% "
                       f"({clean_stats.get('tokens_used', 0)} tokens, "
                       f"{clean_stats.get('processing_time', 0):.2f}s)")
            
            return True, clean_stats
            
        except Exception as e:
            logger.error(f"Failed to clean {text_path.name}: {e}")
            return False, {'error': str(e)}
    
    def get_output_path(self, text_path: Path) -> Path:
        """
        Generate output path maintaining directory structure
        
        Args:
            text_path: Original text file path
            
        Returns:
            Path for output cleaned text file
        """
        try:
            relative_path = text_path.relative_to(self.input_dir)
        except ValueError:
            relative_path = text_path.name
        
        output_path = self.output_dir / relative_path
        return output_path
    
    def find_text_files(self) -> List[Path]:
        """
        Find all text files in input directory recursively
        
        Returns:
            List of text file paths
        """
        if not self.input_dir.exists():
            logger.error(f"Input directory not found: {self.input_dir}")
            return []
        
        text_files = list(self.input_dir.rglob("*.txt"))
        logger.info(f"Found {len(text_files)} text files")
        return text_files
    
    def clean_all(self, limit: Optional[int] = None, skip: int = 0) -> dict:
        """
        Clean all text files in input directory
        
        Args:
            limit: Maximum number of files to process (None for all)
            skip: Number of files to skip from the beginning
            
        Returns:
            Dictionary with cleaning statistics
        """
        text_files = self.find_text_files()
        
        if not text_files:
            logger.warning("No text files found")
            return {
                'total_files': 0,
                'successful': 0,
                'failed': 0,
                'total_tokens': 0,
                'total_time': 0,
                'files': []
            }
        
        # Apply skip and limit
        if skip > 0:
            text_files = text_files[skip:]
        if limit:
            text_files = text_files[:limit]
        
        stats = {
            'total_files': len(text_files),
            'successful': 0,
            'failed': 0,
            'total_tokens': 0,
            'total_time': 0,
            'total_chars_removed': 0,
            'files': []
        }
        
        for i, text_path in enumerate(text_files, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"[{i}/{len(text_files)}] Processing: {text_path.relative_to(self.input_dir)}")
            logger.info(f"{'='*60}")
            
            success, file_stats = self.clean_text_file(text_path)
            
            if success:
                stats['successful'] += 1
                stats['total_tokens'] += file_stats.get('tokens_used', 0)
                stats['total_time'] += file_stats.get('processing_time', 0)
                stats['total_chars_removed'] += file_stats.get('original_length', 0) - file_stats.get('cleaned_length', 0)
                
                stats['files'].append({
                    'file': str(text_path),
                    'status': 'success',
                    'stats': file_stats
                })
            else:
                stats['failed'] += 1
                stats['files'].append({
                    'file': str(text_path),
                    'status': 'failed',
                    'error': file_stats.get('error', 'unknown')
                })
            
            # Small delay to avoid rate limiting
            if i < len(text_files):
                time.sleep(0.5)
        
        return stats
    
    def print_summary(self, stats: dict):
        """Print cleaning summary"""
        print("\n" + "="*60)
        print("LLM TEXT CLEANING SUMMARY")
        print("="*60)
        print(f"Total files processed: {stats['total_files']}")
        print(f"Successful: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        
        if stats['successful'] > 0:
            print(f"\n[SUCCESS] Cleaned text saved to: {self.output_dir}")
            print(f"\nStatistics:")
            print(f"  • Total tokens used: {stats['total_tokens']:,}")
            print(f"  • Total processing time: {stats['total_time']:.2f}s")
            print(f"  • Average time per file: {stats['total_time']/stats['successful']:.2f}s")
            print(f"  • Total characters removed: {stats['total_chars_removed']:,}")
            
            if stats['total_tokens'] > 0:
                print(f"\nCost Estimate (GPT-5 Nano):")
                # GPT-5 Nano pricing (approximate)
                cost_per_1k_tokens = 0.001  # $0.001 per 1K tokens (example)
                estimated_cost = (stats['total_tokens'] / 1000) * cost_per_1k_tokens
                print(f"  • Estimated cost: ${estimated_cost:.4f}")
        
        if stats['failed'] > 0:
            print("\n[FAILED] Failed files:")
            for file_info in stats['files']:
                if file_info['status'] != 'success':
                    file_name = Path(file_info['file']).name
                    error = file_info.get('error', 'unknown')
                    print(f"  [-] {file_name}: {error}")


def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean text files using GPT-5 Nano")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/output",
        help="Input directory containing text files (default: data/output)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/cleaned",
        help="Output directory for cleaned text (default: data/cleaned)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of files to process (default: all)"
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Number of files to skip (default: 0)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-5-nano",
        help="OpenAI model to use (default: gpt-5-nano)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )
    
    # Create cleaner
    cleaner = LLMTextCleaner(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        model=args.model
    )
    
    # Clean all files
    stats = cleaner.clean_all(limit=args.limit, skip=args.skip)
    
    # Print summary
    cleaner.print_summary(stats)


if __name__ == "__main__":
    main()

