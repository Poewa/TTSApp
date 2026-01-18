"""
User authentication module using SQLite for persistent storage.
"""
import sqlite3
import logging
import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# Configure logging
logger = logging.getLogger(__name__)

# Use data directory for persistent storage
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_FILE = DATA_DIR / "users.db"

class User(UserMixin):
    """User class for Flask-Login"""
    def __init__(self, id: str, username: str, password_hash: Optional[str] = None, 
                 email: Optional[str] = None, is_azure_ad: bool = False):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.is_azure_ad = is_azure_ad

    def check_password(self, password: str) -> bool:
        """Verify password against hash"""
        if self.is_azure_ad:
            return False  # Azure AD users don't have local passwords
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

def get_db_connection() -> sqlite3.Connection:
    """Establish and return a database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database schema"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                email TEXT,
                is_azure_ad BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully at %s", DB_FILE)
    except Exception as e:
        logger.error("Failed to initialize database: %s", e)

# Initialize DB on module load
init_db()

def get_user(user_id: str) -> Optional[User]:
    """Get user by ID"""
    try:
        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()

        if user_data:
            return User(
                str(user_data['id']),
                user_data['username'],
                user_data['password_hash'],
                user_data['email'],
                bool(user_data['is_azure_ad'])
            )
    except Exception as e:
        logger.error("Error retrieving user by ID %s: %s", user_id, e)
    return None

def get_user_by_username(username: str) -> Optional[User]:
    """Get user by username"""
    try:
        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user_data:
            return User(
                str(user_data['id']),
                user_data['username'],
                user_data['password_hash'],
                user_data['email'],
                bool(user_data['is_azure_ad'])
            )
    except Exception as e:
        logger.error("Error retrieving user by username %s: %s", username, e)
    return None

def create_user(username: str, password: str) -> Tuple[Optional[User], Optional[str]]:
    """Create a new user"""
    try:
        conn = get_db_connection()
        
        # Check if username already exists
        if conn.execute('SELECT 1 FROM users WHERE username = ?', (username,)).fetchone():
            conn.close()
            return None, "Username already exists"

        password_hash = generate_password_hash(password)
        
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO users (username, password_hash, is_azure_ad) VALUES (?, ?, ?)',
            (username, password_hash, False)
        )
        user_id = cur.lastrowid
        conn.commit()
        conn.close()

        return User(str(user_id), username, password_hash), None

    except Exception as e:
        logger.error("Error creating user %s: %s", username, e)
        return None, "An error occurred during registration"

def create_azure_ad_user(email: str, username: str) -> Tuple[Optional[User], Optional[str]]:
    """Create or update an Azure AD user"""
    try:
        conn = get_db_connection()
        
        # Check if user already exists by email
        existing_user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if existing_user:
            conn.close()
            return User(
                str(existing_user['id']),
                existing_user['username'],
                None,
                email,
                True
            ), None

        # Create new Azure AD user
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO users (username, email, is_azure_ad) VALUES (?, ?, ?)',
            (username, email, True)
        )
        user_id = cur.lastrowid
        conn.commit()
        conn.close()

        return User(str(user_id), username, None, email, True), None

    except Exception as e:
        logger.error("Error creating Azure AD user %s: %s", email, e)
        return None, "An error occurred during Azure AD login"