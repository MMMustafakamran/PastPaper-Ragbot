"""
Process PAST NET SEIRES 200 MCQS(1) solved.txt
Subject divisions:
- Questions 1-80: Mathematics
- Questions 81-140: Physics
- Questions 141-170: Chemistry
- Questions 171-190: English
- Questions 191-200: IQ / General Knowledge
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

SOURCE_FILE = Path("data/Standard_text/NET/PAST NET SEIRES 200 MCQS(1) solved.txt")
OUTPUT_ROOT = Path("processed_data/NET/PAST NET SEIRES 200 MCQS(1) solved")

# Topic keywords from Topics_net
MATH_KEYWORDS = {
    "Functions and Limits": ["function", "limit", "domain", "range", "continuous", "discontinuous", 
                             "identity", "explicit", "implicit", "parametric", "inverse function",
                             "hyperbolic", "cosh", "sinh", "tanh", "sin⁻¹", "cos⁻¹", "tan⁻¹", "cos^{-1}",
                             "inverse cosecant", "domain of"],
    "Differentiation": ["derivative", "differentiation", "tangent", "normal", "maxima", "minima",
                        "chain rule", "product rule", "quotient rule", "dy/dx", "f'(x)", "f''(x)",
                        "dy/dx at", "differential equation", "d/dx", "rate change", "implicit differentiation",
                        "second order derivative", "discontinuity", "removable", "Differentiate", "with respect to"],
    "Integration": ["integral", "integration", "definite", "indefinite", "area under curve",
                   "substitution", "by parts", "partial fractions", "∫", "∫₀", "∫_{-"],
    "Trigonometry": ["sin", "cos", "tan", "cot", "sec", "cosec", "trigonometric", "radian", "degree",
                    "triangle", "angle", "sine", "cosine", "sin⁻¹", "cos⁻¹", "tan⁻¹", "cot⁻¹",
                    "cosec⁻¹", "sec⁻¹", "angle of elevation", "period", "sin(-a)", "cos 3α",
                    "sin13cos77", "cos13sin77", "tan(2x)", "cos inverse", "sin inverse"],
    "Complex Numbers": ["complex number", "complex", "imaginary", "iota", "real component", "imaginary component", "|z|", "arg",
                       "conjugate", "modulus", "i^{", "i^", "z + z̄", "z̄", "Im(", "Re(",
                       "real part", "z = z̅", "z = z̄", "cube root of unity", "w²³", "w²⁸", "is real if"],
    "Matrices and Determinants": ["matrix", "determinant", "singular", "non-singular", "transpose", "row matrix",
                                 "adj", "A⁻¹", "inverse", "A=Aᵗ", "symmetric", "skew symmetric"],
    "Vectors": ["vector", "dot product", "cross product", "magnitude", "direction", "i·", "k×", "j×",
               "collinear", "coplanar", "projection", "|u|", "|v|", "|w|", "unit vector", "UxV",
               "parallelepiped", "parallel vectors"],
    "Sequences and Series": ["sequence", "series", "arithmetic", "geometric", "progression", "fibonacci", "harmonic",
                            "AP", "GP", "sum", "expansion", "binomial", "term independent", "common ratio",
                            "common difference", "sum to infinity", "first term", "nth term", "30th term",
                            "1, 1/3, 1/5, 1/7", "harmonic sequence"],
    "Probability and Statistics": ["probability", "permutation", "permutations", "combination", "combinations",
                                 "mean", "median", "mode", "standard deviation", "variance", "histogram", "dice", 
                                 "rolled", "dice is rolled", "diamond card", "deck cards", "nP4", "nC3", "nP3",
                                 "probability of picking", "rotten apples", "boxes containing", "how many",
                                 "4 digit numbers", "can be formed", "without repetition"],
    "Analytical Geometry": ["coordinate", "distance", "slope", "equation of line", "circle", "centroid", "locus",
                           "point", "line", "intersection", "plane", "sphere", "x²+y²", "3x-4y",
                           "rectangle", "quadrant", "vertices", "anti-parallel"],
    "Conic Sections": ["parabola", "ellipse", "hyperbola", "conic", "focus", "directrix", "eccentricity",
                     "latus rectum", "transverse axis", "quadratic function", "conjugate hyperbola",
                     "e>1", "cut is parallel", "latus rectum", "two foci", "two directrices"],
    "Linear Inequalities": ["inequality", "inequalities", "|x+", "|x-", "linear programming", "max value", "min value",
                           "3-x = x-3"],
    "Sets and Logic": ["set", "subset", "element", "union", "intersection", "proposition", "conjunction",
                      "disjunction", "deduction", "induction", "truth", "logical", "binary operation",
                      "groupoid", "A={a,b,c}", "number of possible subsets"],
    "Number Systems": ["rational", "irrational", "integer", "natural", "whole", "real", "complex",
                     "additive", "multiplicative", "identity", "inverse", "closure", "commutative", "associative",
                     "additive inverse", "repeating decimal", "0.4545", "roots of the equation", "real irrational"],
}

PHYSICS_KEYWORDS = {
    "Mechanics": ["force", "acceleration", "velocity", "momentum", "work", "energy", "power", "gravity",
                  "torque", "vector", "angular", "motion", "mass", "displacement", "kinetic", "potential",
                  "pendulum", "oscillation", "projectile", "friction", "terminal velocity", "escape velocity",
                  "rotational", "moment of inertia", "angular momentum", "couple", "resultant", "equilibrium",
                  "center of gravity", "free fall", "apparent weight", "lift", "bomb", "bomber", "magnetic needle",
                  "magnetic moment", "vibrating magnetometer", "time period", "magnetic induction", "y component",
                  "x component", "kE", "momentum p", "elevator", "apparent value of g", "friction", "self-adjusting",
                  "time period", "length l", "doubling time period"],
    "Waves and Oscillations": ["wave", "frequency", "wavelength", "amplitude", "sound", "doppler", "resonance",
                               "oscillator", "simple harmonic", "diffraction", "interference", "polarization",
                               "ultrasonic", "echo", "stationary wave", "progressive wave", "phase angle", "loops",
                               "air column", "tuning fork", "beats", "fundamental frequency", "Fresnel",
                               "projection on diameter", "w=0.50m/s", "diameter of circle"],
    "Electricity and Magnetism": ["electric", "charge", "field", "current", "voltage", "resistance", "capacitor",
                                  "magnetic", "flux", "circuit", "ohm", "inductor", "ampere", "electron",
                                  "coulomb", "potential gradient", "electric intensity", "resistivity", "weber",
                                  "solenoid", "henry", "reactance", "RLC", "resonant", "parallel plate",
                                  "dielectric", "battery", "wheatstone bridge", "mutual inductance", "emf",
                                  "magnetic field", "magnetic moment", "earth's field", "horizontal component",
                                  "resistances", "R₁", "R₂", "R₃", "series", "equivalent resistance",
                                  "Coulomb's force", "distance between two charges", "capacitance", "C/V", "Q/V",
                                  "fully charged", "current will flow", "electric field", "vector area", "electric flux",
                                  "suspended objects", "attract", "Q²/C", "0.37q charge", "electric intensity", "V/m",
                                  "DC source", "force of repulsion", "charged plates", "deflect", "touches", "force between",
                                  "dielectric", "capacitors", "connected in series", "parallel", "Cs/Cp",
                                  "Ohm's law", "directly proportional", "potential difference", "500watt", "40watt",
                                  "100watt bulb", "heat", "coil", "MAGNET", "Emf", "induced", "area of coil",
                                  "rotated", "moved closer", "current", "increased", "energy stored", "inductor",
                                  "pure capacitive circuit", "leading", "lagging", "in phase"],
    "Optics": ["lens", "refraction", "reflection", "optical", "light", "ray", "image", "phase change",
               "wavelength", "speed of light", "medium", "telescope", "diopter", "magnifying", "microscope",
               "objective", "eye piece", "focal length", "distinct vision", "Sky appears blue",
               "light interference", "light diffraction", "light scattering", "light polarization",
               "grating element", "spectrometer", "number of rulings"],
    "Thermodynamics": ["temperature", "heat", "thermodynamics", "pressure", "kelvin", "gas", "expansion",
                      "melting", "equilibrium", "entropy", "adiabatic", "isothermal", "isobaric", "isochoric",
                      "density", "volume", "perpetual motion", "heat engine", "efficiency", "sink", "source",
                      "black body", "power radiated", "coefficient of expansion", "linear expansion",
                      "volume expansion", "mercury", "glass flask", "Isothermal Process", "Adiabatic Process",
                      "Isobaric Process", "Isochoric Process", "Newton", "speed of light"],
    "Modern Physics": ["photon", "electron", "atom", "transistor", "laser", "photoelectric", "atomic structure",
                      "nuclear", "radioactive", "half-life", "isotope", "relativity", "compton", "x-ray",
                      "threshold frequency", "work function", "uncertainty", "metastable", "population inversion",
                      "excited state", "ground state", "transition", "de Broglie", "wavelength", "K.E",
                      "photoelectrons", "emitted", "Ra 226", "fission", "U²³⁵", "U²³⁸", "neutron", "thermal neutron",
                      "Compton Wave shift", "X-rays", "scattered", "Compton wavelength", "temperature in Kelvin",
                      "energy of radiations", "Time stops", "Space", "Space shuttle", "Satellite",
                      "electron", "box", "size of an atom", "velocity of the electron", "Child Paradox",
                      "Length Contraction", "Time Dilation", "Mass Variation", "Compton Effect"],
    "Properties of Matter": ["crystalline", "solid", "liquid", "gas", "steradian", "significant", "dimensions",
                            "Young's modulus", "Poisson's ratio", "cross sectional area", "tension", "copper wire",
                            "capillary", "surface tension", "angle of contact", "terminal velocity", "drop"],
    "Electronics": ["depletion region", "biasing", "doping", "semiconductor", "LED", "light emitting diode",
                   "AND gate", "NOT gate", "NAND gate", "NOR gate", "XOR gate", "transistor", "Ic/Ie",
                   "Ic/Ib", "gain", "base current", "collector current"],
    "Gravitation": ["gravitational", "gravitational field", "gravitational P.E", "satellite", "circular orbit",
                   "altitude", "escape velocity", "earth", "angular momentum", "rotation", "period"],
    "Quantum Physics": ["quantum physics", "black body radiation", "Plank", "Maxwell", "Einstein",
                       "noble prize", "absolute uncertainty", "length", "precision", "mass spectrometer",
                       "atomic masses", "atomic number", "1 amu", "ionization", "vapor form"],
}

CHEM_KEYWORDS = {
    "Atomic Structure": ["atomic", "atom", "isotope", "electrons", "protons", "neutrons", "orbital",
                        "electronic", "quantum", "ionization potential", "bromine", "Br_{35}",
                        "electron jumps", "higher orbit", "fifth orbit", "Lymann", "Balmer", "Pfund", "Brackett",
                        "Chemical properties", "number of electrons", "Physical and chemical properties",
                        "atomic mass", "atomic number", "velocity of electron", "outer most shell",
                        "boiling point", "He", "Ne", "Kr", "Ar", "bond forces", "molecules", "Water",
                        "Nitrogen", "Neon", "Hydrogen Fluoride", "incomplete d orbital", "Ag", "Cu", "Au", "Ti",
                        "ionization energy", "depend upon", "nuclear charge", "shielding effect", "atomic radius"],
    "Chemical Bonding": ["bond", "ionic", "covalent", "metallic", "hybridization", "molecular", "geometry",
                         "polarizable", "bond order", "N₂⁺", "carbon in benzene", "Sp³", "Sp²", "Sp hybridize"],
    "Organic Chemistry": ["hydrocarbon", "functional", "organic", "alkane", "alkene", "alkyne", "aromatic",
                         "ethylene", "methanol", "ethanol", "CH_{4}", "C_{2}H_{5}OH", "C_{3}H_{5}O_{2}",
                         "C_{6}H_{10}O_{4}", "molecular formula", "empirical formula", "polymer", "nylon",
                         "polystyrene", "terylene", "epoxy resin", "addition polymer", "protein", "amino acids",
                         "primary structure", "secondary structure", "tertiary structure", "glucose",
                         "aromatic compound", "functional group", "OH", "Carbolic acid", "Phenol", "Alcohol",
                         "Methane", "Ethane", "Propane", "GASES", "Grignard's Reagant", "hydrolysis",
                         "Lower hydrocarbon", "Higher hydrocarbon", "Alkyl halide", "oleic acid", "double bond",
                         "carbon number", "combustion analysis", "CO₂", "absorbed", "Mg(OH)₂", "KOH",
                         "Mg(ClO₄)₂", "organic compounds", "most reactive", "Alkane", "Alkene", "Alkyne"],
    "Acids and Bases": ["ph", "acid", "base", "neutralization", "ammonium", "litmus", "poh", "buffer",
                       "Bronsted base", "NaOH", "H₂SO₄", "KOH", "freezing point", "HBr", "ionized",
                       "Kw", "Ka", "Kb", "Kw=Ka×Kb"],
    "Chemical Reactions": ["equilibrium", "reaction", "mass action", "rate", "ksp", "spontaneous",
                          "reversible", "irreversible", "forward reaction", "reverse reaction",
                          "Le Chatelier", "equilibrium constant", "concentration", "oxidation", "reduction",
                          "oxidation number", "NH₃", "H₂ + Br₂", "catalyst", "rate of reaction", "temperature",
                          "K₂Cr₂O₇", "blue crystalline solid", "soluble in water", "strong oxidizing agent",
                          "lead chromate", "boric acid", "ortho boric acid", "meta boric acid", "pyro boric acid"],
    "Thermochemistry": ["enthalpy", "entropy", "endothermic", "exothermic", "thermochemistry",
                       "heat of reaction", "lattice energy", "born haber", "Born Haber process",
                       "Hess law", "free energy"],
    "Stoichiometry": ["mole", "molar", "Avogadro", "N_{A}", "g-atom", "STP", "calcium carbonate",
                     "CaCO_{3}", "limestone", "CO₂", "O_{2}", "H_{2}", "percentage", "empirical",
                     "molecular formula", "vapors density", "weight", "mass", "concentration", "M",
                     "molarity", "Na₂CO₃", "normality", "0.2N", "liter", "oxygen", "S.T.P"],
    "States of Matter": ["ideal gas", "kinetic", "critical temperature", "critical pressure", "liquefied"],
    "Nuclear Chemistry": ["C¹⁴", "C¹²", "half-life", "N¹⁴", "β emission", "neutrons", "parent nucleus",
                         "radioactive", "U²³⁵", "U²³⁸", "fission", "transmutation", "decay", "alpha", "beta", "gamma"],
    "Physical Chemistry": ["colloid", "As₂S₃", "coagulating", "Al³⁺", "ice", "water", "density",
                           "hydrogen bonding", "dipole", "covalent crystal", "silicon", "sulphur",
                           "phosphorous", "iodine", "methylisocyanate", "Bhopal", "gas tragedy",
                           "colligative properties", "Solute", "Solvent", "electrical conductivity",
                           "alkali metals", "alkaline earth metals", "halogens", "coinage metals",
                           "half cells", "salt bridge", "galvanic cell", "electrons flow", "anode", "cathode",
                           "external circuit", "Phosphorus", "isotope", "Red Phosphorus", "Black Phosphorus",
                           "White Phosphorus", "Grey Phosphorus", "reacts readily with water", "Al", "Na", "Ka", "Cu",
                           "Sulphur", "HI", "strong oxidizing agent", "weak oxidizing agent", "strong reducing agent",
                           "weak reducing agent", "halogen", "bleaching", "Chlorine", "Bromine", "Iodine", "Fluorine",
                           "least no.of carbon atoms", "amino acid", "K₂Cr₂O₇", "blue crystalline solid", "soluble in water",
                           "strong oxidizing agent", "lead chromate", "boric acid", "ortho boric acid", "meta boric acid",
                           "pyro boric acid", "nano boric acid"],
}

ENGLISH_KEYWORDS = {
    "Grammar and Syntax": ["grammar", "syntax", "sentence", "tense", "clause", "structure", "suggested",
                          "advised", "requires", "wish", "subjunctive", "article", "a", "an", "the",
                          "new", "equal", "honesty", "virtue", "Send the letter", "address"],
    "Vocabulary": ["synonym", "antonym", "meaning", "definition", "word", "idiom", "phrase",
                  "AUDACIOUS", "ELLICIT", "FLEECE", "pauper", "passé", "actuate", "Trepidation",
                  "Amass", "INSCRUTABLE", "berated", "privately", "magnanimously", "inconspicously",
                  "ignominously", "Brunt", "Pressure", "trouble some", "lively spirited", "Impulsive",
                  "Dashing", "Key", "draw out", "evolve", "Excess", "Leveled", "Steal", "bought",
                  "Wealthy", "Rich", "Poor", "In", "Chic", "Function", "archaic", "Triple", "Motivate",
                  "Discourage", "move", "Doubts", "Quark", "Worries", "apprehension", "Allot", "Gather",
                  "Dispense", "Deiver", "Immoral", "Unethical", "Enigmatic", "Unaccountable"],
    "Reading Comprehension": ["passage", "comprehension", "paragraph", "main idea", "context",
                             "author", "thrust", "purpose", "assumes", "characteristic", "educational",
                             "system", "traditional", "formal", "non-formal", "learn", "pragmatic"],
    "Intelligence": ["analogy", "TELLER", "BANK", "INNING", "BASEBALL", "DEGREE", "TEMPERATURE",
                    "EINSTEIN", "PHYSICS", "JACKET", "LEATHER", "artist", "MUSEUM", "cashier", "check",
                    "waiter", "restaurant", "mourner", "funeral", "puck", "hockey", "serve", "tennis",
                    "outing", "hiking", "round", "boxing", "ounce", "weight", "fathom", "volume", "mass",
                    "energy", "time", "length", "harvey", "biology", "bohr", "periodic table", "moseley",
                    "chemistry", "aristotle", "greek", "shoes", "laces", "shirt", "cotton", "pant", "zip",
                    "geometry", "pen"],
    "General Knowledge": ["president", "European union", "Greece", "Austria", "Germany", "Latvia",
                         "Chief Minister", "Punjab", "spelling", "presamble", "misible", "presible",
                         "permissible", "Prejudice", "Jeduce", "dejuice", "diceju", "Mathimatics",
                         "Mathemaitics", "Mithamatics", "Mathematics", "deciper", "dehcipher", "desipher",
                         "decipher", "Pick the odd one", "March", "July", "September", "October",
                         "Trunk", "Tree", "Leaf", "Flower", "Learn", "Read", "Knowledge", "Write",
                         "next term in the series", "4,8,16,32,64", "6,9,18,21,63,66", "1514131616121718",
                         "Natural gas", "Gasoline", "Coal", "Biogas", "Brinjal", "Potato", "Tomato", "Cucumber",
                         "SHELNXR", "TEDIOUS", "GLAMOUR", "FODPNUQ", "FOBPNXS", "FOBPNXQ", "FODPNUS",
                         "RTTHHX", "purify", "blanch", "DKDSHG", "AOCGTY", "DKCMEG", "EMGCKD"],
}

IQ_KEYWORDS = {
    "Pattern Recognition": ["next term", "series", "4,8,16,32,64", "6,9,18,21,63,66", "1514131616121718",
                            "next number"],
    "Odd One Out": ["Pick the odd one", "Pick the odd one out", "Natural gas", "Gasoline", "Coal", "Biogas",
                    "Brinjal", "Potato", "Tomato", "Cucumber", "March", "July", "September", "October",
                    "Trunk", "Tree", "Leaf", "Flower", "Learn", "Read", "Knowledge", "Write"],
    "Coding": ["SHELNXR", "TEDIOUS", "GLAMOUR", "FODPNUQ", "FOBPNXS", "FOBPNXQ", "FODPNUS",
              "RTTHHX", "purify", "blanch", "DKDSHG", "AOCGTY", "DKCMEG", "EMGCKD", "encode", "code"],
    "General Knowledge": ["Natural gas", "Gasoline", "Coal", "Biogas", "Brinjal", "Potato", "Tomato", "Cucumber"],
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
        
        # Skip header
        if "PAST NET SEIRES" in line and "solved" not in line.lower():
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
            
            # Check for answer - handle Ans: c, Ans:c, Ans c formats, and multiple answers like "Ans: a, c"
            ans_match = re.match(r'^Ans[:\s]*([a-d](?:\s*,\s*[a-d])*)', line, re.IGNORECASE)
            if ans_match:
                # Take first answer if multiple
                answer_key = ans_match.group(1).split(',')[0].strip().lower()
        
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
    elif 81 <= number <= 140:
        return "Physics"
    elif 141 <= number <= 170:
        return "Chemistry"
    elif 171 <= number <= 190:
        return "English"
    elif 191 <= number <= 200:
        return "IQ / General Knowledge"
    return "General"


def classify_topic(question: Dict) -> Tuple[str, str]:
    """Classify question into subject and topic"""
    number = question["number"]
    text = question["text"].lower()
    
    subject = determine_subject(number)
    
    # Special handling: Check if Physics range question is actually Math
    # Check Math keywords first for questions in Physics range (81-140)
    if 81 <= number <= 140:
        math_matches = {}
        for topic, keywords in MATH_KEYWORDS.items():
            matches = sum(1 for keyword in keywords if keyword.lower() in text)
            if matches > 0:
                math_matches[topic] = matches
        
        # If strong Math match found, use Math topic but keep Physics subject
        if math_matches:
            max_math_topic = max(math_matches.items(), key=lambda x: x[1])
            if max_math_topic[1] >= 2:  # Strong match
                return subject, max_math_topic[0]
    
    # Special handling: Check if English range question is actually Chemistry
    # Check Chemistry keywords first for questions in English range (171-190)
    if 171 <= number <= 190:
        chem_matches = {}
        for topic, keywords in CHEM_KEYWORDS.items():
            matches = sum(1 for keyword in keywords if keyword.lower() in text)
            if matches > 0:
                chem_matches[topic] = matches
        
        # If strong Chemistry match found, use Chemistry topic but keep English subject
        if chem_matches:
            max_chem_topic = max(chem_matches.items(), key=lambda x: x[1])
            if max_chem_topic[1] >= 2:  # Strong match
                return subject, max_chem_topic[0]
    
    # Select appropriate keyword map with priority order (more specific first)
    if subject == "Mathematics":
        topic_map = {
            "Complex Numbers": MATH_KEYWORDS["Complex Numbers"],
            "Sequences and Series": MATH_KEYWORDS["Sequences and Series"],
            "Probability and Statistics": MATH_KEYWORDS["Probability and Statistics"],
            "Differentiation": MATH_KEYWORDS["Differentiation"],
            "Conic Sections": MATH_KEYWORDS["Conic Sections"],
            "Analytical Geometry": MATH_KEYWORDS["Analytical Geometry"],
            "Trigonometry": MATH_KEYWORDS["Trigonometry"],
            "Vectors": MATH_KEYWORDS["Vectors"],
            "Matrices and Determinants": MATH_KEYWORDS["Matrices and Determinants"],
            "Integration": MATH_KEYWORDS["Integration"],
            "Linear Inequalities": MATH_KEYWORDS["Linear Inequalities"],
            "Sets and Logic": MATH_KEYWORDS["Sets and Logic"],
            "Functions and Limits": MATH_KEYWORDS["Functions and Limits"],
            "Number Systems": MATH_KEYWORDS["Number Systems"],  # Last as default
        }
    elif subject == "Physics":
        topic_map = {
            "Conic Sections": MATH_KEYWORDS["Conic Sections"],  # Check Math topics first
            "Trigonometry": MATH_KEYWORDS["Trigonometry"],
            "Differentiation": MATH_KEYWORDS["Differentiation"],
            "Linear Inequalities": MATH_KEYWORDS["Linear Inequalities"],
            "Waves and Oscillations": PHYSICS_KEYWORDS["Waves and Oscillations"],
            "Modern Physics": PHYSICS_KEYWORDS["Modern Physics"],
            "Electricity and Magnetism": PHYSICS_KEYWORDS["Electricity and Magnetism"],
            "Optics": PHYSICS_KEYWORDS["Optics"],
            "Thermodynamics": PHYSICS_KEYWORDS["Thermodynamics"],
            "Properties of Matter": PHYSICS_KEYWORDS["Properties of Matter"],
            "Electronics": PHYSICS_KEYWORDS["Electronics"],
            "Gravitation": PHYSICS_KEYWORDS["Gravitation"],
            "Quantum Physics": PHYSICS_KEYWORDS["Quantum Physics"],
            "Mechanics": PHYSICS_KEYWORDS["Mechanics"],  # Last as default
        }
    elif subject == "Chemistry":
        topic_map = {
            "Atomic Structure": CHEM_KEYWORDS["Atomic Structure"],
            "Organic Chemistry": CHEM_KEYWORDS["Organic Chemistry"],
            "Physical Chemistry": CHEM_KEYWORDS["Physical Chemistry"],
            "Chemical Reactions": CHEM_KEYWORDS["Chemical Reactions"],
            "Chemical Bonding": CHEM_KEYWORDS["Chemical Bonding"],
            "Acids and Bases": CHEM_KEYWORDS["Acids and Bases"],
            "Thermochemistry": CHEM_KEYWORDS["Thermochemistry"],
            "Nuclear Chemistry": CHEM_KEYWORDS["Nuclear Chemistry"],
            "States of Matter": CHEM_KEYWORDS["States of Matter"],
            "Stoichiometry": CHEM_KEYWORDS["Stoichiometry"],  # Last as default
        }
    elif subject == "English":
        topic_map = {
            "Physical Chemistry": CHEM_KEYWORDS["Physical Chemistry"],  # Check Chemistry topics first
            "Organic Chemistry": CHEM_KEYWORDS["Organic Chemistry"],
            "Atomic Structure": CHEM_KEYWORDS["Atomic Structure"],
            "Vocabulary": ENGLISH_KEYWORDS["Vocabulary"],
            "Intelligence": ENGLISH_KEYWORDS["Intelligence"],
            "Reading Comprehension": ENGLISH_KEYWORDS["Reading Comprehension"],
            "Grammar and Syntax": ENGLISH_KEYWORDS["Grammar and Syntax"],  # Last as default
        }
    elif subject == "IQ / General Knowledge":
        topic_map = IQ_KEYWORDS
    else:
        return subject, "General"
    
    # Find matching topic (check in priority order)
    main_topic = None
    max_matches = 0
    
    for topic, keywords in topic_map.items():
        matches = sum(1 for keyword in keywords if keyword.lower() in text)
        if matches > max_matches:
            max_matches = matches
            main_topic = topic
    
    # If no matches found, use subject-specific default
    if max_matches == 0 or main_topic is None:
        if subject == "Mathematics":
            main_topic = "Number Systems"
        elif subject == "Physics":
            main_topic = "Mechanics"
        elif subject == "Chemistry":
            main_topic = "Stoichiometry"
        elif subject == "English":
            main_topic = "Grammar and Syntax"
        elif subject == "IQ / General Knowledge":
            main_topic = "Pattern Recognition"
        else:
            main_topic = "General"
    
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
        
        # Clean subject name for file paths
        subject_clean = subject.replace(" / ", "_").replace(" ", "_")
        question_id = f"NET_{subject_clean[:3].upper()}_{topic.replace(' ', '_').upper()}_Q{q['number']:03d}"
        
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
        
        # Clean subject name for file paths
        subject_clean = subject.replace(" / ", "_").replace(" ", "_")
        output_path = OUTPUT_ROOT / subject_clean / f"{topic.replace(' ', '_').lower()}.json"
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

