"""
Question Parser
Parses cleaned text and extracts questions with metadata for RAG
"""

import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)


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
    
    # Features
    has_formulas: bool = False
    has_calculations: bool = False
    has_multiline: bool = False
    
    # Source info
    source_file: str = ""
    exam_type: str = ""
    year: Optional[int] = None
    
    # For RAG
    embedding_text: str = ""
    raw_text: str = ""


class QuestionParser:
    """Parse questions from cleaned text"""
    
    def __init__(self):
        """Initialize parser with patterns"""
        self._compile_patterns()
        self._load_subject_keywords()
    
    def _compile_patterns(self):
        """Compile all regex patterns"""
        
        # Question number patterns (in priority order)
        self.question_patterns = [
            (re.compile(r'^(\d+)\)\s+(.+)$'), 'parenthesis'),  # 1) Question
            (re.compile(r'^Q\.?\s*(\d+)\s+(.+)$', re.IGNORECASE), 'q_dot'),  # Q.1 Question
            (re.compile(r'^(\d+)\.\s+(.+)$'), 'dot'),  # 1. Question
        ]
        
        # Option patterns (in priority order)
        self.option_patterns = [
            (re.compile(r'^([A-D])\.\s*(.*)$'), 'upper_dot'),  # A. Option
            (re.compile(r'^([a-d])\.\s*(.*)$'), 'lower_dot'),  # a. Option
            (re.compile(r'^([A-D])\)\s*(.*)$'), 'upper_paren'),  # A) Option
            (re.compile(r'^([a-d])\)\s*(.*)$'), 'lower_paren'),  # a) Option
        ]
        
        # Solution markers
        self.solution_pattern = re.compile(r'^(?:Sol|Solution|Answer|Explanation)\s*:\s*(.+)$', re.IGNORECASE)
        
        # Answer markers
        self.correct_marker = re.compile(r'\(Correct\)\s*$', re.IGNORECASE)
        
        # Exam tag patterns (to remove)
        self.exam_tag_pattern = re.compile(
            r'\(?\s*(?:NET|NUST|MDCAT)[-\s]*\d*\s*\(?\d{1,2}[-\s]?\w*[-\s]?\d{4}\)?\s*\)?',
            re.IGNORECASE
        )
        
        # Formula indicators
        self.formula_indicators = re.compile(r'[=+\-*/^√∫∑∆πλθαβγ]|\\frac|\\sqrt')
        
        # Calculation indicators
        self.calculation_indicators = re.compile(r'\d+\s*[+\-×÷*/]\s*\d+|=\s*\d+')
    
    def _load_subject_keywords(self):
        """Load subject classification keywords"""
        self.subject_keywords = {
            'physics': [
                'velocity', 'acceleration', 'force', 'energy', 'momentum', 'mass',
                'electric', 'magnetic', 'wave', 'frequency', 'wavelength', 'photon',
                'quantum', 'nuclear', 'atom', 'electron', 'proton', 'neutron',
                'circuit', 'voltage', 'current', 'resistance', 'capacitor',
                'motion', 'gravity', 'friction', 'pressure', 'temperature',
                'thermodynamics', 'optics', 'lens', 'mirror', 'refraction',
                'kinetic', 'potential', 'joule', 'watt', 'newton', 'coulomb'
            ],
            'chemistry': [
                'atom', 'molecule', 'compound', 'element', 'reaction', 'bond',
                'acid', 'base', 'pH', 'oxidation', 'reduction', 'catalyst',
                'organic', 'inorganic', 'alkane', 'alkene', 'alkyne', 'benzene',
                'electron', 'ion', 'cation', 'anion', 'isotope', 'mole',
                'solution', 'solvent', 'solute', 'concentration', 'molarity',
                'periodic', 'valency', 'electronegativity', 'hybridization',
                'equilibrium', 'stoichiometry', 'enthalpy', 'entropy'
            ],
            'biology': [
                'cell', 'DNA', 'RNA', 'gene', 'protein', 'enzyme', 'chromosome',
                'mitochondria', 'chloroplast', 'nucleus', 'ribosome', 'membrane',
                'photosynthesis', 'respiration', 'metabolism', 'glycolysis',
                'mitosis', 'meiosis', 'tissue', 'organ', 'blood', 'heart',
                'nervous', 'brain', 'hormone', 'reproduction', 'evolution',
                'bacteria', 'virus', 'fungi', 'plant', 'animal', 'species',
                'ecosystem', 'genetics', 'mutation', 'allele', 'phenotype'
            ],
            'mathematics': [
                'equation', 'function', 'derivative', 'integral', 'limit',
                'matrix', 'determinant', 'vector', 'trigonometry', 'logarithm',
                'polynomial', 'quadratic', 'linear', 'parabola', 'hyperbola',
                'probability', 'statistics', 'mean', 'median', 'variance',
                'sequence', 'series', 'geometric', 'arithmetic', 'permutation',
                'combination', 'binomial', 'cosine', 'sine', 'tangent',
                'complex', 'imaginary', 'real', 'rational', 'irrational'
            ],
            'english': [
                'grammar', 'vocabulary', 'synonym', 'antonym', 'sentence',
                'noun', 'verb', 'adjective', 'adverb', 'pronoun',
                'tense', 'preposition', 'conjunction', 'article',
                'comprehension', 'passage', 'meaning', 'context'
            ]
        }
    
    def clean_text(self, text: str) -> str:
        """Additional cleaning for parsing"""
        # Remove exam tags
        text = self.exam_tag_pattern.sub('', text)
        # Clean extra whitespace
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()
    
    def detect_question_start(self, line: str) -> Optional[Tuple[int, str, str]]:
        """
        Detect if line starts a question
        
        Returns:
            Tuple of (question_number, question_text, format_type) or None
        """
        line = line.strip()
        if not line:
            return None
        
        for pattern, format_type in self.question_patterns:
            match = pattern.match(line)
            if match:
                try:
                    q_num = int(match.group(1))
                    q_text = match.group(2).strip() if len(match.groups()) > 1 else ""
                    return (q_num, q_text, format_type)
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def detect_option(self, line: str) -> Optional[Tuple[str, str, str]]:
        """
        Detect if line is an option
        
        Returns:
            Tuple of (option_label, option_text, format_type) or None
        """
        line = line.strip()
        if not line:
            return None
        
        for pattern, format_type in self.option_patterns:
            match = pattern.match(line)
            if match:
                label = match.group(1).upper()  # Normalize to uppercase
                text = match.group(2).strip()
                return (label, text, format_type)
        
        return None
    
    def detect_solution(self, line: str) -> Optional[str]:
        """Detect if line starts a solution"""
        match = self.solution_pattern.match(line.strip())
        if match:
            return match.group(1).strip()
        return None
    
    def extract_answer_from_option(self, option_text: str) -> Tuple[str, Optional[str]]:
        """
        Extract (Correct) marker from option text
        
        Returns:
            Tuple of (cleaned_text, answer_label or None)
        """
        match = self.correct_marker.search(option_text)
        if match:
            cleaned = self.correct_marker.sub('', option_text).strip()
            return (cleaned, 'CORRECT')
        return (option_text, None)
    
    def parse_questions_from_text(self, text: str, source_file: str = "") -> List[Question]:
        """
        Parse all questions from text
        
        Args:
            text: Cleaned text content
            source_file: Source filename
            
        Returns:
            List of Question objects
        """
        lines = text.split('\n')
        questions = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check for question start
            q_match = self.detect_question_start(line)
            if q_match:
                q_num, q_text, q_format = q_match
                
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
                    if self.detect_option(next_line):
                        break
                    
                    # Check if this is a new question
                    if self.detect_question_start(next_line):
                        break
                    
                    # Otherwise, it's part of the question
                    question_lines.append(next_line)
                    i += 1
                
                full_question = ' '.join(question_lines).strip()
                
                # Extract options
                options = []
                correct_answer = None
                option_format = None
                
                while i < len(lines):
                    opt_line = lines[i].strip()
                    
                    if not opt_line:
                        i += 1
                        continue
                    
                    # Check for solution
                    sol_text = self.detect_solution(opt_line)
                    if sol_text:
                        break
                    
                    # Check for next question
                    if self.detect_question_start(opt_line):
                        break
                    
                    # Check for option
                    opt_match = self.detect_option(opt_line)
                    if opt_match:
                        opt_label, opt_text, opt_format = opt_match
                        option_format = opt_format
                        
                        # Continue reading multi-line options
                        option_lines = [opt_text] if opt_text else []
                        i += 1
                        
                        while i < len(lines):
                            peek_line = lines[i].strip()
                            
                            if not peek_line:
                                i += 1
                                continue
                            
                            # Stop if we hit next option, question, or solution
                            if (self.detect_option(peek_line) or 
                                self.detect_question_start(peek_line) or
                                self.detect_solution(peek_line)):
                                break
                            
                            # This is a continuation of the option
                            option_lines.append(peek_line)
                            i += 1
                        
                        full_option = ' '.join(option_lines).strip()
                        
                        # Check for (Correct) marker
                        cleaned_option, is_correct = self.extract_answer_from_option(full_option)
                        
                        if is_correct:
                            correct_answer = opt_label
                        
                        options.append({
                            'label': opt_label,
                            'text': cleaned_option
                        })
                    else:
                        # Unknown line, skip it
                        i += 1
                
                # Extract solution if present
                solution = None
                if i < len(lines):
                    sol_text = self.detect_solution(lines[i].strip())
                    if sol_text:
                        solution_lines = [sol_text]
                        i += 1
                        
                        # Continue reading multi-line solution
                        while i < len(lines):
                            peek_line = lines[i].strip()
                            
                            if not peek_line:
                                i += 1
                                continue
                            
                            # Stop if we hit next question
                            if self.detect_question_start(peek_line):
                                break
                            
                            solution_lines.append(peek_line)
                            i += 1
                        
                        solution = ' '.join(solution_lines).strip()
                
                # Only add if we have valid question and options
                if full_question and len(options) >= 2:
                    # Create question object
                    question = self.create_question(
                        question_number=q_num,
                        question_text=full_question,
                        options=options,
                        correct_answer=correct_answer,
                        solution=solution,
                        source_file=source_file
                    )
                    questions.append(question)
                    
                    logger.debug(f"Parsed Q{q_num}: {len(options)} options, "
                               f"answer={'Yes' if correct_answer else 'No'}")
            else:
                i += 1
        
        return questions
    
    def create_question(
        self,
        question_number: int,
        question_text: str,
        options: List[Dict],
        correct_answer: Optional[str],
        solution: Optional[str],
        source_file: str
    ) -> Question:
        """Create a Question object with metadata"""
        
        # Clean text
        question_text = self.clean_text(question_text)
        
        # Extract exam info from filename
        exam_type, year = self.extract_exam_info(source_file)
        
        # Generate ID
        question_id = self.generate_question_id(exam_type, year, question_number)
        
        # Classify subject
        subject = self.classify_subject(question_text, options)
        
        # Detect features
        has_formulas = bool(self.formula_indicators.search(question_text))
        has_calculations = bool(self.calculation_indicators.search(question_text))
        has_multiline = '\n' in question_text or any('\n' in opt['text'] for opt in options)
        
        # Generate embedding text
        embedding_text = self.generate_embedding_text(
            question_text, options, subject, correct_answer
        )
        
        # Create raw text representation
        raw_text = f"Q{question_number}. {question_text}\n"
        for opt in options:
            raw_text += f"{opt['label']}. {opt['text']}\n"
        
        return Question(
            id=question_id,
            question_number=question_number,
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            solution=solution,
            subject=subject,
            has_formulas=has_formulas,
            has_calculations=has_calculations,
            has_multiline=has_multiline,
            source_file=source_file,
            exam_type=exam_type,
            year=year,
            embedding_text=embedding_text,
            raw_text=raw_text
        )
    
    def extract_exam_info(self, filename: str) -> Tuple[str, Optional[int]]:
        """Extract exam type and year from filename"""
        filename = filename.upper()
        
        # Detect exam type
        exam_type = "GENERAL"
        if "MDCAT" in filename:
            exam_type = "MDCAT"
        elif "NET" in filename or "NUST" in filename:
            exam_type = "NET"
        
        # Extract year
        year_match = re.search(r'20\d{2}', filename)
        year = int(year_match.group(0)) if year_match else None
        
        return exam_type, year
    
    def classify_subject(self, question_text: str, options: List[Dict]) -> str:
        """Classify question subject using keyword matching"""
        text = question_text.lower()
        
        # Add option text for better classification
        for opt in options:
            text += " " + opt['text'].lower()
        
        # Score each subject
        scores = {}
        for subject, keywords in self.subject_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 1
            scores[subject] = score
        
        # Return subject with highest score
        if scores:
            best_subject = max(scores, key=scores.get)
            if scores[best_subject] > 0:
                return best_subject
        
        return "general"
    
    def generate_question_id(self, exam_type: str, year: Optional[int], q_num: int) -> str:
        """Generate unique question ID"""
        year_str = str(year) if year else "UNKNOWN"
        return f"{exam_type}_{year_str}_Q{q_num:03d}"
    
    def generate_embedding_text(
        self,
        question_text: str,
        options: List[Dict],
        subject: str,
        correct_answer: Optional[str]
    ) -> str:
        """Generate optimized text for vector embedding"""
        parts = [f"Question: {question_text}"]
        
        # Add options
        option_texts = [opt['text'] for opt in options if opt['text']]
        if option_texts:
            parts.append(f"Options: {' | '.join(option_texts)}")
        
        # Add subject
        parts.append(f"Subject: {subject}")
        
        # Add answer if available
        if correct_answer:
            # Find the answer text
            for opt in options:
                if opt['label'] == correct_answer:
                    parts.append(f"Answer: {opt['text']}")
                    break
        
        return " ".join(parts)
    
    def save_to_json(self, questions: List[Question], output_path: Path) -> bool:
        """Save questions to JSON file"""
        try:
            # Convert to dict
            questions_dict = [asdict(q) for q in questions]
            
            # Create output structure
            output = {
                'metadata': {
                    'total_questions': len(questions),
                    'extraction_date': datetime.now().isoformat(),
                    'parser_version': '1.0'
                },
                'questions': questions_dict
            }
            
            # Add summary statistics
            if questions:
                output['summary'] = self.generate_summary(questions)
            
            # Save to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(questions)} questions to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")
            return False
    
    def generate_summary(self, questions: List[Question]) -> Dict:
        """Generate summary statistics"""
        summary = {
            'total_questions': len(questions),
            'by_subject': {},
            'by_exam_type': {},
            'with_answers': 0,
            'with_solutions': 0,
            'with_formulas': 0,
            'avg_options': 0
        }
        
        total_options = 0
        
        for q in questions:
            # Subject distribution
            summary['by_subject'][q.subject] = summary['by_subject'].get(q.subject, 0) + 1
            
            # Exam type distribution
            if q.exam_type:
                summary['by_exam_type'][q.exam_type] = summary['by_exam_type'].get(q.exam_type, 0) + 1
            
            # Features
            if q.correct_answer:
                summary['with_answers'] += 1
            if q.solution:
                summary['with_solutions'] += 1
            if q.has_formulas:
                summary['with_formulas'] += 1
            
            total_options += len(q.options)
        
        summary['avg_options'] = round(total_options / len(questions), 2) if questions else 0
        
        return summary


def main():
    """Main function for testing"""
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python question_parser.py <text_file>")
        return
    
    text_file = Path(sys.argv[1])
    
    if not text_file.exists():
        print(f"File not found: {text_file}")
        return
    
    # Read text
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Parse
    parser = QuestionParser()
    questions = parser.parse_questions_from_text(text, text_file.name)
    
    print(f"\nParsed {len(questions)} questions")
    
    # Show first few questions
    for q in questions[:3]:
        print(f"\n{'='*60}")
        print(f"Q{q.question_number} [{q.subject}]")
        print(f"Text: {q.question_text[:100]}...")
        print(f"Options: {len(q.options)}")
        print(f"Answer: {q.correct_answer or 'N/A'}")
        print(f"Solution: {'Yes' if q.solution else 'No'}")
    
    # Save to JSON
    output_path = text_file.parent / f"{text_file.stem}_parsed.json"
    parser.save_to_json(questions, output_path)
    print(f"\n✅ Saved to: {output_path}")


if __name__ == "__main__":
    main()

