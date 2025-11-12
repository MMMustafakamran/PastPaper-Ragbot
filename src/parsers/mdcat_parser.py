"""
MDCAT Paper Parser
Parses MDCAT format papers with inline options (A) text1. C) text2.)
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from .base_parser import BasePaperParser, Question

logger = logging.getLogger(__name__)


class MDCATPaperParser(BasePaperParser):
    """
    MDCAT Format:
    - Questions: Q.1, Q.2 (Q. prefix with dot)
    - Options: A), B), C), D) (parenthesis notation)
    - CRITICAL: Options on same line: "A) text1. C) text2." and "B) text3. D) text4."
    - Answers: Usually in separate answer key section at end
    """
    
    def __init__(self):
        """Initialize MDCAT parser"""
        # Question pattern: "Q.1" or "Q1"
        self.question_pattern = re.compile(r'^Q\.?\s*(\d+)\s+(.+)$', re.IGNORECASE)
        
        # Option pattern: "A) text" or "A. text"
        self.option_pattern = re.compile(r'^([A-D])[.)]\s*(.+)$', re.IGNORECASE)
        
        # Inline option pattern: "A) text1. C) text2."
        self.inline_option_pattern = re.compile(
            r'([A-D])\)\s*([^A-D]+?)(?=\s+[A-D]\)|$)',
            re.IGNORECASE
        )
    
    def detect_format(self, text: str) -> bool:
        """Check if text matches MDCAT format"""
        # Check for MDCAT-specific patterns
        has_q_format = bool(re.search(r'^Q\.?\s*\d+', text, re.MULTILINE | re.IGNORECASE))
        has_mdcat_tag = bool(re.search(r'MDCAT', text, re.IGNORECASE))
        has_inline_options = bool(re.search(r'[A-D]\)\s+[^A-D]+\.\s+[A-D]\)', text, re.IGNORECASE))
        
        # MDCAT format has Q. prefix and often inline options
        return has_q_format and (has_mdcat_tag or has_inline_options)
    
    def parse_inline_options(self, line: str) -> List[Dict[str, str]]:
        """
        Parse inline options from a single line
        Example: "A) An alpha particle. C) A positive helium ion."
        
        Args:
            line: Line containing multiple options
            
        Returns:
            List of option dictionaries
        """
        options = []
        
        # Find all option patterns in the line
        matches = self.inline_option_pattern.finditer(line)
        
        for match in matches:
            label = match.group(1).upper()
            text = match.group(2).strip().rstrip('.')
            
            options.append({
                'label': label,
                'text': text
            })
        
        # If no inline options found, try single option
        if not options:
            opt_match = self.option_pattern.match(line)
            if opt_match:
                label = opt_match.group(1).upper()
                text = opt_match.group(2).strip().rstrip('.')
                options.append({
                    'label': label,
                    'text': text
                })
        
        return options
    
    def parse_questions(self, text: str, source_file: str) -> List[Question]:
        """
        Parse MDCAT format questions
        
        Args:
            text: Text content
            source_file: Source filename
            
        Returns:
            List of Question objects
        """
        lines = text.split('\n')
        questions = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # Check for question start
            q_match = self.question_pattern.match(line)
            if q_match:
                q_num = int(q_match.group(1))
                q_text = q_match.group(2).strip()
                
                # Extract full question (may be multi-line)
                question_lines = [q_text] if q_text else []
                i += 1
                
                # Continue reading until we hit an option
                while i < len(lines):
                    next_line = lines[i].strip()
                    if not next_line:
                        i += 1
                        continue
                    
                    # Check if this is an option (look for A), B), C), D))
                    if self.option_pattern.match(next_line) or self.inline_option_pattern.search(next_line):
                        break
                    
                    # Check if this is a new question
                    if self.question_pattern.match(next_line):
                        break
                    
                    # Otherwise, it's part of the question
                    question_lines.append(next_line)
                    i += 1
                
                full_question = ' '.join(question_lines).strip()
                
                # Extract options
                options = []
                option_labels_seen = set()
                
                while i < len(lines):
                    opt_line = lines[i].strip()
                    
                    if not opt_line:
                        i += 1
                        continue
                    
                    # Check for next question
                    if self.question_pattern.match(opt_line):
                        break
                    
                    # Check for inline options (multiple options on one line)
                    if self.inline_option_pattern.search(opt_line):
                        inline_options = self.parse_inline_options(opt_line)
                        for opt in inline_options:
                            if opt['label'] not in option_labels_seen:
                                options.append(opt)
                                option_labels_seen.add(opt['label'])
                        i += 1
                    # Check for single option
                    elif self.option_pattern.match(opt_line):
                        opt_match = self.option_pattern.match(opt_line)
                        if opt_match:
                            label = opt_match.group(1).upper()
                            text = opt_match.group(2).strip().rstrip('.')
                            
                            if label not in option_labels_seen:
                                options.append({
                                    'label': label,
                                    'text': text
                                })
                                option_labels_seen.add(label)
                        i += 1
                    else:
                        # Unknown line, skip it
                        i += 1
                    
                    # Stop if we have all 4 options
                    if len(options) >= 4:
                        break
                
                # Only add if we have valid question and at least 2 options
                if full_question and len(options) >= 2:
                    # Extract year from filename or text
                    year = self._extract_year(source_file, text)
                    
                    # Generate question ID
                    question_id = f"MDCAT_{year or 'UNKNOWN'}_Q{q_num:03d}"
                    
                    # Classify subject
                    subject = self._classify_subject(full_question, options)
                    
                    # Create question object
                    question = Question(
                        id=question_id,
                        question_number=q_num,
                        question_text=full_question,
                        options=options,
                        correct_answer=None,  # Will be filled by answer key matcher
                        subject=subject,
                        exam_type="MDCAT",
                        year=year,
                        raw_text=self._generate_raw_text(q_num, full_question, options)
                    )
                    
                    questions.append(question)
                    logger.debug(f"Parsed Q{q_num}: {len(options)} options")
            else:
                i += 1
        
        return questions
    
    def _extract_year(self, filename: str, text: str) -> Optional[int]:
        """Extract year from filename or text"""
        # Try filename first
        year_match = re.search(r'20\d{2}', filename)
        if year_match:
            try:
                return int(year_match.group(0))
            except ValueError:
                pass
        
        # Try text
        year_match = re.search(r'20\d{2}', text)
        if year_match:
            try:
                return int(year_match.group(0))
            except ValueError:
                pass
        
        return None
    
    def _classify_subject(self, question_text: str, options: List[Dict]) -> str:
        """Simple subject classification"""
        text = question_text.lower()
        for opt in options:
            text += " " + opt['text'].lower()
        
        # Simple keyword matching
        if any(kw in text for kw in ['velocity', 'acceleration', 'force', 'electric', 'magnetic', 'wave', 'photon']):
            return "physics"
        elif any(kw in text for kw in ['atom', 'molecule', 'reaction', 'bond', 'acid', 'base']):
            return "chemistry"
        elif any(kw in text for kw in ['cell', 'dna', 'gene', 'protein', 'enzyme']):
            return "biology"
        elif any(kw in text for kw in ['derivative', 'integral', 'matrix', 'trigonometry']):
            return "mathematics"
        else:
            return "general"
    
    def _generate_raw_text(self, q_num: int, q_text: str, options: List[Dict]) -> str:
        """Generate raw text representation"""
        raw = f"Q.{q_num} {q_text}\n"
        for opt in options:
            raw += f"{opt['label']}) {opt['text']}\n"
        return raw
    
    def parse_answer_key(self, text: str) -> Dict[int, str]:
        """
        Parse answer key from text
        MDCAT format usually has answer key section at end
        
        Args:
            text: Text content
            
        Returns:
            Dictionary mapping question_number to answer_label
        """
        answer_key = {}
        
        # Look for answer key section
        key_section = re.search(
            r'ANSWER\s+KEY.*?(?=\n\n|\Z)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if key_section:
            key_text = key_section.group(0)
            # Pattern: "1. C" or "1) C" or "1: C" or "Q.1 C" or "Q1 C"
            patterns = [
                r'(?:Q\.?\s*)?(\d+)[.:)\s]+([A-D])',  # Q.1 C or 1. C
                r'(\d+)\s*:\s*([A-D])',  # 1: C
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, key_text, re.IGNORECASE)
                for q_num, answer in matches:
                    answer_key[int(q_num)] = answer.upper()
        
        return answer_key

