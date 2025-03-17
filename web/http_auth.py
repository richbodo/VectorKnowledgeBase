"""
Simple HTTP Basic Authentication for Flask routes.
This provides a more reliable alternative to Replit Auth when needed.
"""

import os
from functools import wraps
from flask import request, Response, session

def get_auth_credentials():
    """
    Get authentication credentials from environment variables
    
    This function retrieves the authentication credentials from Replit Secrets.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Detect if we're in a deployment
    is_deployment = bool(os.environ.get("REPL_DEPLOYMENT", False))
    
    # Enhanced logging for environment variable debugging
    env_keys = sorted(os.environ.keys())
    replit_keys = [k for k in env_keys if k.startswith('REPL_')]
    auth_keys = [k for k in env_keys if 'AUTH' in k]
    logger.info(f"Deployment mode: {is_deployment}")
    logger.info(f"Number of environment variables: {len(env_keys)}")
    logger.info(f"Replit-specific keys: {replit_keys}")
    logger.info(f"Auth-related keys found (names only, not values): {auth_keys}")
    
    username = os.environ.get("BASIC_AUTH_USERNAME")
    if username:
        logger.info("Found username in BASIC_AUTH_USERNAME variable")
    
    password = os.environ.get("BASIC_AUTH_PASSWORD")
    if password:
        logger.info("Found password in BASIC_AUTH_PASSWORD variable")
    
    # More detailed diagnostic info 
    logger.info(f"BASIC_AUTH_USERNAME exists: {os.environ.get('BASIC_AUTH_USERNAME') is not None}")
    logger.info(f"BASIC_AUTH_PASSWORD exists: {os.environ.get('BASIC_AUTH_PASSWORD') is not None}")
    
    # Check if we're missing credentials
    if not username or not password:
        logger.error("Authentication credentials not found in environment variables")
        logger.error("Please ensure BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD are set in Replit Secrets")
        if is_deployment:
            logger.error("CRITICAL: Authentication credentials missing in production environment")
            # We'll return None values which will make auth checks fail
        
    return username, password

def check_auth(username, password):
    """Check if the username and password match the expected credentials"""
    expected_username, expected_password = get_auth_credentials()
    
    # Add detailed logging for authentication debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Auth attempt - Provided username: {username}")
    logger.info(f"Auth check - Expected username: {expected_username}")
    logger.info(f"Auth result - Username match: {username == expected_username}")
    
    # Don't log actual passwords, but log if they match
    logger.info(f"Auth result - Password match: {password == expected_password}")
    
    return username == expected_username and password == expected_password

def authenticate():
    """Send a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def session_authenticated():
    """Check if user is authenticated through session"""
    import logging
    logger = logging.getLogger(__name__)
    
    is_authenticated = session.get('authenticated', False)
    logger.info(f"Session authentication check: {is_authenticated}")
    
    # Log session details (keys only, not values)
    session_keys = list(session.keys()) if session else []
    logger.info(f"Session keys: {session_keys}")
    
    return is_authenticated

def set_session_auth(authenticated=True):
    """Set session authentication state"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        session['authenticated'] = authenticated
        logger.info(f"Session authentication set to: {authenticated}")
        logger.info(f"Session ID: {session.get('_id', 'None')}")
    except Exception as e:
        logger.error(f"Error setting session authentication: {str(e)}")
        # Don't re-raise the exception to avoid breaking authentication process

def http_auth_required(f):
    """Decorator for routes that require HTTP Basic Authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        
        # First check if already authenticated in session to avoid asking
        # for credentials on every request
        if session_authenticated():
            logger.info("Using session-based authentication (already authenticated)")
            return f(*args, **kwargs)
            
        # Otherwise check HTTP authentication
        auth = request.authorization
        
        # Enhanced auth header logging
        auth_header = request.headers.get('Authorization', None)
        has_auth_header = auth_header is not None
        logger.info(f"Authorization header present: {has_auth_header}")
        
        # Try to decode the auth header for debugging (without logging the full credentials)
        if has_auth_header and auth_header.startswith('Basic '):
            try:
                from base64 import b64decode
                auth_part = auth_header.split(' ')[1]
                decoded = b64decode(auth_part).decode('utf-8')
                username_part = decoded.split(':')[0] if ':' in decoded else 'INVALID_FORMAT'
                # Only log username part, never the password
                logger.info(f"Auth header analysis - Decoded username: {username_part}")
                logger.info(f"Auth header analysis - Format valid: {'INVALID_FORMAT' not in username_part}")
            except Exception as e:
                logger.warning(f"Failed to decode auth header: {str(e)}")
        
        # Log environment variables presence (without revealing values)
        has_username_env = bool(os.environ.get("BASIC_AUTH_USERNAME"))
        has_password_env = bool(os.environ.get("BASIC_AUTH_PASSWORD"))
        logger.info(f"Environment variables - Username present: {has_username_env}, Password present: {has_password_env}")
        
        # Enhanced diagnostics for env vars
        if not has_username_env or not has_password_env:
            # Use get_auth_credentials for detailed diagnostics
            get_auth_credentials()
            
        # Check if auth object is present
        if not auth:
            logger.warning("Authentication failed: No auth credentials provided")
            return authenticate()
            
        # Check if credentials match
        if not check_auth(auth.username, auth.password):
            logger.warning(f"Authentication failed: Invalid credentials for username: {auth.username}")
            return authenticate()
            
        # If authentication successful, store in session
        logger.info(f"Authentication successful for username: {auth.username}")
        set_session_auth()
        return f(*args, **kwargs)
    return decorated