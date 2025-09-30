"""
Text Cleaner
Removes noise, promotional content, and URLs from extracted text
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class TextCleaner:
    """Clean extracted text by removing noise and promotional content"""
    
    def __init__(self, input_dir: str = "Extracted Text", output_dir: str = "Cleaned Text"):
        """
        Initialize text cleaner
        
        Args:
            input_dir: Directory containing extracted text files
            output_dir: Directory to save cleaned text
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Compile regex patterns once for performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile all regex patterns for efficient processing"""
        
        # Promotional content patterns
        self.promotional_patterns = [
            re.compile(r'TO Order.*?(?:Whats App|WhatsApp).*?\d{4}-?\d{7}', re.IGNORECASE),
            re.compile(r'ALL MDCAT TOPPERS RECOMMENDS.*', re.IGNORECASE),
            re.compile(r'YOU MUST PRACTICE BOOK.*', re.IGNORECASE),
            re.compile(r'MDCAT PAST PAPERS.*WITH ANSWER KEY IS VERY IMPORTANT', re.IGNORECASE),
            re.compile(r'Download.*?App.*?(?:Play Store|App Store)', re.IGNORECASE),
            re.compile(r'For more.*?visit.*', re.IGNORECASE),
            re.compile(r'Join our.*?(?:WhatsApp|Facebook|group)', re.IGNORECASE),
            re.compile(r'Subscribe.*?(?:channel|content)', re.IGNORECASE),
            re.compile(r'MOCK TEST BY ONLINE ACADEMY.*', re.IGNORECASE),
        ]
        
        # URL and website patterns
        self.url_patterns = [
            re.compile(r'www\.[a-zA-Z0-9-]+\.com(?:/[^\s]*)?', re.IGNORECASE),
            re.compile(r'https?://[^\s]+', re.IGNORECASE),
            re.compile(r'[a-zA-Z0-9-]+\.(?:com|net|org|edu|pk)(?:/[^\s]*)?', re.IGNORECASE),
        ]
        
        # Contact information patterns
        self.contact_patterns = [
            re.compile(r'(?:Whats App|WhatsApp|Contact|Helpline|Call)\s*:?\s*\d{4}-?\d{7}', re.IGNORECASE),
            re.compile(r'\+92[-\s]?\d{3}[-\s]?\d{7}', re.IGNORECASE),
            re.compile(r'\b0\d{3}[-\s]?\d{7}\b', re.IGNORECASE),
            re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', re.IGNORECASE),
        ]
        
        # Header/Footer/Instructions patterns
        self.header_footer_patterns = [
            re.compile(r'^Page \d+ of \d+\s*$', re.IGNORECASE),
            re.compile(r'^Total MCQs?:\s*\d+.*Max\.?\s*Marks?:\s*\d+\s*$', re.IGNORECASE),
            re.compile(r'^ENTRANCE TEST\s*-\s*\d{4}\s*$', re.IGNORECASE),
            re.compile(r'^Instructions?:\s*$', re.IGNORECASE),
            re.compile(r'^Time Allowed:\s*\d+.*$', re.IGNORECASE),
            re.compile(r'^For F\.Sc\..*Students Only\s*$', re.IGNORECASE),
            re.compile(r'^[ivxIVX]+\.\s+[A-Z].*(?:instruction|prohibited|required).*', re.IGNORECASE),
            re.compile(r'^Total Time:.*Total Question:.*$', re.IGNORECASE),
            re.compile(r'NIVERSITY OF.*EALTH.*CIENCES', re.IGNORECASE),  # Typo in original: UNIVERSITY
            re.compile(r'^\(UHS\),\s*L?AHORE\s*$', re.IGNORECASE),
            re.compile(r'^M\s*C\s*A\s*T.*(?:MCAT|TEST)\s*$', re.IGNORECASE),
            re.compile(r'^EDICAL.*OLLEGE.*PTITUDE.*EST\s*$', re.IGNORECASE),
        ]
        
        # Exam metadata patterns (to remove or clean)
        self.metadata_patterns = [
            re.compile(r'COMPULSORY QUESTION FOR IDENTIFICATION', re.IGNORECASE),
            re.compile(r'Q-ID\..*What is the color of your Question Paper.*', re.IGNORECASE | re.DOTALL),
            re.compile(r'Fill the Circle Corresponding.*', re.IGNORECASE),
        ]
        
        # Watermark patterns
        self.watermark_patterns = [
            re.compile(r'Prepared by.*?educatedzone', re.IGNORECASE),
            re.compile(r'Copyright.*?\d{4}', re.IGNORECASE),
            re.compile(r'All rights reserved', re.IGNORECASE),
        ]
    
    def clean_line(self, line: str) -> str:
        """
        Clean a single line by removing noise patterns
        
        Args:
            line: Line to clean
            
        Returns:
            Cleaned line or empty string if line should be removed
        """
        original_line = line.strip()
        
        if not original_line:
            return ""
        
        # Check if entire line matches promotional patterns
        for pattern in self.promotional_patterns:
            if pattern.search(original_line):
                logger.debug(f"Removed promotional: {original_line[:50]}...")
                return ""
        
        # Check if entire line matches header/footer patterns
        for pattern in self.header_footer_patterns:
            if pattern.match(original_line):
                logger.debug(f"Removed header/footer: {original_line[:50]}...")
                return ""
        
        # Check metadata patterns
        for pattern in self.metadata_patterns:
            if pattern.search(original_line):
                logger.debug(f"Removed metadata: {original_line[:50]}...")
                return ""
        
        # Remove URLs from line (inline removal)
        cleaned = original_line
        for pattern in self.url_patterns:
            cleaned = pattern.sub('', cleaned)
        
        # Remove contact info from line
        for pattern in self.contact_patterns:
            cleaned = pattern.sub('', cleaned)
        
        # Remove watermarks
        for pattern in self.watermark_patterns:
            cleaned = pattern.sub('', cleaned)
        
        cleaned = cleaned.strip()
        
        # If cleaning removed everything, return empty
        if not cleaned:
            return ""
        
        return cleaned
    
    def remove_section_markers(self, text: str) -> str:
        """
        Remove section markers that might appear alone on lines
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        lines = text.split('\n')
        cleaned_lines = []
        
        section_markers = [
            r'^PHYSICS\s*$',
            r'^CHEMISTRY\s*$',
            r'^BIOLOGY\s*$',
            r'^ENGLISH\s*$',
            r'^MATHEMATICS\s*$',
            r'^LOGICAL REASONING\s*$',
            r'^NET\s*[-–]\s*MATHEMATICS SECTION\s*$',
            r'^\(NET\)\s*$',
        ]
        
        section_patterns = [re.compile(p, re.IGNORECASE) for p in section_markers]
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if line is just a section marker
            is_section_marker = False
            for pattern in section_patterns:
                if pattern.match(line_stripped):
                    is_section_marker = True
                    logger.debug(f"Removed section marker: {line_stripped}")
                    break
            
            if not is_section_marker and line_stripped:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def clean_whitespace(self, text: str) -> str:
        """
        Clean excessive whitespace while preserving structure
        
        Args:
            text: Text to clean
            
        Returns:
            Text with normalized whitespace
        """
        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)
        
        # Replace more than 2 consecutive newlines with 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove trailing whitespace from lines
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]
        
        return '\n'.join(lines)
    
    def clean_text(self, text: str) -> Tuple[str, Dict]:
        """
        Perform comprehensive text cleaning
        
        Args:
            text: Raw extracted text
            
        Returns:
            Tuple of (cleaned_text, statistics)
        """
        original_length = len(text)
        original_lines = text.split('\n')
        
        # Step 1: Clean line by line
        cleaned_lines = []
        removed_lines = 0
        
        for line in original_lines:
            cleaned_line = self.clean_line(line)
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
            else:
                if line.strip():  # Only count non-empty lines as removed
                    removed_lines += 1
        
        # Join cleaned lines
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Step 2: Remove section markers
        cleaned_text = self.remove_section_markers(cleaned_text)
        
        # Step 3: Clean whitespace
        cleaned_text = self.clean_whitespace(cleaned_text)
        
        # Calculate statistics
        stats = {
            'original_chars': original_length,
            'cleaned_chars': len(cleaned_text),
            'chars_removed': original_length - len(cleaned_text),
            'removal_percentage': round((original_length - len(cleaned_text)) / original_length * 100, 2) if original_length > 0 else 0,
            'original_lines': len(original_lines),
            'cleaned_lines': len(cleaned_text.split('\n')),
            'lines_removed': removed_lines
        }
        
        return cleaned_text.strip(), stats
    
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
    
    def get_output_path(self, text_path: Path) -> Path:
        """
        Generate output path for cleaned text file
        Maintains directory structure from input
        
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
        
        # Create parent directories
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        return output_path
    
    def save_text(self, text: str, output_path: Path) -> bool:
        """
        Save cleaned text to file
        
        Args:
            text: Cleaned text content
            output_path: Path to save text file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            logger.info(f"Saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save text to {output_path}: {e}")
            return False
    
    def clean_all(self) -> dict:
        """
        Clean all text files in input directory
        
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
                'files': []
            }
        
        stats = {
            'total_files': len(text_files),
            'successful': 0,
            'failed': 0,
            'total_chars_removed': 0,
            'total_lines_removed': 0,
            'files': []
        }
        
        for text_path in text_files:
            logger.info(f"\n{'='*60}")
            logger.info(f"Cleaning: {text_path.relative_to(self.input_dir)}")
            logger.info(f"{'='*60}")
            
            try:
                # Read text
                with open(text_path, 'r', encoding='utf-8') as f:
                    raw_text = f.read()
                
                # Clean text
                cleaned_text, clean_stats = self.clean_text(raw_text)
                
                # Get output path
                output_path = self.get_output_path(text_path)
                
                # Save cleaned text
                if self.save_text(cleaned_text, output_path):
                    stats['successful'] += 1
                    stats['total_chars_removed'] += clean_stats['chars_removed']
                    stats['total_lines_removed'] += clean_stats['lines_removed']
                    
                    stats['files'].append({
                        'file': str(text_path),
                        'output': str(output_path),
                        'status': 'success',
                        'stats': clean_stats
                    })
                    
                    logger.info(f"✓ Removed {clean_stats['chars_removed']:,} chars "
                              f"({clean_stats['removal_percentage']:.1f}%) and "
                              f"{clean_stats['lines_removed']} lines")
                else:
                    stats['failed'] += 1
                    stats['files'].append({
                        'file': str(text_path),
                        'status': 'failed_to_save'
                    })
            
            except Exception as e:
                logger.error(f"Failed to clean {text_path.name}: {e}")
                stats['failed'] += 1
                stats['files'].append({
                    'file': str(text_path),
                    'status': 'error',
                    'error': str(e)
                })
        
        return stats
    
    def print_summary(self, stats: dict) -> None:
        """Print cleaning summary"""
        print("\n" + "="*60)
        print("CLEANING SUMMARY")
        print("="*60)
        print(f"Total files found: {stats['total_files']}")
        print(f"Successfully cleaned: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        
        if stats['successful'] > 0:
            print(f"\n✅ Cleaned text saved to: {self.output_dir}")
            print(f"\nTotal removed:")
            print(f"  • {stats['total_chars_removed']:,} characters")
            print(f"  • {stats['total_lines_removed']:,} lines")
            
            print("\nSuccessfully cleaned files:")
            for file_info in stats['files']:
                if file_info['status'] == 'success':
                    file_name = Path(file_info['file']).name
                    file_stats = file_info['stats']
                    print(f"  ✓ {file_name}")
                    print(f"    - {file_stats['chars_removed']:,} chars removed "
                          f"({file_stats['removal_percentage']:.1f}%)")
                    print(f"    - {file_stats['lines_removed']} lines removed")
        
        if stats['failed'] > 0:
            print("\n❌ Failed files:")
            for file_info in stats['files']:
                if file_info['status'] != 'success':
                    file_name = Path(file_info['file']).name
                    status = file_info.get('error', file_info['status'])
                    print(f"  ✗ {file_name}: {status}")


def main():
    """Main function for testing"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    # Create cleaner
    cleaner = TextCleaner()
    
    # Clean all text files
    stats = cleaner.clean_all()
    
    # Print summary
    cleaner.print_summary(stats)


if __name__ == "__main__":
    main()

