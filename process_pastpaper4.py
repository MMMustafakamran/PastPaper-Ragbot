"""
Process NUST-Engineering-Pastpaper-4(educatedzone.com)_solved.txt
Subject divisions:
- Questions 1-80: Mathematics
- Questions 81-139: Physics
- Questions 140-169: Chemistry
- Questions 170-200: English
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

SOURCE_FILE = Path("data/Standard_text/NET/NUST-Engineering-Pastpaper-4(educatedzone.com)_solved.txt")
OUTPUT_ROOT = Path("processed_data/NET/pastpaper4")

# Topic keywords from Topics_net
MATH_KEYWORDS = {
    "Functions and Limits": ["function", "limit", "domain", "range", "continuous", "discontinuous", 
                             "identity", "explicit", "implicit", "parametric", "inverse function",
                             "hyperbolic", "cosh", "sinh", "tanh", "sin⁻¹", "cos⁻¹", "tan⁻¹"],
    "Differentiation": ["derivative", "differentiation", "tangent", "normal", "maxima", "minima",
                        "chain rule", "product rule", "quotient rule", "dy/dx", "f'(x)"],
    "Integration": ["integral", "integration", "definite", "indefinite", "area under curve",
                   "substitution", "by parts", "partial fractions", "∫"],
    "Trigonometry": ["sin", "cos", "tan", "cot", "sec", "cosec", "trigonometric", "radian", "degree",
                    "triangle", "angle", "sine", "cosine"],
    "Complex Numbers": ["complex", "imaginary", "iota", "real component", "imaginary component", "|z|", "arg"],
    "Matrices and Determinants": ["matrix", "determinant", "singular", "non-singular", "transpose"],
    "Vectors": ["vector", "dot product", "cross product", "magnitude", "direction"],
    "Sequences and Series": ["sequence", "series", "arithmetic", "geometric", "progression", "fibonacci", "harmonic",
                            "AP", "GP", "sum"],
    "Probability and Statistics": ["probability", "permutation", "combination", "mean", "median", "mode"],
    "Analytical Geometry": ["coordinate", "distance", "slope", "equation of line", "circle", "centroid", "locus",
                           "point", "line", "intersection"],
    "Conic Sections": ["parabola", "ellipse", "hyperbola", "conic", "focus", "directrix", "eccentricity",
                       "latus rectum", "transverse axis"],
    "Linear Inequalities": ["inequality", "inequalities"],
}

PHYSICS_KEYWORDS = {
    "Mechanics": ["force", "acceleration", "velocity", "momentum", "work", "energy", "power", "gravity",
                  "torque", "vector", "angular", "motion", "mass", "displacement", "kinetic", "potential",
                  "pendulum", "oscillation", "projectile", "friction", "terminal velocity", "escape velocity",
                  "rotational", "moment of inertia", "angular momentum", "couple"],
    "Waves and Oscillations": ["wave", "frequency", "wavelength", "amplitude", "sound", "doppler", "resonance",
                               "oscillator", "simple harmonic", "diffraction", "interference", "polarization",
                               "ultrasonic", "echo", "stationary wave", "progressive wave"],
    "Electricity and Magnetism": ["electric", "charge", "field", "current", "voltage", "resistance", "capacitor",
                                  "magnetic", "flux", "circuit", "ohm", "inductor", "ampere", "electron"],
    "Optics": ["lens", "refraction", "reflection", "optical", "light", "ray", "image", "phase change"],
    "Thermodynamics": ["temperature", "heat", "thermodynamics", "pressure", "kelvin", "gas", "expansion",
                      "melting", "equilibrium", "entropy", "adiabatic", "isothermal"],
    "Modern Physics": ["photon", "electron", "atom", "transistor", "laser", "photoelectric", "atomic structure",
                      "nuclear", "radioactive", "half-life", "isotope", "relativity"],
}

CHEM_KEYWORDS = {
    "Atomic Structure": ["atomic", "atom", "isotope", "electrons", "protons", "neutrons", "orbital",
                        "electronic", "quantum", "ionization potential"],
    "Chemical Bonding": ["bond", "ionic", "covalent", "metallic", "hybridization", "molecular", "geometry",
                         "polarizable"],
    "Organic Chemistry": ["hydrocarbon", "functional", "organic", "alkane", "alkene", "alkyne", "aromatic",
                         "ethylene", "methanol", "ethanol"],
    "Acids and Bases": ["ph", "acid", "base", "neutralization", "ammonium", "litmus", "poh", "buffer"],
    "Chemical Reactions": ["equilibrium", "reaction", "mass action", "rate", "ksp", "spontaneous",
                           "reversible", "irreversible"],
    "Thermochemistry": ["enthalpy", "entropy", "endothermic", "exothermic", "thermochemistry",
                        "heat of reaction", "lattice energy", "born haber"],
}

ENGLISH_KEYWORDS = {
    "Grammar and Syntax": ["grammar", "syntax", "sentence", "tense", "clause", "structure", "wages", "class"],
    "Vocabulary": ["synonym", "antonym", "meaning", "definition", "word", "idiom", "phrase", "admonish",
                  "animosity", "portly", "impetuous", "valid"],
    "Reading Comprehension": ["passage", "comprehension", "paragraph", "main idea", "context", "era",
                              "government", "economic", "freedom"],
    "Intelligence": ["analogy", "race", "strut", "industrious", "scholar", "cool"],
}


def parse_file() -> List[Dict]:
    """Parse the past paper file"""
    content = SOURCE_FILE.read_text(encoding="utf-8")
    
    # Remove the header line and any markdown code blocks
    lines = content.split('\n')
    cleaned_lines = []
    skip_block = False
    
    for line in lines:
        # Skip markdown code blocks
        if line.strip().startswith('```'):
            skip_block = not skip_block
            continue
        if skip_block:
            continue
        # Skip header
        if "NUST-Engineering-Pastpaper" in line or "Here are the next" in line:
            continue
        cleaned_lines.append(line)
    
    # Split into question blocks
    blocks = []
    current = []
    
    for line in cleaned_lines:
        stripped = line.strip()
        if stripped:
            current.append(stripped)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    
    questions = []
    for block in blocks:
        if not block:
            continue
        
        # Find question number and text
        head = block[0]
        match = re.match(r'^(\d+)\.\s*(.+)$', head)
        if not match:
            continue
        
        number = int(match.group(1))
        question_text = match.group(2).strip()
        
        # Extract options
        options = []
        answer_key = None
        
        for line in block[1:]:
            # Check for option
            opt_match = re.match(r'^\(([a-d])\)\s*(.+)$', line, re.IGNORECASE)
            if opt_match:
                key = opt_match.group(1).lower()
                value = opt_match.group(2).strip()
                options.append({"key": key, "value": value})
                continue
            
            # Check for answer
            ans_match = re.match(r'^ans[:\s]+([a-d])', line, re.IGNORECASE)
            if ans_match:
                answer_key = ans_match.group(1).lower()
        
        if not options or not answer_key:
            continue
        
        # Find correct answer value
        correct_value = next((opt["value"] for opt in options if opt["key"] == answer_key), "")
        
        questions.append({
            "number": number,
            "text": question_text,
            "options": options,
            "answer_key": answer_key,
            "answer_value": correct_value
        })
    
    return questions


def determine_subject(number: int) -> str:
    """Determine subject based on question number"""
    if 1 <= number <= 80:
        return "Mathematics"
    elif 81 <= number <= 139:
        return "Physics"
    elif 140 <= number <= 169:
        return "Chemistry"
    elif 170 <= number <= 200:
        return "English"
    return "General"


def classify_topic(question: Dict) -> Tuple[str, str]:
    """Classify question into subject and topic"""
    number = question["number"]
    text = question["text"].lower()
    
    subject = determine_subject(number)
    
    # Select appropriate keyword map
    if subject == "Mathematics":
        topic_map = MATH_KEYWORDS
    elif subject == "Physics":
        topic_map = PHYSICS_KEYWORDS
    elif subject == "Chemistry":
        topic_map = CHEM_KEYWORDS
    elif subject == "English":
        topic_map = ENGLISH_KEYWORDS
    else:
        return subject, "General"
    
    # Find matching topic
    main_topic = "General"
    for topic, keywords in topic_map.items():
        if any(keyword in text for keyword in keywords):
            main_topic = topic
            break
    
    return subject, main_topic


def estimate_difficulty(text: str) -> str:
    """Estimate question difficulty"""
    text_lower = text.lower()
    
    easy_keywords = ["define", "what is", "identify", "which one"]
    hard_keywords = ["prove", "derive", "evaluate", "calculate", "find the value", "solve"]
    
    hard_count = sum(1 for kw in hard_keywords if kw in text_lower)
    easy_count = sum(1 for kw in easy_keywords if kw in text_lower)
    
    word_count = len(text.split())
    
    if hard_count > 0 or word_count > 30:
        return "hard"
    elif easy_count > 0 or word_count < 15:
        return "easy"
    else:
        return "medium"


def build_dataset():
    """Build and save JSON datasets"""
    questions = parse_file()
    print(f"Parsed {len(questions)} questions from {SOURCE_FILE.name}")
    
    grouped: Dict[Tuple[str, str], List[Dict]] = {}
    
    for idx, q in enumerate(questions, start=1):
        subject, topic = classify_topic(q)
        difficulty = estimate_difficulty(q["text"])
        
        question_id = f"NET_{subject[:3].upper()}_{topic.replace(' ', '_').upper()}_Q{q['number']:03d}"
        
        embedding_text = (
            f"{subject} - {topic}: {q['text']} Options: "
            f"{', '.join(opt['value'] for opt in q['options'])}. "
            f"Correct answer: {q['answer_value']}"
        )
        
        entry = {
            "question_id": question_id,
            "source": {
                "exam_type": "NET",
                "subject": subject,
                "paper_name": SOURCE_FILE.stem,
                "year": "2024"
            },
            "topic": {
                "main_topic": topic,
                "sub_topic": topic,
                "difficulty": difficulty
            },
            "question": {
                "text": q["text"],
                "type": "mcq",
                "format": "single_choice"
            },
            "options": q["options"],
            "answer": {
                "correct_key": q["answer_key"],
                "correct_value": q["answer_value"],
                "explanation": ""
            },
            "embedding_text": embedding_text,
            "metadata": {
                "keywords": [],
                "related_concepts": [topic.lower()],
                "prerequisites": [topic.lower()],
                "difficulty_level": difficulty,
                "cognitive_skill": "application",
                "bloom_level": "L3_Apply"
            }
        }
        
        grouped.setdefault((subject, topic), []).append(entry)
    
    # Save datasets
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    summaries = []
    
    for (subject, topic), q_list in grouped.items():
        dataset = {
            "dataset_info": {
                "dataset_name": f"NET {subject} - {topic}",
                "version": "1.0",
                "created_date": datetime.now().strftime("%Y-%m-%d"),
                "total_questions": len(q_list),
                "source_file": SOURCE_FILE.name,
                "exam_type": "NET",
                "subject": subject,
                "main_topic": topic
            },
            "questions": q_list
        }
        
        output_path = OUTPUT_ROOT / subject / f"{topic.replace(' ', '_').lower()}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        summaries.append((output_path, len(q_list)))
    
    return summaries


if __name__ == "__main__":
    summaries = build_dataset()
    print(f"\n{'='*60}")
    print("Processing Complete!")
    print(f"{'='*60}\n")
    for path, count in summaries:
        print(f"Saved {path} ({count} questions)")

