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

def get_auth_credentials():
    """Get authentication credentials from environment variables or use defaults"""
    username = os.environ.get("BASIC_AUTH_USERNAME", DEFAULT_USERNAME)
    password = os.environ.get("BASIC_AUTH_PASSWORD", DEFAULT_PASSWORD)
    return username, password

def check_auth(username, password):
    """Check if the username and password match the expected credentials"""
    expected_username, expected_password = get_auth_credentials()
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
    return session.get('authenticated', False)

def set_session_auth(authenticated=True):
    """Set session authentication state"""
    session['authenticated'] = authenticated

def http_auth_required(f):
    """Decorator for routes that require HTTP Basic Authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # First check if already authenticated in session to avoid asking
        # for credentials on every request
        if session_authenticated():
            return f(*args, **kwargs)
            
        # Otherwise check HTTP authentication
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
            
        # If authentication successful, store in session
        set_session_auth()
        return f(*args, **kwargs)
    return decorated