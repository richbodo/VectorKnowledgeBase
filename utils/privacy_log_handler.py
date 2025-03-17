"""
Privacy-focused log handler for filtering sensitive information from logs
"""
import logging
import re
from typing import Dict, List, Pattern, Optional, Union


class PrivacyLogFilter(logging.Filter):
    """Filter that removes sensitive information from log records"""
    
    def __init__(self, patterns: Optional[Dict[str, Pattern]] = None, name: str = ''):
        """
        Initialize the privacy filter with regex patterns to detect sensitive data.
        
        Args:
            patterns: Dictionary of named regex patterns to match sensitive data
            name: Name for the filter (passed to parent class)
        """
        super().__init__(name)
        self.patterns = patterns or {
            # Email addresses
            'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
            
            # API keys (looking for common patterns)
            'api_key': re.compile(r'(api[_-]?key|token|key)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?', re.I),
            
            # OpenAI API keys
            'openai_key': re.compile(r'(OPENAI_API_KEY\s*=\s*["\'`])([^"\'`]+)(["\'`])', re.I),
            
            # Generic API key assignments
            'api_key_assign': re.compile(r'([\w_]+_API_KEY\s*=\s*["\'`])([^"\'`]+)(["\'`])', re.I),
            
            # OAuth/Bearer tokens
            'bearer_token': re.compile(r'bearer\s+([a-zA-Z0-9_\-\.]{20,})', re.I),
            
            # Query content (sanitize actual queries) - extended to catch more patterns
            'query_content': re.compile(r'(query"?\s*[:=]\s*"?)([^"]+)("?)', re.IGNORECASE),
            
            # JSON query content (for API payloads)
            'json_query': re.compile(r'("query":\s*")([^"]+)(")', re.IGNORECASE),
            
            # Form parameter query content
            'form_query': re.compile(r'(query=)([^&]+)(&|$)', re.IGNORECASE),
            
            # URL parameter query content
            'url_query': re.compile(r'(\?|&)query=([^&]+)(&|$)', re.IGNORECASE),
            
            # Query as dictionary key-value pair
            'dict_query': re.compile(r'([\'"]query[\'"]\s*:\s*[\'"])([^\'"]+)([\'"])', re.IGNORECASE),
            
            # Query in string interpolation
            'f_string_query': re.compile(r'(query\s*=\s*f?[\'"])([^\'"]+)([\'"])', re.IGNORECASE),
            
            # Query in log message
            'log_query': re.compile(r'(query:\s*)([^\n\r]+)($|\n|\r)', re.IGNORECASE),
            
            # PDF file content indicators
            'pdf_content': re.compile(r'(%PDF-\d+\.\d+.{10,100})'),
            
            # sk- style API keys (like OpenAI)
            'sk_api_keys': re.compile(r'(sk-[a-zA-Z0-9]{20,})'),
            
            # Newer p-* style OpenAI API keys 
            'openai_p_keys': re.compile(r'(sk-p-[a-zA-Z0-9-]{20,})'),
            
            # Key header API keys pattern
            'key_header_pattern': re.compile(r'(API key|key|token):\s*([a-zA-Z0-9_\-\.]{20,})', re.I),
            
            # Environment variable assignments in logs
            'env_var_api_key': re.compile(r'(\w+_API_KEY)=([^\s]+)'),
            
            # Header-based API keys
            'x_api_key': re.compile(r'(X-API-Key|x-api-key):\s*([a-zA-Z0-9_\-\.]{20,})')
        }
        
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records to remove sensitive information.
        
        Args:
            record: The log record to process
            
        Returns:
            bool: Always True (to allow the record through, but modified)
        """
        try:
            # Skip processing if record doesn't have a string message
            if not hasattr(record, 'msg'):
                return True
                
            # Handle the case where msg is already a string
            if isinstance(record.msg, str):
                message = record.msg
                
                # Replace email addresses
                message = self.patterns['email'].sub('[EMAIL REDACTED]', message)
                
                # Replace API keys
                message = self.patterns['api_key'].sub(r'\1: [API KEY REDACTED]', message)
                
                # Replace OpenAI specific API keys
                message = self.patterns['openai_key'].sub(r'\1[API KEY REDACTED]\3', message)
                
                # Replace generic API key assignments
                message = self.patterns['api_key_assign'].sub(r'\1[API KEY REDACTED]\3', message)
                
                # Replace Bearer tokens
                message = self.patterns['bearer_token'].sub(r'Bearer [TOKEN REDACTED]', message)
                
                # Redact query content but preserve structure
                message = self.patterns['query_content'].sub(r'\1[QUERY CONTENT REDACTED]\3', message)
                
                # Redact JSON query content
                message = self.patterns['json_query'].sub(r'\1[QUERY CONTENT REDACTED]\3', message)
                
                # Redact form parameter query content
                message = self.patterns['form_query'].sub(r'\1[QUERY CONTENT REDACTED]\3', message)
                
                # Redact URL parameter query content
                message = self.patterns['url_query'].sub(r'\1query=[QUERY CONTENT REDACTED]\3', message)
                
                # Redact dictionary key-value query content
                message = self.patterns['dict_query'].sub(r'\1[QUERY CONTENT REDACTED]\3', message)
                
                # Redact f-string query content
                message = self.patterns['f_string_query'].sub(r'\1[QUERY CONTENT REDACTED]\3', message)
                
                # Redact query in log messages
                message = self.patterns['log_query'].sub(r'\1[QUERY CONTENT REDACTED]\3', message)
                
                # Redact PDF content
                message = self.patterns['pdf_content'].sub('[PDF CONTENT REDACTED]', message)
                
                # Redact sk- style API keys (like OpenAI)
                message = self.patterns['sk_api_keys'].sub(r'[API KEY REDACTED]', message)
                
                # Redact newer p-* style OpenAI API keys
                message = self.patterns['openai_p_keys'].sub(r'[API KEY REDACTED]', message)
                
                # Redact environment variable assignments
                message = self.patterns['env_var_api_key'].sub(r'\1=[API KEY REDACTED]', message)
                
                # Redact X-API-Key headers
                message = self.patterns['x_api_key'].sub(r'\1: [API KEY REDACTED]', message)
                
                # Redact header-style API keys
                message = self.patterns['key_header_pattern'].sub(r'\1: [API KEY REDACTED]', message)
                
                # Update the record
                record.msg = message
            
            # Handle string formatting with args
            if hasattr(record, 'args') and record.args:
                if isinstance(record.args, dict):
                    # Handle dict args (for named string formatting)
                    sanitized_args = {}
                    for key, value in record.args.items():
                        if isinstance(value, str):
                            sanitized_value = value
                            for pattern_name, pattern in self.patterns.items():
                                if pattern_name == 'email':
                                    sanitized_value = pattern.sub('[EMAIL REDACTED]', sanitized_value)
                                elif pattern_name == 'api_key':
                                    sanitized_value = pattern.sub(r'\1: [API KEY REDACTED]', sanitized_value)
                                elif pattern_name == 'openai_key':
                                    sanitized_value = pattern.sub(r'\1[API KEY REDACTED]\3', sanitized_value)
                                elif pattern_name == 'api_key_assign':
                                    sanitized_value = pattern.sub(r'\1[API KEY REDACTED]\3', sanitized_value)
                                elif pattern_name == 'bearer_token':
                                    sanitized_value = pattern.sub(r'Bearer [TOKEN REDACTED]', sanitized_value)
                                elif pattern_name == 'query_content':
                                    sanitized_value = pattern.sub(r'\1[QUERY CONTENT REDACTED]\3', sanitized_value)
                                elif pattern_name == 'json_query':
                                    sanitized_value = pattern.sub(r'\1[QUERY CONTENT REDACTED]\3', sanitized_value)
                                elif pattern_name == 'form_query':
                                    sanitized_value = pattern.sub(r'\1[QUERY CONTENT REDACTED]\3', sanitized_value)
                                elif pattern_name == 'url_query':
                                    sanitized_value = pattern.sub(r'\1query=[QUERY CONTENT REDACTED]\3', sanitized_value)
                                elif pattern_name == 'dict_query':
                                    sanitized_value = pattern.sub(r'\1[QUERY CONTENT REDACTED]\3', sanitized_value)
                                elif pattern_name == 'f_string_query':
                                    sanitized_value = pattern.sub(r'\1[QUERY CONTENT REDACTED]\3', sanitized_value)
                                elif pattern_name == 'log_query':
                                    sanitized_value = pattern.sub(r'\1[QUERY CONTENT REDACTED]\3', sanitized_value)
                                elif pattern_name == 'pdf_content':
                                    sanitized_value = pattern.sub('[PDF CONTENT REDACTED]', sanitized_value)
                                elif pattern_name == 'sk_api_keys':
                                    sanitized_value = pattern.sub(r'[API KEY REDACTED]', sanitized_value)
                                elif pattern_name == 'openai_p_keys':
                                    sanitized_value = pattern.sub(r'[API KEY REDACTED]', sanitized_value)
                                elif pattern_name == 'env_var_api_key':
                                    sanitized_value = pattern.sub(r'\1=[API KEY REDACTED]', sanitized_value)
                                elif pattern_name == 'x_api_key':
                                    sanitized_value = pattern.sub(r'\1: [API KEY REDACTED]', sanitized_value)
                            sanitized_args[key] = sanitized_value
                        else:
                            sanitized_args[key] = value
                    record.args = sanitized_args
                elif isinstance(record.args, tuple):
                    # Handle tuple args (for positional string formatting)
                    sanitized_args = []
                    for arg in record.args:
                        if isinstance(arg, str):
                            sanitized_arg = arg
                            for pattern_name, pattern in self.patterns.items():
                                if pattern_name == 'email':
                                    sanitized_arg = pattern.sub('[EMAIL REDACTED]', sanitized_arg)
                                elif pattern_name == 'api_key':
                                    sanitized_arg = pattern.sub(r'\1: [API KEY REDACTED]', sanitized_arg)
                                elif pattern_name == 'openai_key':
                                    sanitized_arg = pattern.sub(r'\1[API KEY REDACTED]\3', sanitized_arg)
                                elif pattern_name == 'api_key_assign':
                                    sanitized_arg = pattern.sub(r'\1[API KEY REDACTED]\3', sanitized_arg)
                                elif pattern_name == 'bearer_token':
                                    sanitized_arg = pattern.sub(r'Bearer [TOKEN REDACTED]', sanitized_arg)
                                elif pattern_name == 'query_content':
                                    sanitized_arg = pattern.sub(r'\1[QUERY CONTENT REDACTED]\3', sanitized_arg)
                                elif pattern_name == 'json_query':
                                    sanitized_arg = pattern.sub(r'\1[QUERY CONTENT REDACTED]\3', sanitized_arg)
                                elif pattern_name == 'form_query':
                                    sanitized_arg = pattern.sub(r'\1[QUERY CONTENT REDACTED]\3', sanitized_arg)
                                elif pattern_name == 'url_query':
                                    sanitized_arg = pattern.sub(r'\1query=[QUERY CONTENT REDACTED]\3', sanitized_arg)
                                elif pattern_name == 'dict_query':
                                    sanitized_arg = pattern.sub(r'\1[QUERY CONTENT REDACTED]\3', sanitized_arg)
                                elif pattern_name == 'f_string_query':
                                    sanitized_arg = pattern.sub(r'\1[QUERY CONTENT REDACTED]\3', sanitized_arg)
                                elif pattern_name == 'log_query':
                                    sanitized_arg = pattern.sub(r'\1[QUERY CONTENT REDACTED]\3', sanitized_arg)
                                elif pattern_name == 'pdf_content':
                                    sanitized_arg = pattern.sub('[PDF CONTENT REDACTED]', sanitized_arg)
                                elif pattern_name == 'sk_api_keys':
                                    sanitized_arg = pattern.sub(r'[API KEY REDACTED]', sanitized_arg)
                                elif pattern_name == 'openai_p_keys':
                                    sanitized_arg = pattern.sub(r'[API KEY REDACTED]', sanitized_arg)
                                elif pattern_name == 'env_var_api_key':
                                    sanitized_arg = pattern.sub(r'\1=[API KEY REDACTED]', sanitized_arg)
                                elif pattern_name == 'x_api_key':
                                    sanitized_arg = pattern.sub(r'\1: [API KEY REDACTED]', sanitized_arg)
                            sanitized_args.append(sanitized_arg)
                        else:
                            sanitized_args.append(arg)
                    record.args = tuple(sanitized_args)
        except Exception:
            # If any error occurs during filtering, allow the log message through unchanged
            # This ensures we don't block critical logging due to filter issues
            pass
            
        return True


def add_privacy_filter_to_logger(logger: Optional[Union[str, logging.Logger]] = None) -> logging.Logger:
    """
    Add a privacy filter to a logger to sanitize sensitive information.
    
    Args:
        logger: Logger instance or name of logger to add filter to.
               If None, the root logger will be used.
    
    Returns:
        The logger that was modified
    """
    # Get the logger to modify
    if logger is None:
        target_logger = logging.getLogger()
    elif isinstance(logger, str):
        target_logger = logging.getLogger(logger)
    else:
        target_logger = logger
    
    # Create and add the filter
    privacy_filter = PrivacyLogFilter()
    target_logger.addFilter(privacy_filter)
    
    return target_logger