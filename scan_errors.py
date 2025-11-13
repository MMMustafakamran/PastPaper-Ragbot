#!/usr/bin/env python3
"""
Script to scan topic files for errors and generate a report.
"""

import re
from pathlib import Path

def scan_file(filepath):
    """Scan a topic file for errors."""
    errors = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    current_q = None
    current_options = []
    q_numbers = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for question number
        q_match = re.match(r'^(\d+)\.\s+(.+)$', line)
        if q_match:
            q_num = int(q_match.group(1))
            q_text = q_match.group(2)
            
            # Check if previous question had issues
            if current_q is not None:
                if len(current_options) < 2:
                    errors.append(f"Question {current_q}: Only {len(current_options)} options found (need at least 2)")
                if len(current_options) > 4:
                    errors.append(f"Question {current_q}: {len(current_options)} options found (should be 4)")
            
            current_q = q_num
            current_options = []
            q_numbers.append(q_num)
            
            # Check for empty question text
            if not q_text or len(q_text) < 3:
                errors.append(f"Question {q_num}: Empty or very short question text")
        
        # Check for options
        elif re.match(r'^\([a-d]\)\s*(.+)$', line):
            opt_match = re.match(r'^\(([a-d])\)\s*(.+)$', line)
            if opt_match:
                opt_text = opt_match.group(2).strip()
                if not opt_text or len(opt_text) < 1:
                    errors.append(f"Question {current_q}: Empty option ({opt_match.group(1)})")
                current_options.append(opt_match.group(1))
        
        # Check for empty option label
        elif re.match(r'^\([a-d]\)\s*$', line):
            errors.append(f"Question {current_q}: Empty option label found")
        
        # Check for answer
        elif line.startswith('ans:'):
            if current_q is None:
                errors.append(f"Answer found without question: {line}")
            elif len(current_options) == 0:
                errors.append(f"Question {current_q}: Answer found but no options")
        
        i += 1
    
    # Check for missing question numbers (gaps)
    if q_numbers:
        q_numbers.sort()
        for i in range(len(q_numbers) - 1):
            if q_numbers[i+1] - q_numbers[i] > 1:
                missing = list(range(q_numbers[i] + 1, q_numbers[i+1]))
                errors.append(f"Missing question numbers: {missing}")
    
    # Check for duplicate question numbers
    seen = set()
    for q_num in q_numbers:
        if q_num in seen:
            errors.append(f"Duplicate question number: {q_num}")
        seen.add(q_num)
    
    return errors

def main():
    base_dir = Path('data/output/OCR/NET/497992392-NUST-NET-Solved-MCQs')
    
    topic_files = [
        'topic_1_functions_and_limits.txt',
        'topic_2_differentiation.txt',
        'topic_3_integration.txt',
        'topic_4_analytical_geometry.txt',
        'topic_5_linear_inequalities.txt',
        'topic_6_conic.txt',
        'topic_7_vector.txt',
    ]
    
    print("Scanning topic files for errors...\n")
    
    all_errors = {}
    for topic_file in topic_files:
        filepath = base_dir / topic_file
        if filepath.exists():
            errors = scan_file(filepath)
            if errors:
                all_errors[topic_file] = errors
    
    if all_errors:
        print("ERRORS FOUND:\n")
        for topic_file, errors in all_errors.items():
            print(f"{topic_file}:")
            for error in errors:
                print(f"  - {error}")
            print()
    else:
        print("No errors found!")
    
    # Summary
    total_errors = sum(len(errors) for errors in all_errors.values())
    print(f"\nTotal errors found: {total_errors}")

if __name__ == '__main__':
    main()

