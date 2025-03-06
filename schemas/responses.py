from typing import List, Optional
from pydantic import BaseModel

class UploadResponse(BaseModel):
    success: bool
    message: str
    document_id: Optional[str] = None

class QueryResponse(BaseModel):
    results: List[dict]
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    error: str
