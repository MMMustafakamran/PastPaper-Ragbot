"""
Noise Remover Module
Removes promotional content, contact information, and unwanted text from extracted PDFs
"""

import re
from typing import List, Set


class NoiseRemover:
    """Remove common noise patterns from past paper PDFs"""
    
    def __init__(self):
        """Initialize noise patterns for different exam sources"""
        
        # Website and URL patterns
        self.url_patterns = [
            r'www\.[a-zA-Z0-9-]+\.(com|net|org|edu|pk|info)',
            r'https?://[^\s]+',
            r'[a-zA-Z0-9-]+\.com',
            r'educatedzone\.com',
            r'pmdc\.org\.pk',
            r'nust\.edu\.pk',
        ]
        
        # Phone number patterns (Pakistani format)
        self.phone_patterns = [
            r'\b0?\d{3}[-\s]?\d{7}\b',  # 0300-1234567 or 300-1234567
            r'\b\d{4}[-\s]?\d{7}\b',    # 0321-1234567
            r'\+92[-\s]?\d{3}[-\s]?\d{7}\b',  # +92-300-1234567
            r'Helpline\s*:?\s*\d+',
            r'Contact\s*:?\s*\d+',
            r'Call\s*:?\s*\d+',
        ]
        
        # Promotional text patterns
        self.promotional_patterns = [
            r'All MDCAT Study Stuff and Free Preparation',
            r'Download MDCAT Guide App',
            r'Download.*?App.*?From.*?Play Store',
            r'Get it on Google Play',
            r'Available on the App Store',
            r'Download.*?from Play Store',
            r'Free MDCAT Preparation',
            r'Join our.*?WhatsApp Group',
            r'Follow us on Facebook',
            r'Subscribe to our channel',
            r'Visit our website',
            r'For more.*?visit',
        ]
        
        # App and social media references
        self.app_patterns = [
            r'MDCAT Guide App',
            r'NET Prep App',
            r'NUST Entry Test App',
            r'Educational Zone App',
            r'Study Guide Application',
        ]
        
        # Email patterns
        self.email_patterns = [
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        ]
        
        # Social media patterns
        self.social_patterns = [
            r'Facebook\.com/[^\s]+',
            r'Instagram\.com/[^\s]+',
            r'Twitter\.com/[^\s]+',
            r'YouTube\.com/[^\s]+',
            r'@[a-zA-Z0-9_]+',  # Social media handles
        ]
        
        # Watermark and footer patterns
        self.watermark_patterns = [
            r'Prepared by.*?educatedzone',
            r'Copyright.*?\d{4}',
            r'All rights reserved',
            r'Unauthorized.*?prohibited',
            r'This material.*?property of',
        ]
        
        # Page number and header/footer patterns
        self.page_patterns = [
            r'^Page\s+\d+\s*$',
            r'^\d+\s*$',  # Standalone page numbers
            r'^-\s*\d+\s*-$',  # -1-
        ]
        
        # Specific known noise strings (case-insensitive)
        self.noise_strings = [
            'educatedzone.com',
            'www.educatedzone.com',
            'All MDCAT Study Stuff and Free Preparation',
            'Download MDCAT Guide App From Play Store',
            'Helpline 03047418334',
            'For more MCQs and past papers visit',
            'Join our Facebook group',
            'Subscribe for more content',
        ]
    
    def remove_noise(self, text: str) -> str:
        """
        Remove all noise patterns from text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text with noise removed
        """
        cleaned_text = text
        
        # Remove URLs
        for pattern in self.url_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # Remove phone numbers
        for pattern in self.phone_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # Remove promotional text
        for pattern in self.promotional_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # Remove app references
        for pattern in self.app_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # Remove email addresses
        for pattern in self.email_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # Remove social media
        for pattern in self.social_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # Remove watermarks
        for pattern in self.watermark_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # Remove exact noise strings
        for noise in self.noise_strings:
            cleaned_text = cleaned_text.replace(noise, '')
            cleaned_text = cleaned_text.replace(noise.lower(), '')
            cleaned_text = cleaned_text.replace(noise.upper(), '')
        
        return cleaned_text
    
    def remove_page_numbers(self, text: str) -> str:
        """Remove page numbers and headers/footers"""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip page number lines
            is_page_number = False
            for pattern in self.page_patterns:
                if re.match(pattern, line_stripped):
                    is_page_number = True
                    break
            
            if not is_page_number and line_stripped:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def clean_text(self, text: str, remove_pages: bool = True) -> str:
        """
        Comprehensive text cleaning
        
        Args:
            text: Raw extracted text
            remove_pages: Whether to remove page numbers
            
        Returns:
            Fully cleaned text
        """
        # First pass: remove noise patterns
        cleaned = self.remove_noise(text)
        
        # Second pass: remove page numbers if requested
        if remove_pages:
            cleaned = self.remove_page_numbers(cleaned)
        
        # Third pass: clean up extra whitespace
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)  # Max 2 consecutive newlines
        cleaned = re.sub(r' {2,}', ' ', cleaned)  # Replace multiple spaces with single
        
        return cleaned.strip()
    
    def get_noise_statistics(self, original_text: str, cleaned_text: str) -> dict:
        """
        Calculate statistics about removed noise
        
        Args:
            original_text: Original text before cleaning
            cleaned_text: Text after cleaning
            
        Returns:
            Dictionary with noise statistics
        """
        original_lines = original_text.split('\n')
        cleaned_lines = cleaned_text.split('\n')
        
        return {
            'original_length': len(original_text),
            'cleaned_length': len(cleaned_text),
            'chars_removed': len(original_text) - len(cleaned_text),
            'removal_percentage': round((len(original_text) - len(cleaned_text)) / len(original_text) * 100, 2),
            'original_lines': len(original_lines),
            'cleaned_lines': len(cleaned_lines),
            'lines_removed': len(original_lines) - len(cleaned_lines)
        }


def test_noise_remover():
    """Test the noise remover with sample text"""
    remover = NoiseRemover()
    
    sample_text = """
    1. What is the atomic number of Carbon?
    a. 6
    b. 12
    c. 14
    d. 16
    
    www.educatedzone.com
    All MDCAT Study Stuff and Free Preparation
    Download MDCAT Guide App From Play Store
    Helpline 03047418334
    
    2. Which organ pumps blood?
    a. Liver
    b. Heart
    c. Kidney
    d. Brain
    
    For more MCQs visit www.educatedzone.com
    Contact: 0321-1234567
    """
    
    cleaned = remover.clean_text(sample_text)
    stats = remover.get_noise_statistics(sample_text, cleaned)
    
    print("Original Text:")
    print("-" * 50)
    print(sample_text)
    print("\n\nCleaned Text:")
    print("-" * 50)
    print(cleaned)
    print("\n\nStatistics:")
    print("-" * 50)
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    test_noise_remover()
