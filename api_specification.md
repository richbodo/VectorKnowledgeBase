# PDF Processing API Specification

## Base URL
The API is accessible at: `https://vector-knowledge-base-RichBodo.replit.app`

The application is deployed using Replit's deployment service which automatically handles HTTPS and domain mapping. No port number is needed in the URL as Replit handles the port forwarding internally.

## Authentication
All API endpoints require authentication using the Vector Knowledge Base API key when running in development/test mode.

**Header Required in Development:**
- `X-API-KEY`: Your Vector Knowledge Base API key (VKB_API_KEY)

**Note:** In deployment mode, authentication is optional. The API will function without the VKB_API_KEY to ensure public accessibility of the deployed service.

**Authentication Errors (Development Mode Only):**
```json
{
  "error": "Missing API key"
}
```
Status Code: 401

```json
{
  "error": "Invalid API key"
}
```
Status Code: 401

## Endpoints

### 1. Upload Document
Upload a PDF document for processing and vector storage. The document will be automatically chunked into smaller segments (approximately 500 tokens each) to stay within OpenAI's embedding model context limits.

**Endpoint:** `POST /api/upload`

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
  "document_id": "uuid-string",
  "metadata": {
    "filename": "example.pdf",
    "size": 1234567,
    "content_type": "application/pdf"
  }
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
- 401: Authentication error (missing or invalid API key)
- 500: Server error

**Example Usage:**
```bash
curl -X POST -F "file=@document.pdf" \
     -H "Accept: application/json" \
     -H "X-API-KEY: your_vkb_api_key" \
     https://vector-knowledge-base-RichBodo.replit.app/api/upload
```

### 2. Query Documents
Search through uploaded documents using semantic similarity. Results are retrieved from chunked document segments and ranked by relevance.

**Endpoint:** `POST /api/query`

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
        "source": "Part 2 of 5",
        "file_type": "application/pdf",
        "uploaded_at": "2025-03-06T23:35:27.648Z",
        "file_size": "1.2MB"
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
- 400: Invalid request (missing or empty query)
- 401: Authentication error (missing or invalid API key)
- 500: Server error

**Example Usage:**
```bash
curl -X POST https://vector-knowledge-base-RichBodo.replit.app/api/query \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "X-API-KEY: your_vkb_api_key" \
  -d '{"query": "What are the main points discussed in the document?"}'
```

### 3. Monitoring Endpoints

#### Health Check
Get system health and resource usage information.

**Endpoint:** `GET /web/monitoring/health`

**Response:** HTML page with health metrics including:
- Memory usage (RSS, VMS)
- CPU utilization
- Process information
- Vector store statistics (document count, collection size)

#### OpenAI Connection Test
Test OpenAI API connectivity and configuration.

**Endpoint:** `GET /web/monitoring/test-openai`

**Response:** HTML page with diagnostic information including:
- API key validation
- Embedding model test results
- Error details if any

## Technical Details

### Document Processing
- Documents are automatically chunked into smaller segments (approximately 500 tokens each)
- Each chunk is processed independently for embedding generation
- Chunks are stored with metadata linking them to the original document
- Vector similarity search is performed across all chunks
- ChromaDB is used for vector storage with telemetry disabled

### Error Handling

Common error responses include:

1. Authentication errors:
```json
{
  "error": "Missing API key"
}
```
```json
{
  "error": "Invalid API key"
}
```

2. File too large:
```json
{
  "error": "File size (X bytes) exceeds maximum limit (50MB)"
}
```

3. Invalid file type:
```json
{
  "error": "Invalid file type. Only PDF files are allowed"
}
```

4. Empty query:
```json
{
  "error": "Query cannot be empty"
}
```

5. OpenAI API errors:
```json
{
  "error": "Error generating embeddings: [Specific OpenAI API error message]"
}
```

6. No results:
```json
{
  "error": "No relevant matches found"
}
```

## Notes
- The API implements robust error handling with detailed error messages
- All endpoints support CORS with appropriate headers
- The application uses ChromaDB for vector storage with telemetry disabled
- Text chunking ensures compliance with OpenAI's token limits
- All responses use UTF-8 encoding
- Authentication is required for all API endpoints using the VKB_API_KEY