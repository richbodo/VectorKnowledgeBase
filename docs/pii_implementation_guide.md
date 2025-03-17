# PII Protection: Technical Implementation Guide

This guide provides detailed technical information about how PII (Personally Identifiable Information) protection is implemented in the Vector Knowledge Base application. It's intended for developers who need to maintain or extend the privacy features.

## Core Components

### 1. The Privacy Log Filter (`utils/privacy_log_handler.py`)

The central component of PII protection is the `PrivacyLogFilter` class, which intercepts and sanitizes log records before they're written:

```python
def filter(self, record: logging.LogRecord) -> bool:
    """Filter log records to remove sensitive information."""
    try:
        # Skip processing if record doesn't have a string message
        if not hasattr(record, 'msg'):
            return True
        
        # Handle the case where msg is already a string
        if isinstance(record.msg, str):
            message = record.msg
            
            # Apply each pattern in sequence
            for pattern_name, pattern in self.patterns.items():
                if pattern_name == 'email':
                    message = pattern.sub('[EMAIL REDACTED]', message)
                elif 'query' in pattern_name:
                    message = pattern.sub(r'\1[QUERY CONTENT REDACTED]\3', message)
                # ... additional pattern handlers
            
            # Update the record
            record.msg = message
        
        # Additional handling for args
        # ...
    except Exception:
        # Log filter should never block messages
        pass
    
    return True  # Always allow the message through (but sanitized)
```

### 2. Privacy Context Manager (`services/vector_store.py`)

For sensitive operations, we use context managers to ensure privacy:

```python
def privacy_context():
    """Context manager to ensure privacy during query execution"""
    original_query = query  # Save original for reference
    try:
        # Execute the operation with full query 
        yield
    except Exception as e:
        # Ensure exception message doesn't contain query content
        sanitized_message = str(e)
        for pattern in privacy_patterns:
            sanitized_message = pattern.sub('[QUERY CONTENT REDACTED]', sanitized_message)
        
        # Raise new exception with sanitized message
        raise type(e)(sanitized_message) from None
```

### 3. Request Middleware (`main.py`)

Request middleware intercepts all incoming requests to apply privacy filtering:

```python
@app.before_request
def log_request_info():
    """Log and sanitize request information"""
    # Basic request metadata is safe to log
    app.logger.info(f"=== New Request ===")
    app.logger.info(f"Method: {request.method}")
    app.logger.info(f"Path: {request.path}")
    
    # Sanitize headers before logging
    sanitized_headers = {}
    for key, value in request.headers.items():
        if key.lower() in ('authorization', 'cookie', 'x-api-key'):
            sanitized_headers[key] = '[REDACTED]'
        else:
            sanitized_headers[key] = value
    
    app.logger.info(f"Headers: {sanitized_headers}")
    
    # For sensitive endpoints, don't log request body at all
    if request.path.startswith('/api/query'):
        # Only log that a query was received, not its content
        app.logger.info(f"Received query request (content filtered)")
    elif request.is_json:
        # For other JSON endpoints, sanitize sensitive fields
        sanitized_json = sanitize_json(request.get_json())
        app.logger.debug(f"JSON Body: {sanitized_json}")
```

### 4. API Routes Privacy (`api/routes.py`)

API endpoints implement additional protection:

```python
@api_blueprint.route('/query', methods=['POST'])
@require_api_key
def query_documents():
    """Query endpoint for semantic search"""
    try:
        if not request.is_json:
            return error_response("Request must be JSON")
        
        data = request.get_json()
        
        # Log only that a query was received (not the content)
        app.logger.info(f"Received query request, length: {len(data.get('query', ''))}")
        
        # Process the query (with privacy protections)
        results, error = vector_store.search(
            query=data.get('query', ''),
            k=data.get('limit', 3),
            similarity_threshold=data.get('threshold', 0.1)
        )
        
        if error:
            # Sanitize any error before returning
            return error_response(f"Error during search: {sanitize_error(error)}")
            
        return query_response(
            # Return only necessary fields
            results=[{
                'document_id': r.document_id,
                'content': r.content,
                'similarity_score': r.similarity_score,
                'metadata': r.metadata
            } for r in results]
        )
    except Exception as e:
        # Additional exception handling with privacy protection
        app.logger.error(f"Exception in query endpoint: {sanitize_error(str(e))}")
        return error_response("An error occurred processing your request")
```

## Implementation Patterns

### Pattern 1: Privacy-Aware Logging

Whenever adding a new logger or log statement:

```python
# WRONG - May expose PII:
logger.info(f"Processing query: {user_query}")

# RIGHT - Apply privacy filter:
from utils.privacy_log_handler import add_privacy_filter_to_logger
logger = logging.getLogger("my_component")
add_privacy_filter_to_logger(logger)

# Now logs are automatically filtered
logger.info(f"Processing query: {user_query}")  # Will be sanitized
```

### Pattern 2: Privacy-First Error Handling

When handling exceptions:

```python
# WRONG - May expose PII in error message:
try:
    result = process_query(user_query)
except Exception as e:
    logger.error(f"Error processing query {user_query}: {str(e)}")
    raise

# RIGHT - Sanitize error message:
from utils.privacy_log_handler import sanitize_error
try:
    result = process_query(user_query)
except Exception as e:
    sanitized_error = sanitize_error(str(e))
    logger.error(f"Error processing request: {sanitized_error}")
    raise Exception(sanitized_error) from None
```

### Pattern 3: Request Content Sanitization

When working with request data:

```python
# WRONG - May log PII:
app.logger.info(f"Request data: {request.form}")

# RIGHT - Sanitize request data:
def sanitize_form_data(form_data):
    """Create a copy of form data with sensitive fields redacted"""
    sanitized = {}
    for key, value in form_data.items():
        if key.lower() in ('query', 'password', 'token', 'key'):
            sanitized[key] = '[REDACTED]'
        else:
            sanitized[key] = value
    return sanitized

app.logger.info(f"Request data: {sanitize_form_data(request.form)}")
```

### Pattern 4: Testing Privacy Controls

After making changes, verify privacy controls:

```python
def test_privacy_protection():
    """Test that sensitive information is properly redacted"""
    sensitive_query = "Find information about John Doe with SSN 123-45-6789"
    
    # Make a test request
    response = client.post('/api/query', 
                          json={'query': sensitive_query},
                          headers={'X-API-Key': TEST_API_KEY})
    
    # Check logs for leakage
    with open('app.log', 'r') as f:
        logs = f.read()
        assert "John Doe" not in logs
        assert "123-45-6789" not in logs
        assert "[QUERY CONTENT REDACTED]" in logs
```

## Debugging Privacy Issues

When troubleshooting privacy issues:

1. **Inspect raw logs**: Check if PII appears in logs before filtering
2. **Test specific patterns**: Verify regex patterns are catching expected PII formats
3. **Add tracing**: Add temporary debug statements (outside of production)
4. **Verify context**: Ensure privacy context managers are used correctly

## Common Pitfalls

1. **Nested error handling**: Make sure nested exception handlers maintain privacy
2. **Third-party loggers**: Ensure third-party libraries use privacy-filtered loggers
3. **New PII formats**: Watch for emerging PII formats that might not be caught
4. **Performance impact**: Monitoring for impact of regex filtering on high-volume operations

## Future Enhancement Areas

1. **ML-based detection**: Consider ML models for more accurate PII detection
2. **Config-driven patterns**: Allow customization of PII patterns through configuration
3. **Real-time monitoring**: Add metrics to track privacy filter performance
4. **Privacy scoring**: Implement scoring system for privacy compliance

---

*For any questions about PII protection implementation, contact the security team.*