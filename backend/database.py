import sqlite3
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash

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
        # Normalize email to lowercase for consistent matching
        email = email.lower().strip()
        username = username.strip()
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print(f"🔍 Creating user: {username} with email: {email}")
        
        # Check if email already exists
        cursor.execute('SELECT id, username FROM users WHERE email = ?', (email,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            print(f"❌ Email already exists: {email} (user: {existing[1]})")
            return {'success': False, 'error': 'Email already registered'}
        
        # Check if username already exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return {'success': False, 'error': 'Username already exists'}
        
        # Hash the password
        password_hash = generate_password_hash(password)
        
        cursor.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        print(f"✅ User created successfully: {username} (id: {user_id})")
        
        return {
            'success': True,
            'user': {
                'id': user_id,
                'username': username,
                'email': email,
                'name': username
            }
        }
    except sqlite3.IntegrityError as e:
        print(f"❌ Database integrity error: {e}")
        return {'success': False, 'error': 'Registration failed - user already exists'}
    except Exception as e:
        print(f"❌ Error in create_user: {e}")
        return {'success': False, 'error': str(e)}

def verify_user(email, password):
    """Verify user credentials"""
    try:
        # Normalize email to lowercase for consistent matching
        email = email.lower().strip()
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print(f"🔍 Looking for user with email: {email}")
        
        cursor.execute(
            'SELECT id, username, email, password_hash FROM users WHERE email = ?',
            (email,)
        )
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            print(f"❌ User not found with email: {email}")
            return {'success': False, 'error': 'No account found with this email. Please check your email or create a new account.'}
        
        print(f"✅ User found: {user[1]} (id: {user[0]})")
        
        # Verify password
        if check_password_hash(user[3], password):
            print(f"✅ Password verified for: {email}")
            return {
                'success': True,
                'user': {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'name': user[1]
                }
            }
        else:
            print(f"❌ Wrong password for: {email}")
            return {'success': False, 'error': 'Incorrect password. Please try again.'}
    except Exception as e:
        print(f"❌ Error in verify_user: {str(e)}")
        return {'success': False, 'error': f'Login error: {str(e)}'}

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

def update_user_profile(original_email, name=None, new_email=None, current_password=None, new_password=None):
    """Update user profile information using original email to identify user"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print(f"🔍 Looking for user with email: {original_email}")
        
        cursor.execute(
            'SELECT id, username, email, password_hash FROM users WHERE email = ?',
            (original_email,)
        )
        user = cursor.fetchone()
        
        if not user:
            print("❌ User not found")
            return {"success": False, "error": "User not found"}
        
        print(f"✅ User found: {user[1]}")
        
        if new_password:
            print("🔐 Password change requested")
            if not current_password:
                return {"success": False, "error": "Current password is required to change password"}
            
            if not check_password_hash(user[3], current_password):
                print("❌ Current password incorrect")
                return {"success": False, "error": "Current password is incorrect"}
            
            new_password_hash = generate_password_hash(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE email = ?",
                (new_password_hash, original_email)
            )
            print("✅ Password updated")
        
        if name:
            print(f"📝 Updating name to: {name}")
            cursor.execute(
                "UPDATE users SET username = ? WHERE email = ?",
                (name, original_email)
            )
        
        final_email = original_email
        if new_email and new_email != original_email:
            print(f"📧 Changing email from {original_email} to {new_email}")
            
            cursor.execute("SELECT id FROM users WHERE email = ?", (new_email,))
            if cursor.fetchone():
                return {"success": False, "error": "Email already exists"}
            
            cursor.execute(
                "UPDATE users SET email = ? WHERE email = ?",
                (new_email, original_email)
            )
            final_email = new_email
            print("✅ Email updated")
        
        conn.commit()
        
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

def save_user_chat(user_id, chat_data):
    """Save user chat to cloud database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
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

def save_chat_to_cloud(user_id, chat_data):
    """Save a complete chat to cloud database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cloud_chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                messages TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_chats 
            ON cloud_chats(user_id, created_at)
        ''')
        
        cursor.execute(
            'SELECT id FROM cloud_chats WHERE user_id = ? AND chat_id = ?',
            (user_id, chat_data.get('id', ''))
        )
        
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE cloud_chats 
                SET title = ?, messages = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (chat_data.get('title', 'Untitled'), json.dumps(chat_data.get('messages', [])), existing[0]))
            print(f"✅ Updated chat {chat_data.get('id')} for user {user_id}")
        else:
            cursor.execute('''
                INSERT INTO cloud_chats (user_id, chat_id, title, messages)
                VALUES (?, ?, ?, ?)
            ''', (user_id, chat_data.get('id', ''), chat_data.get('title', 'Untitled'), json.dumps(chat_data.get('messages', []))))
            print(f"✅ Saved new chat {chat_data.get('id')} for user {user_id}")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Chat saved to cloud"}
        
    except Exception as e:
        print(f"❌ Error saving chat to cloud: {str(e)}")
        return {"success": False, "error": str(e)}

def get_user_chats_from_cloud(user_id):
    """Get all chats for a user from cloud"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cloud_chats'")
        if not cursor.fetchone():
            print("❌ cloud_chats table doesn't exist")
            conn.close()
            return {}
        
        cursor.execute('''
            SELECT chat_id, title, messages, created_at, updated_at 
            FROM cloud_chats 
            WHERE user_id = ? 
            ORDER BY updated_at DESC
        ''', (user_id,))
        
        chats = {}
        rows = cursor.fetchall()
        
        print(f"📊 Database query returned {len(rows)} rows for user {user_id}")
        
        for row in rows:
            chat_id = row[0]
            title = row[1]
            messages_json = row[2]
            created_at = row[3]
            updated_at = row[4]
            
            try:
                messages = json.loads(messages_json) if messages_json else []
                if not isinstance(messages, list):
                    messages = []
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing JSON for chat {chat_id}: {e}")
                messages = []
            
            chats[chat_id] = {
                'id': chat_id,
                'title': title,
                'messages': messages,
                'date': created_at,
                'updated': updated_at
            }
            
            print(f"  ✅ Loaded chat: {chat_id} with {len(messages)} messages")
        
        conn.close()
        print(f"📥 Total loaded {len(chats)} chats from cloud for user {user_id}")
        return chats
        
    except Exception as e:
        print(f"❌ Error loading chats from cloud: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

def delete_chat_from_cloud(user_id, chat_id):
    """Delete a chat from cloud"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            'DELETE FROM cloud_chats WHERE user_id = ? AND chat_id = ?',
            (user_id, chat_id)
        )
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Chat deleted from cloud"}
        
    except Exception as e:
        print(f"❌ Error deleting chat from cloud: {str(e)}")
        return {"success": False, "error": str(e)}

def delete_user_account(email, password):
    """Delete a user account and all associated data"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, password_hash FROM users WHERE email = ?',
            (email,)
        )
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return {"success": False, "error": "User not found"}
        
        user_id = user[0]
        password_hash = user[1]
        
        if not check_password_hash(password_hash, password):
            conn.close()
            return {"success": False, "error": "Incorrect password"}
        
        cursor.execute('DELETE FROM cloud_chats WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM user_chats WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Account deleted for user: {email}")
        return {"success": True, "message": "Account deleted successfully"}
        
    except Exception as e:
        print(f"❌ Error deleting account: {str(e)}")
        return {"success": False, "error": str(e)}

def reset_password(email, new_password):
    """Reset user password (called after email verification)"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return {"success": False, "error": "User not found"}
        
        new_password_hash = generate_password_hash(new_password)
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE email = ?",
            (new_password_hash, email)
        )
        
        conn.commit()
        conn.close()
        
        print(f"✅ Password reset for user: {email}")
        return {"success": True, "message": "Password reset successfully"}
        
    except Exception as e:
        print(f"❌ Error resetting password: {str(e)}")
        return {"success": False, "error": str(e)}

def check_email_exists(email):
    """Check if an email exists in the database"""
    try:
        email = email.lower().strip()
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT username FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            print(f"✅ Email found: {email} (user: {user[0]})")
            return {"success": True, "exists": True, "username": user[0]}
        else:
            print(f"❌ Email not found: {email}")
            return {"success": True, "exists": False}
            
    except Exception as e:
        print(f"❌ Error in check_email_exists: {str(e)}")
        return {"success": False, "error": str(e)}

# Initialize database when module is imported
init_db()
