"""
Authentication Module for Video Library

Provides secure user authentication with password hashing and session management.
"""

from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
from flask import session, redirect, url_for, request

# Initialize Flask-Login
login_manager = LoginManager()


class User(UserMixin):
    """User class for authentication."""
    
    def __init__(self, user_id, username, password_hash):
        self.id = user_id
        self.username = username
        self.password_hash = password_hash
    
    def check_password(self, password):
        """Verify password against hash."""
        return check_password_hash(self.password_hash, password)


# In-memory user database (for production, use proper database)
# Default credentials - CHANGE THESE in production via environment variables!
USERS = {
    'admin': User(
        user_id='1',
        username=os.environ.get('ADMIN_USERNAME', 'admin'),
        password_hash=generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'changeme123'))
    )
}


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    for user in USERS.values():
        if user.id == user_id:
            return user
    return None


def authenticate_user(username, password):
    """
    Authenticate user with username and password.
    
    Args:
        username: Username string
        password: Password string
    
    Returns:
        User object if authenticated, None otherwise
    """
    user = USERS.get(username)
    if user and user.check_password(password):
        return user
    return None


def create_user(username, password):
    """
    Create a new user (admin function).
    
    Args:
        username: Unique username
        password: Plain text password (will be hashed)
    
    Returns:
        User object
    """
    user_id = str(len(USERS) + 1)
    user = User(
        user_id=user_id,
        username=username,
        password_hash=generate_password_hash(password)
    )
    USERS[username] = user
    return user


def init_auth(app):
    """Initialize authentication for Flask app."""
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.session_protection = 'strong'
    
    # Set secret key from environment or generate one
    app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())
    
    # Session configuration for security
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour


def change_password(username, old_password, new_password):
    """
    Change user password.
    
    Args:
        username: Username
        old_password: Current password
        new_password: New password
    
    Returns:
        bool: True if successful, False otherwise
    """
    user = authenticate_user(username, old_password)
    if user:
        user.password_hash = generate_password_hash(new_password)
        return True
    return False
