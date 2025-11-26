import sqlite3
import hashlib
import secrets
import os

def get_db_connection():
    """Create and return a database connection"""
    # Get the directory where this script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, 'users.db')
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def init_db():
    """Initialize the database with users table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

def hash_password(password):
    """Hash a password for storing."""
    salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('ascii'), 100000)
    pwdhash = pwdhash.hex()
    return f"{salt}${pwdhash}"

def verify_password(provided_password, stored_password):
    """Verify a stored password against one provided by user"""
    try:
        salt, stored_hash = stored_password.split('$')
        pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt.encode('ascii'), 100000)
        pwdhash = pwdhash.hex()
        return pwdhash == stored_hash
    except:
        return False

def create_user(username, email, password):
    """Create a new user in the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return {"success": False, "error": "User already exists with this email"}
        
        # Hash the password
        password_hash = hash_password(password)
        
        # Insert new user
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        
        conn.commit()
        
        # Get the newly created user
        cursor.execute("SELECT id, username, email, created_at FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        conn.close()
        
        return {
            "success": True,
            "user": {
                "id": user['id'],
                "name": user['username'],
                "email": user['email'],
                "created_at": user['created_at']
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def verify_user(email, password):
    """Verify user credentials"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Find user by email
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Verify password
        if verify_password(password, user['password_hash']):
            return {
                "success": True,
                "user": {
                    "id": user['id'],
                    "name": user['username'],
                    "email": user['email'],
                    "created_at": user['created_at']
                }
            }
        else:
            return {"success": False, "error": "Invalid password"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_user_profile(original_email, name=None, new_email=None, current_password=None, new_password=None):
    """
    Update user profile information using original email to identify user
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print(f"🔍 Looking for user with email: {original_email}")
        
        # Get the current user by original email
        cursor.execute("SELECT * FROM users WHERE email = ?", (original_email,))
        user = cursor.fetchone()
        
        if not user:
            print("❌ User not found")
            return {"success": False, "error": "User not found"}
        
        print(f"✅ User found: {user['username']}")
        
        # If changing password, verify current password
        if new_password:
            print("🔐 Password change requested")
            if not current_password:
                return {"success": False, "error": "Current password is required to change password"}
            
            # Verify current password
            if not verify_password(current_password, user['password_hash']):
                print("❌ Current password incorrect")
                return {"success": False, "error": "Current password is incorrect"}
            
            # Hash new password
            new_password_hash = hash_password(new_password)
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
        cursor.execute("SELECT id, username, email, created_at FROM users WHERE email = ?", (final_email,))
        updated_user = cursor.fetchone()
        
        conn.close()
        
        print(f"🎉 Profile update successful for: {updated_user['username']}")
        
        return {
            "success": True,
            "user": {
                "id": updated_user['id'],
                "name": updated_user['username'],  # Return as 'name' for frontend
                "email": updated_user['email']
            }
        }
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return {"success": False, "error": str(e)}

# Initialize the database when this module is imported
init_db()
print("✅ Database module loaded successfully")
