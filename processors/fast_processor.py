#!/usr/bin/env python3
"""
Script to process FAST Entry Test Past Papers.
Combines questions with answers for 3 papers.
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Paper configuration
PAPERS = {
    1: {
        'name': 'FAST Past Paper 1',
        'question_pages': list(range(1, 17)),  # pages 1-16
        'answer_page': 17,
        'filename': 'fast_paper_1.txt'
    },
    2: {
        'name': 'FAST Past Paper 2',
        'question_pages': list(range(18, 36)),  # pages 18-35
        'answer_page': 36,
        'filename': 'fast_paper_2.txt'
    },
    3: {
        'name': 'FAST Past Paper 3',
        'question_pages': list(range(38, 55)),  # pages 38-54
        'answer_page': 55,
        'filename': 'fast_paper_3.txt'
    }
}


def parse_answers(answer_page_text: str) -> Dict[int, str]:
    """
    Parse answer sheet and extract answers.
    Format: CSV with question numbers and answers in MATHEMATICS section.
    Returns: {question_num: answer_letter}
    """
    answers = {}
    
    # Find MATHEMATICS section
    lines = answer_page_text.split('\n')
    math_section_start = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip header lines with W,W or R,R
        if line.startswith('W,W') or line.startswith('R,R'):
            continue
        
        # Check if this is the MATHEMATICS section header
        if 'MATHEMATICS' in line.upper() and 'SECTION' in line.upper():
            math_section_start = True
            continue
        
        # Also check for lines that start with MATHEMATICS
        if 'MATHEMATICS' in line.upper() and not math_section_start:
            math_section_start = True
            # Check if this line already has answers
            if ',' in line:
                parts = [p.strip() for p in line.split(',')]
                i = 0
                while i < len(parts):
                    if parts[i].isdigit():
                        q_num = int(parts[i])
                        if i + 1 < len(parts) and parts[i + 1]:
                            answer = parts[i + 1].strip().upper()
                            if answer and answer.isalpha() and len(answer) == 1:
                                answers[q_num] = answer.lower()
                        i += 2
                    else:
                        i += 1
            continue
        
        # Stop if we hit another section (but allow continuation if we're in math section)
        if math_section_start:
            # Check if this line starts a new section
            if line.startswith('SECTION') and 'MATHEMATICS' not in line.upper():
                # Check if we've already parsed math answers (questions 1-40)
                if answers:
                    break
            
            # Parse CSV format: "1,A," or "1,A,41,D," or "21,A,,,"
            # Only parse the first column (MATHEMATICS section)
            parts = [p.strip() for p in line.split(',')]
            
            # In MATHEMATICS section, answers are in first two columns: "1,A," or "21,A,,,"
            # Stop when we hit the third column which starts another section
            i = 0
            while i < len(parts):
                # Look for question number
                if parts[i].isdigit():
                    q_num = int(parts[i])
                    # Next part should be the answer (only if it's in MATHEMATICS column)
                    if i + 1 < len(parts) and parts[i + 1]:
                        answer = parts[i + 1].strip().upper()
                        # Only accept valid answer letters (a-e) and single character
                        # Skip if answer is empty, is a number, or is invalid (like 'W', 'R', 'U', etc.)
                        if answer and answer.isalpha() and len(answer) == 1 and answer in 'ABCDE':
                            answers[q_num] = answer.lower()
                        # If we hit a non-answer (like 'W', 'R', or another section), stop
                        elif answer and (answer in 'WR' or len(answer) > 1):
                            break
                        i += 2
                    else:
                        i += 1
                elif parts[i] and parts[i] in 'WR':  # Stop at W,W or R,R lines
                    break
                else:
                    i += 1
    
    return answers


def parse_question_block(text: str, start_pos: int) -> Tuple[int, str, List[str], int]:
    """
    Parse a single question block starting at start_pos.
    Returns: (question_num, question_text, options_list, next_pos)
    """
    # Find question number - pattern: "1. " or "12. "
    q_num_pattern = r'^(\d+)\.\s+'
    match = re.search(q_num_pattern, text[start_pos:], re.MULTILINE)
    
    if not match:
        return None, None, None, start_pos
    
    q_num = int(match.group(1))
    content_start = start_pos + match.end()
    
    # Find the end of this question (next question number)
    next_q_pattern = r'\n(\d+)\.\s+'
    next_q_match = re.search(next_q_pattern, text[content_start:], re.MULTILINE)
    
    # Also check for page markers
    page_pattern = r'\nPage\s+\d+|www\.|📄'
    page_match = re.search(page_pattern, text[content_start:], re.MULTILINE | re.IGNORECASE)
    
    # Determine end position
    end_pos = len(text)
    if next_q_match:
        end_pos = min(end_pos, content_start + next_q_match.start())
    if page_match:
        end_pos = min(end_pos, content_start + page_match.start())
    
    question_block = text[content_start:end_pos].strip()
    
    # Parse question text and options
    lines = question_block.split('\n')
    question_lines = []
    options = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip page markers and URLs
        if re.match(r'^(Page\s+\d+|www\.|📄)', line, re.IGNORECASE):
            break
        
        # Check for option patterns: "a. " or "a) " or "A. " or "A) " or "41a) " (from OCR artifacts)
        # Also handle patterns like "41a) -1" which are OCR artifacts
        option_match = re.match(r'^(\d+)?([a-eA-E])[\.\)]\s*(.+)$', line)
        if option_match:
            opt_letter = option_match.group(2).lower()
            opt_text = option_match.group(3).strip()
            # Skip if this looks like an OCR artifact (has number prefix and very short)
            if option_match.group(1) and len(opt_text) < 5:
                # Might be OCR artifact, skip
                pass
            else:
                options.append(f"({opt_letter}) {opt_text}")
        elif re.match(r'^\([a-e]\)', line, re.IGNORECASE):
            # Option in format "(a) text"
            opt_match = re.match(r'^\(([a-e])\)\s*(.+)$', line, re.IGNORECASE)
            if opt_match:
                options.append(f"({opt_match.group(1).lower()}) {opt_match.group(2).strip()}")
        elif options:
            # Continuation of previous option (multi-line options)
            options[-1] += ' ' + line
        else:
            # Question text
            question_lines.append(line)
    
    question_text = '\n'.join(question_lines).strip()
    
    # Clean up question text
    question_text = re.sub(r'\s+Page\s+\d+.*$', '', question_text, flags=re.IGNORECASE)
    question_text = re.sub(r'\s+www\..*$', '', question_text, flags=re.IGNORECASE)
    question_text = re.sub(r'\s+📄.*$', '', question_text)
    question_text = question_text.strip()
    
    next_pos = end_pos
    
    return q_num, question_text, options, next_pos


def parse_special_format_page(page_text: str) -> Dict[int, Tuple[str, List[str]]]:
    """
    Parse page 37/38 format where questions are in a single line with embedded numbers.
    Format: "1. question 1a) opt1 2b) opt2 3c) opt3 4d) opt4 52. next question..."
    """
    questions = {}
    
    # Remove header
    page_text = re.sub(r'Page \d+.*?MATHEMATICS\)', '', page_text, flags=re.DOTALL | re.IGNORECASE)
    page_text = re.sub(r'\(Options c and d are on the next page\).*?📄', '', page_text, flags=re.DOTALL | re.IGNORECASE)
    page_text = re.sub(r'\(Continuation of Question \d+\).*?📄', '', page_text, flags=re.DOTALL | re.IGNORECASE)
    page_text = re.sub(r'📄 Page \d+.*?MATHEMATICS\)', '', page_text, flags=re.DOTALL | re.IGNORECASE)
    
    # Fix concatenated numbers like "4510." -> should be end of option then "10."
    # Pattern: digit followed by 10. (likely question 10)
    page_text = re.sub(r'(\d)(10)\.\s+', r'\1 \2. ', page_text)
    # Pattern: 45 followed by 10. -> "45 10."
    page_text = re.sub(r'(45)(10)\.\s+', r'\1 \2. ', page_text)
    
    # Split by question numbers - look for pattern: number followed by period and space
    # But be careful not to split option numbers
    # Use pattern: start of string or space, then digits, then period and space
    parts = re.split(r'(?:^|\s)(\d+)\.\s+', page_text)
    
    i = 1  # Start from 1 (skip empty first part if any)
    if parts[0].strip() and not parts[0].strip()[0].isdigit():
        # First part might be text before first question
        i = 0
    
    while i < len(parts) - 1:
        if i % 2 == 0:
            # This is text content
            i += 1
            continue
            
        q_num_str = parts[i]
        content = parts[i + 1] if i + 1 < len(parts) else ""
        
        try:
            q_num = int(q_num_str)
        except ValueError:
            i += 2
            continue
        
        # Skip if question number is too high (likely OCR error)
        if q_num > 50:
            i += 2
            continue
        
        # Parse content - extract question text and options
        options = []
        
        # Split content by option patterns
        # Look for patterns like "1a)", "2b)", "a)", "b)", etc.
        # Pattern: optional number + letter + ) or . + text until next option or question
        opt_pattern = r'(\d+)?([a-e])[\.\)]\s*([^0-9]*?)(?=\d+[a-e][\.\)]|\d+\.\s+|$)'
        matches = list(re.finditer(opt_pattern, content, re.IGNORECASE))
        
        if matches:
            # First part is question text
            first_match_start = matches[0].start()
            q_text = content[:first_match_start].strip()
            
            # Extract options
            for match in matches:
                opt_letter = match.group(2).lower()
                opt_text = match.group(3).strip()
                # Clean option text - remove leading numbers and extra spaces
                opt_text = re.sub(r'^\d+\s*', '', opt_text)
                opt_text = re.sub(r'\s+', ' ', opt_text)  # Normalize spaces
                # Remove LaTeX markers
                opt_text = re.sub(r'\$([^\$]+)\$', r'\1', opt_text)
                if opt_text and len(opt_text) > 0:
                    options.append(f"({opt_letter}) {opt_text}")
        else:
            # No options found, treat entire content as question text
            q_text = content.strip()
        
        # Clean question text
        q_text = re.sub(r'\$\$.*?\$\$', '', q_text)  # Remove LaTeX
        q_text = re.sub(r'\$([^\$]+)\$', r'\1', q_text)  # Simplify LaTeX
        q_text = re.sub(r'\s+', ' ', q_text)  # Normalize spaces
        q_text = q_text.strip()
        
        # Remove OCR artifact numbers at start/end
        q_text = re.sub(r'^\d+\s+', '', q_text)  # Remove leading numbers
        q_text = re.sub(r'\s+\d+$', '', q_text)  # Remove trailing numbers
        
        if q_text and len(options) >= 2:
            # Only keep first 4 options if more than 4
            if len(options) > 4:
                options = options[:4]
            questions[q_num] = (q_text, options)
        
        i += 2
    
    return questions


def parse_questions(question_pages: List[str]) -> Dict[int, Tuple[str, List[str]]]:
    """
    Parse questions from question pages.
    Returns: {question_num: (question_text, options_list)}
    """
    questions = {}
    
    # Check if we have page 37/38 (special format)
    special_pages_text = []
    regular_pages = []
    
    # Combine pages 37 and 38 if they exist (question 9 spans both)
    page_37_text = None
    page_38_text = None
    
    for i, page_text in enumerate(question_pages):
        if 'Page 37' in page_text:
            page_37_text = page_text
        elif 'Page 38' in page_text:
            page_38_text = page_text
        elif len(page_text.split('\n')) < 5 and re.search(r'\d+[a-e]\)', page_text):
            # Other compact format pages
            special_pages_text.append(page_text)
        else:
            regular_pages.append(page_text)
    
    # Combine page 37 and 38 if both exist
    if page_37_text and page_38_text:
        # Merge them - remove the continuation markers
        combined = page_37_text + ' ' + page_38_text
        special_pages_text.insert(0, combined)
    elif page_37_text:
        special_pages_text.insert(0, page_37_text)
    elif page_38_text:
        special_pages_text.insert(0, page_38_text)
    
    # Parse special format pages first
    for page_text in special_pages_text:
        special_questions = parse_special_format_page(page_text)
        questions.update(special_questions)
    
    # Combine regular pages
    full_text = '\n'.join(regular_pages)
    
    # Remove garbage headers
    full_text = re.sub(r'FAST ENTRY TEST PAST PAPERS.*?\n', '', full_text, flags=re.DOTALL | re.IGNORECASE)
    full_text = re.sub(r'WWW\.PakLearningSpot\.com.*?\n', '', full_text, flags=re.DOTALL | re.IGNORECASE)
    full_text = re.sub(r'www PakLearningSpot\.com.*?\n', '', full_text, flags=re.DOTALL | re.IGNORECASE)
    full_text = re.sub(r'Download More MCQs.*?\n', '', full_text, flags=re.DOTALL | re.IGNORECASE)
    full_text = re.sub(r'📄 Page \d+.*?\n', '', full_text, flags=re.DOTALL)
    full_text = re.sub(r'\(Options c and d are on the next page\).*?📄', '', full_text, flags=re.DOTALL | re.IGNORECASE)
    full_text = re.sub(r'\(Continuation of Question \d+\).*?📄', '', full_text, flags=re.DOTALL | re.IGNORECASE)
    
    # Parse all questions
    pos = 0
    max_iterations = 1000
    iteration = 0
    last_q_num = 0
    
    while pos < len(full_text) and iteration < max_iterations:
        iteration += 1
        q_num, q_text, options, next_pos = parse_question_block(full_text, pos)
        
        if q_num is None or next_pos <= pos:
            break
        
        # Skip if question number is lower than last (likely a page number or error)
        if q_num < last_q_num and last_q_num > 0:
            pos = next_pos
            continue
        
        if q_text and len(options) >= 2:
            questions[q_num] = (q_text, options)
            last_q_num = q_num
        
        pos = next_pos
    
    return questions


def format_question_output(q_num: int, q_text: str, options: List[str], answer: str) -> str:
    """Format a single question with its answer."""
    # Clean question text - remove OCR artifacts
    q_text = re.sub(r'Page\s+\d+.*$', '', q_text, flags=re.IGNORECASE | re.MULTILINE)
    q_text = re.sub(r'www\..*$', '', q_text, flags=re.IGNORECASE | re.MULTILINE)
    q_text = re.sub(r'📄.*$', '', q_text, flags=re.MULTILINE)
    q_text = re.sub(r'Notes?:.*$', '', q_text, flags=re.DOTALL | re.IGNORECASE)
    q_text = re.sub(r'If you provide.*$', '', q_text, flags=re.DOTALL | re.IGNORECASE)
    q_text = re.sub(r'The line for.*$', '', q_text, flags=re.DOTALL | re.IGNORECASE)
    q_text = re.sub(r'\(Note:.*?\)', '', q_text, flags=re.DOTALL)
    q_text = re.sub(r'FAST PAST PAPER \d+.*$', '', q_text, flags=re.IGNORECASE | re.MULTILINE)
    q_text = re.sub(r'If you provide.*$', '', q_text, flags=re.DOTALL | re.IGNORECASE)
    q_text = re.sub(r'especially of questions.*$', '', q_text, flags=re.DOTALL | re.IGNORECASE)
    q_text = re.sub(r'including any answer keys.*$', '', q_text, flags=re.DOTALL | re.IGNORECASE)
    q_text = q_text.strip()
    
    # Clean options - remove empty or invalid options
    cleaned_options = []
    seen_letters = set()
    
    for option in options:
        opt_match = re.match(r'^\(([a-e])\)\s*(.+)$', option)
        if opt_match:
            opt_letter = opt_match.group(1)
            opt_text = opt_match.group(2).strip()
            
            # Clean option text - remove OCR artifacts
            opt_text = re.sub(r'FAST PAST PAPER.*$', '', opt_text, flags=re.IGNORECASE)
            opt_text = re.sub(r'Notes?:.*$', '', opt_text, flags=re.DOTALL | re.IGNORECASE)
            opt_text = re.sub(r'If you provide.*$', '', opt_text, flags=re.DOTALL | re.IGNORECASE)
            opt_text = re.sub(r'especially of questions.*$', '', opt_text, flags=re.DOTALL | re.IGNORECASE)
            opt_text = re.sub(r'including any answer keys.*$', '', opt_text, flags=re.DOTALL | re.IGNORECASE)
            opt_text = opt_text.strip()
            
            # Skip duplicates and empty options
            if opt_letter not in seen_letters and opt_text and len(opt_text) > 0:
                cleaned_options.append(f"({opt_letter}) {opt_text}")
                seen_letters.add(opt_letter)
    
    # Skip questions with less than 2 options
    if len(cleaned_options) < 2:
        return ""
    
    # Limit to 4 options maximum
    if len(cleaned_options) > 4:
        cleaned_options = cleaned_options[:4]
    
    output = f"{q_num}. {q_text}\n"
    
    for option in cleaned_options:
        output += f"{option}\n"
    
    if answer:
        output += f"ans:{answer}\n"
    else:
        output += "ans: [ANSWER NOT FOUND]\n"
    
    output += "\n"
    return output


def process_fast_papers():
    """Process FAST papers - main entry point"""
    base_dir = Path('data/output/OCR/FAST/FAST ENTRY TEST PAST PAPERS PLSPOT_watermark')
    
    for paper_num, paper_info in PAPERS.items():
        print(f"\nProcessing {paper_info['name']}...")
        
        # Read answer page
        answer_file = base_dir / f'page_{paper_info["answer_page"]:03d}.txt'
        if answer_file.exists():
            with open(answer_file, 'r', encoding='utf-8') as f:
                answer_text = f.read()
            answers = parse_answers(answer_text)
            print(f"Found {len(answers)} answers")
        else:
            print(f"Warning: {answer_file} not found")
            answers = {}
        
        # Read question pages
        question_pages = []
        for page_num in paper_info['question_pages']:
            page_file = base_dir / f'page_{page_num:03d}.txt'
            if page_file.exists():
                with open(page_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Skip very short files (likely empty or just headers)
                    if len(content.strip()) > 50:
                        question_pages.append(content)
            else:
                print(f"Warning: {page_file} not found")
        
        # Parse questions
        questions = parse_questions(question_pages)
        print(f"Found {len(questions)} questions")
        
        # Generate output file
        output_file = base_dir / paper_info['filename']
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"{paper_info['name']}\n")
            f.write("=" * len(paper_info['name']) + "\n\n")
            
            # Write questions with answers
            for q_num in sorted(questions.keys()):
                q_text, options = questions[q_num]
                answer = answers.get(q_num, '')
                
                formatted = format_question_output(q_num, q_text, options, answer)
                if formatted:
                    f.write(formatted)
        
        print(f"Created: {output_file}")
    
    print("\nDone! Generated 3 paper files.")


def main():
    """Main function for direct execution"""
    process_fast_papers()

if __name__ == '__main__':
    main()

