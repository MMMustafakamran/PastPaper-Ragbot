import pdfplumber
import PyPDF2
import json
import re
from typing import List, Dict, Any

def extract_text_with_pdfplumber(pdf_path: str) -> str:
    """Extract text using pdfplumber (better for complex layouts)"""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_text_with_pypdf2(pdf_path: str) -> str:
    """Extract text using PyPDF2 (fallback method)"""
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text

def analyze_pdf_structure(text: str) -> Dict[str, Any]:
    """Analyze the structure of the extracted text"""
    analysis = {
        "total_length": len(text),
        "lines": len(text.split('\n')),
        "questions_found": [],
        "sections": [],
        "patterns": {}
    }
    
    # Look for question patterns
    question_patterns = [
        r'Question\s+\d+',
        r'Q\d+',
        r'\d+\.\s+[A-Z]',
        r'^\d+\)',
        r'Part\s+[A-Z]',
        r'Section\s+[A-Z]'
    ]
    
    for pattern in question_patterns:
        matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
        if matches:
            analysis["patterns"][pattern] = len(matches)
            analysis["questions_found"].extend(matches[:10])  # First 10 matches
    
    # Look for option patterns
    option_patterns = [
        r'[A-D]\)',
        r'\([A-D]\)',
        r'Option\s+[A-D]'
    ]
    
    for pattern in option_patterns:
        matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
        if matches:
            analysis["patterns"][pattern] = len(matches)
    
    return analysis

def extract_questions_and_answers(text: str) -> List[Dict[str, Any]]:
    """Extract structured questions and answers"""
    questions = []
    
    # Split text into lines for processing
    lines = text.split('\n')
    current_question = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check if line starts a new question
        if re.match(r'^\d+\.', line) or re.match(r'^Question\s+\d+', line, re.IGNORECASE):
            if current_question:
                questions.append(current_question)
            
            current_question = {
                "question_number": re.findall(r'\d+', line)[0] if re.findall(r'\d+', line) else None,
                "question_text": line,
                "options": [],
                "answer": None,
                "explanation": None
            }
        
        # Check for options
        elif current_question and re.match(r'^[A-D]\)', line):
            current_question["options"].append(line)
        
        # Check for answer indicators
        elif current_question and re.search(r'Answer|Correct|Solution', line, re.IGNORECASE):
            current_question["answer"] = line
    
    if current_question:
        questions.append(current_question)
    
    return questions

def main():
    pdf_path = "NUST-Engineering-Pastpaper-4(educatedzone.com).pdf"
    
    print("Extracting text from PDF...")
    
    # Try pdfplumber first
    try:
        text = extract_text_with_pdfplumber(pdf_path)
        print(f"Extracted {len(text)} characters using pdfplumber")
    except Exception as e:
        print(f"pdfplumber failed: {e}")
        # Fallback to PyPDF2
        try:
            text = extract_text_with_pypdf2(pdf_path)
            print(f"Extracted {len(text)} characters using PyPDF2")
        except Exception as e:
            print(f"Both methods failed: {e}")
            return
    
    if not text.strip():
        print("No text extracted from PDF")
        return
    
    # Save raw text
    with open("extracted_text.txt", "w", encoding="utf-8") as f:
        f.write(text)
    
    # Analyze structure
    print("\nAnalyzing PDF structure...")
    analysis = analyze_pdf_structure(text)
    
    # Extract questions
    print("\nExtracting questions...")
    questions = extract_questions_and_answers(text)
    
    # Save analysis
    with open("pdf_analysis.json", "w", encoding="utf-8") as f:
        json.dump({
            "analysis": analysis,
            "questions": questions,
            "sample_text": text[:1000]  # First 1000 characters
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nAnalysis complete:")
    print(f"- Total text length: {analysis['total_length']} characters")
    print(f"- Number of lines: {analysis['lines']}")
    print(f"- Questions found: {len(questions)}")
    print(f"- Patterns detected: {list(analysis['patterns'].keys())}")
    
    if questions:
        print(f"\nFirst question sample:")
        print(json.dumps(questions[0], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
