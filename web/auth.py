import logging
import os
from functools import wraps
from flask import request, redirect, url_for, session, flash
from replit import web as replit_web

logger = logging.getLogger(__name__)

def is_authenticated():
    """Check if user is authenticated using Replit Auth"""
    try:
        # Sometimes this is a method, sometimes a property - handle both cases
        if callable(replit_web.auth.is_authenticated):
            return replit_web.auth.is_authenticated()
        else:
            return replit_web.auth.is_authenticated
    except Exception as e:
        logger.error(f"Error checking authentication: {str(e)}")
        return False

def get_user_info():
    """Get authenticated user information"""
    if not is_authenticated():
        return None
    
    try:
        return {
            'username': replit_web.auth.name(),
            'id': replit_web.auth.id(),
            'profile_image': replit_web.auth.picture()
        }
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        return None

def auth_required(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            # Store the requested URL for redirecting after login
            session['next_url'] = request.url
            flash("Please log in to access this page", "warning")
            return redirect(url_for('web.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_login_url():
    """Get the Replit Auth login URL"""
    try:
        # Check if we have the login_url method or if we need to use the auth_url property
        if hasattr(replit_web.auth, 'login_url') and callable(replit_web.auth.login_url):
            return replit_web.auth.login_url(redirect_url=request.url)
        elif hasattr(replit_web.auth, 'auth_url'):
            # Use the auth_url property which is available in some versions
            return replit_web.auth.auth_url
        else:
            # Last resort, use a hardcoded URL pattern that works with Replit Auth
            repl_slug = os.environ.get("REPL_SLUG", "")
            repl_owner = os.environ.get("REPL_OWNER", "")
            if repl_slug and repl_owner:
                return f"https://replit.com/auth_with_repl_site?domain={repl_slug}.{repl_owner}.repl.co"
            else:
                return request.host_url
    except Exception as e:
        logger.error(f"Error generating login URL: {str(e)}")
        # Return to home page if all else fails
        return "/"

def handle_logout():
    """Clear authentication session"""
    try:
        replit_web.auth.clear()
    except Exception as e:
        logger.error(f"Error logging out: {str(e)}")
    # Clear session data
    session.clear()