#!/usr/bin/env python3
"""
Script to combine questions with answers from OCR text files.
Processes pages 1-50 (questions) and pages 51-53 (answers),
then outputs 7 separate topic files with questions and inline answers.
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Topic configuration
TOPICS = {
    1: {
        'name': 'Functions and Limits',
        'pages': list(range(1, 8)),  # pages 1-7
        'filename': 'topic_1_functions_and_limits.txt'
    },
    2: {
        'name': 'Differentiation',
        'pages': list(range(7, 18)),  # pages 7-17
        'filename': 'topic_2_differentiation.txt'
    },
    3: {
        'name': 'Integration',
        'pages': list(range(17, 24)),  # pages 17-23
        'filename': 'topic_3_integration.txt'
    },
    4: {
        'name': 'Analytical Geometry',
        'pages': list(range(23, 31)),  # pages 23-30
        'filename': 'topic_4_analytical_geometry.txt'
    },
    5: {
        'name': 'Linear Inequalities',
        'pages': list(range(30, 33)),  # pages 30-32
        'filename': 'topic_5_linear_inequalities.txt'
    },
    6: {
        'name': 'Conic',
        'pages': list(range(32, 46)),  # pages 32-45
        'filename': 'topic_6_conic.txt'
    },
    7: {
        'name': 'Vector',
        'pages': list(range(45, 51)),  # pages 45-50
        'filename': 'topic_7_vector.txt'
    }
}


def parse_answers(answer_pages: List[str]) -> Dict[int, Dict[int, str]]:
    """
    Parse answer pages and extract answers by unit.
    Returns: {unit_num: {question_num: answer_letter}}
    """
    answers = {i: {} for i in range(1, 8)}
    
    # Combine all answer pages
    full_text = '\n'.join(answer_pages)
    
    # Find all unit answer sections
    unit_pattern = r'Unit\s*[-–]\s*(\d+)\s+ANSWERS'
    unit_matches = list(re.finditer(unit_pattern, full_text, re.IGNORECASE))
    
    for i, match in enumerate(unit_matches):
        unit_num = int(match.group(1))
        start_pos = match.end()
        
        # Find the end of this unit's answers (next unit or end of file)
        if i + 1 < len(unit_matches):
            end_pos = unit_matches[i + 1].start()
        else:
            end_pos = len(full_text)
        
        unit_text = full_text[start_pos:end_pos]
        
        # Parse answer lines - handle both formats: "1. b 2. a" and "1. b, 2. a,"
        # Also handle "1. b, 2. a," format from page 53
        answer_pattern = r'(\d+)\.\s*([a-d])[,]?\s*'
        answer_matches = re.findall(answer_pattern, unit_text)
        
        for q_num_str, answer_letter in answer_matches:
            q_num = int(q_num_str)
            answers[unit_num][q_num] = answer_letter.lower().strip()
    
    return answers


def parse_question_block(text: str, start_pos: int) -> Tuple[int, str, List[str], int]:
    """
    Parse a single question block starting at start_pos.
    Returns: (question_num, question_text, options_list, next_pos)
    """
    # Find question number - look for pattern like "19. " or "1. "
    # Skip standalone page numbers (single digit followed by period and newline/end)
    q_num_pattern = r'^(\d+)\.\s+'
    match = re.search(q_num_pattern, text[start_pos:], re.MULTILINE)
    
    if not match:
        return None, None, None, start_pos
    
    q_num = int(match.group(1))
    content_start = start_pos + match.end()
    
    # Check if this is likely a page number (appears alone on a line with little/no content after)
    # Page numbers are usually followed by newlines and then headers/questions
    next_content = text[content_start:content_start+100].strip()
    # If the content after is very short or starts with newline/whitespace, might be page number
    if len(next_content) < 10:
        # Check if next line starts with a question number (higher than current)
        next_q_match = re.search(r'^(\d+)\.\s+', next_content, re.MULTILINE)
        if next_q_match:
            next_q_num = int(next_q_match.group(1))
            # If next question number is higher, current might be page number
            if next_q_num > q_num:
                q_num = next_q_num
                content_start = start_pos + match.end() + next_q_match.start() + next_q_match.end()
            elif next_q_num == q_num + 1:
                # Current is likely page number, use next
                q_num = next_q_num
                content_start = start_pos + match.end() + next_q_match.start() + next_q_match.end()
    
    # Find the end of this question (next question number or unit header)
    next_q_pattern = r'\n(\d+)\.\s+'
    next_q_match = re.search(next_q_pattern, text[content_start:], re.MULTILINE)
    
    unit_pattern = r'\nUnit\s*[-–]\s*\d+'
    unit_match = re.search(unit_pattern, text[content_start:], re.IGNORECASE | re.MULTILINE)
    
    # Determine end position
    end_pos = len(text)
    if next_q_match:
        end_pos = min(end_pos, content_start + next_q_match.start())
    if unit_match:
        end_pos = min(end_pos, content_start + unit_match.start())
    
    question_block = text[content_start:end_pos].strip()
    
    # Parse question text and options
    # Options can be on separate lines: (a) ... or on same line: (a) ... (b) ...
    lines = question_block.split('\n')
    question_lines = []
    options = []
    
    # First, try to find options in the format (a) ... (b) ... on same line
    inline_option_pattern = r'\(([a-d])\)\s*([^(]+?)(?=\s*\([a-d]\)|$)'
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for inline options (multiple options on one line)
        inline_options = re.findall(inline_option_pattern, line)
        if inline_options:
            # This line has inline options
            # Extract question part before first option
            first_option_pos = line.find('(')
            if first_option_pos > 0:
                question_part = line[:first_option_pos].strip()
                if question_part:
                    question_lines.append(question_part)
            
            # Add all inline options
            for opt_letter, opt_text in inline_options:
                options.append(f"({opt_letter}) {opt_text.strip()}")
        else:
            # Check if this is a standalone option line
            option_match = re.match(r'^\(([a-d])\)\s*(.+)$', line)
            if option_match:
                options.append(f"({option_match.group(1)}) {option_match.group(2)}")
            else:
                # Check if this continues a previous option (no leading (a-d))
                if options and not re.match(r'^\([a-d]\)', line):
                    # Might be continuation of last option
                    options[-1] += ' ' + line
                else:
                    # Regular question text
                    question_lines.append(line)
    
    question_text = '\n'.join(question_lines).strip()
    
    # Clean up OCR artifacts
    # Remove common OCR artifacts like page numbers, URLs, headers
    question_text = re.sub(r'\s+\d+\s*$', '', question_text)  # Remove trailing page numbers
    question_text = re.sub(r'NET Past Papers.*?EduManias', '', question_text, flags=re.DOTALL | re.IGNORECASE)
    question_text = re.sub(r'NET Past Papers.*?facebook\.com.*?EduManias', '', question_text, flags=re.DOTALL | re.IGNORECASE)
    question_text = re.sub(r'NET Past Papers.*?Objective Type Questions', '', question_text, flags=re.DOTALL | re.IGNORECASE)
    question_text = re.sub(r'Objective Type Questions\s*\d*', '', question_text, flags=re.IGNORECASE | re.MULTILINE)
    question_text = re.sub(r'https?://[^\s]+', '', question_text)  # Remove URLs
    question_text = re.sub(r'https://edumanias\.com/', '', question_text, flags=re.IGNORECASE)
    question_text = re.sub(r'https://www\.facebook\.com/[^\s]+', '', question_text, flags=re.IGNORECASE)
    # Remove standalone "NET Past Papers" or similar headers
    question_text = re.sub(r'^NET Past Papers\s*$', '', question_text, flags=re.MULTILINE | re.IGNORECASE)
    question_text = re.sub(r'NET Past Papers\s+', '', question_text, flags=re.IGNORECASE)
    # Remove duplicate question numbers at start of lines (but keep the first one)
    lines = question_text.split('\n')
    cleaned_lines = []
    for i, line in enumerate(lines):
        # Remove standalone question numbers that appear after the first line
        if i > 0 and re.match(r'^\d+\.\s*$', line.strip()):
            continue
        # Remove question number prefix from continuation lines
        if i > 0 and re.match(r'^\d+\.\s+', line):
            line = re.sub(r'^\d+\.\s+', '', line)
        cleaned_lines.append(line)
    question_text = '\n'.join(cleaned_lines).strip()
    
    # Remove question numbers that appear at the very start of the question text
    # Pattern: "2. 9. Question text" -> "Question text"
    question_text = re.sub(r'^\d+\.\s+(\d+\.\s+)', r'\1', question_text)
    # If still starts with a number pattern that looks wrong, clean it
    if re.match(r'^\d+\.\s+\d+\.\s+', question_text):
        question_text = re.sub(r'^\d+\.\s+', '', question_text, count=1)
    
    # Clean up options - remove "[text unreadable]" markers
    for i, opt in enumerate(options):
        cleaned_opt = re.sub(r'\[text unreadable\]', '', opt, flags=re.IGNORECASE).strip()
        cleaned_opt = re.sub(r'\[unreadable\]', '', cleaned_opt, flags=re.IGNORECASE).strip()
        # Remove empty options or options that are just markers
        if cleaned_opt and not re.match(r'^\([a-d]\)\s*$', cleaned_opt):
            # Keep the option
            options[i] = cleaned_opt
        elif cleaned_opt:  # Has label but no content
            # Try to extract just the label
            label_match = re.match(r'^\(([a-d])\)', cleaned_opt)
            if label_match:
                options[i] = f"({label_match.group(1)}) [Option text unavailable]"
            else:
                options[i] = cleaned_opt
        else:
            # Try to preserve the option label if possible
            label_match = re.match(r'^\(([a-d])\)', opt)
            if label_match:
                options[i] = f"({label_match.group(1)}) [Option text unavailable]"
            else:
                options[i] = opt
    
    next_pos = end_pos
    
    return q_num, question_text, options, next_pos


def parse_questions(question_pages: List[str], unit_num: int) -> Dict[int, Tuple[str, List[str]]]:
    """
    Parse questions from question pages for a specific unit.
    Returns: {question_num: (question_text, options_list)}
    """
    questions = {}
    
    # Combine pages for this unit
    full_text = '\n'.join(question_pages)
    
    # Find the unit header - try multiple patterns
    unit_patterns = [
        rf'Unit\s*[-–]\s*{unit_num}\s*[\(\[].*?[\)\]]',  # Unit -1 ( Functions and Limits)
        rf'Unit\s*[-–]\s*{unit_num}\s+',  # Unit -1 
        rf'Unit\s*[-–]\s*{unit_num}[^\d]',  # Unit -1 followed by non-digit
    ]
    
    unit_match = None
    for pattern in unit_patterns:
        unit_match = re.search(pattern, full_text, re.IGNORECASE)
        if unit_match:
            break
    
    if unit_match:
        start_pos = unit_match.end()
    else:
        # If no unit header found, start from beginning
        # But for Unit 2, skip Unit 1 questions if they appear
        if unit_num == 2:
            # Look for Unit 1 header and skip past its questions
            unit1_pattern = r'Unit\s*[-–]\s*1\s*[\(\[].*?[\)\]]'
            unit1_match = re.search(unit1_pattern, full_text, re.IGNORECASE)
            if unit1_match:
                # Find where Unit 1 questions end (question 75)
                # Look for question 75 or higher, then find where questions reset to 1
                # Find question 75 (last Unit 1 question)
                q75_pattern = r'75\.\s+'
                q75_matches = list(re.finditer(q75_pattern, full_text))
                if q75_matches:
                    # Use the last occurrence of question 75
                    q75_match = q75_matches[-1]
                    # After question 75, find where questions restart at 1 (Unit 2 starts)
                    after_q75 = full_text[q75_match.end():]
                    # Look for question 1 that's followed by Unit 2 content (differentiation-related)
                    q1_pattern = r'^1\.\s+'
                    q1_matches = list(re.finditer(q1_pattern, after_q75, re.MULTILINE))
                    if q1_matches:
                        # Use the first question 1 after question 75
                        q1_match = q1_matches[0]
                        start_pos = q75_match.end() + q1_match.start()
                    else:
                        # If no question 1 found, start after question 75
                        start_pos = q75_match.end()
                else:
                    # If question 75 not found, look for first question 1 in the text
                    q1_pattern = r'^1\.\s+'
                    q1_match = re.search(q1_pattern, full_text, re.MULTILINE)
                    if q1_match:
                        start_pos = q1_match.start()
                    else:
                        start_pos = 0
            else:
                start_pos = 0
        else:
            start_pos = 0
    
    # Find next unit or end
    next_unit_patterns = [
        rf'Unit\s*[-–]\s*{unit_num + 1}\s*[\(\[].*?[\)\]]',
        rf'Unit\s*[-–]\s*{unit_num + 1}\s+',
        rf'Unit\s*[-–]\s*{unit_num + 1}[^\d]',
    ]
    
    next_unit_match = None
    for pattern in next_unit_patterns:
        next_unit_match = re.search(pattern, full_text[start_pos:], re.IGNORECASE)
        if next_unit_match:
            break
    
    if next_unit_match:
        end_pos = start_pos + next_unit_match.start()
    else:
        end_pos = len(full_text)
    
    unit_text = full_text[start_pos:end_pos]
    
    # Clean up common OCR artifacts at the start
    unit_text = re.sub(r'^[^\d]*', '', unit_text)  # Remove non-digit characters at start
    
    # Parse all questions in this unit
    pos = 0
    max_iterations = 1000  # Safety limit
    iteration = 0
    last_q_num = 0
    
    while pos < len(unit_text) and iteration < max_iterations:
        iteration += 1
        q_num, q_text, options, next_pos = parse_question_block(unit_text, pos)
        
        if q_num is None or next_pos <= pos:
            # No more questions found or stuck
            break
        
        # Skip if this question number is lower than last (likely a page number)
        # But allow if it's the first question or if it's reasonable (within 5 of last)
        # Special case: Unit 2 questions start at 1, so skip any questions > 75 (those are Unit 1)
        if unit_num == 2 and q_num > 75:
            pos = next_pos
            continue
        
        if q_num < last_q_num and last_q_num > 0:
            # Allow if we're starting a new unit (question number resets to 1)
            if q_num == 1 and last_q_num > 50:
                # This is likely a new unit starting
                pass
            else:
                pos = next_pos
                continue
        
        # Check if this looks like a page number: number followed by newline and then higher number
        # But be less aggressive - only skip if it's a very small number (likely page number)
        if q_num <= 10 and last_q_num > 0:  # Page numbers are typically <= 10
            # Look ahead to see if next question number is much higher
            lookahead_text = unit_text[next_pos:next_pos+200]
            next_q_match = re.search(r'^(\d+)\.\s+', lookahead_text, re.MULTILINE)
            if next_q_match:
                next_q_num = int(next_q_match.group(1))
                # If next question is much higher (more than 10 higher), current might be page number
                if next_q_num > q_num + 10:
                    pos = next_pos
                    continue
        
        if q_text and len(options) >= 2:  # At least 2 options
            questions[q_num] = (q_text, options)
            last_q_num = q_num
        elif q_num and q_text:  # Store even if options are incomplete
            questions[q_num] = (q_text, options if options else [])
            last_q_num = q_num
        
        pos = next_pos
    
    return questions


def format_question_output(q_num: int, q_text: str, options: List[str], answer: str) -> str:
    """Format a single question with its answer."""
    # Clean question text - remove garbage statements
    q_text = re.sub(r'NET Past Papers.*?EduManias', '', q_text, flags=re.DOTALL | re.IGNORECASE)
    q_text = re.sub(r'NET Past Papers.*?facebook\.com.*?EduManias', '', q_text, flags=re.DOTALL | re.IGNORECASE)
    q_text = re.sub(r'NET Past Papers.*?Objective Type Questions', '', q_text, flags=re.DOTALL | re.IGNORECASE)
    q_text = re.sub(r'Objective Type Questions\s*\d*', '', q_text, flags=re.IGNORECASE | re.MULTILINE)
    q_text = re.sub(r'https?://[^\s]+', '', q_text)  # Remove URLs
    q_text = re.sub(r'NET Past Papers\s+', '', q_text, flags=re.IGNORECASE)
    q_text = q_text.strip()
    
    # Clean options - remove unreadable markers and garbage
    cleaned_options = []
    for option in options:
        opt = option
        opt = re.sub(r'\[text unreadable\]', '', opt, flags=re.IGNORECASE)
        opt = re.sub(r'\[unreadable\]', '', opt, flags=re.IGNORECASE)
        opt = re.sub(r'NET Past Papers.*?EduManias', '', opt, flags=re.DOTALL | re.IGNORECASE)
        opt = re.sub(r'Objective Type Questions.*', '', opt, flags=re.IGNORECASE)
        opt = re.sub(r'https?://[^\s]+', '', opt)
        opt = opt.strip()
        if opt and not re.match(r'^\([a-d]\)\s*$', opt):  # Not just empty label
            # Check if option contains only placeholder text
            if not re.search(r'\[Option text unavailable\]|unavailable|unreadable', opt, re.IGNORECASE):
                cleaned_options.append(opt)
        # Skip options that are just labels with no content or are marked as unavailable
    
    # Skip questions where all options are unavailable/unreadable
    if len(cleaned_options) == 0:
        return ""  # Return empty string to skip this question
    
    output = f"{q_num}. {q_text}\n"
    
    for option in cleaned_options:
        output += f"{option}\n"
    
    if answer:
        output += f"ans:{answer}\n"
    else:
        output += "ans: [ANSWER NOT FOUND]\n"
    
    output += "\n"
    return output


def main():
    base_dir = Path('data/output/OCR/NET/497992392-NUST-NET-Solved-MCQs')
    
    # Read answer pages
    print("Reading answer pages...")
    answer_pages = []
    for page_num in [51, 52, 53]:
        page_file = base_dir / f'page_{page_num:03d}.txt'
        if page_file.exists():
            with open(page_file, 'r', encoding='utf-8') as f:
                answer_pages.append(f.read())
        else:
            print(f"Warning: {page_file} not found")
    
    # Parse answers
    print("Parsing answers...")
    answers = parse_answers(answer_pages)
    
    # Process each topic
    for unit_num, topic_info in TOPICS.items():
        print(f"\nProcessing Topic {unit_num}: {topic_info['name']}...")
        
        # Read question pages for this topic
        question_pages = []
        for page_num in topic_info['pages']:
            page_file = base_dir / f'page_{page_num:03d}.txt'
            if page_file.exists():
                with open(page_file, 'r', encoding='utf-8') as f:
                    question_pages.append(f.read())
            else:
                print(f"Warning: {page_file} not found")
        
        # Parse questions for this unit
        questions = parse_questions(question_pages, unit_num)
        
        print(f"Found {len(questions)} questions, {len(answers[unit_num])} answers")
        
        # Generate output file
        output_file = base_dir / topic_info['filename']
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"{topic_info['name']}\n")
            f.write("=" * len(topic_info['name']) + "\n\n")
            
            # Write questions with answers
            for q_num in sorted(questions.keys()):
                q_text, options = questions[q_num]
                answer = answers[unit_num].get(q_num, '')
                
                formatted = format_question_output(q_num, q_text, options, answer)
                # Only write if formatted output is not empty (skipped questions)
                if formatted:
                    f.write(formatted)
        
        print(f"Created: {output_file}")
    
    print("\nDone! Generated 7 topic files.")


if __name__ == '__main__':
    main()

