"""
Parser Factory
Auto-detects paper format and returns appropriate parser
"""

import logging
from typing import Optional
from .base_parser import BasePaperParser
from .net_parser import NETPaperParser
from .fast_parser import FASTPaperParser

logger = logging.getLogger(__name__)


class ParserFactory:
    """Factory for creating format-specific parsers"""
    
    def __init__(self):
        """Initialize factory with available parsers (excluding MDCAT)"""
        # Only NET and FAST parsers for solved papers
        self.parsers = [
            NETPaperParser(),
            FASTPaperParser(),
        ]
    
    def get_parser(self, text: str, filename: str) -> BasePaperParser:
        """
        Get appropriate parser for the given text
        
        Args:
            text: Text content to analyze
            filename: Source filename (for additional hints)
            
        Returns:
            Appropriate parser instance
        """
        # Try each parser's detect_format method
        for parser in self.parsers:
            if parser.detect_format(text):
                logger.info(f"Detected format: {parser.__class__.__name__}")
                return parser
        
        # Fallback: Try filename-based detection
        filename_upper = filename.upper()
        if 'NET' in filename_upper or 'NUST' in filename_upper:
            logger.info("Detected format from filename: NET")
            return NETPaperParser()
        elif 'FAST' in filename_upper:
            logger.info("Detected format from filename: FAST")
            return FASTPaperParser()
        
        # Default: Return NET parser as fallback
        logger.warning("No format detected, using NET parser as fallback")
        return NETPaperParser()
