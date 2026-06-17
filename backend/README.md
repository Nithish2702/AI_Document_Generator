# AI Document Generator - Backend

FastAPI backend for the AI-powered document generation system with RAG.

## Features

- **Document Upload & Processing**: Upload PDF, DOCX, TXT documents
- **RAG Pipeline**: Retrieval-Augmented Generation for context-aware document creation
- **Vector Search**: FAISS-based semantic similarity search
- **LLM Integration**: OpenAI GPT for document generation
- **Export**: Generate PDF and DOCX outputs
- **RESTful API**: Complete API for frontend integration

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy
- **AI/ML**: sentence-transformers, OpenAI, FAISS
- **Document Processing**: PyMuPDF, python-docx, reportlab

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:
- Database connection string
- OpenAI API key
- File storage paths

### 3. Initialize Database

```bash
# Create database tables
python -c "from app.database import init_db; init_db()"
```

### 4. Run Server

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python -m app.main
```

## API Endpoints

### Documents

- `POST /api/documents/upload` - Upload source document
- `GET /api/documents/` - List source documents
- `GET /api/documents/{id}` - Get document by ID
- `DELETE /api/documents/{id}` - Delete document

### Document Generation

- `POST /api/documents/generate` - Generate new document
- `GET /api/documents/generated/list` - List generated documents
- `GET /api/documents/generated/{id}` - Get generated document
- `GET /api/documents/generated/{id}/download` - Download document
- `DELETE /api/documents/generated/{id}` - Delete generated document

### Health

- `GET /` - Root endpoint
- `GET /health` - Health check

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── api/
│   │   ├── __init__.py
│   │   └── documents.py     # Document routes
│   └── services/
│       ├── __init__.py
│       ├── embedding_service.py    # Embedding generation
│       ├── vector_store.py         # FAISS vector store
│       ├── document_processor.py   # Document text extraction
│       ├── rag_service.py          # RAG pipeline
│       ├── llm_service.py          # LLM integration
│       └── export_service.py       # PDF/DOCX export
├── storage/
│   ├── uploads/            # Uploaded documents
│   ├── generated/          # Generated documents
│   └── vector_store/       # FAISS index files
├── requirements.txt
├── .env.example
└── README.md
```

## Usage Examples

### Upload a Document

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@proposal.pdf" \
  -F "document_type=proposal" \
  -F "category=marketing"
```

### Generate a Document

```bash
curl -X POST "http://localhost:8000/api/documents/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "proposal",
    "title": "Q1 Marketing Campaign",
    "description": "Create a marketing proposal for new product launch",
    "context": "Target audience: millennials, Budget: $50k",
    "tone": "formal",
    "length": "medium",
    "format": "pdf"
  }'
```

### List Generated Documents

```bash
curl "http://localhost:8000/api/documents/generated/list?skip=0&limit=20"
```

## Development

### Run Tests

```bash
pytest
```

### API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `SECRET_KEY` | Application secret key | - |
| `UPLOAD_DIR` | Directory for uploaded files | `./storage/uploads` |
| `GENERATED_DIR` | Directory for generated files | `./storage/generated` |
| `VECTOR_STORE_DIR` | Directory for FAISS index | `./storage/vector_store` |
| `EMBEDDING_MODEL` | Sentence transformer model | `sentence-transformers/all-MiniLM-L6-v2` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |

## Troubleshooting

### Database Connection Issues

Ensure PostgreSQL is running and the connection string is correct:

```bash
psql -U user -d document_generator
```

### OpenAI API Errors

Verify your API key is valid and has sufficient credits.

### Vector Store Issues

If the vector store fails to load, delete the index files and reindex:

```bash
rm -rf storage/vector_store/*
# Then reindex documents through the API
```

## License

MIT
