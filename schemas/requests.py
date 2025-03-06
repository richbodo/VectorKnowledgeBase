from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    query: str = Field(..., description="The query string to search for in the documents")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "What are the main points discussed in the document?"
                }
            ]
        }
    }