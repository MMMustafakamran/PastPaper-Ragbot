import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Question:
    question_number: str
    question_text: str
    options: List[str]
    answer: Optional[str] = None
    explanation: Optional[str] = None
    subject_area: Optional[str] = None
    difficulty: Optional[str] = None

class ImprovedQuestionParser:
    def __init__(self):
        # Patterns for different question formats
        self.question_patterns = [
            r'^(\d+)\.\s+(.+?)(?=\n[a-d]\.)',  # Standard numbered questions
            r'^(\d+)\.\s+(.+?)(?=\n[a-e]\.)',  # Questions with 5 options
        ]
        
        # Option patterns
        self.option_patterns = [
            r'^([a-e])\.\s*(.+?)(?=\n[a-e]\.|\n\d+\.|\nwww\.|$)',  # Standard options
            r'^([a-e])\.\s*(.+?)$',  # Last option in sequence
        ]
        
        # Subject area patterns
        self.subject_patterns = {
            'mathematics': [r'sin|cos|tan|log|integral|derivative|function|equation|triangle|circle|ellipse|hyperbola|parabola|matrix|vector|complex|limit|continuity'],
            'physics': [r'force|energy|momentum|velocity|acceleration|electric|magnetic|wave|frequency|wavelength|quantum|thermodynamics|optics'],
            'chemistry': [r'atom|molecule|bond|reaction|compound|element|organic|inorganic|acid|base|pH|oxidation|reduction'],
            'english': [r'synonym|antonym|grammar|vocabulary|sentence|paragraph|essay|literature|poetry|novel'],
            'general_knowledge': [r'country|capital|president|prime minister|award|prize|sport|cricket|football|history|geography']
        }
    
    def extract_questions_from_text(self, text: str) -> List[Question]:
        """Extract all questions from the text with improved parsing"""
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
                options = []
                j = i + 1
                
                # Look for options in the next lines
                while j < len(lines):
                    option_line = lines[j].strip()
                    
                    # Skip empty lines
                    if not option_line:
                        j += 1
                        continue
                    
                    # Check if this is an option
                    option_match = self._match_option(option_line)
                    if option_match:
                        option_letter, option_text = option_match
                        options.append(f"{option_letter}. {option_text}")
                        j += 1
                    else:
                        # Check if this is the start of a new question
                        if self._match_question_start(option_line) or 'www.educatedzone.com' in option_line:
                            break
                        else:
                            # This might be a continuation of the previous option
                            if options:
                                options[-1] += " " + option_line
                            j += 1
                
                # Create question object
                if options:  # Only add if we found options
                    question = Question(
                        question_number=question_num,
                        question_text=question_text.strip(),
                        options=options,
                        subject_area=self._detect_subject_area(question_text)
                    )
                    questions.append(question)
                
                i = j
            else:
                i += 1
        
        return questions
    
    def _match_question_start(self, line: str) -> Optional[tuple]:
        """Check if line starts a new question and extract number and text"""
        # Pattern for numbered questions
        pattern = r'^(\d+)\.\s+(.+)$'
        match = re.match(pattern, line)
        
        if match:
            question_num = match.group(1)
            question_text = match.group(2)
            return (question_num, question_text)
        
        return None
    
    def _match_option(self, line: str) -> Optional[tuple]:
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
        
        for subject, patterns in self.subject_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    return subject
        
        return 'general'
    
    def extract_answers_from_text(self, text: str) -> Dict[str, str]:
        """Extract answers if they exist in the text"""
        answers = {}
        
        # Look for answer patterns
        answer_patterns = [
            r'Answer\s*:\s*([a-e])',
            r'Correct\s*Answer\s*:\s*([a-e])',
            r'Solution\s*:\s*([a-e])',
            r'Key\s*:\s*([a-e])',
        ]
        
        for pattern in answer_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # This is a simplified approach - in reality, you'd need to match
                # answers to specific questions based on context
                answers[match] = match
        
        return answers
    
    def clean_question_text(self, text: str) -> str:
        """Clean and normalize question text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors
        text = text.replace('sin-1', 'sin⁻¹')
        text = text.replace('cos-1', 'cos⁻¹')
        text = text.replace('tan-1', 'tan⁻¹')
        
        return text.strip()
    
    def validate_question(self, question: Question) -> bool:
        """Validate that a question has the required components"""
        return (
            question.question_number and
            question.question_text and
            len(question.options) >= 2 and
            all(option.strip() for option in question.options)
        )

def main():
    # Read the extracted text
    with open('extracted_text.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Initialize parser
    parser = ImprovedQuestionParser()
    
    # Extract questions
    print("Extracting questions with improved parser...")
    questions = parser.extract_questions_from_text(text)
    
    # Filter valid questions
    valid_questions = [q for q in questions if parser.validate_question(q)]
    
    # Extract answers if available
    answers = parser.extract_answers_from_text(text)
    
    # Clean question texts
    for question in valid_questions:
        question.question_text = parser.clean_question_text(question.question_text)
        question.options = [parser.clean_question_text(opt) for opt in question.options]
    
    # Save results
    results = {
        'total_questions': len(valid_questions),
        'questions': [
            {
                'question_number': q.question_number,
                'question_text': q.question_text,
                'options': q.options,
                'subject_area': q.subject_area,
                'num_options': len(q.options)
            }
            for q in valid_questions
        ],
        'subject_distribution': {},
        'statistics': {
            'questions_with_4_options': 0,
            'questions_with_5_options': 0,
            'average_options_per_question': 0
        }
    }
    
    # Calculate statistics
    option_counts = [len(q.options) for q in valid_questions]
    results['statistics']['questions_with_4_options'] = option_counts.count(4)
    results['statistics']['questions_with_5_options'] = option_counts.count(5)
    results['statistics']['average_options_per_question'] = sum(option_counts) / len(option_counts) if option_counts else 0
    
    # Subject distribution
    for question in valid_questions:
        subject = question.subject_area
        results['subject_distribution'][subject] = results['subject_distribution'].get(subject, 0) + 1
    
    # Save to file
    with open('improved_questions.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\nImproved parsing results:")
    print(f"- Total valid questions: {len(valid_questions)}")
    print(f"- Questions with 4 options: {results['statistics']['questions_with_4_options']}")
    print(f"- Questions with 5 options: {results['statistics']['questions_with_5_options']}")
    print(f"- Average options per question: {results['statistics']['average_options_per_question']:.2f}")
    print(f"- Subject distribution: {results['subject_distribution']}")
    
    # Show sample questions
    print(f"\nSample questions:")
    for i, question in enumerate(valid_questions[:3]):
        print(f"\nQuestion {question.question_number}:")
        print(f"Text: {question.question_text[:100]}...")
        print(f"Options: {len(question.options)} options")
        print(f"Subject: {question.subject_area}")
        for j, option in enumerate(question.options[:2]):  # Show first 2 options
            print(f"  {option[:50]}...")

if __name__ == "__main__":
    main()
