"""
RAG (Retrieval-Augmented Generation) Service
Core service that combines retrieval and generation
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service
from app.models import Document, GeneratedDocument
import time


class RAGService:
    """Service for RAG pipeline"""
    
    def __init__(self):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.llm_service = llm_service
    
    def retrieve_similar_documents(
        self, 
        query: str, 
        k: int = 5,
        db: Session = None
    ) -> List[Document]:
        """
        Retrieve similar documents using semantic search
        
        Args:
            query: User query text
            k: Number of documents to retrieve
            db: Database session
            
        Returns:
            List of similar documents
        """
        # Generate query embedding
        query_embedding = self.embedding_service.generate_embedding(query)
        
        # Search in vector store
        distances, document_ids = self.vector_store.search(query_embedding, k=k)
        
        # Fetch documents from database
        if db:
            documents = db.query(Document).filter(
                Document.id.in_(document_ids)
            ).all()
            
            # Sort by retrieval order
            doc_dict = {str(doc.id): doc for doc in documents}
            sorted_docs = [doc_dict[doc_id] for doc_id in document_ids if doc_id in doc_dict]
            
            return sorted_docs
        
        return []
    
    def build_context(self, documents: List[Document], max_tokens: int = 3000) -> str:
        """
        Build context string from retrieved documents
        
        Args:
            documents: List of retrieved documents
            max_tokens: Maximum tokens for context (approximate)
            
        Returns:
            Context string
        """
        context_parts = []
        total_length = 0
        max_length = max_tokens * 4  # Rough estimate: 1 token ≈ 4 chars
        
        for doc in documents:
            doc_text = f"Document: {doc.title}\nType: {doc.document_type}\n\n{doc.content_text}\n\n---\n\n"
            
            if total_length + len(doc_text) > max_length:
                # Truncate if needed
                remaining = max_length - total_length
                if remaining > 200:  # Only add if meaningful content can fit
                    context_parts.append(doc_text[:remaining] + "...")
                break
            
            context_parts.append(doc_text)
            total_length += len(doc_text)
        
        return "".join(context_parts)
    
    def generate_document(
        self,
        request_text: str,
        document_type: str,
        title: str,
        tone: str = "formal",
        length: str = "medium",
        db: Session = None
    ) -> Dict:
        """
        Generate document using RAG pipeline
        
        Args:
            request_text: User's document request
            document_type: Type of document to generate
            title: Document title
            tone: Writing tone
            length: Document length
            db: Database session
            
        Returns:
            Dictionary with generated content and metadata
        """
        start_time = time.time()
        
        # Step 1: Retrieve similar documents
        similar_docs = self.retrieve_similar_documents(
            query=f"{document_type}: {request_text}",
            k=5,
            db=db
        )
        
        # Step 2: Build context from retrieved documents
        context = self.build_context(similar_docs)
        
        # Step 3: Generate content using LLM
        generated_content = self.llm_service.generate_document(
            request_text=request_text,
            document_type=document_type,
            title=title,
            context=context,
            tone=tone,
            length=length
        )
        
        generation_time = int((time.time() - start_time) * 1000)  # milliseconds
        
        return {
            'content': generated_content,
            'source_documents': [str(doc.id) for doc in similar_docs],
            'generation_time_ms': generation_time,
            'num_sources': len(similar_docs)
        }
    
    def index_document(self, document: Document):
        """
        Index a document in the vector store
        
        Args:
            document: Document to index
        """
        # Generate embedding
        embedding = self.embedding_service.generate_embedding(document.content_text)
        
        # Add to vector store
        self.vector_store.add_vectors(
            vectors=embedding.reshape(1, -1),
            document_ids=[str(document.id)]
        )
    
    def reindex_all_documents(self, db: Session):
        """
        Reindex all documents in the database
        
        Args:
            db: Database session
        """
        # Clear existing index
        self.vector_store.clear()
        
        # Get all documents
        documents = db.query(Document).all()
        
        if not documents:
            print("No documents to index")
            return
        
        # Generate embeddings for all documents
        texts = [doc.content_text for doc in documents]
        document_ids = [str(doc.id) for doc in documents]
        
        embeddings = self.embedding_service.generate_embeddings_batch(texts)
        
        # Add to vector store
        self.vector_store.add_vectors(embeddings, document_ids)
        
        # Save index
        self.vector_store.save()
        
        print(f"Indexed {len(documents)} documents")


# Global instance
rag_service = RAGService()
