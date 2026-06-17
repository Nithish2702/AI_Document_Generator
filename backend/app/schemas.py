"""
Pydantic Schemas for Request/Response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# Document Schemas
class DocumentBase(BaseModel):
    title: str
    document_type: str
    category: Optional[str] = None
    content_text: str
    author: Optional[str] = None
    department: Optional[str] = None


class DocumentCreate(DocumentBase):
    file_path: Optional[str] = None
    file_format: Optional[str] = None
    tags: Optional[List[str]] = []


class DocumentResponse(DocumentBase):
    id: UUID
    file_path: Optional[str]
    file_format: Optional[str]
    created_date: Optional[datetime]
    uploaded_date: datetime
    word_count: Optional[int]
    page_count: Optional[int]
    success_rating: Optional[float]
    usage_count: int
    
    class Config:
        from_attributes = True


# Generated Document Schemas
class GenerateDocumentRequest(BaseModel):
    document_type: str = Field(..., description="Type of document to generate")
    title: str = Field(..., description="Document title")
    description: str = Field(..., description="Brief description of what the document should contain")
    context: str = Field(..., description="Additional context or requirements")
    tone: str = Field(default="formal", description="Tone: formal, casual, technical")
    length: str = Field(default="medium", description="Length: short, medium, long")
    format: str = Field(default="pdf", description="Output format: pdf or docx")


class GeneratedDocumentResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    request_text: str
    document_type: str
    title: Optional[str]
    generated_content: Optional[str] = None  # Add this for preview
    status: str
    file_path: Optional[str]
    output_format: str
    created_at: datetime
    generation_time_ms: Optional[int]
    
    class Config:
        from_attributes = True


class GeneratedDocumentListResponse(BaseModel):
    documents: List[GeneratedDocumentResponse]
    total: int
    page: int
    page_size: int


# Feedback Schemas
class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    feedback_text: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    document_id: UUID
    user_id: Optional[UUID]
    rating: int
    feedback_text: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Search and Filter Schemas
class DocumentSearchRequest(BaseModel):
    query: Optional[str] = None
    document_type: Optional[str] = None
    category: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# Health Check
class HealthCheckResponse(BaseModel):
    status: str
    version: str
    database: str
    vector_store: str


# Chat Schemas
class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message")
    conversation_history: Optional[List[dict]] = Field(default=None, description="Previous conversation messages")


class ChatResponse(BaseModel):
    response: str = Field(..., description="AI's response")
    requires_document_generation: bool = Field(default=False, description="Whether the conversation should trigger document generation")


# Analysis Schemas
class AnalyzeRequest(BaseModel):
    message: str = Field(..., description="User's message to analyze")
    conversation_history: Optional[List[dict]] = Field(default=None, description="Previous conversation messages")


class ExtractedInfo(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    document_type: Optional[str] = None
    context: Optional[str] = None


class AnalyzeResponse(BaseModel):
    wants_document: bool = Field(..., description="Whether user wants to create a document")
    has_sufficient_info: bool = Field(..., description="Whether we have enough info to generate")
    missing_info: Optional[str] = Field(None, description="Question to ask user for missing info")
    extracted_info: ExtractedInfo = Field(..., description="Information extracted from conversation")


# Update Document Schema
class UpdateDocumentRequest(BaseModel):
    generated_content: str = Field(..., description="Updated document content")
