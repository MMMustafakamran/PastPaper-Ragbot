# Quick Start Guide - MCQ Processing Pipeline

## Step-by-Step Instructions

### Step 1: Test the Pipeline

Run tests to ensure everything works:

```bash
python test_processor.py
```

**Expected Output:**
```
✓ Parsed 100 questions from data/...
✓ Generated 3 topic datasets
✓ All required fields present
✓ ALL TESTS PASSED!
```

If tests fail, check:
- Files exist in `data/Standard_text/`
- `Topics_net` file is present
- File format matches expected pattern

---

### Step 2: Process All Files

Once tests pass, process everything:

```bash
python mcq_processor.py
```

**What it does:**
1. Scans `data/Standard_text/` recursively
2. Parses all `.txt` files
3. Classifies questions by topic
4. Generates JSON files in `processed_data/`

**Progress Output:**
```
Processing: data/Standard_text/NET/100_netquestions/NET-Mathematics-100-MCQs(2)(1).doc.txt
  Found 100 questions
  Saved: processed_data/NET/Mathematics/functions_and_limits.json (35 questions)
  Saved: processed_data/NET/Mathematics/differentiation.json (28 questions)
  ...
```

---

### Step 3: Review Output

Check the generated files:

```bash
ls processed_data/NET/Mathematics/
```

**You should see:**
```
functions_and_limits.json
differentiation.json
integration.json
trigonometry.json
...
```

**Inspect a file:**
```bash
head -n 50 processed_data/NET/Mathematics/functions_and_limits.json
```

---

### Step 4: Quality Check

Review some questions manually:

```python
import json

# Load a dataset
with open('processed_data/NET/Mathematics/functions_and_limits.json', 'r') as f:
    data = json.load(f)

# Check dataset info
print(f"Total questions: {data['dataset_info']['total_questions']}")

# Check first question
q = data['questions'][0]
print(f"\nQuestion ID: {q['question_id']}")
print(f"Topic: {q['topic']['main_topic']} → {q['topic']['sub_topic']}")
print(f"Difficulty: {q['topic']['difficulty']}")
print(f"Text: {q['question']['text']}")
print(f"Answer: {q['answer']['correct_value']}")
```

---

### Step 5: Adjust Classification (Optional)

If topic classification is wrong:

**Edit `mcq_processor.py` → `TopicClassifier._build_keyword_map()`**

Add more keywords:
```python
math_keywords = {
    "Your Topic Here": ["keyword1", "keyword2", "phrase here"],
    # ... existing topics
}
```

Then re-run:
```bash
python mcq_processor.py
```

---

## Common Issues & Solutions

### Issue: "No questions found"

**Cause:** File format doesn't match expected pattern

**Solution:** Check your file format:
```
1. Question text here?
(a) Option A
(b) Option B
(c) Option C
(d) Option D
ans:a

2. Next question...
```

**Requirements:**
- Questions numbered with `1.`, `2.`, etc.
- Options in format `(a)`, `(b)`, `(c)`, `(d)`
- Answer in format `ans:a` (lowercase)
- Empty line between questions

---

### Issue: Wrong topic classification

**Cause:** Question keywords don't match topic keywords

**Solution 1:** Add more keywords to `TopicClassifier`

**Solution 2:** Create topic override file:
```python
# topic_overrides.json
{
    "NET_MATH_Q001": "Differentiation",
    "NET_MATH_Q045": "Integration"
}
```

Load in processor:
```python
with open('topic_overrides.json') as f:
    overrides = json.load(f)

# Apply after processing
for question in questions:
    if question['question_id'] in overrides:
        question['topic']['main_topic'] = overrides[question['question_id']]
```

---

### Issue: File too large

**Cause:** Many questions in one topic

**This is expected!** The JSON file is for preprocessing only.

**For runtime RAG:**
```python
# Load once and create embeddings
import json
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

with open('processed_data/NET/Mathematics/functions_and_limits.json') as f:
    data = json.load(f)

# Generate embeddings (one-time)
embeddings = []
for q in data['questions']:
    emb = model.encode(q['embedding_text'])
    embeddings.append(emb)
    
# Store in vector DB (fast retrieval)
# ... ChromaDB, Pinecone, Weaviate, etc.
```

---

## Next Steps: RAG Integration

After processing all files, move to RAG implementation:

### 1. Generate Embeddings

```python
from sentence_transformers import SentenceTransformer
import json
import glob

model = SentenceTransformer('all-MiniLM-L6-v2')

# Process all JSON files
for json_file in glob.glob('processed_data/**/*.json', recursive=True):
    with open(json_file) as f:
        data = json.load(f)
    
    for question in data['questions']:
        embedding = model.encode(question['embedding_text'])
        # Store in vector DB...
```

### 2. Create Vector Database

```python
import chromadb

client = chromadb.Client()
collection = client.create_collection(
    name="mcq_questions",
    metadata={"description": "Entrance exam MCQs"}
)

# Add questions
collection.add(
    embeddings=embeddings_list,
    documents=[q['embedding_text'] for q in questions],
    metadatas=[{
        'question_id': q['question_id'],
        'topic': q['topic']['main_topic'],
        'difficulty': q['topic']['difficulty']
    } for q in questions],
    ids=[q['question_id'] for q in questions]
)
```

### 3. Build RAG Query System

```python
def generate_quiz(topic: str, difficulty: str, num_questions: int = 10):
    """Generate custom quiz using RAG"""
    
    # Query vector DB
    results = collection.query(
        query_texts=[f"questions about {topic}"],
        n_results=num_questions * 2,  # Get extras for filtering
        where={
            "difficulty": difficulty
        }
    )
    
    # Extract questions
    question_ids = results['ids'][0][:num_questions]
    
    # Load full question data
    quiz_questions = []
    for qid in question_ids:
        # Lookup in original JSON or metadata
        quiz_questions.append(get_question_by_id(qid))
    
    return quiz_questions
```

---

## File Structure After Processing

```
your_project/
├── data/
│   └── Standard_text/          # Original text files
│       ├── NET/
│       └── FAST/
├── processed_data/              # Generated JSON files
│   ├── NET/
│   │   ├── Mathematics/
│   │   │   ├── functions_and_limits.json
│   │   │   ├── differentiation.json
│   │   │   └── ...
│   │   ├── Physics/
│   │   └── Chemistry/
│   └── FAST/
├── mcq_processor.py            # Main processor
├── test_processor.py           # Test suite
├── Topics_net                  # Topic taxonomy
└── README_PROCESSING.md        # Full documentation
```

---

## Tips for Best Results

1. **Review first file output** before processing all files
2. **Adjust keywords** based on your specific content
3. **Keep original files** as backup
4. **Version control** your processed data
5. **Validate** random samples after processing
6. **Document** any manual corrections

---

## Performance Expectations

- **Processing Speed**: ~1000 questions/second
- **Memory Usage**: ~100MB for 10,000 questions
- **Output Size**: ~40KB per question (detailed format)
- **Total Time**: ~5-10 minutes for 5,000 questions

---

## Getting Help

If you encounter issues:

1. Check `test_processor.py` output
2. Review `README_PROCESSING.md`
3. Inspect sample output JSON
4. Verify input file format
5. Check Python version (requires 3.7+)

---

## Ready to Start?

```bash
# Test first
python test_processor.py

# Then process all
python mcq_processor.py

# Check output
ls -R processed_data/
```

Good luck! 🚀

