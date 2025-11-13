# RAG Dataset Preparation Plan for MCQ Teaching Chatbot

## 🎯 Objective
Build a high-quality RAG (Retrieval-Augmented Generation) dataset from past paper MCQs to enable:
1. **Teaching**: Answer student questions using relevant past paper MCQs
2. **Quiz Generation**: Create custom quizzes based on topics, difficulty, and exam type
3. **Learning Support**: Provide explanations, solutions, and practice questions

---

## 📊 Current Data Analysis

### Data Structure
- **Location**: `data/Standard_text/`
- **Formats**: 
  - NET: `NET-Mathematics-100-MCQs(2)(1).doc.txt` (100 questions)
  - NET (Topic-organized): `497992392-NUST-NET-Solved-MCQs/topic_*.txt`
  - FAST: `fast_paper_*.txt` (multiple papers)
- **Format Pattern**:
  ```
  [Number]. [Question Text]
  (a) [Option A]
  (b) [Option B]
  (c) [Option C]
  (d) [Option D]
  ans:[letter]
  ```

### Topics Available
- **Mathematics** (40%): 12 topics (Functions, Differentiation, Integration, etc.)
- **Physics** (30%): 6 topics (Mechanics, Waves, Electricity, etc.)
- **Chemistry** (15%): 6 topics (Atomic Structure, Bonding, Organic, etc.)
- **English** (10%): Grammar, Vocabulary, Comprehension
- **Intelligence** (5%): Logical reasoning, Patterns

---

## 🏗️ Dataset Preparation Pipeline

### **Phase 1: Data Extraction & Standardization** ✅ (Partially Done)

#### 1.1 Parse All MCQs
- **Action**: Extract all questions from `Standard_text/` folder
- **Output Format**: Structured JSON per question
- **Fields Required**:
  ```json
  {
    "id": "unique_id",
    "question_number": 1,
    "question_text": "Full question text",
    "options": [
      {"label": "a", "text": "Option A text"},
      {"label": "b", "text": "Option B text"},
      {"label": "c", "text": "Option C text"},
      {"label": "d", "text": "Option D text"}
    ],
    "correct_answer": "a",
    "solution": null,  // Will be generated/enhanced later
    "subject": "Mathematics",
    "topic": "Functions and Limits",
    "subtopic": null,  // More granular classification
    "difficulty": "medium",  // easy/medium/hard
    "exam_type": "NET",  // NET/FAST
    "year": null,  // Extract if available
    "source_file": "NET-Mathematics-100-MCQs(2)(1).doc.txt",
    "raw_text": "Original text block"
  }
  ```

#### 1.2 Handle Topic Classification
- **For files already organized by topic**: Extract topic from filename/folder
- **For unorganized files**: Use LLM or keyword matching to classify
- **Topic Mapping**: Map to standardized topics from `Topics_net`

#### 1.3 Data Validation
- Check for missing answers
- Validate option format (should have 4 options)
- Flag malformed questions for manual review

**Output**: `data/rag_dataset/raw_questions.jsonl` (one JSON object per line)

---

### **Phase 2: Metadata Enhancement** 🔄

#### 2.1 Topic Classification (LLM-Powered)
- **Use LLM** to classify questions into topics from `Topics_net`
- **Input**: Question text + options
- **Output**: Primary topic + subtopic (if applicable)
- **Fallback**: Keyword-based classification

#### 2.2 Difficulty Assessment
- **Methods**:
  1. **Heuristic**: Based on mathematical complexity (formulas, steps required)
  2. **LLM-based**: Ask LLM to assess difficulty (easy/medium/hard)
  3. **Statistical**: Based on answer patterns (if available)

#### 2.3 Subject Classification
- Auto-detect subject from question content
- Categories: Mathematics, Physics, Chemistry, English, Intelligence

#### 2.4 Solution Generation (Optional but Recommended)
- **For questions without solutions**: Generate step-by-step solutions using LLM
- **Format**: 
  ```json
  "solution": {
    "steps": [
      {"step": 1, "description": "Identify the problem type"},
      {"step": 2, "description": "Apply relevant formula"},
      {"step": 3, "description": "Calculate result"}
    ],
    "explanation": "Full explanation text",
    "key_concepts": ["concept1", "concept2"]
  }
  ```

**Output**: `data/rag_dataset/enhanced_questions.jsonl`

---

### **Phase 3: Text Chunking & Embedding Preparation** 🎯

#### 3.1 Create Embedding Text
For RAG retrieval, create multiple text representations:

**Option A: Question-Only Chunk**
```json
{
  "embedding_text": "Question: [question text]\nOptions:\nA) [option A]\nB) [option B]\nC) [option C]\nD) [option D]",
  "chunk_type": "question_only"
}
```

**Option B: Question + Topic Context**
```json
{
  "embedding_text": "Topic: [topic name]\nQuestion: [question text]\nOptions:\nA) [option A]\nB) [option B]\nC) [option C]\nD) [option D]",
  "chunk_type": "question_with_topic"
}
```

**Option C: Question + Solution**
```json
{
  "embedding_text": "Question: [question text]\nOptions:\nA) [option A]\nB) [option B]\nC) [option C]\nD) [option D]\nSolution: [solution text]",
  "chunk_type": "question_with_solution"
}
```

**Recommendation**: Create **all three types** for flexible retrieval:
- Use `question_only` for quiz generation
- Use `question_with_topic` for topic-based teaching
- Use `question_with_solution` for explanation retrieval

#### 3.2 Chunk Metadata
Each chunk needs:
```json
{
  "chunk_id": "unique_chunk_id",
  "question_id": "parent_question_id",
  "chunk_type": "question_only|question_with_topic|question_with_solution",
  "subject": "Mathematics",
  "topic": "Functions and Limits",
  "difficulty": "medium",
  "exam_type": "NET",
  "embedding_text": "...",
  "metadata": {
    "correct_answer": "a",
    "has_solution": true,
    "year": null
  }
}
```

**Output**: `data/rag_dataset/chunks.jsonl`

---

### **Phase 4: Vector Embedding Generation** 🔢

#### 4.1 Choose Embedding Model
**Recommendations**:
- **OpenAI**: `text-embedding-3-small` or `text-embedding-3-large` (best quality, paid)
- **Open Source**: `sentence-transformers/all-MiniLM-L6-v2` (fast, free)
- **Domain-Specific**: `sentence-transformers/ms-marco-MiniLM-L-12-v2` (good for Q&A)

#### 4.2 Generate Embeddings
- Process all chunks from Phase 3
- Store embeddings in vector database format
- **Vector DB Options**:
  - **ChromaDB** (recommended for development)
  - **Pinecone** (cloud, scalable)
  - **Weaviate** (self-hosted)
  - **FAISS** (Facebook, in-memory)

#### 4.3 Embedding Storage Format
```json
{
  "chunk_id": "chunk_123",
  "embedding": [0.123, -0.456, ...],  // 384 or 1536 dimensions
  "metadata": { /* chunk metadata */ }
}
```

**Output**: 
- `data/rag_dataset/embeddings.jsonl` (backup)
- Vector database (primary storage)

---

### **Phase 5: Index Creation & Organization** 📚

#### 5.1 Create Multiple Indexes
For efficient retrieval, create separate indexes:

1. **Topic Index**: Group by topic → subtopic
2. **Subject Index**: Group by subject
3. **Difficulty Index**: Group by difficulty level
4. **Exam Type Index**: Group by NET/FAST
5. **Composite Index**: Multi-dimensional filtering

#### 5.2 Index Structure
```
data/rag_dataset/
├── indexes/
│   ├── by_topic/
│   │   ├── functions_and_limits.json
│   │   ├── differentiation.json
│   │   └── ...
│   ├── by_subject/
│   │   ├── mathematics.json
│   │   ├── physics.json
│   │   └── ...
│   └── by_difficulty/
│       ├── easy.json
│       ├── medium.json
│       └── hard.json
```

---

### **Phase 6: Quality Assurance & Validation** ✅

#### 6.1 Data Quality Checks
- [ ] All questions have 4 options
- [ ] All questions have correct answers
- [ ] All questions have topic classification
- [ ] No duplicate questions (fuzzy matching)
- [ ] Embedding dimensions are consistent

#### 6.2 Sample Validation
- Manually review 10-20 questions per topic
- Verify topic classification accuracy
- Test retrieval on sample queries

#### 6.3 Statistics Report
Generate report:
- Total questions count
- Questions per subject
- Questions per topic
- Questions per difficulty
- Questions per exam type
- Average embedding similarity (check for duplicates)

---

## 🚀 Implementation Steps

### Step 1: Create Data Processing Script
**File**: `scripts/prepare_rag_dataset.py`

**Functions**:
1. `extract_all_questions()` - Parse all files in Standard_text
2. `classify_topics()` - LLM-based topic classification
3. `assess_difficulty()` - Difficulty assessment
4. `generate_solutions()` - Generate solutions for questions without them
5. `create_chunks()` - Create embedding chunks
6. `generate_embeddings()` - Generate vector embeddings
7. `build_indexes()` - Create retrieval indexes

### Step 2: Create Configuration File
**File**: `config/rag_config.yaml`
```yaml
embedding:
  model: "text-embedding-3-small"
  provider: "openai"  # or "sentence-transformers"
  dimension: 1536

vector_db:
  type: "chromadb"  # or "pinecone", "weaviate", "faiss"
  path: "data/rag_dataset/vector_db"

chunking:
  create_question_only: true
  create_with_topic: true
  create_with_solution: true

topics:
  source_file: "Topics_net"
  subjects:
    - Mathematics
    - Physics
    - Chemistry
    - English
    - Intelligence
```

### Step 3: Create RAG Query Interface
**File**: `src/rag/retriever.py`

**Functions**:
1. `search_by_topic(topic, limit=10)` - Get questions by topic
2. `search_by_query(query, limit=10)` - Semantic search
3. `generate_quiz(topic, difficulty, count=10)` - Generate custom quiz
4. `get_explanation(question_id)` - Get solution/explanation

---

## 📁 Final Dataset Structure

```
data/rag_dataset/
├── raw_questions.jsonl          # Phase 1: Parsed questions
├── enhanced_questions.jsonl      # Phase 2: With metadata
├── chunks.jsonl                  # Phase 3: Embedding chunks
├── embeddings.jsonl              # Phase 4: Vector embeddings (backup)
├── vector_db/                    # Phase 4: Vector database
│   └── chroma_db/
├── indexes/                      # Phase 5: Retrieval indexes
│   ├── by_topic/
│   ├── by_subject/
│   └── by_difficulty/
├── statistics.json               # Phase 6: Dataset statistics
└── metadata.json                 # Dataset metadata (version, date, etc.)
```

---

## 🎓 RAG Use Cases

### Use Case 1: Student Question Answering
**Query**: "How do I solve limits problems?"
**Retrieval**: 
- Search for questions with topic "Functions and Limits"
- Retrieve questions with solutions
- Return relevant examples with explanations

### Use Case 2: Custom Quiz Generation
**Query**: "Generate a 10-question quiz on Differentiation, medium difficulty"
**Retrieval**:
- Filter by topic: "Differentiation"
- Filter by difficulty: "medium"
- Randomly sample 10 questions
- Return quiz format

### Use Case 3: Topic-Based Learning
**Query**: "Teach me about Integration"
**Retrieval**:
- Get all questions on "Integration"
- Group by subtopics (definite, indefinite, techniques)
- Return structured learning material

---

## 🔧 Tools & Libraries Needed

### Core Libraries
- `sentence-transformers` - For embeddings (if using open-source)
- `chromadb` or `pinecone` - Vector database
- `openai` - For LLM-based classification and embeddings (if using OpenAI)
- `langchain` - Optional, for RAG pipeline utilities
- `numpy` - For vector operations
- `json` - For data handling

### LLM Services (for classification)
- OpenAI GPT-4/GPT-3.5 (for topic classification, solution generation)
- Or local LLM (Llama, Mistral) via Ollama

---

## ⏱️ Estimated Timeline

1. **Phase 1**: 2-3 days (parsing, standardization)
2. **Phase 2**: 3-4 days (metadata enhancement, LLM calls)
3. **Phase 3**: 1-2 days (chunking)
4. **Phase 4**: 1-2 days (embedding generation)
5. **Phase 5**: 1 day (index creation)
6. **Phase 6**: 1-2 days (QA, validation)

**Total**: ~10-14 days for complete pipeline

---

## 🎯 Success Metrics

1. **Coverage**: All questions from Standard_text processed
2. **Topic Accuracy**: >90% correct topic classification
3. **Retrieval Quality**: Top-5 retrieved questions are relevant to query
4. **Quiz Generation**: Can generate quizzes for any topic/difficulty combination
5. **Response Time**: <500ms for retrieval queries

---

## 📝 Next Steps

1. **Review this plan** and adjust based on your priorities
2. **Set up environment** (install libraries, API keys)
3. **Start with Phase 1** - Create extraction script
4. **Iterate** - Test each phase before moving to next
5. **Deploy** - Integrate with your chatbot application

---

## 💡 Recommendations

1. **Start Small**: Process 100 questions first, validate, then scale
2. **Use LLM Wisely**: Batch LLM calls to reduce costs
3. **Cache Embeddings**: Don't regenerate if data hasn't changed
4. **Version Control**: Track dataset versions
5. **Monitor Quality**: Regularly check retrieval accuracy

---

**Ready to start?** Let me know which phase you'd like to begin with, and I can help implement it!

