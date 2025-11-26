from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import hashlib
import secrets
import os
import sys

# Force UTF-8 encoding for stdout to handle Twi characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = Flask(__name__)
# Enable CORS for all origins
CORS(app)

# ============================================
# DATABASE FUNCTIONS
# ============================================

def get_db_connection():
    """Create and return a database connection"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, 'users.db')
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with users table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
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
                "name": updated_user['username'],
                "email": updated_user['email']
            }
        }
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return {"success": False, "error": str(e)}

# ============================================
# AI SERVICE (SIMPLIFIED VERSION)
# ============================================

class AIService:
    def __init__(self):
        self.api_key = os.environ.get('GROQ_API_KEY')
    
    def analyze_text(self, text):
        """Simple AI analysis - replace with your actual AI service"""
        try:
            # This is a placeholder - replace with your actual AI logic
            return {
                "response": f"I received your message: '{text}'. This is a placeholder response.",
                "translation": "Translation placeholder",
                "is_medical": False,
                "drug_recommendation": None,
                "disclaimer": "This is a test response. Real AI integration needed."
            }
        except Exception as e:
            return {
                "error": str(e),
                "response": "Sorry, I encountered an error processing your request.",
                "translation": "Error",
                "is_medical": False
            }

# Initialize AI service
ai_service = AIService()

# ============================================
# FLASK ROUTES
# ============================================

@app.route('/')
def home():
    return jsonify({
        "message": "MED AI Backend is running!",
        "status": "active",
        "endpoints": {
            "analyze": "/api/analyze (POST)",
            "register": "/api/register (POST)",
            "login": "/api/login (POST)",
            "update-profile": "/api/update-profile (POST)",
            "test-db": "/api/test-db (GET)"
        }
    })

@app.route('/api/test-db', methods=['GET'])
def test_db():
    """Test database connection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            cursor.execute("SELECT COUNT(*) as count FROM users")
            user_count = cursor.fetchone()['count']
            conn.close()
            return jsonify({
                "success": True,
                "message": "Database is working!",
                "user_count": user_count
            })
        else:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Users table doesn't exist"
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'email' not in data or 'password' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required fields (username, email, password)"
            }), 400
        
        result = create_user(data['username'], data['email'], data['password'])
        
        if result['success']:
            return jsonify({
                "success": True,
                "message": "Registration successful!",
                "user": result['user']
            }), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login a user"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({
                "success": False,
                "error": "Missing email or password"
            }), 400
        
        result = verify_user(data['email'], data['password'])
        
        if result['success']:
            return jsonify({
                "success": True,
                "message": "Login successful!",
                "user": result['user']
            }), 200
        else:
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/update-profile', methods=['POST'])
def update_profile():
    """Update user profile using email to identify user"""
    try:
        data = request.get_json()
        print(f"📧 Update profile request received for email: {data.get('originalEmail')}")
        
        if not data or 'originalEmail' not in data:
            return jsonify({
                "success": False,
                "error": "Need to know which user to update (originalEmail required)"
            }), 400
        
        # Call database function to update user
        result = update_user_profile(
            original_email=data['originalEmail'],
            name=data.get('name'),
            new_email=data.get('newEmail'),
            current_password=data.get('currentPassword'),
            new_password=data.get('newPassword')
        )
        
        if result['success']:
            return jsonify({
                "success": True,
                "message": "Profile updated successfully!",
                "user": result['user']
            }), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"❌ Error in update_profile: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    """AI analysis endpoint"""
    print("--- Incoming Request to /api/analyze ---")
    try:
        data = request.get_json()
        print(f"Request received with {len(data.get('text', ''))} characters")
        
        if not data or 'text' not in data:
            print("Error: Missing 'text' in request body")
            return jsonify({
                "error": "Missing 'text' in request body",
                "translation": "Invalid request",
                "response": "Please provide text to analyze",
                "is_medical": False
            }), 400
        
        text = data['text']
        print(f"Processing text (length: {len(text)})")
        
        # Use AI service to process the text
        result = ai_service.analyze_text(text)
        
        print(f"Analysis complete, returning result")
        return jsonify(result)
        
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR in analyze_text")
        print(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "translation": "Server error",
            "response": "An error occurred while processing your request",
            "is_medical": False,
            "details": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "MED AI Backend"})

# ============================================
# INITIALIZATION
# ============================================

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting MED AI Backend on port {port}...")
    print(f"📊 Database: users.db")
    print(f"🔑 API Key configured: {'Yes' if ai_service.api_key else 'No'}")
    print(f"🌐 CORS: Enabled for all origins")
    print("✅ Backend ready!")
    
    app.run(debug=True, host='0.0.0.0', port=port)
