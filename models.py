from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel

class Document:
    def __init__(self, id: str, content: str, metadata: Dict):
        self.id = id
        self.content = content
        self.metadata = metadata
        self.created_at = datetime.utcnow()

class VectorSearchResult(BaseModel):
    document_id: str
    content: str
    similarity_score: float
    metadata: Dict
