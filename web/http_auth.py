"""
Simple HTTP Basic Authentication for Flask routes.
This provides a more reliable alternative to Replit Auth when needed.
"""

import os
from functools import wraps
from flask import request, Response, session

# Default credentials for development environments only
# These defaults should NEVER be used in production!
# For production deployments, use Replit Secrets to set:
#   - U: A secure username (Short form of BASIC_AUTH_USERNAME)
#   - P: A strong password (Short form of BASIC_AUTH_PASSWORD)
#   - SESSION_SECRET: A random string for session security
# 
# Note: We use short names like "U" and "P" because they seem to be more reliably 
# accessible in production deployments than longer variable names.
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "changeme123"

def get_auth_credentials():
    """
    Get authentication credentials from environment variables or use deployment-safe defaults
    
    This function has special handling for Replit Deployments, where environment variables
    from Secrets might not be properly loaded.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Default credentials - use these in development only!
    # In production, use environment variables set in Replit Secrets
    # If all else fails, we'll use these specific credentials that match what you've set
    # in the App Secrets: U=snhuser and P=snhpass
    FALLBACK_USERNAME = "snhuser"
    FALLBACK_PASSWORD = "snhpass"
    
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
    
    # Test reading the TEST_ENV_VAR - this is a special variable set for debugging
    # Using multiple methods to see which one works in production
    logger.info("=== TEST_ENV_VAR Access Testing (HTTP AUTH) ===")
    
    # Standard method
    test_var = os.environ.get("TEST_ENV_VAR")
    logger.info(f"TEST_ENV_VAR value: '{test_var}'")
    
    # Using direct dictionary access
    try:
        test_var_direct = os.environ["TEST_ENV_VAR"] if "TEST_ENV_VAR" in os.environ else "not_found_direct"
        logger.info(f"TEST_ENV_VAR using direct access: '{test_var_direct}'")
    except Exception as e:
        logger.warning(f"Error accessing TEST_ENV_VAR directly: {str(e)}")
    
    # Try multiple approaches to get credentials - prioritizing short names first
    # Approach 1: Short variable names (more reliable in production)
    username = os.environ.get("U")
    if username:
        logger.info("Found username in U variable")
    
    password = os.environ.get("P")
    if password:
        logger.info("Found password in P variable")
    
    # Approach 2: Original longer variable names
    if not username:
        username = os.environ.get("BASIC_AUTH_USERNAME")
        if username:
            logger.info("Found username in BASIC_AUTH_USERNAME variable")
    
    if not password:
        password = os.environ.get("BASIC_AUTH_PASSWORD")
        if password:
            logger.info("Found password in BASIC_AUTH_PASSWORD variable")
    
    # Approach 3: Try alternate variable names (in case of renaming)
    if not username:
        username = os.environ.get("AUTH_USER")
        if username:
            logger.info("Found username in AUTH_USER variable")
    
    if not password:
        password = os.environ.get("AUTH_PASS")
        if password:
            logger.info("Found password in AUTH_PASS variable")
    
    # Approach 4: Try with prefix
    if not username:
        username = os.environ.get("SECRETS_BASIC_AUTH_USERNAME")
        if username:
            logger.info("Found username in SECRETS_BASIC_AUTH_USERNAME variable")
    
    if not password:
        password = os.environ.get("SECRETS_BASIC_AUTH_PASSWORD")
        if password:
            logger.info("Found password in SECRETS_BASIC_AUTH_PASSWORD variable")
    
    # More detailed diagnostic info 
    logger.info(f"U exists: {os.environ.get('U') is not None}")
    logger.info(f"P exists: {os.environ.get('P') is not None}")
    logger.info(f"BASIC_AUTH_USERNAME exists: {os.environ.get('BASIC_AUTH_USERNAME') is not None}")
    logger.info(f"BASIC_AUTH_PASSWORD exists: {os.environ.get('BASIC_AUTH_PASSWORD') is not None}")
    
    # Check if we're missing credentials after all attempts
    if not username or not password:
        logger.warning("Authentication credentials not found in any environment variables")
        
        # In production, use the specific fallback that matches our App Secrets
        if is_deployment:
            logger.error("CRITICAL: Authentication credentials missing in production environment")
            logger.error("Using hardcoded production fallback credentials that match App Secrets")
            username = FALLBACK_USERNAME
            password = FALLBACK_PASSWORD
            logger.warning("Using hardcoded fallback credentials - App Secret issue detected")
        else:
            # Use defaults as fallback - this is only secure in development
            username = DEFAULT_USERNAME
            password = DEFAULT_PASSWORD
            logger.info("Using default development credentials")
        
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
        has_u_env = bool(os.environ.get("U"))
        has_p_env = bool(os.environ.get("P"))
        logger.info(f"Environment variables - Username present: {has_username_env or has_u_env}, Password present: {has_password_env or has_p_env}")
        logger.info(f"Short env vars - U present: {has_u_env}, P present: {has_p_env}")
        
        # Enhanced diagnostics for env vars
        if not (has_username_env or has_u_env) or not (has_password_env or has_p_env):
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