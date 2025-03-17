# Privacy Controls Documentation

## Overview

This document outlines the privacy controls implemented in the Vector Knowledge Base application to protect sensitive information in logs and error handling. These controls focus primarily on query content, which may contain sensitive information from users.

## Key Privacy Features

### 1. Privacy Log Filter

A custom `PrivacyLogFilter` class (located in `utils/privacy_log_handler.py`) provides comprehensive filtering of sensitive information in logs:

- **Query Content Filtering**: All user queries are redacted in logs with `[QUERY CONTENT REDACTED]`
- **API Key Protection**: API keys and authentication tokens are filtered with `[API KEY REDACTED]`
- **Email Redaction**: Email addresses in logs are replaced with `[EMAIL REDACTED]`
- **Pattern-Based Filtering**: Multiple regex patterns catch different formats of sensitive data:
  - URL parameters (`?query=sensitive`)
  - JSON fields (`{"query": "sensitive"}`)
  - Form data (`query=sensitive`)
  - String interpolation (`query='sensitive'`)
  - Dictionary format (`'query': 'sensitive'`)

### 2. Request Middleware Privacy

Request middleware in `main.py` provides additional privacy protections:

- **Endpoint-Specific Controls**: More strict filtering for `/api/query` endpoints
- **Headers Protection**: Sensitive headers like Authorization are automatically redacted
- **Metadata-Only Logging**: For sensitive endpoints, only metadata is logged (not content):
  - Request method and route
  - Number of parameters (not their values)
  - File metadata (filenames, content types) without content

### 3. Enhanced Vector Search Privacy

The vector search implementation in `services/vector_store.py` includes:

- **Privacy Context Manager**: Ensures query content isn't leaked in exceptions
- **Error Sanitization**: Sanitizes error messages to remove query content
- **Content Length Logging**: Logs only content length, not the content itself
- **Traceback Protection**: Special handling of exception tracebacks to prevent leaking query content

### 4. Embedding Service Privacy

The embedding service (`services/embedding_service.py`) implements:

- **Zero Content Logging**: No logging of actual text being embedded
- **Sanitized Error Handling**: Special exception handling to remove text content from error messages
- **Exception Wrapping**: Catches and rewraps exceptions to prevent content leakage

### 5. API Route Privacy

API query endpoints in `api/routes.py` implement:

- **Request Sanitization**: Logging only that a query was received, not its content
- **Length-Only Metrics**: Logging only query length for diagnostic purposes
- **Response Privacy**: Careful handling of response logging to avoid leaking sensitive data

## Testing Privacy Controls

You can test the privacy controls by:

1. Making a query request to `/api/query` endpoint
2. Examining the logs to verify query content is properly redacted
3. Intentionally causing an error (e.g., with malformed input) to verify error privacy

## Additional Considerations

- **Third-Party Services**: Ensure OpenAI API calls and other external services are properly filtered
- **Log Rotation**: Logs should be regularly rotated and old logs securely deleted
- **Monitoring**: Regularly audit logs to verify privacy controls are working

## Future Enhancements

1. **Content Fingerprinting**: Implement content fingerprinting to catch data fragments
2. **User-Specific Controls**: Allow users to specify additional privacy requirements
3. **Data Minimization**: Further reduce logging of non-essential information