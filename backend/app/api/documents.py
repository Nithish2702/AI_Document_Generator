"""
Document API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import shutil
from pathlib import Path
import logging

from app.database import get_db
from app.models import Document, GeneratedDocument
from app.schemas import (
    DocumentResponse,
    GenerateDocumentRequest,
    GeneratedDocumentResponse,
    GeneratedDocumentListResponse,
    ChatRequest,
    ChatResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    UpdateDocumentRequest
)
from app.services.document_processor import document_processor
from app.services.rag_service import rag_service
from app.services.export_service import export_service
from app.services.llm_service import llm_service
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    General chat endpoint for interactive conversations
    """
    logger.info(f"💬 Chat message received: {request.message[:50]}...")
    
    try:
        # Call LLM service for general chat
        response_text = llm_service.chat(
            message=request.message,
            conversation_history=request.conversation_history
        )
        
        logger.info(f"✅ Chat response generated ({len(response_text)} characters)")
        
        return ChatResponse(
            response=response_text,
            requires_document_generation=False
        )
        
    except Exception as e:
        logger.error(f"❌ Chat failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_request(request: AnalyzeRequest):
    """
    Analyze user message to determine if they want to create a document
    and what information is missing
    """
    logger.info(f"🔍 Analyzing request: {request.message[:50]}...")
    
    try:
        # Analyze the request using LLM
        analysis = llm_service.analyze_document_request(
            message=request.message,
            conversation_history=request.conversation_history
        )
        
        logger.info(f"✅ Analysis complete: wants_document={analysis['wants_document']}, has_sufficient_info={analysis['has_sufficient_info']}")
        
        return AnalyzeResponse(**analysis)
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Query(...),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Upload a source document for RAG
    """
    logger.info(f"📤 Uploading document: {file.filename} (type: {document_type})")
    
    # Save uploaded file
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    logger.info(f"💾 Saving file to: {file_path}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Extract text
        logger.info(f"📝 Extracting text from document...")
        text = document_processor.extract_text(str(file_path))
        logger.info(f"✅ Extracted {len(text)} characters")
        
        # Validate document
        logger.info(f"🔍 Validating document quality...")
        if not document_processor.validate_document(text):
            logger.warning(f"❌ Document validation failed")
            raise HTTPException(status_code=400, detail="Document does not meet quality criteria")
        logger.info(f"✅ Document validation passed")
        
        # Extract metadata
        logger.info(f"📊 Extracting metadata...")
        metadata = document_processor.extract_metadata(str(file_path), text)
        logger.info(f"✅ Metadata extracted: {metadata.get('word_count')} words")
        
        # Create document record
        logger.info(f"💾 Creating database record...")
        document = Document(
            title=file.filename,
            document_type=document_type,
            category=category,
            content_text=text,
            file_path=str(file_path),
            file_format=metadata['file_format'],
            word_count=metadata['word_count'],
            doc_metadata=metadata
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        logger.info(f"✅ Document saved with ID: {document.id}")
        
        # Index document in vector store
        logger.info(f"🔍 Indexing document in vector store...")
        rag_service.index_document(document)
        logger.info(f"✅ Document indexed successfully")
        
        logger.info(f"🎉 Upload complete: {file.filename}")
        return document
        
    except Exception as e:
        logger.error(f"❌ Upload failed: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[DocumentResponse])
def get_documents(
    document_type: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get list of source documents
    """
    logger.info(f"📚 Fetching documents (type: {document_type}, category: {category}, skip: {skip}, limit: {limit})")
    
    query = db.query(Document)
    
    if document_type:
        query = query.filter(Document.document_type == document_type)
    if category:
        query = query.filter(Document.category == category)
    
    documents = query.offset(skip).limit(limit).all()
    logger.info(f"✅ Found {len(documents)} documents")
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: UUID, db: Session = Depends(get_db)):
    """
    Get a specific document by ID
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/{document_id}")
def delete_document(document_id: UUID, db: Session = Depends(get_db)):
    """
    Delete a document
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}


@router.post("/generate", response_model=GeneratedDocumentResponse)
async def generate_document(
    request: GenerateDocumentRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a new document using RAG
    """
    logger.info("=" * 60)
    logger.info(f"🤖 Starting document generation")
    logger.info(f"📋 Title: {request.title}")
    logger.info(f"📄 Type: {request.document_type}")
    logger.info(f"🎨 Tone: {request.tone}")
    logger.info(f"📏 Length: {request.length}")
    logger.info(f"📦 Format: {request.format}")
    logger.info("=" * 60)
    
    try:
        # Generate document using RAG service
        logger.info(f"🔍 Step 1: Retrieving relevant context from knowledge base...")
        result = rag_service.generate_document(
            request_text=request.description + " " + request.context,
            document_type=request.document_type,
            title=request.title,
            tone=request.tone,
            length=request.length,
            db=db
        )
        logger.info(f"✅ Content generated ({len(result['content'])} characters)")
        logger.info(f"📚 Used {len(result.get('source_documents', []))} source documents")
        
        # Export to requested format
        logger.info(f"📦 Step 2: Exporting to {request.format.upper()} format...")
        file_path = export_service.export_document(
            content=result['content'],
            title=request.title,
            document_id="temp",
            format=request.format,
            document_type=request.document_type
        )
        logger.info(f"✅ File created: {file_path}")
        
        # Create generated document record
        logger.info(f"💾 Step 3: Saving to database...")
        generated_doc = GeneratedDocument(
            request_text=request.description,
            document_type=request.document_type,
            title=request.title,
            generated_content=result['content'],
            source_documents=result['source_documents'],
            output_format=request.format,
            file_path=file_path,
            status="completed",
            generation_time_ms=result['generation_time_ms'],
            tone=request.tone,
            length=request.length
        )
        
        db.add(generated_doc)
        db.commit()
        db.refresh(generated_doc)
        
        logger.info(f"✅ Document saved with ID: {generated_doc.id}")
        logger.info(f"⏱️  Total generation time: {result['generation_time_ms']}ms")
        logger.info("=" * 60)
        logger.info(f"🎉 Document generation complete!")
        logger.info("=" * 60)
        
        return generated_doc
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ Document generation failed: {str(e)}")
        logger.error("=" * 60)
        logger.error(f"Error details:", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generated/list", response_model=GeneratedDocumentListResponse)
def get_generated_documents(
    skip: int = 0,
    limit: int = 20,
    document_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of generated documents
    """
    logger.info(f"📋 Fetching generated documents (type: {document_type}, skip: {skip}, limit: {limit})")
    
    query = db.query(GeneratedDocument)
    
    if document_type:
        query = query.filter(GeneratedDocument.document_type == document_type)
    
    total = query.count()
    documents = query.order_by(GeneratedDocument.created_at.desc()).offset(skip).limit(limit).all()
    
    logger.info(f"✅ Found {len(documents)} documents (total: {total})")
    
    return {
        "documents": documents,
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit
    }


@router.get("/generated/{document_id}", response_model=GeneratedDocumentResponse)
def get_generated_document(document_id: UUID, db: Session = Depends(get_db)):
    """
    Get a specific generated document
    """
    document = db.query(GeneratedDocument).filter(GeneratedDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/generated/{document_id}/preview")
def get_document_preview(document_id: UUID, db: Session = Depends(get_db)):
    """
    Get document preview with structured content for rendering
    """
    
    document = db.query(GeneratedDocument).filter(GeneratedDocument.id == document_id).first()
    if not document:
        logger.warning(f"❌ Document not found: {document_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    logger.info(f"📄 Parsing preview for document: {document.title}")
    
    logger.info(f"📄 Parsing preview for document: {document.title}")
    
    # Parse the content into structured format
    content_blocks = []
    lines = document.generated_content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            content_blocks.append({"type": "spacer"})
            i += 1
            continue
        
        # Check for table
        if line.startswith('TABLE:') or (line.startswith('|') and '|' in line[1:]):
            table_lines = []
            table_title = None
            
            # Collect all table lines
            while i < len(lines):
                current_line = lines[i].strip()
                
                # Check if this is a table title
                if current_line.startswith('TABLE:'):
                    table_title = current_line.replace('TABLE:', '').strip()
                    i += 1
                    continue
                
                # Check if this is a table row
                if current_line.startswith('|') and current_line.endswith('|'):
                    table_lines.append(current_line)
                    i += 1
                else:
                    # End of table
                    break
            
            # Parse table rows
            table_rows = []
            for tline in table_lines:
                tline = tline.strip()
                if tline.startswith('|') and tline.endswith('|'):
                    # Remove leading and trailing pipes
                    cells = [cell.strip() for cell in tline[1:-1].split('|')]
                    
                    # Skip separator rows (rows with only dashes and spaces)
                    is_separator = all(
                        set(cell.replace('-', '').replace(':', '').strip()) == set() 
                        for cell in cells
                    )
                    
                    if not is_separator and cells:
                        # Clean up cell content - remove markdown formatting
                        cleaned_cells = []
                        for cell in cells:
                            # Remove bold, italic, etc.
                            cleaned = cell.replace('**', '').replace('*', '').replace('__', '').replace('_', '').strip()
                            cleaned_cells.append(cleaned)
                        table_rows.append(cleaned_cells)
            
            if table_rows:
                logger.info(f"📊 Parsed table with {len(table_rows)} rows, {len(table_rows[0]) if table_rows else 0} columns")
                logger.info(f"   First row: {table_rows[0] if table_rows else 'N/A'}")
                content_blocks.append({
                    "type": "table",
                    "title": table_title,
                    "rows": table_rows
                })
            else:
                logger.warning(f"⚠️ Table detected but no rows parsed from {len(table_lines)} lines")
            continue
        
        # Check for headings
        if line.startswith('# '):
            content_blocks.append({"type": "heading1", "text": line[2:].strip()})
        elif line.startswith('## '):
            content_blocks.append({"type": "heading2", "text": line[3:].strip()})
        elif line.startswith('### '):
            content_blocks.append({"type": "heading3", "text": line[4:].strip()})
        elif line.startswith('- ') or line.startswith('* '):
            content_blocks.append({"type": "bullet", "text": line[2:].strip()})
        elif line.startswith(tuple(f"{i}. " for i in range(1, 100))):
            # Numbered list
            import re
            text = re.sub(r'^\d+\.\s+', '', line)
            content_blocks.append({"type": "bullet", "text": text})
        else:
            # Regular paragraph
            content_blocks.append({"type": "paragraph", "text": line})
        
        i += 1
    
    logger.info(f"✅ Parsed {len(content_blocks)} content blocks")
    table_count = sum(1 for block in content_blocks if block.get('type') == 'table')
    logger.info(f"   Tables: {table_count}")
    
    return {
        "id": str(document.id),
        "title": document.title,
        "document_type": document.document_type,
        "created_at": document.created_at.isoformat(),
        "content_blocks": content_blocks
    }


@router.put("/generated/{document_id}")
async def update_document_content(
    document_id: UUID,
    request: UpdateDocumentRequest,
    db: Session = Depends(get_db)
):
    """
    Update the content of a generated document and regenerate files
    """
    logger.info(f"📝 Updating document content: {document_id}")
    logger.info(f"   New content length: {len(request.generated_content)} characters")
    
    document = db.query(GeneratedDocument).filter(GeneratedDocument.id == document_id).first()
    if not document:
        logger.warning(f"❌ Document not found: {document_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Log old content for comparison
        old_content_preview = document.generated_content[:200] if document.generated_content else "None"
        logger.info(f"   Old content preview: {old_content_preview}...")
        
        # Update the generated content
        document.generated_content = request.generated_content
        
        # Log new content for comparison
        new_content_preview = request.generated_content[:200]
        logger.info(f"   New content preview: {new_content_preview}...")
        
        # Regenerate the DOCX and PDF files with updated content
        logger.info(f"🔄 Regenerating DOCX file with updated content...")
        
        # Generate new DOCX file
        docx_path = export_service.export_document(
            content=request.generated_content,
            title=document.title or "Updated Document",
            document_id=str(document_id),
            format='docx'
        )
        
        logger.info(f"   New DOCX file created at: {docx_path}")
        
        # Update file path
        document.file_path = docx_path
        
        # Commit changes
        db.commit()
        db.refresh(document)
        
        logger.info(f"✅ Document updated successfully: {document_id}")
        logger.info(f"   Database content length: {len(document.generated_content)} characters")
        logger.info(f"   File path: {document.file_path}")
        
        return {
            "success": True,
            "message": "Document updated successfully",
            "document_id": str(document_id),
            "file_path": docx_path,
            "content_length": len(document.generated_content)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to update document: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")


@router.get("/generated/{document_id}/download")
async def download_document(
    document_id: UUID, 
    format: Optional[str] = Query(None, description="Download format: docx or pdf"),
    db: Session = Depends(get_db)
):
    """
    Download a generated document in specified format
    """
    
    document = db.query(GeneratedDocument).filter(GeneratedDocument.id == document_id).first()
    if not document:
        logger.warning(f"❌ Document not found: {document_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    # If no format specified or same as original, return original file
    if not format or format == document.output_format:
        if not document.file_path or not Path(document.file_path).exists():
            logger.error(f"❌ File not found: {document.file_path}")
            raise HTTPException(status_code=404, detail="File not found")
        
        logger.info(f"✅ Sending original file: {document.file_path}")
        
        return FileResponse(
            path=document.file_path,
            filename=Path(document.file_path).name,
            media_type='application/octet-stream'
        )
    
    # Generate file in requested format
    try:
        logger.info(f"🔄 Converting document to {format.upper()} format...")
        file_path = export_service.export_document(
            content=document.generated_content,
            title=document.title,
            document_id=str(document.id),
            format=format
        )
        logger.info(f"✅ Converted file created: {file_path}")
        
        return FileResponse(
            path=file_path,
            filename=Path(file_path).name,
            media_type='application/octet-stream'
        )
    except Exception as e:
        logger.error(f"❌ Format conversion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to convert to {format}: {str(e)}")


@router.delete("/generated/{document_id}")
def delete_generated_document(document_id: UUID, db: Session = Depends(get_db)):
    """
    Delete a generated document
    """
    document = db.query(GeneratedDocument).filter(GeneratedDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file if exists
    if document.file_path and Path(document.file_path).exists():
        Path(document.file_path).unlink()
    
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}
