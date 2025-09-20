import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
from datetime import datetime

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
    source: str = "NUST Engineering Past Paper 4"

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class FinalQuestionParser:
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
        
        # Enhanced subject area detection with more specific patterns
        self.subject_patterns = {
            'mathematics': [
                r'sin|cos|tan|log|integral|derivative|function|equation|triangle|circle|ellipse|hyperbola|parabola|matrix|vector|complex|limit|continuity|trigonometry|calculus|geometry|algebra|probability|statistics|permutation|combination|binomial|series|sequence|convergence|divergence|asymptote|tangent|normal|slope|gradient|area|volume|surface|integration|differentiation'
            ],
            'physics': [
                r'force|energy|momentum|velocity|acceleration|electric|magnetic|wave|frequency|wavelength|quantum|thermodynamics|optics|mechanics|kinematics|dynamics|electromagnetism|nuclear|atomic|molecular|particle|photon|electron|proton|neutron|field|potential|current|resistance|capacitance|inductance|oscillation|vibration|resonance|interference|diffraction|polarization|reflection|refraction'
            ],
            'chemistry': [
                r'atom|molecule|bond|reaction|compound|element|organic|inorganic|acid|base|pH|oxidation|reduction|stoichiometry|thermodynamics|kinetics|equilibrium|electrochemistry|organic chemistry|inorganic chemistry|alkane|alkene|alkyne|alcohol|aldehyde|ketone|carboxylic acid|ester|amine|amide|polymer|catalyst|enzyme|buffer|salt|ion|cation|anion|isotope|radioactive|half-life'
            ],
            'english': [
                r'synonym|antonym|grammar|vocabulary|sentence|paragraph|essay|literature|poetry|novel|comprehension|reading|writing|language|linguistics|etymology|phonics|pronunciation|spelling|punctuation|syntax|semantics|morphology|phonetics|rhetoric|figurative|metaphor|simile|alliteration|assonance|consonance|rhyme|meter|stanza|verse|prose|drama|fiction|non-fiction'
            ],
            'general_knowledge': [
                r'country|capital|president|prime minister|award|prize|sport|cricket|football|history|geography|current affairs|politics|economics|culture|religion|science|technology|environment|health|medicine|biology|zoology|botany|ecology|conservation|climate|weather|astronomy|space|universe|planet|star|galaxy|solar system'
            ],
            'computer_science': [
                r'programming|algorithm|data structure|computer|software|hardware|network|database|artificial intelligence|machine learning|cybersecurity|web development|mobile development|operating system|memory|processor|storage|input|output|user interface|graphics|multimedia|simulation|modeling|optimization|complexity|efficiency|security|privacy|encryption|decryption'
            ]
        }
        
        # Answer patterns - more comprehensive
        self.answer_patterns = [
            r'Answer\s*:\s*([a-e])',
            r'Correct\s*Answer\s*:\s*([a-e])',
            r'Solution\s*:\s*([a-e])',
            r'Key\s*:\s*([a-e])',
            r'Ans\s*:\s*([a-e])',
            r'Right\s*Answer\s*:\s*([a-e])',
            r'Correct\s*:\s*([a-e])',
        ]
        
        # Difficulty indicators
        self.difficulty_indicators = {
            'easy': [r'simple|basic|elementary|straightforward|direct'],
            'medium': [r'moderate|intermediate|standard|typical'],
            'hard': [r'complex|difficult|challenging|advanced|sophisticated|intricate']
        }
    
    def extract_questions_from_text(self, text: str) -> List[Question]:
        """Extract all questions from the text with final parsing"""
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
                        difficulty=self._detect_difficulty(question_text),
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
        elif 'identify' in text_lower or 'determine' in text_lower:
            return 'identification'
        else:
            return 'multiple_choice'
    
    def _detect_difficulty(self, question_text: str) -> str:
        """Detect question difficulty based on content"""
        text_lower = question_text.lower()
        
        for difficulty, patterns in self.difficulty_indicators.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return difficulty
        
        # Default to medium if no clear indicators
        return 'medium'
    
    def _extract_metadata(self, question_text: str, options: List[str]) -> Dict[str, Any]:
        """Extract additional metadata from the question"""
        metadata = {
            'num_options': len(options),
            'has_mathematical_notation': bool(re.search(r'[π√∑∫∂∆∇∞±×÷]', question_text)),
            'has_chemical_formulas': bool(re.search(r'[A-Z][a-z]?\d*', question_text)),
            'has_equations': bool(re.search(r'[=<>≤≥]', question_text)),
            'has_functions': bool(re.search(r'f\(|g\(|h\(', question_text)),
            'has_coordinates': bool(re.search(r'\([0-9,-]+\)', question_text)),
            'has_angles': bool(re.search(r'[0-9]+°|[0-9]+π', question_text)),
            'question_length': len(question_text),
            'avg_option_length': sum(len(opt) for opt in options) / len(options) if options else 0,
            'complexity_score': self._calculate_complexity_score(question_text, options)
        }
        
        return metadata
    
    def _calculate_complexity_score(self, question_text: str, options: List[str]) -> float:
        """Calculate a complexity score for the question"""
        score = 0
        
        # Length factor
        score += min(len(question_text) / 100, 2)
        
        # Mathematical notation factor
        if re.search(r'[π√∑∫∂∆∇∞±×÷]', question_text):
            score += 1
        
        # Equation factor
        if re.search(r'[=<>≤≥]', question_text):
            score += 0.5
        
        # Function factor
        if re.search(r'f\(|g\(|h\(', question_text):
            score += 0.5
        
        # Option complexity
        avg_option_length = sum(len(opt) for opt in options) / len(options) if options else 0
        score += min(avg_option_length / 50, 1)
        
        return round(score, 2)
    
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
            'Δ': 'Δ',
            '∑': '∑',
            '∫': '∫',
            '∞': '∞',
            '±': '±',
            '×': '×',
            '÷': '÷',
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
    
    def generate_comprehensive_summary(self, questions: List[Question]) -> Dict[str, Any]:
        """Generate a comprehensive summary of the questions"""
        if not questions:
            return {}
        
        summary = {
            'total_questions': len(questions),
            'subject_distribution': {},
            'question_type_distribution': {},
            'difficulty_distribution': {},
            'option_count_distribution': {},
            'statistics': {
                'avg_question_length': 0,
                'avg_options_per_question': 0,
                'avg_complexity_score': 0,
                'questions_with_math_notation': 0,
                'questions_with_equations': 0,
                'questions_with_chemical_formulas': 0,
                'questions_with_functions': 0,
                'questions_with_coordinates': 0,
                'questions_with_angles': 0
            },
            'quality_metrics': {
                'valid_questions': 0,
                'questions_with_4_options': 0,
                'questions_with_5_options': 0,
                'mathematical_questions': 0,
                'physics_questions': 0,
                'chemistry_questions': 0,
                'english_questions': 0,
                'general_knowledge_questions': 0
            }
        }
        
        # Calculate distributions and statistics
        question_lengths = []
        option_counts = []
        complexity_scores = []
        
        for question in questions:
            # Subject distribution
            subject = question.subject_area
            summary['subject_distribution'][subject] = summary['subject_distribution'].get(subject, 0) + 1
            
            # Question type distribution
            q_type = question.question_type
            summary['question_type_distribution'][q_type] = summary['question_type_distribution'].get(q_type, 0) + 1
            
            # Difficulty distribution
            difficulty = question.difficulty
            summary['difficulty_distribution'][difficulty] = summary['difficulty_distribution'].get(difficulty, 0) + 1
            
            # Option count distribution
            num_options = len(question.options)
            summary['option_count_distribution'][str(num_options)] = summary['option_count_distribution'].get(str(num_options), 0) + 1
            
            # Statistics
            question_lengths.append(len(question.question_text))
            option_counts.append(num_options)
            complexity_scores.append(question.metadata.get('complexity_score', 0))
            
            # Feature detection
            if question.metadata.get('has_mathematical_notation'):
                summary['statistics']['questions_with_math_notation'] += 1
            if question.metadata.get('has_equations'):
                summary['statistics']['questions_with_equations'] += 1
            if question.metadata.get('has_chemical_formulas'):
                summary['statistics']['questions_with_chemical_formulas'] += 1
            if question.metadata.get('has_functions'):
                summary['statistics']['questions_with_functions'] += 1
            if question.metadata.get('has_coordinates'):
                summary['statistics']['questions_with_coordinates'] += 1
            if question.metadata.get('has_angles'):
                summary['statistics']['questions_with_angles'] += 1
            
            # Quality metrics
            if self.validate_question(question):
                summary['quality_metrics']['valid_questions'] += 1
            
            if num_options == 4:
                summary['quality_metrics']['questions_with_4_options'] += 1
            elif num_options == 5:
                summary['quality_metrics']['questions_with_5_options'] += 1
            
            # Subject-specific counts
            if subject == 'mathematics':
                summary['quality_metrics']['mathematical_questions'] += 1
            elif subject == 'physics':
                summary['quality_metrics']['physics_questions'] += 1
            elif subject == 'chemistry':
                summary['quality_metrics']['chemistry_questions'] += 1
            elif subject == 'english':
                summary['quality_metrics']['english_questions'] += 1
            elif subject == 'general_knowledge':
                summary['quality_metrics']['general_knowledge_questions'] += 1
        
        # Calculate averages
        summary['statistics']['avg_question_length'] = sum(question_lengths) / len(question_lengths)
        summary['statistics']['avg_options_per_question'] = sum(option_counts) / len(option_counts)
        summary['statistics']['avg_complexity_score'] = sum(complexity_scores) / len(complexity_scores)
        
        return summary

def main():
    # Read the extracted text
    with open('extracted_text.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Initialize parser
    parser = FinalQuestionParser()
    
    # Extract questions
    logger.info("Extracting questions with final parser...")
    questions = parser.extract_questions_from_text(text)
    
    # Filter valid questions
    valid_questions = [q for q in questions if parser.validate_question(q)]
    
    # Extract answers if available
    answers = parser.extract_answers_from_text(text)
    
    # Generate comprehensive summary
    summary = parser.generate_comprehensive_summary(valid_questions)
    
    # Prepare results for saving
    results = {
        'summary': summary,
        'questions': [asdict(q) for q in valid_questions],
        'answers': answers,
        'extraction_metadata': {
            'total_lines_processed': len(text.split('\n')),
            'extraction_timestamp': datetime.now().isoformat(),
            'parser_version': '3.0',
            'source_file': 'NUST-Engineering-Pastpaper-4(educatedzone.com).pdf'
        }
    }
    
    # Save results
    with open('final_questions.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print comprehensive summary
    print(f"\nFinal parsing results:")
    print(f"- Total valid questions: {summary['total_questions']}")
    print(f"- Subject distribution: {summary['subject_distribution']}")
    print(f"- Question types: {summary['question_type_distribution']}")
    print(f"- Difficulty levels: {summary['difficulty_distribution']}")
    print(f"- Option counts: {summary['option_count_distribution']}")
    print(f"- Average question length: {summary['statistics']['avg_question_length']:.1f} characters")
    print(f"- Average options per question: {summary['statistics']['avg_options_per_question']:.2f}")
    print(f"- Average complexity score: {summary['statistics']['avg_complexity_score']:.2f}")
    print(f"- Questions with math notation: {summary['statistics']['questions_with_math_notation']}")
    print(f"- Questions with equations: {summary['statistics']['questions_with_equations']}")
    print(f"- Questions with functions: {summary['statistics']['questions_with_functions']}")
    print(f"- Questions with coordinates: {summary['statistics']['questions_with_coordinates']}")
    print(f"- Questions with angles: {summary['statistics']['questions_with_angles']}")
    
    # Quality metrics
    print(f"\nQuality metrics:")
    print(f"- Valid questions: {summary['quality_metrics']['valid_questions']}")
    print(f"- Questions with 4 options: {summary['quality_metrics']['questions_with_4_options']}")
    print(f"- Questions with 5 options: {summary['quality_metrics']['questions_with_5_options']}")
    print(f"- Mathematical questions: {summary['quality_metrics']['mathematical_questions']}")
    print(f"- Physics questions: {summary['quality_metrics']['physics_questions']}")
    print(f"- Chemistry questions: {summary['quality_metrics']['chemistry_questions']}")
    print(f"- English questions: {summary['quality_metrics']['english_questions']}")
    print(f"- General knowledge questions: {summary['quality_metrics']['general_knowledge_questions']}")
    
    # Show sample questions
    print(f"\nSample questions:")
    for i, question in enumerate(valid_questions[:3]):
        print(f"\nQuestion {question.question_number} ({question.subject_area}, {question.difficulty}):")
        print(f"Text: {question.question_text[:100]}...")
        print(f"Options: {len(question.options)} options")
        print(f"Type: {question.question_type}")
        print(f"Complexity: {question.metadata.get('complexity_score', 0)}")
        print(f"Features: {[k for k, v in question.metadata.items() if v and k.startswith('has_')]}")

if __name__ == "__main__":
    main()
