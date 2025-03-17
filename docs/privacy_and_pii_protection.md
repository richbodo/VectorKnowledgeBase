# Privacy and PII Protection Guide

## Introduction

This comprehensive document covers privacy controls and Personally Identifiable Information (PII) protection in the Vector Knowledge Base application. It provides information for both users and developers on how sensitive information is protected throughout the system.

## Table of Contents

1. [What is PII?](#what-is-pii)
2. [Privacy Features Overview](#privacy-features-overview)
3. [Technical Implementation](#technical-implementation)
4. [User Guidelines](#user-guidelines)
5. [Testing Privacy Controls](#testing-privacy-controls)
6. [Best Practices](#best-practices)
7. [Implementation Patterns](#implementation-patterns)
8. [Future Enhancements](#future-enhancements)

## What is PII?

Personally Identifiable Information (PII) is any data that could potentially identify a specific individual. This includes:

- Names, addresses, phone numbers
- Email addresses
- Government-issued ID numbers (SSN, passport numbers)
- Financial account numbers
- Health information
- Biometric data
- IP addresses and device identifiers
- Any other unique identifiers that can be linked to an individual

## Privacy Features Overview

The Vector Knowledge Base application implements several layers of privacy protection:

### 1. Privacy Log Filter

A custom `PrivacyLogFilter` class (located in `utils/privacy_log_handler.py`) provides comprehensive filtering of sensitive information in logs:

- **Query Content Filtering**: All user queries are redacted in logs with `[QUERY CONTENT REDACTED]`
- **API Key Protection**: API keys and authentication tokens are filtered with `[API KEY REDACTED]`
- **Email Redaction**: Email addresses in logs are replaced with `[EMAIL REDACTED]`
- **Pattern-Based Filtering**: Multiple regex patterns catch different formats of sensitive data

### 2. Privacy Context Management

When executing sensitive operations, privacy context managers ensure that even in case of exceptions, sensitive information is never logged.

### 3. Request Middleware Privacy

All incoming HTTP requests are processed through middleware that removes sensitive information before logging:

- Headers like `Authorization` are redacted
- Query parameters containing potentially sensitive information are filtered
- Request body content is analyzed for sensitive patterns and redacted
- Only metadata about requests is logged, not content

### 4. Error Handling with Privacy Protection

Exception handling throughout the application is designed to protect privacy:

- Exception messages are sanitized before logging
- Stack traces are filtered to remove sensitive data
- Custom error responses never include the original query content
- In case of failures, only generic error messages are returned to users

### 5. OpenAI API Request Protection

Special patterns and filters ensure that sensitive query content is never exposed in OpenAI API request logs:

- **Request JSON Data**: OpenAI API request payloads containing query text are redacted
- **Embedding Requests**: Text submitted for embeddings is automatically filtered
- **Debug Logging**: Even debug-level logs from the OpenAI client never expose sensitive content

## Technical Implementation

### Core Components

#### 1. The Privacy Log Filter (`utils/privacy_log_handler.py`)

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

#### 2. Privacy Context Manager (`services/vector_store.py`)

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

#### 3. Request Middleware (`main.py`)

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

### Privacy Patterns

The following patterns are used to detect sensitive information:

| Pattern Type | Description | Example | Replacement |
|--------------|-------------|---------|------------|
| Email | Detects email addresses | user@example.com | [EMAIL REDACTED] |
| API Keys | Detects various API key formats | api_key="sk-1234..." | api_key="[API KEY REDACTED]" |
| Bearer Tokens | Detects OAuth bearer tokens | Bearer eyJ0eXAi... | Bearer [TOKEN REDACTED] |
| Query Content | Detects query content in various formats | query="sensitive info" | query="[QUERY CONTENT REDACTED]" |
| PDF Content | Detects PDF file content in logs | %PDF-1.5... | [PDF CONTENT REDACTED] |
| SK/P-Style Keys | Detects OpenAI-style API keys | sk-abcd1234... | [API KEY REDACTED] |
| OpenAI Request Input | Detects query content in OpenAI API requests | 'input': ['search query text'] | 'input': ['[QUERY CONTENT REDACTED]'] |

## User Guidelines

### How We Protect Your PII

Our Vector Knowledge Base application has built-in privacy protections to ensure your sensitive information remains secure:

#### Privacy in Queries

When you submit a query, our system:

- Never stores the actual content of your queries in logs
- Filters out sensitive information before storing any data
- Ensures that error messages don't reveal your query content
- Uses secure connections for all data transmission

#### Document Privacy

When you upload documents:

- Document content is processed securely
- Only authorized users can access the documents
- System logs never contain the full content of your documents
- Metadata about documents is separated from actual content

### Best Practices for Users

To maximize your privacy protection:

1. **Be cautious with sensitive data in queries**: Though our system filters PII, it's best to minimize sensitive information in your queries
2. **Use document references**: Rather than including sensitive data in queries, reference document names or topics
3. **Review search results**: Before saving or sharing search results, check for any sensitive information
4. **Report concerns**: If you believe sensitive information is being exposed, contact the administrator immediately

## Testing Privacy Controls

### Automated Privacy Testing

The application includes automated tests to verify privacy protection:

1. **Basic Filter Tests**: Verify that the privacy filter correctly redacts sensitive information
2. **API Request Tests**: Ensure that API endpoints properly protect query content
3. **Log Auditing**: Scan log files to verify no sensitive data is being logged

### Running Privacy Tests

1. Ensure the application is running
2. Execute the test script:

```bash
./utils/run_privacy_tests.sh
```

This will:
- Make test requests with sensitive sample data
- Check logs for any content leakage
- Generate a test report in `test_reports/` directory

### Manual Privacy Testing

You can also manually test the privacy controls:

1. Make a request to the API with sensitive information:

```bash
curl -X POST -H "Content-Type: application/json" -H "X-API-Key: your_api_key" \
  -d '{"query": "This is sensitive information"}' \
  http://localhost:8080/api/query
```

2. Check the logs to verify no sensitive data was leaked:

```bash
tail -n 50 app.log | grep -v "QUERY CONTENT REDACTED"
```

## Best Practices

### For Developers

When working with the application:

1. **Never bypass the privacy filter**: All logging should use loggers with privacy filters applied
2. **Use privacy context managers**: When processing sensitive data, always use privacy contexts
3. **Sanitize before logging**: Always sanitize sensitive data before logging it
4. **Test privacy after changes**: Always run privacy tests after making code changes
5. **Update patterns as needed**: Add new patterns when new sensitive data formats are identified

### Implementation Patterns

#### Pattern 1: Privacy-Aware Logging

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

#### Pattern 2: Privacy-First Error Handling

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

#### Pattern 3: Request Content Sanitization

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

## PII Minimization Strategy

The application follows a comprehensive PII minimization strategy:

1. **Collection Limitation**: Only collect information necessary for the functions being performed
2. **Purpose Limitation**: Use PII only for the specific purpose for which it was collected
3. **Data Minimization**: Minimize the PII displayed in logs, error messages, and user interfaces
4. **Retention Limitation**: Implement automatic cleanup of logs containing potential PII
5. **Security Safeguards**: Implement strong security controls to protect PII

## Limitations and Edge Cases

The current PII protection has some limitations:

1. **Embedded PII in documents**: The system cannot identify and redact PII within uploaded documents
2. **Complex PII formats**: Highly unusual PII formats might not be detected by the current patterns
3. **Image-based PII**: PII contained within images cannot be detected
4. **False positives**: Some non-PII content might be mistakenly identified as PII

## Future Enhancements

Planned enhancements to PII protection:

1. **Machine Learning-based PII detection**: Implement ML models to better identify PII in unstructured content
2. **Document PII scanning**: Add capability to scan uploaded documents for PII
3. **User-configurable PII controls**: Allow users to specify additional PII categories to protect
4. **Enhanced reporting**: Provide anonymized metrics on PII detection and filtering
5. **Real-time monitoring**: Add metrics to track privacy filter performance
6. **Privacy scoring**: Implement scoring system for privacy compliance

## Related Resources

- [Privacy Demo Script](./privacy_demo.py) - Demonstration of privacy features
- [Privacy Test Runner](../utils/run_privacy_tests.sh) - Tool for comprehensive privacy testing
- [Authentication Guide](./authentication.md) - How authentication credentials are protected

---

*Documentation last updated: March 17, 2025*