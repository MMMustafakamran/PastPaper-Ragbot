"""
Utility script to convert `nust_phyiscs_chem_unsolved.txt` into RAG-optimized JSON.
Focused on Physics and Chemistry MCQs only.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

SOURCE_FILE = Path("data/Standard_text/NET/nust_phyiscs_chem_unsolved.txt")
OUTPUT_ROOT = Path("processed_data/NET/custom_physics_chem")

PHYSICS_KEYWORDS: Dict[str, List[str]] = {
    "Mechanics": [
        "force",
        "acceleration",
        "velocity",
        "momentum",
        "work",
        "energy",
        "power",
        "gravity",
        "torque",
        "vector",
        "angular",
        "inertia",
        "mass",
        "displacement",
        "pendulum",
        "oscillation",
        "wave",
        "fluid",
    ],
    "Waves and Oscillations": [
        "wave",
        "frequency",
        "wavelength",
        "amplitude",
        "doppler",
        "resonance",
        "oscill",
        "diffraction",
        "polarization",
        "huygens",
    ],
    "Electricity and Magnetism": [
        "electric",
        "charge",
        "current",
        "voltage",
        "resistance",
        "magnetic",
        "capacitor",
        "flux",
        "circuit",
        "inductor",
        "ampere",
        "electron",
        "potential",
        "coil",
        "resist",
        "voltmeter",
        "inductive",
    ],
    "Optics": [
        "refraction",
        "reflection",
        "lens",
        "optical",
        "light",
        "image",
        "wave front",
    ],
    "Thermodynamics": [
        "temperature",
        "thermodynamics",
        "pressure",
        "kelvin",
        "heat",
        "gas",
        "melting",
        "equilibrium",
    ],
    "Modern Physics": [
        "photon",
        "transistor",
        "laser",
        "population inversion",
        "atom",
        "ionized",
        "sodium",
        "diameter of an atom",
    ],
}

CHEM_KEYWORDS: Dict[str, List[str]] = {
    "Atomic Structure": [
        "atomic",
        "electron",
        "proton",
        "neutron",
        "isotope",
        "atomic mass",
    ],
    "Chemical Bonding": [
        "bond",
        "ionic",
        "covalent",
        "metallic",
        "molecular geometry",
    ],
    "Organic Chemistry": [
        "hydrocarbon",
        "organic",
    ],
    "Acids and Bases": [
        "ph",
        "acid",
        "base",
        "neutralization",
        "ammonium",
    ],
    "Chemical Reactions": [
        "equilibrium",
        "reaction",
        "mass action",
        "rate",
        "ksp",
    ],
    "Thermochemistry": [
        "enthalpy",
        "entropy",
        "endothermic",
        "exothermic",
        "thermo",
    ],
}


@dataclass
class MCQ:
    number: int
    text: str
    options: List[Dict[str, str]]
    answer_key: str
    answer_value: str


def parse_file() -> List[MCQ]:
    content = SOURCE_FILE.read_text(encoding="utf-8")
    blocks: List[List[str]] = []
    current: List[str] = []

    for line in content.splitlines():
        stripped = line.strip()
        if stripped:
            current.append(stripped)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)

    questions: List[MCQ] = []
    for block in blocks:
        head = block[0]
        match = re.match(r"^Q?(\d+)\.\s*(.+)$", head, re.IGNORECASE)
        if not match:
            continue
        number = int(match.group(1))
        question_text = match.group(2).strip()
        options: List[Dict[str, str]] = []
        answer_key = None

        for line in block[1:]:
            opt_match = re.match(r"^\(([a-d])\)\s*(.+)$", line, re.IGNORECASE)
            if opt_match:
                key = opt_match.group(1).lower()
                value = opt_match.group(2).strip()
                options.append({"key": key, "value": value})
                continue
            ans_match = re.match(r"^ans[:\s]+([a-d])", line, re.IGNORECASE)
            if ans_match:
                answer_key = ans_match.group(1).lower()

        if not options or not answer_key:
            continue

        answer_value = next(
            (opt["value"] for opt in options if opt["key"] == answer_key), ""
        )
        questions.append(
            MCQ(
                number=number,
                text=question_text,
                options=options,
                answer_key=answer_key,
                answer_value=answer_value,
            )
        )
    return questions


def classify(question: MCQ) -> Tuple[str, str]:
    text = question.text.lower()
    subject = "Physics" if question.number < 142 else "Chemistry"
    topic_map = PHYSICS_KEYWORDS if subject == "Physics" else CHEM_KEYWORDS
    main_topic = "General"
    for topic, keywords in topic_map.items():
        if any(keyword in text for keyword in keywords):
            main_topic = topic
            break
    return subject, main_topic


def build_dataset():
    questions = parse_file()
    print(f"Parsed {len(questions)} questions from {SOURCE_FILE}")
    grouped: Dict[Tuple[str, str], List[Dict]] = {}

    for idx, mcq in enumerate(questions, start=1):
        subject, topic = classify(mcq)
        question_id = f"NET_{subject[:3].upper()}_{topic.replace(' ', '_').upper()}_Q{idx:03d}"
        embedding_text = (
            f"{subject} - {topic}: {mcq.text} Options: "
            f"{', '.join(opt['value'] for opt in mcq.options)}. "
            f"Correct answer: {mcq.answer_value}"
        )
        entry = {
            "question_id": question_id,
            "source": {
                "exam_type": "NET",
                "subject": subject,
                "paper_name": SOURCE_FILE.stem,
                "year": "2024",
            },
            "topic": {
                "main_topic": topic,
                "sub_topic": topic,
                "difficulty": "medium",
            },
            "question": {
                "text": mcq.text,
                "type": "mcq",
                "format": "single_choice",
            },
            "options": mcq.options,
            "answer": {
                "correct_key": mcq.answer_key,
                "correct_value": mcq.answer_value,
                "explanation": "",
            },
            "embedding_text": embedding_text,
            "metadata": {
                "keywords": [],
                "related_concepts": [topic.lower()],
                "prerequisites": [topic.lower()],
                "difficulty_level": "medium",
                "cognitive_skill": "application",
                "bloom_level": "L3_Apply",
            },
        }
        grouped.setdefault((subject, topic), []).append(entry)

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
                "main_topic": topic,
            },
            "questions": q_list,
        }
        output_path = (
            OUTPUT_ROOT / subject / f"{topic.replace(' ', '_').lower()}.json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(dataset, indent=2), encoding="utf-8")
        summaries.append((output_path, len(q_list)))
    return summaries


if __name__ == "__main__":
    info = build_dataset()
    for path, count in info:
        print(f"Saved {path} ({count} questions)")

