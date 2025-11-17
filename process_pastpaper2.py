"""
Process NUST-Engineering-Pastpaper-2(educatedzone.com)_solved.txt
Subject divisions:
- Questions 1-81: Mathematics
- Questions 82-138: Physics
- Questions 139-170: Chemistry
- Questions 171-200: English
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

SOURCE_FILE = Path("data/Standard_text/NET/NUST-Engineering-Pastpaper-2(educatedzone.com)_solved.txt")
OUTPUT_ROOT = Path("processed_data/NET/pastpaper2")

# Topic keywords from Topics_net
MATH_KEYWORDS = {
    "Functions and Limits": ["function", "limit", "domain", "range", "continuous", "discontinuous", 
                             "identity", "explicit", "implicit", "parametric", "inverse function",
                             "hyperbolic", "cosh", "sinh", "tanh", "sin⁻¹", "cos⁻¹", "tan⁻¹", "sin^{-1}"],
    "Differentiation": ["derivative", "differentiation", "tangent", "normal", "maxima", "minima",
                        "chain rule", "product rule", "quotient rule", "dy/dx", "f'(x)", "f''(x)"],
    "Integration": ["integral", "integration", "definite", "indefinite", "area under curve",
                   "substitution", "by parts", "partial fractions", "∫"],
    "Trigonometry": ["sin", "cos", "tan", "cot", "sec", "cosec", "trigonometric", "radian", "degree",
                    "triangle", "angle", "sine", "cosine", "sin^{-1}", "cos^{-1}", "sec^2", "cos^2"],
    "Complex Numbers": ["complex", "imaginary", "iota", "real component", "imaginary component", "|z|", "arg",
                       "conjugate", "modulus", "i^{", "i^"],
    "Matrices and Determinants": ["matrix", "determinant", "singular", "non-singular", "transpose", "row matrix"],
    "Vectors": ["vector", "dot product", "cross product", "magnitude", "direction", "i·", "k×"],
    "Sequences and Series": ["sequence", "series", "arithmetic", "geometric", "progression", "fibonacci", "harmonic",
                            "AP", "GP", "sum"],
    "Probability and Statistics": ["probability", "permutation", "combination", "mean", "median", "mode"],
    "Analytical Geometry": ["coordinate", "distance", "slope", "equation of line", "circle", "centroid", "locus",
                           "point", "line", "intersection"],
    "Conic Sections": ["parabola", "ellipse", "hyperbola", "conic", "focus", "directrix", "eccentricity",
                       "latus rectum", "transverse axis", "quadratic function"],
    "Linear Inequalities": ["inequality", "inequalities", "|x+", "|x-"],
    "Sets and Logic": ["set", "subset", "element", "union", "intersection", "proposition", "conjunction",
                      "disjunction", "deduction", "induction", "truth", "logical"],
    "Number Systems": ["rational", "irrational", "integer", "natural", "whole", "real", "complex",
                      "additive", "multiplicative", "identity", "inverse"],
    "Groups": ["group", "binary operation", "commutative", "associative", "identity element", "inverse element"],
}

PHYSICS_KEYWORDS = {
    "Mechanics": ["force", "acceleration", "velocity", "momentum", "work", "energy", "power", "gravity",
                  "torque", "vector", "angular", "motion", "mass", "displacement", "kinetic", "potential",
                  "pendulum", "oscillation", "projectile", "friction", "terminal velocity", "escape velocity",
                  "rotational", "moment of inertia", "angular momentum", "couple", "resultant", "equilibrium",
                  "center of gravity", "free fall", "apparent weight", "lift", "bomb", "bomber"],
    "Waves and Oscillations": ["wave", "frequency", "wavelength", "amplitude", "sound", "doppler", "resonance",
                               "oscillator", "simple harmonic", "diffraction", "interference", "polarization",
                               "ultrasonic", "echo", "stationary wave", "progressive wave", "phase angle", "loops"],
    "Electricity and Magnetism": ["electric", "charge", "field", "current", "voltage", "resistance", "capacitor",
                                  "magnetic", "flux", "circuit", "ohm", "inductor", "ampere", "electron",
                                  "coulomb", "potential gradient", "electric intensity", "resistivity", "weber",
                                  "solenoid", "henry", "reactance", "RLC", "resonant"],
    "Optics": ["lens", "refraction", "reflection", "optical", "light", "ray", "image", "phase change",
               "wavelength", "speed of light", "medium", "telescope", "diopter", "magnifying"],
    "Thermodynamics": ["temperature", "heat", "thermodynamics", "pressure", "kelvin", "gas", "expansion",
                      "melting", "equilibrium", "entropy", "adiabatic", "isothermal", "isobaric", "isochoric",
                      "density", "volume", "perpetual motion"],
    "Modern Physics": ["photon", "electron", "atom", "transistor", "laser", "photoelectric", "atomic structure",
                      "nuclear", "radioactive", "half-life", "isotope", "relativity", "compton", "x-ray",
                      "threshold frequency", "work function", "uncertainty", "metastable", "population inversion",
                      "excited state", "ground state", "transition"],
    "Properties of Matter": ["crystalline", "solid", "liquid", "gas", "steradian", "significant", "dimensions"],
    "Electronics": ["depletion region", "biasing", "doping", "semiconductor", "LED", "light emitting diode",
                   "AND gate", "NOT gate", "NAND gate", "NOR gate", "XOR gate"],
}

CHEM_KEYWORDS = {
    "Atomic Structure": ["atomic", "atom", "isotope", "electrons", "protons", "neutrons", "orbital",
                        "electronic", "quantum", "ionization potential", "bromine", "Br_{35}"],
    "Chemical Bonding": ["bond", "ionic", "covalent", "metallic", "hybridization", "molecular", "geometry",
                         "polarizable"],
    "Organic Chemistry": ["hydrocarbon", "functional", "organic", "alkane", "alkene", "alkyne", "aromatic",
                         "ethylene", "methanol", "ethanol", "CH_{4}", "C_{2}H_{5}OH", "C_{3}H_{5}O_{2}",
                         "C_{6}H_{10}O_{4}", "molecular formula", "empirical formula"],
    "Acids and Bases": ["ph", "acid", "base", "neutralization", "ammonium", "litmus", "poh", "buffer"],
    "Chemical Reactions": ["equilibrium", "reaction", "mass action", "rate", "ksp", "spontaneous",
                           "reversible", "irreversible", "forward reaction", "reverse reaction",
                           "Le Chatelier", "equilibrium constant"],
    "Thermochemistry": ["enthalpy", "entropy", "endothermic", "exothermic", "thermochemistry",
                        "heat of reaction", "lattice energy", "born haber"],
    "Stoichiometry": ["mole", "molar", "Avogadro", "N_{A}", "g-atom", "STP", "calcium carbonate",
                     "CaCO_{3}", "limestone", "CO_{2}", "O_{2}", "H_{2}", "percentage", "empirical",
                     "molecular formula", "vapors density", "weight", "mass", "concentration", "M"],
    "States of Matter": ["ideal gas", "kinetic", "critical temperature", "critical pressure", "liquefied"],
}

ENGLISH_KEYWORDS = {
    "Grammar and Syntax": ["grammar", "syntax", "sentence", "tense", "clause", "structure", "suggested",
                          "advised", "requires", "wish", "subjunctive"],
    "Vocabulary": ["synonym", "antonym", "meaning", "definition", "word", "idiom", "phrase",
                  "industrious", "nerve", "apathy", "outbreak", "indulgent"],
    "Reading Comprehension": ["passage", "comprehension", "paragraph", "main idea", "context",
                             "public distribution", "food", "supply", "policy", "government"],
    "Intelligence": ["analogy", "RIB CAGE", "LUNGS", "Scientist", "laboratory", "Brittle", "fracture",
                    "Gymnasium", "exercise", "Compass", "navigation"],
    "General Knowledge": ["Dasu", "hydro power", "river", "Anjuman Tariqi-i-Urdu", "APNS", "earth hour",
                         "world water day", "book", "author", "Competition Commission", "P.M.", "Italy",
                         "Cholistan jeep rally"],
}


def parse_file() -> List[Dict]:
    """Parse the past paper file"""
    content = SOURCE_FILE.read_text(encoding="utf-8")
    
    # Process line by line, grouping into question blocks
    lines = content.split('\n')
    blocks = []
    current = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip header and markdown blocks
        if "NUST-Engineering-Pastpaper" in line and "solved" not in line.lower():
            continue
        if stripped.startswith('```'):
            continue
        
        # Check if this is a new question (starts with number.)
        is_new_question = bool(re.match(r'^\d+\.\s+', stripped))
        
        if is_new_question and current:
            # Save previous block if it has content
            if len(current) >= 3:  # At least question + some options + answer
                blocks.append(current)
            current = []
        
        if stripped:
            current.append(stripped)
    
    # Don't forget last block
    if current and len(current) >= 3:
        blocks.append(current)
    
    questions = []
    for block in blocks:
        if not block:
            continue
        
        # Find question number and text (first line should be question)
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
            # Check for option - handle (a) format
            opt_match = re.match(r'^\(([a-d])\)\s*(.+)$', line, re.IGNORECASE)
            if opt_match:
                key = opt_match.group(1).lower()
                value = opt_match.group(2).strip()
                options.append({"key": key, "value": value})
                continue
            
            # Check for answer - handle ans: c, ans:c, ans c formats
            ans_match = re.match(r'^ans[:\s]*([a-d])', line, re.IGNORECASE)
            if ans_match:
                answer_key = ans_match.group(1).lower()
        
        if not options or not answer_key:
            # Handle special cases where answer might be in note format
            if "*Note:" in str(block):
                # Skip questions with notes for now, or handle them specially
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
    if 1 <= number <= 81:
        return "Mathematics"
    elif 82 <= number <= 138:
        return "Physics"
    elif 139 <= number <= 170:
        return "Chemistry"
    elif 171 <= number <= 200:
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
    max_matches = 0
    
    for topic, keywords in topic_map.items():
        matches = sum(1 for keyword in keywords if keyword.lower() in text)
        if matches > max_matches:
            max_matches = matches
            main_topic = topic
    
    # If no matches found, use subject-specific default
    if max_matches == 0:
        if subject == "Mathematics":
            main_topic = "Number Systems"
        elif subject == "Physics":
            main_topic = "Mechanics"
        elif subject == "Chemistry":
            main_topic = "Stoichiometry"
        elif subject == "English":
            main_topic = "Grammar and Syntax"
    
    return subject, main_topic


def estimate_difficulty(text: str) -> str:
    """Estimate question difficulty"""
    text_lower = text.lower()
    
    easy_keywords = ["define", "what is", "identify", "which one", "is called", "are called"]
    hard_keywords = ["prove", "derive", "evaluate", "calculate", "find the value", "solve", "if", "then"]
    
    hard_count = sum(1 for kw in hard_keywords if kw in text_lower)
    easy_count = sum(1 for kw in easy_keywords if kw in text_lower)
    
    word_count = len(text.split())
    
    if hard_count > 1 or word_count > 30:
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
    
    # Count by subject
    subject_counts = {}
    topic_counts = {}
    
    for (subject, topic), q_list in grouped.items():
        subject_counts[subject] = subject_counts.get(subject, 0) + len(q_list)
        topic_counts[topic] = topic_counts.get(topic, 0) + len(q_list)
        
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
    
    # Print summary
    print(f"\n{'='*60}")
    print("Processing Summary")
    print(f"{'='*60}")
    print(f"\nTotal questions processed: {len(questions)}")
    print(f"\nBy Subject:")
    for subject, count in sorted(subject_counts.items()):
        print(f"  {subject}: {count} questions")
    print(f"\nBy Topic:")
    for topic, count in sorted(topic_counts.items()):
        print(f"  {topic}: {count} questions")
    print(f"\n{'='*60}")
    print("Files Generated:")
    print(f"{'='*60}")
    for path, count in sorted(summaries):
        print(f"  {path} ({count} questions)")
    
    return summaries


if __name__ == "__main__":
    summaries = build_dataset()
    print(f"\n{'='*60}")
    print("Processing Complete!")
    print(f"{'='*60}\n")

