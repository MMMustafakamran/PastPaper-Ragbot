"""
Answer Key Matcher
Matches answer keys to questions and validates answers
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Question:
    """Question data structure (simplified for matching)"""
    question_number: int
    correct_answer: Optional[str] = None
    options: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = []


class AnswerKeyMatcher:
    """Match answer keys to questions"""
    
    def match_answers_to_questions(
        self,
        questions: List[Any],
        answer_key: Dict[int, str]
    ) -> List[Any]:
        """
        Apply answer key to questions
        
        Args:
            questions: List of Question objects
            answer_key: Dictionary mapping question_number to answer_label
            
        Returns:
            Updated list of questions with correct_answer set
        """
        matched_count = 0
        
        for question in questions:
            q_num = question.question_number
            
            if q_num in answer_key:
                answer_label = answer_key[q_num].upper()
                
                # Validate answer label exists in options
                valid_labels = [opt['label'].upper() for opt in question.options]
                
                if answer_label in valid_labels:
                    question.correct_answer = answer_label
                    
                    # Mark correct option
                    for opt in question.options:
                        opt['is_correct'] = (opt['label'].upper() == answer_label)
                    
                    matched_count += 1
                else:
                    logger.warning(
                        f"Q{q_num}: Invalid answer '{answer_label}' "
                        f"(valid options: {valid_labels})"
                    )
        
        if matched_count > 0:
            logger.info(f"Matched {matched_count} answers from answer key")
        
        return questions
    
    def validate_answers(self, questions: List[Any]) -> Dict[str, Any]:
        """
        Validate that answers match available options
        
        Args:
            questions: List of Question objects
            
        Returns:
            Validation statistics dictionary
        """
        stats = {
            'total': len(questions),
            'with_answers': 0,
            'invalid_answers': [],
            'valid_answers': 0
        }
        
        for q in questions:
            if q.correct_answer:
                stats['with_answers'] += 1
                
                # Check if answer is valid
                valid_labels = [opt['label'].upper() for opt in q.options]
                if q.correct_answer.upper() in valid_labels:
                    stats['valid_answers'] += 1
                else:
                    stats['invalid_answers'].append({
                        'question_id': getattr(q, 'id', f"Q{q.question_number}"),
                        'question_number': q.question_number,
                        'invalid_answer': q.correct_answer,
                        'valid_options': valid_labels
                    })
        
        return stats
    
    def find_answer_key_file(self, question_file: Any) -> Optional[Any]:
        """
        Look for companion answer key file
        
        Args:
            question_file: Path to question file
            
        Returns:
            Path to answer key file or None
        """
        from pathlib import Path
        
        if not isinstance(question_file, Path):
            question_file = Path(question_file)
        
        base_name = question_file.stem
        parent_dir = question_file.parent
        
        # Patterns to search for
        patterns = [
            f"{base_name}_answers*",
            f"{base_name}_key*",
            f"{base_name}_solutions*",
            f"*{base_name}*answer*",
        ]
        
        for pattern in patterns:
            matches = list(parent_dir.glob(pattern))
            if matches:
                return matches[0]
        
        return None

