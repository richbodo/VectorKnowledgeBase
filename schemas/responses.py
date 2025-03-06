"""Response schemas for API endpoints"""
from typing import List, Dict, Optional

def upload_response(success: bool, message: str, document_id: Optional[str] = None) -> Dict:
    """Format upload endpoint response"""
    response = {
        "success": success,
        "message": message
    }
    if document_id:
        response["document_id"] = document_id
    return response

def query_response(results: List[Dict], message: Optional[str] = None) -> Dict:
    """Format query endpoint response"""
    return {
        "results": results,
        "message": message or "Query processed successfully"
    }

def error_response(error: str) -> Dict:
    """Format error response"""
    return {"error": error}