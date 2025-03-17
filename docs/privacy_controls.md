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

### 2. Privacy Context Management

When executing sensitive operations, privacy context managers ensure that even in case of exceptions, sensitive information is never logged:

```python
def search(self, query: str, k: int = 3, similarity_threshold: float = 0.1):
    """Search for similar document chunks"""
    with privacy_context(query):
        # Inside this context, any exceptions will have query content redacted
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        return process_results(results)
```

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

### 5. Privacy-Aware Logging Integration

All loggers in the application use the privacy filter:

```python
# Configuring loggers with privacy protection
def setup_logging():
    """Configure application logging with privacy controls"""
    # Root logger configuration
    root_logger = logging.getLogger()
    add_privacy_filter_to_logger(root_logger)
    
    # Component-specific loggers
    for logger_name in ["api", "services", "web"]:
        logger = logging.getLogger(logger_name)
        add_privacy_filter_to_logger(logger)
```

## Implementation Details

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

### Pattern Implementation

The pattern implementation uses regular expressions to match various formats of sensitive data:

```python
# Sample pattern implementations
patterns = {
    # Email addresses
    'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    
    # API keys (looking for common patterns)
    'api_key': re.compile(r'(api[_-]?key|token|key)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?', re.I),
    
    # Query content (sanitize actual queries)
    'query_content': re.compile(r'(query"?\s*[:=]\s*"?)([^"]+)("?)', re.IGNORECASE),
    
    # JSON query content (for API payloads)
    'json_query': re.compile(r'("query":\s*")([^"]+)(")', re.IGNORECASE),
}
```

## Testing Privacy Controls

### Automated Privacy Testing

The application includes automated tests to verify privacy protection:

1. **Basic Filter Tests**: Verify that the privacy filter correctly redacts sensitive information
2. **API Request Tests**: Ensure that API endpoints properly protect query content
3. **Log Auditing**: Scan log files to verify no sensitive data is being logged

### Manual Privacy Testing

To manually test privacy controls:

1. Make API requests with sensitive information
2. Check application logs to verify the information is redacted
3. Intentionally trigger errors to ensure error messages don't contain sensitive data

```bash
# Example manual test
curl -X POST -H "Content-Type: application/json" -H "X-API-Key: your_api_key" \
  -d '{"query": "This is sensitive information"}' \
  http://localhost:8080/api/query

# Then check logs
grep "sensitive information" app.log  # Should find no matches
grep "QUERY CONTENT REDACTED" app.log  # Should find matches
```

## Best Practices for Developers

When working with the application:

1. **Never bypass the privacy filter**: All logging should use loggers with privacy filters applied
2. **Use privacy context managers**: When processing sensitive data, always use privacy contexts
3. **Sanitize before logging**: Always sanitize sensitive data before logging it
4. **Test privacy after changes**: Always run privacy tests after making code changes
5. **Update patterns as needed**: Add new patterns when new sensitive data formats are identified

## Monitoring and Improvement

To continuously monitor and improve privacy protection:

1. **Log Analysis**: Regularly review logs for potential privacy leaks
2. **Filter Pattern Updates**: Update regex patterns as new data formats emerge
3. **Security Testing**: Conduct security testing to identify potential vulnerabilities
4. **User Feedback**: Incorporate user feedback about privacy concerns

## Related Resources

- [PII Protection Implementation](./pii_protection.md)
- [User PII Guide](./user_pii_guide.md)
- [PII Implementation Guide](./pii_implementation_guide.md)
- [Privacy Demo Script](./privacy_demo.py)
- [Privacy Test Runner](../utils/run_privacy_tests.sh)