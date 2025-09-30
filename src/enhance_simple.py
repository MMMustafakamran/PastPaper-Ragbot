"""
Simple Metadata Enhancer
Adds critical metadata for quiz generation: topics, tags, difficulty scores
"""

import json
import logging
from pathlib import Path
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


# Simple topic classification rules
TOPICS = {
    'physics': {
        'circular_motion': ['centripetal', 'tangential', 'angular', 'circular', 'radius'],
        'waves': ['wave', 'frequency', 'wavelength', 'sound', 'doppler', 'interference', 'diffraction'],
        'electricity': ['electric', 'current', 'voltage', 'charge', 'circuit', 'resistance', 'capacitor'],
        'mechanics': ['force', 'velocity', 'acceleration', 'motion', 'momentum', 'friction', 'mass'],
        'optics': ['light', 'lens', 'reflection', 'refraction', 'mirror', 'optical'],
        'thermodynamics': ['heat', 'temperature', 'thermal', 'isothermal', 'adiabatic', 'entropy'],
        'magnetism': ['magnetic', 'flux', 'induction', 'magnet'],
        'modern_physics': ['quantum', 'photon', 'nuclear', 'radioactive', 'atom', 'electron']
    },
    'chemistry': {
        'atomic_structure': ['atom', 'electron', 'orbital', 'quantum number', 'shell'],
        'bonding': ['bond', 'covalent', 'ionic', 'metallic', 'hybridization'],
        'organic': ['alkane', 'alkene', 'alkyne', 'benzene', 'aromatic', 'functional group', 'hydrocarbon'],
        'acids_bases': ['acid', 'base', 'pH', 'buffer', 'neutralization'],
        'reactions': ['reaction', 'oxidation', 'reduction', 'redox', 'catalyst'],
        'periodic_table': ['periodic', 'group', 'period', 'alkali', 'halogen'],
        'thermochemistry': ['enthalpy', 'entropy', 'exothermic', 'endothermic']
    },
    'mathematics': {
        'calculus': ['derivative', 'integral', 'limit', 'differentiation', 'integration', 'antiderivative'],
        'trigonometry': ['sine', 'cosine', 'tangent', 'secant', 'cosecant', 'cotangent', 'inverse'],
        'probability': ['probability', 'dice', 'sample space', 'event', 'outcome', 'permutation', 'combination'],
        'algebra': ['equation', 'polynomial', 'roots', 'function', 'quadratic', 'linear'],
        'geometry': ['circle', 'parabola', 'ellipse', 'hyperbola', 'coordinate', 'distance'],
        'sequences': ['sequence', 'series', 'arithmetic', 'geometric', 'progression'],
        'sets': ['set', 'subset', 'union', 'intersection', 'complement'],
        'complex_numbers': ['complex', 'imaginary', 'real', 'conjugate'],
        'matrices': ['matrix', 'determinant', 'inverse', 'transpose']
    },
    'biology': {
        'cell': ['cell', 'membrane', 'nucleus', 'organelle', 'cytoplasm', 'mitochondria'],
        'genetics': ['DNA', 'RNA', 'gene', 'chromosome', 'mutation', 'allele', 'heredity'],
        'metabolism': ['respiration', 'photosynthesis', 'ATP', 'glycolysis', 'krebs'],
        'evolution': ['evolution', 'natural selection', 'adaptation', 'species'],
        'ecology': ['ecosystem', 'food chain', 'biodiversity']
    },
    'english': {
        'grammar': ['grammar', 'noun', 'verb', 'adjective', 'tense', 'sentence'],
        'vocabulary': ['synonym', 'antonym', 'meaning', 'vocabulary']
    }
}


class SimpleEnhancer:
    """Add critical metadata to questions"""
    
    def __init__(self):
        """Initialize enhancer"""
        self.topics = TOPICS
    
    def find_topic(self, text: str, subject: str) -> Tuple[Optional[str], List[str]]:
        """
        Find best matching topic and extract tags
        
        Args:
            text: Question text
            subject: Question subject
            
        Returns:
            Tuple of (topic, tags)
        """
        text_lower = text.lower()
        
        if subject not in self.topics:
            return None, []
        
        best_topic = None
        best_score = 0
        all_tags = []
        
        for topic, keywords in self.topics[subject].items():
            score = 0
            matched = []
            
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
                    matched.append(keyword)
            
            if score > best_score:
                best_score = score
                best_topic = topic
                all_tags = matched
        
        return best_topic, all_tags[:5]  # Max 5 tags
    
    def calculate_difficulty_score(self, question_text: str, options: List[dict]) -> float:
        """
        Calculate difficulty score (1-10)
        
        Args:
            question_text: Question text
            options: List of options
            
        Returns:
            Difficulty score (1-10)
        """
        score = 5.0  # Default medium
        
        # Length factor
        q_len = len(question_text)
        if q_len > 200:
            score += 1.0
        elif q_len > 300:
            score += 1.5
        elif q_len < 50:
            score -= 0.5
        
        # Detect formulas and calculations
        import re
        has_formulas = bool(re.search(r'[=+\-*/^√∫∑∆πλθαβγ]|\\frac|\\sqrt', question_text))
        has_calculations = bool(re.search(r'\d+\s*[+\-×÷*/]\s*\d+|=\s*\d+', question_text))
        
        # Formula & calculations
        if has_formulas:
            score += 0.5
        if has_calculations:
            score += 0.5
        
        # Option complexity
        if options:
            avg_opt_len = sum(len(opt.get('text', '')) for opt in options) / len(options)
            if avg_opt_len > 50:
                score += 0.5
        
        # Complexity keywords
        text_lower = question_text.lower()
        if any(w in text_lower for w in ['complex', 'advanced', 'derive', 'prove']):
            score += 1.0
        elif any(w in text_lower for w in ['simple', 'basic', 'elementary']):
            score -= 0.5
        
        # Multi-step indicators
        if 'and' in text_lower and ('calculate' in text_lower or 'find' in text_lower):
            score += 0.5
        
        # Clamp to 1-10 range
        return max(1.0, min(10.0, round(score, 1)))
    
    def get_difficulty_level(self, score: float) -> str:
        """
        Convert numeric score to difficulty level
        
        Args:
            score: Difficulty score (1-10)
            
        Returns:
            Difficulty level string
        """
        if score < 3.5:
            return "easy"
        elif score < 6.5:
            return "medium"
        elif score < 8.5:
            return "hard"
        else:
            return "expert"
    
    def enhance_question(self, question: dict) -> dict:
        """
        Add critical metadata to a question
        
        Args:
            question: Question dictionary
            
        Returns:
            Enhanced question dictionary
        """
        # 1. Find topic and tags
        topic, tags = self.find_topic(question['question_text'], question['subject'])
        question['topic'] = topic
        question['tags'] = tags
        
        # 2. Calculate real difficulty
        score = self.calculate_difficulty_score(
            question['question_text'],
            question.get('options', [])
        )
        question['difficulty'] = self.get_difficulty_level(score)
        question['difficulty_score'] = score
        
        # 3. Mark correct options (only if answer is known)
        correct = question.get('correct_answer')
        for opt in question.get('options', []):
            if correct:
                opt['is_correct'] = (opt['label'] == correct)
            else:
                opt['is_correct'] = None  # Unknown answer
        
        # 4. Better embedding text
        parts = []
        
        # Add subject and topic context
        if question['subject']:
            context = question['subject'].title()
            if topic:
                context += f" {topic.replace('_', ' ')}"
            parts.append(f"{context}:")
        
        # Add question text
        parts.append(question['question_text'])
        
        # Add concepts/tags
        if tags:
            parts.append(f"Concepts: {' '.join(tags)}")
        
        # Add answer if available
        if correct:
            correct_text = next((o['text'] for o in question.get('options', []) 
                               if o['label'] == correct), None)
            if correct_text:
                parts.append(f"Answer: {correct_text}")
        
        question['embedding_text'] = ' '.join(parts)
        
        return question
    
    def enhance_json_file(self, input_file: Path) -> dict:
        """
        Enhance a JSON file with metadata
        
        Args:
            input_file: Path to JSON file
            
        Returns:
            Statistics dictionary
        """
        logger.info(f"Enhancing: {input_file.name}")
        
        # Load JSON
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        questions = data.get('questions', [])
        
        if not questions:
            logger.warning(f"No questions found in {input_file.name}")
            return {'enhanced': 0}
        
        # Enhance each question
        for i, q in enumerate(questions, 1):
            questions[i-1] = self.enhance_question(q)
            
            if i % 50 == 0:
                logger.info(f"  Processed {i}/{len(questions)}...")
        
        # Update data
        data['questions'] = questions
        
        # Save back
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Generate statistics
        topics = {}
        difficulties = {}
        with_tags = 0
        
        for q in questions:
            topic = q.get('topic', 'unknown')
            topics[topic] = topics.get(topic, 0) + 1
            
            diff = q.get('difficulty', 'unknown')
            difficulties[diff] = difficulties.get(diff, 0) + 1
            
            if q.get('tags'):
                with_tags += 1
        
        stats = {
            'enhanced': len(questions),
            'topics': topics,
            'difficulties': difficulties,
            'with_tags': with_tags
        }
        
        logger.info(f"✅ Enhanced {len(questions)} questions")
        logger.info(f"   Topics: {topics}")
        logger.info(f"   Difficulties: {difficulties}")
        logger.info(f"   With tags: {with_tags}/{len(questions)}")
        
        return stats
    
    def enhance_all(self, processed_dir: str = "Processed Data") -> dict:
        """
        Enhance all JSON files in processed directory
        
        Args:
            processed_dir: Directory containing JSON files
            
        Returns:
            Overall statistics
        """
        processed_path = Path(processed_dir)
        
        if not processed_path.exists():
            logger.error(f"Directory not found: {processed_dir}")
            return {'total_files': 0, 'successful': 0, 'failed': 0}
        
        # Find all JSON files
        json_files = list(processed_path.rglob("*.json"))
        
        if not json_files:
            logger.warning(f"No JSON files found in {processed_dir}")
            return {'total_files': 0, 'successful': 0, 'failed': 0}
        
        logger.info(f"Found {len(json_files)} JSON files to enhance\n")
        
        overall_stats = {
            'total_files': len(json_files),
            'successful': 0,
            'failed': 0,
            'total_questions': 0,
            'files': []
        }
        
        for json_file in json_files:
            logger.info(f"{'='*60}")
            
            try:
                stats = self.enhance_json_file(json_file)
                overall_stats['successful'] += 1
                overall_stats['total_questions'] += stats['enhanced']
                overall_stats['files'].append({
                    'file': str(json_file),
                    'status': 'success',
                    'stats': stats
                })
            except Exception as e:
                logger.error(f"Failed to enhance {json_file.name}: {e}")
                overall_stats['failed'] += 1
                overall_stats['files'].append({
                    'file': str(json_file),
                    'status': 'failed',
                    'error': str(e)
                })
            
            logger.info("")
        
        return overall_stats
    
    def print_summary(self, stats: dict):
        """Print enhancement summary"""
        print("\n" + "="*60)
        print("ENHANCEMENT SUMMARY")
        print("="*60)
        print(f"Total files: {stats['total_files']}")
        print(f"Successfully enhanced: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        print(f"Total questions enhanced: {stats['total_questions']}")
        
        if stats['successful'] > 0:
            print("\nAll JSON files have been enhanced with:")
            print("   - Topic classification")
            print("   - Concept tags")
            print("   - Real difficulty scores")
            print("   - Correct answer flags")
            print("   - Improved embedding text")


def main():
    """Main function"""
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    enhancer = SimpleEnhancer()
    
    if len(sys.argv) > 1:
        # Single file
        json_file = Path(sys.argv[1])
        if json_file.exists():
            enhancer.enhance_json_file(json_file)
        else:
            print(f"File not found: {json_file}")
    else:
        # All files
        stats = enhancer.enhance_all()
        enhancer.print_summary(stats)


if __name__ == "__main__":
    main()

