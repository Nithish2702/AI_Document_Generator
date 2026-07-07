"""
FAISS Vector Store Service
Handles similarity search using FAISS
"""
import faiss
import numpy as np
import pickle
from typing import List, Tuple
from pathlib import Path
from app.config import settings


class VectorStore:
    """FAISS-based vector store for similarity search"""
    
    def __init__(self, dimension: int = 384):
        """
        Initialize vector store
        
        Args:
            dimension: Dimension of embedding vectors
        """
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)  # L2 distance
        self.document_ids = []  # Store document IDs corresponding to vectors
        self.index_path = Path(settings.VECTOR_STORE_DIR)
        self.index_path.mkdir(parents=True, exist_ok=True)
    
    def add_vectors(self, vectors: np.ndarray, document_ids: List[str]):
        """
        Add vectors to the index
        
        Args:
            vectors: numpy array of shape (n, dimension)
            document_ids: List of document IDs corresponding to vectors
        """
        if vectors.shape[1] != self.dimension:
            raise ValueError(f"Vector dimension {vectors.shape[1]} doesn't match index dimension {self.dimension}")
        
        self.index.add(vectors.astype('float32'))
        self.document_ids.extend(document_ids)
    
    def search(self, query_vector: np.ndarray, k: int = 5) -> Tuple[List[float], List[str]]:
        """
        Search for k nearest neighbors
        
        Args:
            query_vector: Query embedding vector
            k: Number of results to return
            
        Returns:
            Tuple of (distances, document_ids)
        """
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        
        distances, indices = self.index.search(query_vector.astype('float32'), k)
        
        # Get document IDs for the results
        result_doc_ids = [self.document_ids[idx] for idx in indices[0] if idx < len(self.document_ids)]
        result_distances = distances[0].tolist()
        
        return result_distances, result_doc_ids
    
    def save(self, filename: str = "faiss_index.bin"):
        """
        Save index to disk
        
        Args:
            filename: Name of the file to save
        """
        index_file = self.index_path / filename
        metadata_file = self.index_path / "metadata.pkl"
        
        # Save FAISS index
        faiss.write_index(self.index, str(index_file))
        
        # Save metadata (document IDs)
        with open(metadata_file, 'wb') as f:
            pickle.dump(self.document_ids, f)
    
    def load(self, filename: str = "faiss_index.bin"):
        """
        Load index from disk
        
        Args:
            filename: Name of the file to load
        """
        index_file = self.index_path / filename
        metadata_file = self.index_path / "metadata.pkl"
        
        if not index_file.exists():
            print(f"Index file {index_file} not found. Starting with empty index.")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(index_file))
        
        # Load metadata
        if metadata_file.exists():
            with open(metadata_file, 'rb') as f:
                self.document_ids = pickle.load(f)
    
    def get_size(self) -> int:
        """Get number of vectors in the index"""
        return self.index.ntotal
    
    def clear(self):
        """Clear the index"""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.document_ids = []


# Global instance
vector_store = VectorStore(dimension=settings.EMBEDDING_DIMENSION)
