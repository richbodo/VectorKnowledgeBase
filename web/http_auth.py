"""
Simple HTTP Basic Authentication for Flask routes.
This provides a more reliable alternative to Replit Auth when needed.
"""

import os
from functools import wraps
from flask import request, Response, session

# Environment variable for the password, with a default fallback for development
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "changeme123"  # Default password - CHANGE THIS in production!

# Hard-coded credentials for production deployment - this ensures authentication works even if
# environment variables aren't properly loaded in the Replit Deployment environment
# These should match the values set in the Replit Secrets
PROD_USERNAME = "snhuser"
PROD_PASSWORD = "snhpass"

def get_auth_credentials():
    """
    Get authentication credentials from environment variables or use deployment-safe defaults
    
    This function has special handling for Replit Deployments, where environment variables
    from Secrets might not be properly loaded.
    """
    # Check if we're in deployment mode
    is_deployment = bool(os.environ.get("REPL_DEPLOYMENT", False))
    
    import logging
    logger = logging.getLogger(__name__)
    
    # Try to get credentials from environment
    env_username = os.environ.get("BASIC_AUTH_USERNAME")
    env_password = os.environ.get("BASIC_AUTH_PASSWORD")
    
    # Log what we're using (without revealing actual values)
    if is_deployment:
        logger.info(f"Running in deployment mode, using production-safe auth method")
        if env_username and env_password:
            logger.info("Using environment variables for authentication")
            return env_username, env_password
        else:
            logger.info("Environment variables not available in deployment, using hard-coded production credentials")
            return PROD_USERNAME, PROD_PASSWORD
    else:
        # In development, prefer environment variables with fallback to defaults
        username = env_username or DEFAULT_USERNAME
        password = env_password or DEFAULT_PASSWORD
        logger.info(f"Using development authentication mode")
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
        
        # Log authentication header presence
        auth_header = request.headers.get('Authorization', None)
        has_auth_header = auth_header is not None
        logger.info(f"Authorization header present: {has_auth_header}")
        
        # Log environment variables presence (without revealing values)
        has_username_env = bool(os.environ.get("BASIC_AUTH_USERNAME"))
        has_password_env = bool(os.environ.get("BASIC_AUTH_PASSWORD"))
        logger.info(f"Environment variables - Username present: {has_username_env}, Password present: {has_password_env}")
        
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