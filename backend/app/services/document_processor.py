"""
Document Processing Service
Handles text extraction from various document formats
"""
import fitz  # PyMuPDF
from docx import Document as DocxDocument
from pathlib import Path
from typing import Dict, Optional
import re


class DocumentProcessor:
    """Service for processing and extracting text from documents"""
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """
        Extract text from PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """
        Extract text from DOCX file
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text content
        """
        try:
            doc = DocxDocument(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from DOCX: {str(e)}")
    
    @staticmethod
    def extract_text_from_txt(file_path: str) -> str:
        """
        Extract text from TXT file
        
        Args:
            file_path: Path to TXT file
            
        Returns:
            Extracted text content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            raise Exception(f"Error reading text file: {str(e)}")
    
    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extract text from document based on file extension
        
        Args:
            file_path: Path to document file
            
        Returns:
            Extracted text content
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension == '.pdf':
            return DocumentProcessor.extract_text_from_pdf(file_path)
        elif extension in ['.docx', '.doc']:
            return DocumentProcessor.extract_text_from_docx(file_path)
        elif extension in ['.txt', '.md']:
            return DocumentProcessor.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    
    @staticmethod
    def extract_metadata(file_path: str, text: str) -> Dict:
        """
        Extract metadata from document
        
        Args:
            file_path: Path to document
            text: Extracted text content
            
        Returns:
            Dictionary of metadata
        """
        path = Path(file_path)
        
        metadata = {
            'file_name': path.name,
            'file_format': path.suffix.lower().replace('.', ''),
            'file_size_kb': path.stat().st_size / 1024,
            'word_count': len(text.split()),
            'char_count': len(text)
        }
        
        return metadata
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Sanitize text by removing PII and sensitive information
        
        Args:
            text: Input text
            
        Returns:
            Sanitized text
        """
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Remove phone numbers (US format)
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        
        # Remove SSN
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
        
        return text
    
    @staticmethod
    def validate_document(text: str) -> bool:
        """
        Validate if document meets quality criteria
        
        Args:
            text: Document text
            
        Returns:
            True if valid, False otherwise
        """
        word_count = len(text.split())
        
        # Minimum word count
        if word_count < 100:
            return False
        
        # Check if text is not just whitespace
        if not text.strip():
            return False
        
        return True


# Global instance
document_processor = DocumentProcessor()
