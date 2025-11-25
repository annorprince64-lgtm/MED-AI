import sqlite3
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'users.db')

def init_db():
    """Initialize the database with users table"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")

def create_user(username, email, password):
    """Create a new user"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30)
        cursor = conn.cursor()
        
        # Hash the password
        password_hash = generate_password_hash(password)
        
        cursor.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return {
            'success': True,
            'user': {
                'id': user_id,
                'username': username,
                'email': email
            }
        }
    except sqlite3.IntegrityError as e:
        if 'username' in str(e):
            return {'success': False, 'error': 'Username already exists'}
        elif 'email' in str(e):
            return {'success': False, 'error': 'Email already exists'}
        else:
            return {'success': False, 'error': 'User creation failed'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def verify_user(email, password):
    """Verify user credentials"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, username, email, password_hash FROM users WHERE email = ?',
            (email,)
        )
        
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            return {
                'success': True,
                'user': {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2]
                }
            }
        else:
            return {'success': False, 'error': 'Invalid email or password'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_user_by_id(user_id):
    """Get user by ID"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=30)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, username, email FROM users WHERE id = ?',
            (user_id,)
        )
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2]
            }
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

# Initialize database only if run directly or explicitly called
if __name__ == '__main__':
    init_db()
