from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    query: str = Field(..., description="The query string to search for in the documents")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What are the main points discussed in the document?"
            }
        }
