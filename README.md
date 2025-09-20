# Past Papers RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot system for querying engineering past papers, specifically designed for NUST and other educational institutions.

## 🎯 Project Overview

This project creates an intelligent chatbot that can:
- Extract and process past paper content from PDF files
- Store questions, answers, and solutions in a vector database
- Provide accurate answers to user queries about past papers
- Support multiple question formats (MCQs, descriptive, numerical)

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PDF Parser    │───▶│  Text Processor  │───▶│ Vector Database │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐             │
│   Chatbot UI    │◀───│   RAG Engine     │◀────────────┘
└─────────────────┘    └──────────────────┘
```

## 🚀 Features

- **PDF Processing**: Extract text, questions, and answers from past papers
- **Vector Search**: Semantic search through past paper content
- **Multiple Formats**: Support for MCQs, descriptive questions, and numerical problems
- **Web Interface**: User-friendly Streamlit-based chat interface
- **API Support**: RESTful API for integration with other systems

## 📋 Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment support

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd past-papers-parsing
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   
   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

## 📁 Project Structure

```
past-papers-parsing/
├── src/
│   ├── pdf_parser/          # PDF extraction modules
│   ├── text_processor/      # Text cleaning and processing
│   ├── vector_db/          # Vector database operations
│   ├── rag_engine/         # RAG implementation
│   └── chatbot/            # Chatbot interface
├── data/
│   ├── raw_pdfs/           # Original PDF files
│   ├── processed/          # Extracted text files
│   └── vector_db/          # ChromaDB storage
├── tests/                  # Unit and integration tests
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## 🔧 Configuration

1. **Environment Variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your configuration:
   ```
   OPENAI_API_KEY=your_openai_api_key
   CHROMA_PERSIST_DIRECTORY=./data/vector_db
   MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
   ```

## 🚀 Usage

### 1. Process Past Papers
```bash
python src/pdf_parser/main.py --input data/raw_pdfs/ --output data/processed/
```

### 2. Build Vector Database
```bash
python src/vector_db/build_db.py --input data/processed/ --db_path data/vector_db/
```

### 3. Start Chatbot Interface
```bash
streamlit run src/chatbot/app.py
```

### 4. API Server
```bash
uvicorn src.api.main:app --reload
```

## 📊 Data Extraction Strategy

### PDF Analysis
- **Question Types**: Multiple Choice, Descriptive, Numerical
- **Content Structure**: Questions, options, answers, solutions
- **Metadata**: Subject, year, semester, difficulty level

### Text Processing Pipeline
1. **PDF Text Extraction**: Using PyPDF2 and pdfplumber
2. **Content Segmentation**: Identify questions, options, answers
3. **Text Cleaning**: Remove formatting artifacts, normalize text
4. **Metadata Extraction**: Extract paper information, question numbers
5. **Chunking**: Split content into searchable segments

### Vector Database Schema
```python
{
    "id": "unique_identifier",
    "content": "question_text_or_answer",
    "metadata": {
        "paper_id": "paper_identifier",
        "question_number": "Q1, Q2, etc.",
        "question_type": "MCQ/Descriptive/Numerical",
        "subject": "Engineering_Subject",
        "year": "2023",
        "semester": "Fall/Spring",
        "difficulty": "Easy/Medium/Hard"
    },
    "embedding": "vector_representation"
}
```

## 🔍 Query Processing

### RAG Pipeline
1. **Query Understanding**: Parse user question
2. **Vector Search**: Find relevant past paper content
3. **Context Retrieval**: Get top-k similar questions/answers
4. **Answer Generation**: Use LLM to generate contextual response
5. **Source Attribution**: Provide references to original papers

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

## 📈 Performance Metrics

- **Retrieval Accuracy**: Precision@K for relevant content
- **Response Quality**: BLEU, ROUGE scores for generated answers
- **Response Time**: Average query processing time
- **User Satisfaction**: Feedback-based metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact: [your-email@domain.com]

## 🔮 Future Enhancements

- [ ] Support for more PDF formats
- [ ] Multi-language support
- [ ] Advanced question classification
- [ ] Integration with learning management systems
- [ ] Mobile app interface
- [ ] Offline mode support

## 📚 References

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [RAG Paper](https://arxiv.org/abs/2005.11401)
