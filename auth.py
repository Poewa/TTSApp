"""
Simple user authentication module with JSON-based user storage.
For production, consider using a proper database like PostgreSQL or MySQL.
"""
import json
import os
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# Use data directory for persistent storage
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"

class User(UserMixin):
    """User class for Flask-Login"""
    def __init__(self, id, username, password_hash=None, email=None, is_azure_ad=False):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.is_azure_ad = is_azure_ad

    def check_password(self, password):
        """Verify password against hash"""
        if self.is_azure_ad:
            return False  # Azure AD users don't have local passwords
        return check_password_hash(self.password_hash, password)

def init_users_storage():
    """Initialize users storage file"""
    if not USERS_FILE.exists():
        try:
            with open(USERS_FILE, 'w') as f:
                json.dump({}, f)
        except Exception as e:
            print(f"⚠️  Warning: Could not create users file: {e}")
            print(f"   User data will not persist between restarts")

def load_users():
    """Load users from JSON file"""
    init_users_storage()
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users_data):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users_data, f, indent=2)

def get_user(user_id):
    """Get user by ID"""
    users = load_users()
    user_data = users.get(str(user_id))
    if user_data:
        return User(
            user_id,
            user_data['username'],
            user_data.get('password_hash'),
            user_data.get('email'),
            user_data.get('is_azure_ad', False)
        )
    return None

def get_user_by_username(username):
    """Get user by username"""
    users = load_users()
    for user_id, user_data in users.items():
        if user_data['username'] == username:
            return User(
                user_id,
                user_data['username'],
                user_data.get('password_hash'),
                user_data.get('email'),
                user_data.get('is_azure_ad', False)
            )
    return None

def create_user(username, password):
    """Create a new user"""
    users = load_users()

    # Check if username already exists
    for user_data in users.values():
        if user_data['username'] == username:
            return None, "Username already exists"

    # Generate new user ID
    user_id = str(len(users) + 1)

    # Create user
    users[user_id] = {
        'username': username,
        'password_hash': generate_password_hash(password)
    }

    save_users(users)
    return User(user_id, username, users[user_id]['password_hash']), None

def create_azure_ad_user(email, username):
    """Create or update an Azure AD user"""
    users = load_users()

    # Check if user already exists by email
    for user_id, user_data in users.items():
        if user_data.get('email') == email:
            # Update existing user
            return User(
                user_id,
                user_data['username'],
                None,
                email,
                True
            ), None

    # Create new Azure AD user
    user_id = str(len(users) + 1)
    users[user_id] = {
        'username': username,
        'email': email,
        'is_azure_ad': True
    }

    save_users(users)
    return User(user_id, username, None, email, True), None

def init_demo_user():
    """Create a demo user if no users exist"""
    users = load_users()
    if not users:
        print("📝 Creating demo user: username='demo', password='demo123'")
        create_user('demo', 'demo123')
