"""
Enhanced Embedding Generator
Generates rich embedding text (400+ chars) for better RAG retrieval
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EnhancedEmbeddingGenerator:
    """Generate comprehensive embedding text for RAG"""
    
    def generate_comprehensive_embedding(
        self,
        question: any,
        include_answer: bool = True
    ) -> str:
        """
        Generate rich embedding text with all context
        
        Target length: 400+ characters
        
        Args:
            question: Question object (dataclass or dict)
            include_answer: Whether to include answer in embedding
            
        Returns:
            Comprehensive embedding text
        """
        parts = []
        
        # Convert to dict if dataclass
        if hasattr(question, '__dict__'):
            q_dict = question.__dict__
        elif isinstance(question, dict):
            q_dict = question
        else:
            q_dict = {}
        
        # 1. Subject and topic hierarchy
        subject = q_dict.get('subject', '')
        topic = q_dict.get('topic', '')
        
        if subject:
            subject_text = subject.title()
            if topic:
                topic_text = topic.replace('_', ' ').title()
                parts.append(f"Subject: {subject_text} | Topic: {topic_text}")
            else:
                parts.append(f"Subject: {subject_text}")
        
        # 2. Difficulty context
        difficulty = q_dict.get('difficulty', '')
        if difficulty:
            parts.append(f"Difficulty: {difficulty.title()}")
        
        # 3. Full question text
        question_text = q_dict.get('question_text', '')
        if question_text:
            parts.append(f"Question: {question_text}")
        
        # 4. ALL options (complete context)
        options = q_dict.get('options', [])
        if options:
            option_strs = []
            for opt in options:
                label = opt.get('label', '')
                text = opt.get('text', '')
                if label and text:
                    option_strs.append(f"{label}) {text}")
            
            if option_strs:
                parts.append(f"Options: {' | '.join(option_strs)}")
        
        # 5. Concept tags
        tags = q_dict.get('tags', [])
        if tags:
            if isinstance(tags, list):
                parts.append(f"Concepts: {', '.join(tags)}")
            else:
                parts.append(f"Concepts: {tags}")
        
        # 6. Correct answer (if available and requested)
        if include_answer:
            correct_answer = q_dict.get('correct_answer', '')
            if correct_answer:
                # Find the answer text
                answer_text = None
                for opt in options:
                    if opt.get('label', '').upper() == correct_answer.upper():
                        answer_text = opt.get('text', '')
                        break
                
                if answer_text:
                    parts.append(f"Answer: {correct_answer}) {answer_text}")
        
        # 7. Solution/explanation (if available)
        solution = q_dict.get('solution', '')
        if solution:
            # Truncate long solutions for embedding
            if len(solution) > 200:
                solution = solution[:200] + "..."
            parts.append(f"Explanation: {solution}")
        
        # 8. Source metadata
        exam_type = q_dict.get('exam_type', '')
        year = q_dict.get('year')
        if exam_type and year:
            parts.append(f"Source: {exam_type} {year}")
        elif exam_type:
            parts.append(f"Source: {exam_type}")
        
        # Join all parts
        embedding_text = " | ".join(parts)
        
        # Log if embedding is too short
        if len(embedding_text) < 200:
            logger.warning(
                f"Embedding text too short ({len(embedding_text)} chars) "
                f"for Q{q_dict.get('question_number', '?')}"
            )
        
        return embedding_text
    
    def generate_search_variants(self, question: any) -> list:
        """
        Generate multiple embedding variants for better retrieval
        Useful for multi-vector indexing
        
        Args:
            question: Question object
            
        Returns:
            List of embedding text variants
        """
        variants = []
        
        # Convert to dict
        if hasattr(question, '__dict__'):
            q_dict = question.__dict__
        elif isinstance(question, dict):
            q_dict = question
        else:
            return []
        
        subject = q_dict.get('subject', '')
        question_text = q_dict.get('question_text', '')
        tags = q_dict.get('tags', [])
        correct_answer = q_dict.get('correct_answer', '')
        options = q_dict.get('options', [])
        
        # Variant 1: Question only
        if question_text:
            if subject:
                variants.append(f"{subject}: {question_text}")
            else:
                variants.append(question_text)
        
        # Variant 2: Question + concepts
        if question_text and tags:
            if isinstance(tags, list):
                tags_str = ' '.join(tags)
            else:
                tags_str = str(tags)
            variants.append(f"{question_text} Concepts: {tags_str}")
        
        # Variant 3: Question + answer
        if question_text and correct_answer:
            answer_text = None
            for opt in options:
                if opt.get('label', '').upper() == correct_answer.upper():
                    answer_text = opt.get('text', '')
                    break
            
            if answer_text:
                variants.append(f"{question_text} Answer: {answer_text}")
        
        # Variant 4: Full context (primary)
        variants.append(self.generate_comprehensive_embedding(question))
        
        return variants

