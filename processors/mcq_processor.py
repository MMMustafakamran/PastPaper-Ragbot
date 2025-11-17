"""
MCQ Processing Pipeline for RAG Dataset Generation
Converts raw MCQ text files into RAG-optimized JSON format
"""

import re
import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime


class MCQParser:
    """Parse MCQ text files into structured format"""
    
    def __init__(self):
        self.question_pattern = re.compile(r'^\d+\.\s+(.+)$', re.MULTILINE)
        self.option_pattern = re.compile(r'^\(([a-d])\)\s+(.+)$', re.MULTILINE)
        self.answer_pattern = re.compile(r'^ans:([a-d])$', re.MULTILINE | re.IGNORECASE)
    
    def parse_file(self, filepath: str) -> List[Dict]:
        """Parse MCQ file and extract questions"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by empty lines to separate questions
        questions = []
        current_block = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line:
                current_block.append(line)
            elif current_block:
                # Process the block
                question = self._parse_question_block(current_block)
                if question:
                    questions.append(question)
                current_block = []
        
        # Process last block if exists
        if current_block:
            question = self._parse_question_block(current_block)
            if question:
                questions.append(question)
        
        return questions
    
    def _parse_question_block(self, lines: List[str]) -> Optional[Dict]:
        """Parse a single question block"""
        if not lines:
            return None
        
        # Extract question number and text
        first_line = lines[0]
        question_match = re.match(r'^(\d+)\.\s+(.+)$', first_line)
        
        if not question_match:
            return None
        
        question_num = question_match.group(1)
        question_text = question_match.group(2)
        
        # Extract options
        options = []
        answer_key = None
        
        i = 1
        while i < len(lines):
            line = lines[i]
            
            # Check for option
            option_match = re.match(r'^\(([a-d])\)\s+(.+)$', line)
            if option_match:
                key = option_match.group(1)
                value = option_match.group(2)
                options.append({"key": key, "value": value})
                i += 1
                continue
            
            # Check for answer
            answer_match = re.match(r'^ans:([a-d])$', line, re.IGNORECASE)
            if answer_match:
                answer_key = answer_match.group(1).lower()
                i += 1
                continue
            
            # If it's not an option or answer, it might be continuation of question
            if not options:
                question_text += " " + line
            
            i += 1
        
        # Validate we have all required parts
        if not options or not answer_key:
            return None
        
        # Find correct answer value
        correct_value = None
        for opt in options:
            if opt["key"] == answer_key:
                correct_value = opt["value"]
                break
        
        return {
            "number": int(question_num),
            "text": question_text.strip(),
            "options": options,
            "answer_key": answer_key,
            "answer_value": correct_value or ""
        }


class TopicClassifier:
    """Classify questions into topics based on keywords"""
    
    def __init__(self, topics_file: str):
        self.topics = self._load_topics(topics_file)
        self.keyword_map = self._build_keyword_map()
    
    def _load_topics(self, filepath: str) -> Dict:
        """Load topics from Topics_net file"""
        topics = {
            "Mathematics": {},
            "Physics": {},
            "Chemistry": {},
            "English": {},
            "Intelligence": {}
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse topics (simplified version)
            # You can enhance this to parse the full structure
            current_subject = None
            current_topic = None
            
            for line in content.split('\n'):
                line = line.strip()
                
                if 'Mathematics' in line and 'weightage' in line.lower():
                    current_subject = 'Mathematics'
                    current_topic = None
                elif 'Physics' in line and 'weightage' in line.lower():
                    current_subject = 'Physics'
                    current_topic = None
                elif 'Chemistry' in line and 'weightage' in line.lower():
                    current_subject = 'Chemistry'
                    current_topic = None
                elif 'English' in line and 'weightage' in line.lower():
                    current_subject = 'English'
                    current_topic = None
                elif 'Intelligence' in line and 'weightage' in line.lower():
                    current_subject = 'Intelligence'
                    current_topic = None
                
                # Extract topics (look for numbered items or **bold** items)
                topic_match = re.match(r'^\d+\.\s+\*\*(.+?)\*\*', line)
                if topic_match and current_subject:
                    current_topic = topic_match.group(1)
                    topics[current_subject][current_topic] = []
                
                # For English and Intelligence, topics are listed as "1. Topic name" (without **)
                if current_subject in ['English', 'Intelligence']:
                    simple_topic_match = re.match(r'^\d+\.\s+(.+)$', line)
                    if simple_topic_match and not topic_match:  # Not already matched as bold topic
                        topic_name = simple_topic_match.group(1).strip()
                        # Skip if it's the subject header line
                        if topic_name and 'weightage' not in topic_name.lower():
                            current_topic = topic_name
                            if current_topic not in topics[current_subject]:
                                topics[current_subject][current_topic] = []
                
                # Extract sub-topics (items with - or *)
                subtopic_match = re.match(r'^\s*[-*]\s+(.+)$', line)
                if subtopic_match and current_subject and current_topic:
                    subtopic = subtopic_match.group(1)
                    topics[current_subject][current_topic].append(subtopic)
        
        except Exception as e:
            print(f"Warning: Could not parse topics file: {e}")
        
        return topics
    
    def _build_keyword_map(self) -> Dict:
        """Build keyword to topic mapping"""
        keyword_map = {}
        
        # Mathematics keywords
        math_keywords = {
            "Functions and Limits": ["function", "limit", "domain", "range", "continuous", "discontinuous", 
                                     "identity", "explicit", "implicit", "parametric", "inverse function",
                                     "hyperbolic", "cosh", "sinh", "tanh"],
            "Differentiation": ["derivative", "differentiation", "tangent", "normal", "maxima", "minima",
                               "chain rule", "product rule", "quotient rule"],
            "Integration": ["integral", "integration", "definite", "indefinite", "area under curve",
                           "substitution", "by parts", "partial fractions"],
            "Trigonometry": ["sin", "cos", "tan", "cot", "sec", "cosec", "trigonometric", "radian", "degree"],
            "Complex Numbers": ["complex", "imaginary", "iota", "real component", "imaginary component"],
            "Matrices and Determinants": ["matrix", "determinant", "singular", "non-singular", "transpose"],
            "Vectors": ["vector", "dot product", "cross product", "magnitude", "direction"],
            "Sequences and Series": ["sequence", "series", "arithmetic", "geometric", "progression", "fibonacci", "harmonic"],
            "Probability and Statistics": ["probability", "permutation", "combination", "mean", "median", "mode"],
            "Analytical Geometry": ["coordinate", "distance", "slope", "equation of line", "circle"],
            "Conic Sections": ["parabola", "ellipse", "hyperbola", "conic", "focus", "directrix", "eccentricity"],
        }
        
        # English keywords (English is a subject, these are topics matching Topics_net)
        # Note: Avoid generic words that appear in math questions (e.g., "word" appears in permutation problems)
        english_keywords = {
            "Grammar and syntax": ["grammar", "syntax", "noun", "verb", "adjective", "adverb", "pronoun", 
                                   "preposition", "prepositions", "conjunction", "article", "tense", "sentence structure", "clause", "phrase"],
            "Vocabulary (synonyms, antonyms)": ["synonym of", "antonym of", "synonyms", "antonyms", "vocabulary", 
                                                "word meaning", "definition of", "means the same", "opposite meaning", 
                                                "synonym", "antonym"],
            "Reading comprehension": ["reading comprehension", "comprehension passage", "read the passage", 
                                     "according to the passage", "paragraph", "text says"],
            "Sentence correction": ["sentence correction", "sentence completion", "grammatical error", 
                                   "grammatically correct", "grammatical mistake", "correct the sentence"],
            "Idioms and phrases": ["idiom", "idiomatic expression", "phrase means", "proverb", "figure of speech"],
        }
        
        # Intelligence/IQ keywords (Intelligence is a subject, these are topics matching Topics_net)
        # NOTE: These must be very specific to avoid matching math questions
        # Only match when clearly IQ/intelligence questions, NOT math
        intelligence_keywords = {
            "Logical reasoning": ["logical reasoning", "deduce", "infer", "conclusion", "premise", "syllogism"],
            "Pattern recognition": ["pattern recognition", "visual pattern", "identify the pattern"],
            # Series completion - only for IQ number/letter patterns, NOT math sequences
            "Series completion": ["complete the series", "what comes next in", "next in the pattern"],
            # Analogies - only for word/relationship analogies with explicit "is to" pattern
            # Pattern: WORD1 is to WORD2 as WORD3 is to WORD4
            "Analogies": ["word analogy", "verbal analogy", "is to", "is to", "as"],
            # Critical thinking - only for logic puzzles, NOT math evaluations
            "Critical thinking": ["critical thinking", "logical puzzle", "reasoning puzzle"],
        }
        
        # Add all keywords to map
        for topic, keywords in math_keywords.items():
            for keyword in keywords:
                keyword_map[keyword.lower()] = ("Mathematics", topic)
        
        for topic, keywords in english_keywords.items():
            for keyword in keywords:
                keyword_map[keyword.lower()] = ("English", topic)
        
        for topic, keywords in intelligence_keywords.items():
            for keyword in keywords:
                keyword_map[keyword.lower()] = ("Intelligence", topic)
        
        return keyword_map
    
    def classify(self, question_text: str) -> Tuple[str, str, str]:
        """
        Classify question into subject, main topic, and sub-topic
        Returns: (subject, main_topic, sub_topic)
        """
        text_lower = question_text.lower()
        
        # Default classification
        subject = "Mathematics"
        main_topic = "General"
        sub_topic = "General"
        
        # Try to match keywords
        # FIRST: Check if question has strong math indicators - if so, skip English/Intelligence classification
        has_math_indicators = any(indicator in text_lower for indicator in [
            'sin', 'cos', 'tan', 'derivative', 'integral', 'matrix', 'vector', 'equation',
            'solve', 'evaluate', 'calculate', 'find the value', 'coordinate', 'point',
            'ratio', 'proportion', 'fraction', '=', '^', 'sqrt', 'log', 'ln', 'x^', 'y^',
            'polynomial', 'roots', 'slope', 'parallel', 'perpendicular', 'intersect',
            'geometric sequence', 'arithmetic sequence', 'nth term', 'determinant', 'determinants',
            'quadratic', 'alpha', 'beta', 'α', 'β', 'determinant', '|', 'determinant of',
            'period', 'function', 'tangent function', 'sine function', 'cosine function',
            'diagonal', 'square', 'side', 'units', 'played', 'out of', 'total', 'boys',
            'cricket', 'hockey', 'basketball', 'f(x)', 'with respect to', 'defined as',
            'same as', 'has the same', 'pairs has', 'length of'
        ]) or re.search(r'[0-9]+\s*[+\-*/=]\s*[0-9]|\([0-9]+,\s*[0-9]+\)|x\^[0-9]|y\^[0-9]|α|β|2x\^|3x\^|f\(x\)|sqrt\(', question_text)
        
        matched_topics = []
        for keyword, (subj, topic) in self.keyword_map.items():
            # Skip English and Intelligence keywords if math indicators are present
            if (subj in ["English", "Intelligence"]) and has_math_indicators:
                continue
            # For Intelligence "as" keyword, only match if it's part of an analogy pattern
            if subj == "Intelligence" and keyword == "as":
                # Only match "as" if it's in an analogy pattern: WORD is to WORD as WORD is to WORD
                if not re.search(r'\b\w+\s+is\s+to\s+\w+\s+as\s+\w+\s+is\s+to\s+\w+', text_lower, re.IGNORECASE):
                    continue
            if keyword in text_lower:
                matched_topics.append((subj, topic))
        
        # Special patterns for English questions (only if no strong math indicators)
        if not has_math_indicators:
            # Check for analogies pattern (WORD1 : WORD2) - must be actual words
            # Look for pattern like "BANDAGE : LACERATION" (all caps words, no numbers)
            # Pattern: word(s) in caps followed by colon followed by word(s) in caps
            analogy_pattern = re.search(r'([A-Z][A-Z\s]{1,})\s*:\s*([A-Z][A-Z\s]{1,})', question_text)
            if analogy_pattern:
                word1, word2 = analogy_pattern.groups()
                word1_clean = word1.strip()
                word2_clean = word2.strip()
                # Must be actual words (no numbers, no math symbols, reasonable length)
                if (not re.search(r'[0-9+\-*/^=()\[\]{}]', word1_clean + word2_clean) and
                    len(word1_clean) >= 3 and len(word2_clean) >= 3 and
                    # Exclude common math patterns
                    'coordinate' not in text_lower and 'point' not in text_lower and
                    'ratio' not in text_lower and 'proportion' not in text_lower):
                    matched_topics.append(("English", "Analogies"))
            
            # Check for synonym/antonym patterns (explicit)
            if re.search(r'\b(synonym|antonym)\s+of\s+[A-Z]', question_text, re.IGNORECASE):
                matched_topics.append(("English", "Vocabulary (synonyms, antonyms)"))
            
            # Check for sentence completion pattern
            if re.search(r'after having\s+\w+|offered to\s+\w+|would like to\s+\w+', text_lower):
                matched_topics.append(("English", "Sentence correction"))
            
            # Check for preposition questions (specific patterns)
            if re.search(r'\b(appear|move|trust|hostile)\s+\w+\s+(the|to|in|on|at|for|before|behind)', text_lower):
                matched_topics.append(("English", "Grammar and syntax"))
        
        if matched_topics:
            # Prioritize English matches if found (English questions are often misclassified)
            english_matches = [m for m in matched_topics if m[0] == "English"]
            if english_matches:
                subject, main_topic = english_matches[0]
            else:
                # Use the first match
                subject, main_topic = matched_topics[0]
            sub_topic = self._infer_subtopic(text_lower, main_topic)
        
        return subject, main_topic, sub_topic
    
    def _infer_subtopic(self, text: str, main_topic: str) -> str:
        """Infer sub-topic based on main topic and question text"""
        
        subtopic_keywords = {
            "Functions and Limits": {
                "Types of Functions": ["identity function", "explicit function", "implicit function", 
                                      "linear function", "quadratic function", "constant function"],
                "Domain and Range": ["domain", "range", "co-domain"],
                "Limits": ["limit", "approaches", "infinity", "lim"],
                "Continuity": ["continuous", "discontinuous"],
                "Hyperbolic Functions": ["cosh", "sinh", "tanh", "sech", "cosech", "coth"],
                "Parametric Functions": ["parametric", "parameter"],
                "Even and Odd Functions": ["even function", "odd function", "symmetry"],
                "Composite Functions": ["composite", "fog", "composition"],
                "Inverse Functions": ["inverse", "f^-1", "invertible"],
            },
            "Differentiation": {
                "Basic Derivatives": ["derivative", "differentiate"],
                "Rules": ["chain rule", "product rule", "quotient rule"],
                "Applications": ["maxima", "minima", "tangent", "normal", "rate of change"],
            },
            "Trigonometry": {
                "Trigonometric Functions": ["sin", "cos", "tan", "cot", "sec", "cosec"],
                "Identities": ["identity", "identities"],
                "Inverse Trigonometric": ["sin^-1", "cos^-1", "tan^-1", "inverse"],
            },
            "Grammar and syntax": {
                "Parts of Speech": ["noun", "verb", "adjective", "adverb", "pronoun"],
                "Tenses": ["tense", "present", "past", "future", "perfect", "continuous"],
                "Sentence Structure": ["sentence", "clause", "phrase", "subject", "predicate"],
                "Prepositions": ["preposition", "prepositions", "appear", "move", "trust", "hostile"],
            },
            "Vocabulary (synonyms, antonyms)": {
                "Synonyms": ["synonym", "similar meaning", "same meaning"],
                "Antonyms": ["antonym", "opposite", "opposite meaning"],
                "Word Meaning": ["meaning", "definition", "define"],
            },
            "Reading comprehension": {
                "Passage Analysis": ["passage", "paragraph", "text", "reading"],
                "Comprehension": ["comprehension", "understand", "interpret"],
            },
            "Sentence correction": {
                "Error Detection": ["error", "mistake", "incorrect"],
                "Correction": ["correct", "fix", "improve"],
                "Sentence Completion": ["sentence completion", "after having", "offered to", "would like to"],
            },
            "Idioms and phrases": {
                "Idioms": ["idiom", "expression"],
                "Phrases": ["phrase", "proverb"],
            },
            "Analogies": {
                "Word Analogies": ["analogy", "similar", "relationship", ":"],
                "Pattern Analogies": ["like", "as", "analogous"],
            },
            "Logical reasoning": {
                "Deductive": ["deduce", "deduction", "conclusion", "premise"],
                "Inductive": ["inductive", "infer", "inference"],
            },
            "Pattern recognition": {
                "Number Patterns": ["number", "digit", "sequence"],
                "Visual Patterns": ["pattern", "shape", "figure"],
            },
            "Series completion": {
                "Number Series": ["number", "sequence", "series"],
                "Pattern Completion": ["complete", "next", "missing"],
            },
            "Analogies": {
                "Word Analogies": ["analogy", "similar", "relationship"],
                "Pattern Analogies": ["like", "as", "analogous"],
            },
            "Critical thinking": {
                "Analysis": ["analyze", "examine", "evaluate"],
                "Assessment": ["assess", "judge", "critical"],
            },
        }
        
        if main_topic in subtopic_keywords:
            for subtopic, keywords in subtopic_keywords[main_topic].items():
                for keyword in keywords:
                    if keyword in text:
                        return subtopic
        
        return main_topic
    
    def estimate_difficulty(self, question_text: str, has_explanation: bool = False) -> str:
        """Estimate question difficulty"""
        text_lower = question_text.lower()
        
        # Easy indicators
        easy_keywords = ["define", "what is", "identify", "select", "which one"]
        
        # Hard indicators
        hard_keywords = ["prove", "derive", "evaluate", "simplify", "solve for", 
                        "find the value", "calculate", "determine"]
        
        # Check complexity
        hard_count = sum(1 for keyword in hard_keywords if keyword in text_lower)
        easy_count = sum(1 for keyword in easy_keywords if keyword in text_lower)
        
        # Check question length
        word_count = len(question_text.split())
        
        if hard_count > 0 or word_count > 25:
            return "hard"
        elif easy_count > 0 or word_count < 15:
            return "easy"
        else:
            return "medium"


class JSONGenerator:
    """Generate RAG-optimized JSON from parsed MCQs"""
    
    def __init__(self, classifier: TopicClassifier):
        self.classifier = classifier
    
    def generate_dataset(self, questions: List[Dict], source_info: Dict) -> Dict:
        """Generate complete dataset JSON"""
        
        processed_questions = []
        
        for idx, q in enumerate(questions, 1):
            processed_q = self._process_question(q, idx, source_info)
            processed_questions.append(processed_q)
        
        # Group by subject and main topic (to handle multi-subject papers like FAST)
        subject_topic_groups = {}
        for q in processed_questions:
            subject = q["source"]["subject"]  # Actual subject from classifier
            main_topic = q["topic"]["main_topic"]
            key = (subject, main_topic)
            if key not in subject_topic_groups:
                subject_topic_groups[key] = []
            subject_topic_groups[key].append(q)
        
        # Create separate files per subject-topic combination
        datasets = {}
        for (subject, main_topic), questions in subject_topic_groups.items():
            dataset = {
                "dataset_info": {
                    "dataset_name": f"{source_info['exam_type']} {subject} - {main_topic}",
                    "version": "1.0",
                    "created_date": datetime.now().strftime("%Y-%m-%d"),
                    "total_questions": len(questions),
                    "source_file": source_info['source_file'],
                    "exam_type": source_info['exam_type'],
                    "subject": subject,  # Use actual subject from classifier
                    "main_topic": main_topic
                },
                "questions": questions
            }
            datasets[(subject, main_topic)] = dataset
        
        return datasets
    
    def _process_question(self, question: Dict, index: int, source_info: Dict) -> Dict:
        """Process single question into JSON format"""
        
        # Classify question
        subject, main_topic, sub_topic = self.classifier.classify(question['text'])
        difficulty = self.classifier.estimate_difficulty(question['text'])
        
        # Generate question ID
        question_id = self._generate_id(source_info['exam_type'], subject, main_topic, index)
        
        # Generate embedding text
        embedding_text = self._generate_embedding_text(
            main_topic, sub_topic, question['text'], 
            question['options'], question['answer_value']
        )
        
        # Extract keywords
        keywords = self._extract_keywords(question['text'])
        
        # Determine cognitive skill
        cognitive_skill, bloom_level = self._determine_cognitive_level(question['text'])
        
        return {
            "question_id": question_id,
            "source": {
                "exam_type": source_info['exam_type'],
                "subject": subject,
                "paper_name": source_info.get('paper_name', 'Unknown'),
                "year": source_info.get('year', '2024')
            },
            "topic": {
                "main_topic": main_topic,
                "sub_topic": sub_topic,
                "difficulty": difficulty
            },
            "question": {
                "text": question['text'],
                "type": "mcq",
                "format": "single_choice"
            },
            "options": question['options'],
            "answer": {
                "correct_key": question['answer_key'],
                "correct_value": question['answer_value'],
                "explanation": ""
            },
            "embedding_text": embedding_text,
            "metadata": {
                "keywords": keywords,
                "related_concepts": self._get_related_concepts(main_topic, sub_topic),
                "prerequisites": [main_topic.lower()],
                "difficulty_level": difficulty,
                "cognitive_skill": cognitive_skill,
                "bloom_level": bloom_level
            }
        }
    
    def _generate_id(self, exam_type: str, subject: str, topic: str, index: int) -> str:
        """Generate unique question ID"""
        exam_abbr = exam_type[:3].upper()
        subject_abbr = ''.join([c for c in subject if c.isupper()])[:4]
        topic_abbr = ''.join([word[0].upper() for word in topic.split()[:2]])
        return f"{exam_abbr}_{subject_abbr}_{topic_abbr}_Q{index:03d}"
    
    def _generate_embedding_text(self, main_topic: str, sub_topic: str, 
                                 question: str, options: List[Dict], answer: str) -> str:
        """Generate optimized text for embedding"""
        options_text = ", ".join([opt['value'] for opt in options])
        return (f"{main_topic} - {sub_topic}: {question} "
                f"Options: {options_text}. Correct answer: {answer}")
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from question"""
        text_lower = text.lower()
        
        # Common mathematical/scientific terms
        important_terms = [
            "function", "derivative", "integral", "limit", "matrix", "vector",
            "probability", "equation", "formula", "theorem", "proof", "solve",
            "calculate", "evaluate", "determine", "find", "graph", "curve"
        ]
        
        keywords = []
        for term in important_terms:
            if term in text_lower:
                keywords.append(term)
        
        # Extract mathematical symbols/patterns
        if re.search(r'x\^?\d', text):
            keywords.append("polynomial")
        if re.search(r'sin|cos|tan', text_lower):
            keywords.append("trigonometric")
        
        return keywords[:5]  # Limit to top 5
    
    def _get_related_concepts(self, main_topic: str, sub_topic: str) -> List[str]:
        """Get related concepts for a topic"""
        concept_map = {
            "Functions and Limits": ["function properties", "limit evaluation", "continuity"],
            "Differentiation": ["derivatives", "rate of change", "optimization"],
            "Integration": ["antiderivatives", "area calculation", "integration techniques"],
            "Trigonometry": ["trigonometric identities", "angle measurement", "periodic functions"],
        }
        return concept_map.get(main_topic, [main_topic.lower()])
    
    def _determine_cognitive_level(self, question_text: str) -> Tuple[str, str]:
        """Determine cognitive skill and Bloom's taxonomy level"""
        text_lower = question_text.lower()
        
        # Bloom's taxonomy mapping
        if any(word in text_lower for word in ["define", "identify", "recall", "what is"]):
            return "recall", "L1_Remember"
        elif any(word in text_lower for word in ["explain", "describe", "interpret"]):
            return "understanding", "L2_Understand"
        elif any(word in text_lower for word in ["calculate", "solve", "apply", "compute"]):
            return "application", "L3_Apply"
        elif any(word in text_lower for word in ["analyze", "compare", "examine"]):
            return "analysis", "L4_Analyze"
        elif any(word in text_lower for word in ["evaluate", "assess", "judge"]):
            return "evaluation", "L5_Evaluate"
        elif any(word in text_lower for word in ["create", "design", "construct"]):
            return "creation", "L6_Create"
        else:
            return "application", "L3_Apply"


class BatchProcessor:
    """Process multiple MCQ files"""
    
    def __init__(self, topics_file: str, output_dir: str):
        self.parser = MCQParser()
        self.classifier = TopicClassifier(topics_file)
        self.generator = JSONGenerator(self.classifier)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def process_directory(self, input_dir: str):
        """Process all MCQ files in directory"""
        input_path = Path(input_dir)
        
        print(f"Processing files in: {input_dir}")
        
        # Find all .txt files recursively
        txt_files = list(input_path.rglob("*.txt"))
        
        print(f"Found {len(txt_files)} text files")
        
        for txt_file in txt_files:
            try:
                self.process_file(str(txt_file))
            except Exception as e:
                print(f"Error processing {txt_file}: {e}")
    
    def process_file(self, filepath: str):
        """Process single MCQ file"""
        print(f"\nProcessing: {filepath}")
        
        # Parse questions
        questions = self.parser.parse_file(filepath)
        
        if not questions:
            print(f"  No questions found in {filepath}")
            return
        
        print(f"  Found {len(questions)} questions")
        
        # Determine source info from filepath
        source_info = self._extract_source_info(filepath)
        
        # Generate datasets (one per subject-topic combination)
        datasets = self.generator.generate_dataset(questions, source_info)
        
        # Save each dataset
        for key, dataset in datasets.items():
            # key is (subject, main_topic) tuple
            subject, main_topic = key
            output_path = self._get_output_path(source_info, main_topic, subject=subject)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, indent=2, ensure_ascii=False)
            
            print(f"  Saved: {output_path} ({dataset['dataset_info']['total_questions']} questions)")
    
    def _extract_source_info(self, filepath: str) -> Dict:
        """Extract source information from filepath"""
        path_parts = Path(filepath).parts
        filepath_obj = Path(filepath)
        
        # Determine exam type
        exam_type = "Unknown"
        if "NET" in path_parts:
            exam_type = "NET"
        elif "FAST" in path_parts:
            exam_type = "FAST"
        
        # Determine subject (default, will be overridden by classifier)
        subject = "Mathematics"  # Default
        filename = filepath_obj.stem.lower()
        if "physics" in filename:
            subject = "Physics"
        elif "chemistry" in filename:
            subject = "Chemistry"
        elif "english" in filename:
            subject = "English"
        elif "intelligence" in filename or "iq" in filename:
            subject = "Intelligence"
        
        # Extract paper/source folder name for NET papers
        # Example: data/Standard_text/NET/100_netquestions/file.txt -> paper_folder = "100_netquestions"
        paper_folder = None
        if exam_type == "NET":
            # Find the folder name after NET in the path
            try:
                net_index = None
                for i, part in enumerate(path_parts):
                    if "NET" in part.upper() and i + 1 < len(path_parts):
                        net_index = i
                        break
                if net_index is not None and net_index + 1 < len(path_parts):
                    # Get the folder after NET (e.g., "100_netquestions" or "497992392-NUST-NET-Solved-MCQs")
                    paper_folder = path_parts[net_index + 1]
            except (IndexError, ValueError):
                pass
        
        return {
            "exam_type": exam_type,
            "subject": subject,  # Default subject, actual subject determined by classifier per question
            "source_file": filepath_obj.name,
            "paper_name": filepath_obj.stem,
            "paper_folder": paper_folder,  # For NET papers, keep separate folders
            "year": "2024"
        }
    
    def _get_output_path(self, source_info: Dict, main_topic: str, subject: str = None) -> Path:
        """Generate output file path
        
        Args:
            source_info: Source information dictionary
            main_topic: Main topic name
            subject: Actual subject (from classifier, overrides source_info['subject'])
        """
        # Use actual subject from classifier if provided
        actual_subject = subject if subject else source_info['subject']
        
        # Sanitize topic name for filename
        topic_filename = re.sub(r'[^\w\s-]', '', main_topic).strip().replace(' ', '_').lower()
        
        # Build path
        path_parts = [self.output_dir, source_info['exam_type']]
        
        # For NET papers, include paper folder to keep them separate
        if source_info['exam_type'] == "NET" and source_info.get('paper_folder'):
            path_parts.append(source_info['paper_folder'])
        
        path_parts.append(actual_subject)
        path_parts.append(f"{topic_filename}.json")
        
        return Path(*path_parts)


def main():
    """Main processing function"""
    
    # Configuration
    TOPICS_FILE = "Topics_net"
    INPUT_DIR = "data/Standard_text"
    OUTPUT_DIR = "processed_data"
    
    print("=" * 60)
    print("MCQ Processing Pipeline - RAG Dataset Generation")
    print("=" * 60)
    
    # Initialize processor
    processor = BatchProcessor(TOPICS_FILE, OUTPUT_DIR)
    
    # Process all files
    processor.process_directory(INPUT_DIR)
    
    print("\n" + "=" * 60)
    print("Processing complete!")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()

