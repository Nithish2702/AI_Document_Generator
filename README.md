# AI Document Generator with RAG

AI-powered document generation system using Retrieval-Augmented Generation (RAG) to create high-quality business documents.

## Features

- 🤖 AI-powered document generation using GPT
- 🔍 Semantic search with RAG
- 📄 DOCX document support
- 📊 PDF export
- ☁️ Supabase cloud storage
- 🗄️ PostgreSQL database

## Tech Stack

**Backend**: FastAPI, Python
**Frontend**: React, TypeScript
**AI/ML**: OpenAI GPT, sentence-transformers, FAISS
**Database**: PostgreSQL (Render)
**Storage**: Supabase Storage

## Quick Setup

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Configure `.env`:
```env
DATABASE_URL=your_render_postgresql_url
OPENAI_API_KEY=your_openai_key
SECRET_KEY=your_secret_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

Initialize database:
```bash
python -c "from app.database import init_db; init_db()"
```

Start server:
```bash
uvicorn app.main:app --reload
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Usage

1. Upload DOCX documents to build knowledge base
2. Generate new documents using the web interface
3. Download generated PDFs or DOCX files

## API Endpoints

- `POST /api/documents/upload` - Upload document
- `POST /api/documents/generate` - Generate document
- `GET /api/documents/generated/list` - List generated documents
- `GET /api/documents/generated/{id}/download` - Download document

## License

MIT
