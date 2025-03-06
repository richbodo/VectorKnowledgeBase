from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel

class Document:
    def __init__(self, id: str, content: str, metadata: Dict, created_at: Optional[datetime] = None):
        self.id = id
        self.content = content
        self.metadata = metadata
        self.created_at = created_at or datetime.utcnow()

class VectorSearchResult(BaseModel):
    document_id: str
    content: str
    similarity_score: float
    metadata: Dict

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "content": "Sample document content",
                "similarity_score": 0.95,
                "metadata": {
                    "filename": "example.pdf",
                    "content_type": "application/pdf",
                    "size": 1024
                }
            }]
        }
    }