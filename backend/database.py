import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'users.db')

def init_db():
    """Initialize the database with users table"""
    conn = sqlite3.connect(DATABASE_PATH)
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

def create_user(username, email, password):
    """Create a new user"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
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
        conn = sqlite3.connect(DATABASE_PATH)
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
        conn = sqlite3.connect(DATABASE_PATH)
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

# ADD THIS NEW FUNCTION - Profile Update
def update_user_profile(original_email, name=None, new_email=None, current_password=None, new_password=None):
    """
    Update user profile information using original email to identify user
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print(f"🔍 Looking for user with email: {original_email}")
        
        # Get the current user by original email
        cursor.execute(
            'SELECT id, username, email, password_hash FROM users WHERE email = ?',
            (original_email,)
        )
        user = cursor.fetchone()
        
        if not user:
            print("❌ User not found")
            return {"success": False, "error": "User not found"}
        
        print(f"✅ User found: {user[1]}")
        
        # If changing password, verify current password
        if new_password:
            print("🔐 Password change requested")
            if not current_password:
                return {"success": False, "error": "Current password is required to change password"}
            
            # Verify current password
            if not check_password_hash(user[3], current_password):
                print("❌ Current password incorrect")
                return {"success": False, "error": "Current password is incorrect"}
            
            # Hash new password
            new_password_hash = generate_password_hash(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE email = ?",
                (new_password_hash, original_email)
            )
            print("✅ Password updated")
        
        # Update name if provided
        if name:
            print(f"📝 Updating name to: {name}")
            cursor.execute(
                "UPDATE users SET username = ? WHERE email = ?",
                (name, original_email)
            )
        
        # Update email if provided
        final_email = original_email  # Start with original email
        if new_email and new_email != original_email:
            print(f"📧 Changing email from {original_email} to {new_email}")
            
            # Check if new email already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (new_email,))
            if cursor.fetchone():
                return {"success": False, "error": "Email already exists"}
            
            cursor.execute(
                "UPDATE users SET email = ? WHERE email = ?",
                (new_email, original_email)
            )
            final_email = new_email  # Use new email for the response
            print("✅ Email updated")
        
        conn.commit()
        
        # Get updated user data
        cursor.execute(
            "SELECT id, username, email FROM users WHERE email = ?", 
            (final_email,)
        )
        updated_user = cursor.fetchone()
        
        conn.close()
        
        print(f"🎉 Profile update successful for: {updated_user[1]}")
        
        return {
            "success": True,
            "user": {
                "id": updated_user[0],
                "username": updated_user[1],
                "email": updated_user[2]
            }
        }
        
    except sqlite3.IntegrityError as e:
        if 'username' in str(e):
            return {"success": False, "error": "Username already exists"}
        elif 'email' in str(e):
            return {"success": False, "error": "Email already exists"}
        else:
            return {"success": False, "error": "Database integrity error"}
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return {"success": False, "error": str(e)}
def update_user_profile(original_email, name=None, new_email=None, current_password=None, new_password=None):
    """
    Update user profile - SIMPLE VERSION
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print(f"Updating profile for: {original_email}")
        
        # Get the user
        cursor.execute('SELECT * FROM users WHERE email = ?', (original_email,))
        user = cursor.fetchone()
        
        if not user:
            return {"success": False, "error": "User not found"}
        
        # If changing password, check current password
        if new_password:
            if not current_password:
                return {"success": False, "error": "Current password required"}
            
            if not check_password_hash(user[3], current_password):
                return {"success": False, "error": "Current password is wrong"}
            
            # Update password
            new_hash = generate_password_hash(new_password)
            cursor.execute('UPDATE users SET password_hash = ? WHERE email = ?', (new_hash, original_email))
        
        # Update name if provided
        if name:
            cursor.execute('UPDATE users SET username = ? WHERE email = ?', (name, original_email))
        
        # Update email if provided
        final_email = original_email
        if new_email and new_email != original_email:
            cursor.execute('UPDATE users SET email = ? WHERE email = ?', (new_email, original_email))
            final_email = new_email
        
        conn.commit()
        
        # Get updated user
        cursor.execute('SELECT id, username, email FROM users WHERE email = ?', (final_email,))
        updated = cursor.fetchone()
        
        conn.close()
        
        return {
            "success": True,
            "user": {
                "id": updated[0],
                "username": updated[1],
                "email": updated[2]
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
def save_user_chat(user_id, chat_data):
    """Save user chat to cloud database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Create chats table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id TEXT NOT NULL,
                chat_data TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Save each chat
        for chat_id, chat in chat_data.items():
            cursor.execute('''
                INSERT OR REPLACE INTO user_chats (user_id, chat_id, chat_data)
                VALUES (?, ?, ?)
            ''', (user_id, chat_id, json.dumps(chat)))
        
        conn.commit()
        conn.close()
        return {"success": True}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_user_chats(user_id):
    """Get all chats for a user"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT chat_id, chat_data FROM user_chats WHERE user_id = ?',
            (user_id,)
        )
        
        chats = {}
        for row in cursor.fetchall():
            chats[row[0]] = json.loads(row[1])
        
        conn.close()
        return chats
        
    except Exception as e:
        return {}
# Initialize database when module is imported
init_db()


