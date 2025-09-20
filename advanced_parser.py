import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Question:
    question_number: str
    question_text: str
    options: List[str]
    answer: Optional[str] = None
    explanation: Optional[str] = None
    subject_area: Optional[str] = None
    difficulty: Optional[str] = None
    question_type: str = "multiple_choice"
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class AdvancedQuestionParser:
    def __init__(self):
        # Enhanced patterns for different question formats
        self.question_patterns = [
            r'^(\d+)\.\s+(.+?)(?=\n[a-e]\.)',  # Standard numbered questions
            r'^(\d+)\.\s+(.+?)(?=\n\d+\.)',    # Questions without clear option separation
        ]
        
        # More comprehensive option patterns
        self.option_patterns = [
            r'^([a-e])\.\s*(.+?)(?=\n[a-e]\.|\n\d+\.|\nwww\.|$)',  # Standard options
            r'^([a-e])\.\s*(.+?)$',  # Last option in sequence
        ]
        
        # Enhanced subject area detection
        self.subject_patterns = {
            'mathematics': [
                r'sin|cos|tan|log|integral|derivative|function|equation|triangle|circle|ellipse|hyperbola|parabola|matrix|vector|complex|limit|continuity|trigonometry|calculus|geometry|algebra|probability|statistics|permutation|combination'
            ],
            'physics': [
                r'force|energy|momentum|velocity|acceleration|electric|magnetic|wave|frequency|wavelength|quantum|thermodynamics|optics|mechanics|kinematics|dynamics|electromagnetism|nuclear|atomic|molecular'
            ],
            'chemistry': [
                r'atom|molecule|bond|reaction|compound|element|organic|inorganic|acid|base|pH|oxidation|reduction|stoichiometry|thermodynamics|kinetics|equilibrium|electrochemistry|organic chemistry|inorganic chemistry'
            ],
            'english': [
                r'synonym|antonym|grammar|vocabulary|sentence|paragraph|essay|literature|poetry|novel|comprehension|reading|writing|language|linguistics|etymology|phonics'
            ],
            'general_knowledge': [
                r'country|capital|president|prime minister|award|prize|sport|cricket|football|history|geography|current affairs|politics|economics|culture|religion|science|technology|environment|health'
            ],
            'computer_science': [
                r'programming|algorithm|data structure|computer|software|hardware|network|database|artificial intelligence|machine learning|cybersecurity|web development|mobile development'
            ]
        }
        
        # Answer patterns
        self.answer_patterns = [
            r'Answer\s*:\s*([a-e])',
            r'Correct\s*Answer\s*:\s*([a-e])',
            r'Solution\s*:\s*([a-e])',
            r'Key\s*:\s*([a-e])',
            r'Ans\s*:\s*([a-e])',
        ]
    
    def extract_questions_from_text(self, text: str) -> List[Question]:
        """Extract all questions from the text with advanced parsing"""
        questions = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and website references
            if not line or 'www.educatedzone.com' in line:
                i += 1
                continue
            
            # Check if this line starts a new question
            question_match = self._match_question_start(line)
            if question_match:
                question_num, question_text = question_match
                
                # Extract options for this question
                options, next_index = self._extract_options(lines, i + 1)
                
                # Create question object
                if options:  # Only add if we found options
                    question = Question(
                        question_number=question_num,
                        question_text=self._clean_text(question_text),
                        options=[self._clean_text(opt) for opt in options],
                        subject_area=self._detect_subject_area(question_text),
                        question_type=self._detect_question_type(question_text, options),
                        metadata=self._extract_metadata(question_text, options)
                    )
                    questions.append(question)
                
                i = next_index
            else:
                i += 1
        
        return questions
    
    def _match_question_start(self, line: str) -> Optional[Tuple[str, str]]:
        """Check if line starts a new question and extract number and text"""
        # Pattern for numbered questions
        pattern = r'^(\d+)\.\s+(.+)$'
        match = re.match(pattern, line)
        
        if match:
            question_num = match.group(1)
            question_text = match.group(2)
            return (question_num, question_text)
        
        return None
    
    def _extract_options(self, lines: List[str], start_index: int) -> Tuple[List[str], int]:
        """Extract options starting from the given index"""
        options = []
        i = start_index
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check if this is an option
            option_match = self._match_option(line)
            if option_match:
                option_letter, option_text = option_match
                options.append(f"{option_letter}. {option_text}")
                i += 1
            else:
                # Check if this is the start of a new question or end of document
                if (self._match_question_start(line) or 
                    'www.educatedzone.com' in line or
                    i >= len(lines) - 1):
                    break
                else:
                    # This might be a continuation of the previous option
                    if options:
                        options[-1] += " " + line
                    i += 1
        
        return options, i
    
    def _match_option(self, line: str) -> Optional[Tuple[str, str]]:
        """Check if line is an option and extract letter and text"""
        # Pattern for options (a. b. c. d. e.)
        pattern = r'^([a-e])\.\s*(.+)$'
        match = re.match(pattern, line)
        
        if match:
            option_letter = match.group(1)
            option_text = match.group(2)
            return (option_letter, option_text)
        
        return None
    
    def _detect_subject_area(self, question_text: str) -> str:
        """Detect the subject area based on question content"""
        question_lower = question_text.lower()
        
        # Count matches for each subject
        subject_scores = {}
        for subject, patterns in self.subject_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, question_lower)
                score += len(matches)
            subject_scores[subject] = score
        
        # Return subject with highest score, or 'general' if no clear match
        if subject_scores:
            best_subject = max(subject_scores, key=subject_scores.get)
            if subject_scores[best_subject] > 0:
                return best_subject
        
        return 'general'
    
    def _detect_question_type(self, question_text: str, options: List[str]) -> str:
        """Detect the type of question"""
        text_lower = question_text.lower()
        
        if 'calculate' in text_lower or 'find' in text_lower or 'solve' in text_lower:
            return 'calculation'
        elif 'choose' in text_lower or 'select' in text_lower:
            return 'selection'
        elif 'true' in text_lower and 'false' in text_lower:
            return 'true_false'
        else:
            return 'multiple_choice'
    
    def _extract_metadata(self, question_text: str, options: List[str]) -> Dict[str, Any]:
        """Extract additional metadata from the question"""
        metadata = {
            'num_options': len(options),
            'has_mathematical_notation': bool(re.search(r'[π√∑∫∂∆∇]', question_text)),
            'has_chemical_formulas': bool(re.search(r'[A-Z][a-z]?\d*', question_text)),
            'has_equations': bool(re.search(r'[=<>≤≥]', question_text)),
            'question_length': len(question_text),
            'avg_option_length': sum(len(opt) for opt in options) / len(options) if options else 0
        }
        
        return metadata
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors and mathematical notation
        replacements = {
            'sin-1': 'sin⁻¹',
            'cos-1': 'cos⁻¹',
            'tan-1': 'tan⁻¹',
            'log-1': 'log⁻¹',
            'd2y/dx2': 'd²y/dx²',
            'dy/dx': 'dy/dx',
            'x2': 'x²',
            'y2': 'y²',
            'z2': 'z²',
            'r2': 'r²',
            'p2': 'p²',
            'q2': 'q²',
            '3π/2': '3π/2',
            'π/2': 'π/2',
            'π/4': 'π/4',
            'π/6': 'π/6',
            'π/3': 'π/3',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text.strip()
    
    def extract_answers_from_text(self, text: str) -> Dict[str, str]:
        """Extract answers if they exist in the text"""
        answers = {}
        
        for pattern in self.answer_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                answers[match] = match
        
        return answers
    
    def validate_question(self, question: Question) -> bool:
        """Validate that a question has the required components"""
        return (
            question.question_number and
            question.question_text and
            len(question.options) >= 2 and
            all(option.strip() for option in question.options) and
            len(question.question_text) > 10  # Minimum question length
        )
    
    def generate_question_summary(self, questions: List[Question]) -> Dict[str, Any]:
        """Generate a comprehensive summary of the questions"""
        if not questions:
            return {}
        
        summary = {
            'total_questions': len(questions),
            'subject_distribution': {},
            'question_type_distribution': {},
            'option_count_distribution': {},
            'statistics': {
                'avg_question_length': 0,
                'avg_options_per_question': 0,
                'questions_with_math_notation': 0,
                'questions_with_equations': 0,
                'questions_with_chemical_formulas': 0
            }
        }
        
        # Calculate distributions and statistics
        question_lengths = []
        option_counts = []
        
        for question in questions:
            # Subject distribution
            subject = question.subject_area
            summary['subject_distribution'][subject] = summary['subject_distribution'].get(subject, 0) + 1
            
            # Question type distribution
            q_type = question.question_type
            summary['question_type_distribution'][q_type] = summary['question_type_distribution'].get(q_type, 0) + 1
            
            # Option count distribution
            num_options = len(question.options)
            summary['option_count_distribution'][str(num_options)] = summary['option_count_distribution'].get(str(num_options), 0) + 1
            
            # Statistics
            question_lengths.append(len(question.question_text))
            option_counts.append(num_options)
            
            if question.metadata.get('has_mathematical_notation'):
                summary['statistics']['questions_with_math_notation'] += 1
            if question.metadata.get('has_equations'):
                summary['statistics']['questions_with_equations'] += 1
            if question.metadata.get('has_chemical_formulas'):
                summary['statistics']['questions_with_chemical_formulas'] += 1
        
        # Calculate averages
        summary['statistics']['avg_question_length'] = sum(question_lengths) / len(question_lengths)
        summary['statistics']['avg_options_per_question'] = sum(option_counts) / len(option_counts)
        
        return summary

def main():
    # Read the extracted text
    with open('extracted_text.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Initialize parser
    parser = AdvancedQuestionParser()
    
    # Extract questions
    logger.info("Extracting questions with advanced parser...")
    questions = parser.extract_questions_from_text(text)
    
    # Filter valid questions
    valid_questions = [q for q in questions if parser.validate_question(q)]
    
    # Extract answers if available
    answers = parser.extract_answers_from_text(text)
    
    # Generate summary
    summary = parser.generate_question_summary(valid_questions)
    
    # Prepare results for saving
    results = {
        'summary': summary,
        'questions': [asdict(q) for q in valid_questions],
        'answers': answers,
        'extraction_metadata': {
            'total_lines_processed': len(text.split('\n')),
            'extraction_timestamp': '2024-01-01T00:00:00Z',  # You can add actual timestamp
            'parser_version': '2.0'
        }
    }
    
    # Save results
    with open('advanced_questions.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\nAdvanced parsing results:")
    print(f"- Total valid questions: {summary['total_questions']}")
    print(f"- Subject distribution: {summary['subject_distribution']}")
    print(f"- Question types: {summary['question_type_distribution']}")
    print(f"- Option counts: {summary['option_count_distribution']}")
    print(f"- Average question length: {summary['statistics']['avg_question_length']:.1f} characters")
    print(f"- Average options per question: {summary['statistics']['avg_options_per_question']:.2f}")
    print(f"- Questions with math notation: {summary['statistics']['questions_with_math_notation']}")
    print(f"- Questions with equations: {summary['statistics']['questions_with_equations']}")
    
    # Show sample questions
    print(f"\nSample questions:")
    for i, question in enumerate(valid_questions[:3]):
        print(f"\nQuestion {question.question_number} ({question.subject_area}):")
        print(f"Text: {question.question_text[:100]}...")
        print(f"Options: {len(question.options)} options")
        print(f"Type: {question.question_type}")
        print(f"Metadata: {question.metadata}")

if __name__ == "__main__":
    main()
