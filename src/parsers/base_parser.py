"""
Base Parser Interface
Abstract base class for format-specific parsers
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Question:
    """Question data structure"""
    id: str
    question_number: int
    question_text: str
    options: List[Dict[str, str]]
    correct_answer: Optional[str] = None
    solution: Optional[str] = None
    
    # Metadata
    subject: str = "general"
    topic: Optional[str] = None
    difficulty: str = "medium"
    
    # Source info
    exam_type: str = ""
    year: Optional[int] = None
    
    # For RAG
    embedding_text: str = ""
    raw_text: str = ""


class BasePaperParser(ABC):
    """Abstract base class for format-specific parsers"""
    
    @abstractmethod
    def parse_questions(self, text: str, source_file: str) -> List[Question]:
        """
        Parse questions from text
        
        Args:
            text: Text content
            source_file: Source filename
            
        Returns:
            List of Question objects
        """
        pass
    
    @abstractmethod
    def parse_answer_key(self, text: str) -> Dict[int, str]:
        """
        Parse answer key from text
        
        Args:
            text: Text content
            
        Returns:
            Dictionary mapping question_number to answer_label
        """
        pass
    
    @abstractmethod
    def detect_format(self, text: str) -> bool:
        """
        Check if this parser matches the format
        
        Args:
            text: Text content to check
            
        Returns:
            True if format matches, False otherwise
        """
        pass
    
    def clean_text(self, text: str) -> str:
        """
        Common text cleaning utilities
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        import re
        # Remove extra whitespace
        text = re.sub(r' {2,}', ' ', text)
        # Remove trailing whitespace from lines
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]
        return '\n'.join(lines).strip()

