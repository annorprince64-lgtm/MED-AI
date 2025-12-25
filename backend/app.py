from flask import Flask, request, jsonify
from flask_cors import CORS
from ai_service import ai_service
import database
import os
import sys

# Force UTF-8 encoding for stdout to handle Twi characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = Flask(__name__)
# Enable CORS for all origins (you can restrict this in production)
CORS(app)  # Allow all origins to support file:// access

@app.route('/')
def home():
    return jsonify({
        "message": "MED AI Backend is running!",
        "status": "active",
        "endpoints": {
            "analyze": "/api/analyze (POST)",
            "register": "/api/register (POST)",
            "login": "/api/login (POST)",
            "update-profile": "/api/update-profile (POST)"  # Added this
        }
    })

# Authentication Endpoints
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

        result = database.create_user(data['username'], data['email'], data['password'])

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

        result = database.verify_user(data['email'], data['password'])

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

# ADD THIS NEW ENDPOINT - Profile Update
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
        result = database.update_user_profile(
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

# Existing AI Endpoint (unchanged)
@app.route('/api/analyze', methods=['POST'])
def analyze_text():
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

        # Use your AIService to process the text
        result = ai_service.analyze_text(text)

        print(f"Analysis complete, returning result")
        return jsonify(result)

    except Exception as e:
        import traceback
        print(f"An error occured when processing")
        print(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "translation": "Server error",
            "response": "An error occurred while processing your request",
            "is_medical": False,
            "details": str(e)
        }), 500
# Add these endpoints after your existing endpoints

@app.route('/api/chats/save', methods=['POST'])
def save_chat():
    """Save chat to cloud database"""
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data or 'chat_data' not in data:
            return jsonify({
                "success": False,
                "error": "Missing user_id or chat_data"
            }), 400
        
        # Call database function
        result = database.save_chat_to_cloud(
            user_id=data['user_id'],
            chat_data=data['chat_data']
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in save_chat: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/chats/load', methods=['GET'])
def load_chats():
    """Load user chats from cloud"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Missing user_id parameter"
            }), 400
        
        # Get chats from cloud
        chats = database.get_user_chats_from_cloud(user_id)
        
        return jsonify({
            "success": True,
            "chats": chats
        })
        
    except Exception as e:
        print(f"❌ Error in load_chats: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/chats/delete', methods=['POST'])
def delete_chat():
    """Delete chat from cloud"""
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data or 'chat_id' not in data:
            return jsonify({
                "success": False,
                "error": "Missing user_id or chat_id"
            }), 400
        
        # Delete from cloud
        result = database.delete_chat_from_cloud(
            user_id=data['user_id'],
            chat_id=data['chat_id']
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in delete_chat: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/chats/load', methods=['GET'])
def load_chats():
    """Load user chats from cloud"""
    try:
        user_id = request.args.get('user_id')
        chats = database.get_user_chats(user_id)
        return jsonify({"success": True, "chats": chats})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "MED AI Backend"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Grok AI Backend on port {port}...")
    print(f"API Key configured: {'Yes' if ai_service.api_key else 'No'}")
    app.run(debug=True, host='0.0.0.0', port=port)

