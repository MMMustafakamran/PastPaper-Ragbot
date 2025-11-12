"""
NET Paper Parser
Parses NET format papers with (Correct) markers
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from .base_parser import BasePaperParser, Question

logger = logging.getLogger(__name__)


class NETPaperParser(BasePaperParser):
    """
    NET Format:
    - Questions: 1), 2), 3) (number with parenthesis)
    - Options: A., B., C., D. (dot notation, each on separate line)
    - Answers: (Correct) marker after option text
    """
    
    def __init__(self):
        """Initialize NET parser"""
        # Question pattern: "1) Question text"
        self.question_pattern = re.compile(r'^(\d+)\)\s+(.+)$')
        
        # Option pattern: "A. Option text" or "A. Option text (Correct)"
        self.option_pattern = re.compile(r'^([A-D])\.\s*(.+)$', re.IGNORECASE)
        
        # Correct marker
        self.correct_marker = re.compile(r'\s*\(Correct\)\s*$', re.IGNORECASE)
        
        # Year tag pattern: "(NET 1 2015)" or "(NET-2015)"
        self.year_pattern = re.compile(r'\(NET[-\s]*(?:\d+[-\s]*)?(\d{4})\)', re.IGNORECASE)
    
    def detect_format(self, text: str) -> bool:
        """Check if text matches NET format"""
        # Check for NET-specific patterns
        has_question_format = bool(re.search(r'^\d+\)\s+', text, re.MULTILINE))
        has_correct_markers = bool(re.search(r'\(Correct\)', text, re.IGNORECASE))
        has_net_tag = bool(re.search(r'\(NET', text, re.IGNORECASE))
        
        # NET format has questions with parenthesis and (Correct) markers
        return has_question_format and (has_correct_markers or has_net_tag)
    
    def extract_correct_answer(self, option_text: str) -> Tuple[str, Optional[str]]:
        """
        Extract (Correct) marker from option text
        
        Args:
            option_text: Option text that may contain (Correct)
            
        Returns:
            Tuple of (cleaned_text, answer_label or None)
        """
        match = self.correct_marker.search(option_text)
        if match:
            cleaned = self.correct_marker.sub('', option_text).strip()
            return cleaned, True  # Return True to indicate this is correct
        return option_text.strip(), False
    
    def extract_year(self, text: str) -> Optional[int]:
        """Extract year from NET tags in text"""
        match = self.year_pattern.search(text)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                pass
        return None
    
    def parse_questions(self, text: str, source_file: str) -> List[Question]:
        """
        Parse NET format questions
        
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
                    
                    # Check if this is an option
                    if self.option_pattern.match(next_line):
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
                correct_answer = None
                
                while i < len(lines):
                    opt_line = lines[i].strip()
                    
                    if not opt_line:
                        i += 1
                        continue
                    
                    # Check for next question
                    if self.question_pattern.match(opt_line):
                        break
                    
                    # Check for option
                    opt_match = self.option_pattern.match(opt_line)
                    if opt_match:
                        opt_label = opt_match.group(1).upper()
                        opt_text = opt_match.group(2).strip()
                        
                        # Extract correct answer marker
                        cleaned_text, is_correct = self.extract_correct_answer(opt_text)
                        
                        options.append({
                            'label': opt_label,
                            'text': cleaned_text
                        })
                        
                        if is_correct:
                            correct_answer = opt_label
                        
                        i += 1
                    else:
                        # Unknown line, skip it
                        i += 1
                
                # Only add if we have valid question and options
                if full_question and len(options) >= 2:
                    # Extract year from text
                    year = self.extract_year(text)
                    
                    # Generate question ID
                    question_id = f"NET_{year or 'UNKNOWN'}_Q{q_num:03d}"
                    
                    # Classify subject (simplified - can be enhanced)
                    subject = self._classify_subject(full_question, options)
                    
                    # Create question object
                    question = Question(
                        id=question_id,
                        question_number=q_num,
                        question_text=full_question,
                        options=options,
                        correct_answer=correct_answer,
                        subject=subject,
                        exam_type="NET",
                        year=year,
                        raw_text=self._generate_raw_text(q_num, full_question, options)
                    )
                    
                    questions.append(question)
                    logger.debug(f"Parsed Q{q_num}: {len(options)} options, "
                               f"answer={'Yes' if correct_answer else 'No'}")
            else:
                i += 1
        
        return questions
    
    def _classify_subject(self, question_text: str, options: List[Dict]) -> str:
        """Simple subject classification"""
        text = question_text.lower()
        for opt in options:
            text += " " + opt['text'].lower()
        
        # Simple keyword matching
        if any(kw in text for kw in ['derivative', 'integral', 'matrix', 'trigonometry', 'calculus']):
            return "mathematics"
        elif any(kw in text for kw in ['atom', 'molecule', 'reaction', 'bond']):
            return "chemistry"
        elif any(kw in text for kw in ['cell', 'dna', 'gene', 'protein']):
            return "biology"
        elif any(kw in text for kw in ['force', 'velocity', 'electric', 'magnetic']):
            return "physics"
        else:
            return "general"
    
    def _generate_raw_text(self, q_num: int, q_text: str, options: List[Dict]) -> str:
        """Generate raw text representation"""
        raw = f"{q_num}) {q_text}\n"
        for opt in options:
            raw += f"{opt['label']}. {opt['text']}\n"
        return raw
    
    def parse_answer_key(self, text: str) -> Dict[int, str]:
        """
        Parse answer key from text
        NET format usually has inline (Correct) markers, but may have separate key
        
        Args:
            text: Text content
            
        Returns:
            Dictionary mapping question_number to answer_label
        """
        # NET format typically has inline answers, so this is mainly for separate keys
        answer_key = {}
        
        # Look for answer key section
        key_section = re.search(
            r'ANSWER\s+KEY.*?(?=\n\n|\Z)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if key_section:
            key_text = key_section.group(0)
            # Pattern: "1. C" or "1) C" or "1: C"
            matches = re.findall(r'(\d+)[.:)\s]+([A-D])', key_text)
            for q_num, answer in matches:
                answer_key[int(q_num)] = answer.upper()
        
        return answer_key

