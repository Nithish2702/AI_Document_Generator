"""
Pydantic Schemas for Request/Response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# Document Schemas
class DocumentResponse(BaseModel):
    id: UUID
    title: str
    document_type: str
    category: Optional[str]
    content_text: str
    author: Optional[str]
    department: Optional[str]
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
