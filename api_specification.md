# PDF Processing API Specification

## Base URL
All endpoints are relative to: `https://your-replit-app.replit.app/`

## Endpoints

### 1. Upload Document
Upload a PDF document for processing and vector storage.

**Endpoint:** `POST /upload`

**Content-Type:** `multipart/form-data`

**Request Parameters:**
- `file` (required): PDF file to upload
  - Maximum size: 50MB
  - Accepted MIME type: application/pdf

**Response Format:**
```json
{
  "success": true,
  "message": "Document processed successfully",
  "document_id": "uuid-string"
}
```

**Error Response:**
```json
{
  "error": "Error message description"
}
```

**Status Codes:**
- 200: Success
- 400: Invalid request (file missing, wrong type, or too large)
- 500: Server error

**Example Usage:**
```bash
curl -X POST https://your-replit-app.replit.app/upload \
  -F "file=@document.pdf" 
```

### 2. Query Documents
Search through uploaded documents using semantic similarity.

**Endpoint:** `POST /query`

**Content-Type:** `application/json`

**Request Format:**
```json
{
  "query": "Your search query text"
}
```

**Response Format:**
```json
{
  "results": [
    {
      "title": "document-name.pdf",
      "content": "Relevant text excerpt from the document",
      "score": 0.89,
      "metadata": {
        "source": "document-name.pdf",
        "section": "Part 2 of 5"
      }
    }
  ]
}
```

**Error Response:**
```json
{
  "error": "Error message description"
}
```

**Status Codes:**
- 200: Success
- 400: Invalid request (missing query)
- 500: Server error

**Example Usage:**
```bash
curl -X POST https://your-replit-app.replit.app/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main points discussed in the document?"}'
```

## Error Handling

Common error responses include:

1. File too large:
```json
{
  "error": "File size exceeds maximum limit (50MB)"
}
```

2. Invalid file type:
```json
{
  "error": "Invalid file type. Only PDF files are allowed"
}
```

3. Empty query:
```json
{
  "error": "Query cannot be empty"
}
```

4. No results:
```json
{
  "error": "No relevant matches found"
}
```

## Notes
- The query endpoint uses semantic similarity to find relevant document sections
- Results are ordered by relevance score (0-1, higher is better)
- The API automatically chunks documents and maintains context
- All responses use UTF-8 encoding
