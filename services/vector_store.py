import json
import logging
import faiss
import numpy as np
from typing import List, Dict, Optional
from models import Document, VectorSearchResult
from services.embedding_service import EmbeddingService
from config import VECTOR_DIMENSION, FAISS_INDEX_PATH, DOCUMENT_STORE_PATH

logger = logging.getLogger(__name__)

class VectorStore:
    _instance = None
    
    def __init__(self):
        self.index = faiss.IndexFlatL2(VECTOR_DIMENSION)
        self.documents: Dict[str, Document] = {}
        self.embedding_service = EmbeddingService()
        
    @classmethod
    def get_instance(cls) -> 'VectorStore':
        if cls._instance is None:
            cls._instance = VectorStore()
        return cls._instance
    
    def add_document(self, document: Document) -> bool:
        """Add document to vector store"""
        try:
            embedding = self.embedding_service.generate_embedding(document.content)
            if embedding is None:
                return False
                
            self.index.add(np.array([embedding], dtype=np.float32))
            self.documents[document.id] = document
            self._save_state()
            return True
            
        except Exception as e:
            logger.error(f"Error adding document to vector store: {str(e)}")
            return False
    
    def search(self, query: str, k: int = 3) -> List[VectorSearchResult]:
        """Search for similar documents"""
        try:
            query_embedding = self.embedding_service.generate_embedding(query)
            if query_embedding is None:
                return []
                
            distances, indices = self.index.search(
                np.array([query_embedding], dtype=np.float32), 
                k
            )
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < 0 or idx >= len(self.documents):
                    continue
                    
                doc_id = list(self.documents.keys())[idx]
                doc = self.documents[doc_id]
                
                results.append(
                    VectorSearchResult(
                        document_id=doc.id,
                        content=doc.content,
                        similarity_score=float(1 / (1 + distances[0][i])),
                        metadata=doc.metadata
                    )
                )
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            return []
    
    def _save_state(self):
        """Save index and documents to disk"""
        try:
            faiss.write_index(self.index, FAISS_INDEX_PATH)
            
            document_data = {
                doc_id: {
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "created_at": doc.created_at.isoformat()
                }
                for doc_id, doc in self.documents.items()
            }
            
            with open(DOCUMENT_STORE_PATH, 'w') as f:
                json.dump(document_data, f)
                
        except Exception as e:
            logger.error(f"Error saving vector store state: {str(e)}")

def init_vector_store():
    """Initialize vector store singleton"""
    return VectorStore.get_instance()
