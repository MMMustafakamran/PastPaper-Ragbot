# MCQ Processing Pipeline for RAG

Automated pipeline to convert raw MCQ text files into RAG-optimized JSON format.

## Features

✅ **Automatic parsing** of MCQ text files  
✅ **Topic classification** using keyword matching  
✅ **Difficulty estimation** (easy/medium/hard)  
✅ **Sub-topic inference** from question content  
✅ **Embedding text generation** optimized for RAG  
✅ **Rich metadata** (keywords, concepts, Bloom's taxonomy)  
✅ **Batch processing** for multiple files  

## Output Structure

```
processed_data/
├── NET/
│   ├── Mathematics/
│   │   ├── functions_and_limits.json
│   │   ├── differentiation.json
│   │   ├── integration.json
│   │   └── ...
│   ├── Physics/
│   └── Chemistry/
├── FAST/
│   └── Mathematics/
│       └── ...
```

## JSON Format

Each JSON file contains:

```json
{
  "dataset_info": {
    "dataset_name": "NET Mathematics - Functions and Limits",
    "version": "1.0",
    "total_questions": 71,
    "exam_type": "NET",
    "subject": "Mathematics",
    "main_topic": "Functions and Limits"
  },
  "questions": [
    {
      "question_id": "NET_MATH_FUNC_Q001",
      "topic": {
        "main_topic": "Functions and Limits",
        "sub_topic": "Types of Functions",
        "difficulty": "easy"
      },
      "question": {...},
      "options": [...],
      "answer": {...},
      "embedding_text": "Optimized text for semantic search",
      "metadata": {...}
    }
  ]
}
```

## Usage

### Quick Start

```bash
python mcq_processor.py
```

This will:
1. Read all `.txt` files from `data/Standard_text/`
2. Parse and classify questions
3. Generate JSON files in `processed_data/`

### Process Specific Directory

```python
from processors.mcq_processor import BatchProcessor

processor = BatchProcessor(
    topics_file="Topics_net",
    output_dir="processed_data"
)

processor.process_directory("data/Standard_text/NET")
```

### Process Single File

```python
from processors.mcq_processor import BatchProcessor

processor = BatchProcessor(
    topics_file="Topics_net", 
    output_dir="processed_data"
)

processor.process_file("data/Standard_text/NET/100_netquestions/NET-Mathematics-100-MCQs(2)(1).doc.txt")
```

## Components

### 1. MCQParser
Parses raw text files into structured format:
- Extracts question number and text
- Identifies options (a, b, c, d)
- Finds correct answer

### 2. TopicClassifier
Classifies questions into topics:
- Uses keyword matching
- References `Topics_net` file
- Infers sub-topics
- Estimates difficulty

### 3. JSONGenerator
Creates RAG-optimized JSON:
- Generates unique question IDs
- Creates embedding text
- Extracts keywords
- Determines Bloom's taxonomy level

### 4. BatchProcessor
Processes multiple files:
- Scans directories recursively
- Handles errors gracefully
- Organizes output by exam/subject/topic

## Configuration

Edit these variables in `processors/mcq_processor.py`:

```python
TOPICS_FILE = "Topics_net"          # Topic taxonomy file
INPUT_DIR = "data/Standard_text"    # Input directory
OUTPUT_DIR = "processed_data"        # Output directory
```

## Next Steps: RAG Integration

After processing, use the JSON files for:

1. **Embedding Generation**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

for question in data["questions"]:
    embedding = model.encode(question["embedding_text"])
```

2. **Vector Database Ingestion**
```python
import chromadb

client = chromadb.Client()
collection = client.create_collection("mcq_questions")

collection.add(
    embeddings=[embedding],
    metadatas=[question["metadata"]],
    documents=[question["embedding_text"]],
    ids=[question["question_id"]]
)
```

3. **RAG Query**
```python
results = collection.query(
    query_texts=["questions about derivatives"],
    n_results=5
)
```

## Customization

### Add Custom Topic Keywords

Edit `TopicClassifier._build_keyword_map()`:

```python
math_keywords = {
    "Your Topic": ["keyword1", "keyword2", ...],
}
```

### Adjust Difficulty Estimation

Edit `TopicClassifier.estimate_difficulty()`:

```python
hard_keywords = ["prove", "derive", ...]
easy_keywords = ["define", "what is", ...]
```

### Modify JSON Structure

Edit `JSONGenerator._process_question()` to add/remove fields.

## Troubleshooting

**No questions found:**
- Check file format matches expected pattern
- Ensure questions are numbered (1., 2., etc.)
- Verify options use (a), (b), (c), (d) format
- Check answers use `ans:a` format

**Wrong topic classification:**
- Add more keywords to `TopicClassifier`
- Review `Topics_net` file structure
- Manually override in post-processing

**Large file size:**
- This is normal for detailed format
- JSON files are for preprocessing only
- Runtime RAG uses vector database

## Performance

- **Processing speed**: ~1000 questions/second
- **Memory usage**: Minimal (streaming)
- **Output size**: ~40KB per question with full metadata
- **Compression**: Use `gzip` for storage if needed

## Quality Checks

After processing, review:
- [ ] All questions have correct answers
- [ ] Topics are accurately classified
- [ ] Difficulty levels are reasonable
- [ ] Embedding text is complete
- [ ] No duplicate question IDs

## Support

For issues or enhancements, check:
1. File format in `data/Standard_text/`
2. Topics defined in `Topics_net`
3. Parser regex patterns in `MCQParser`

