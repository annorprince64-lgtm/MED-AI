from flask import Flask, request, jsonify
from flask_cors import CORS
from ai_service import ai_service
import database
import os
import sys

# Force UTF-8 encoding (for Twi and special characters)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

app = Flask(__name__)
CORS(app)

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
            "chats": "/api/chats/save , /api/chats/load"
        }
    })

# -----------------------------
# AUTHENTICATION
# -----------------------------
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    result = database.create_user(
        data.get('username'),
        data.get('email'),
        data.get('password')
    )
    return jsonify(result), (201 if result.get('success') else 400)


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    result = database.verify_user(
        data.get('email'),
        data.get('password')
    )
    return jsonify(result), (200 if result.get('success') else 401)


@app.route('/api/update-profile', methods=['POST'])
def update_profile():
    data = request.get_json()
    if not data or 'originalEmail' not in data:
        return jsonify({"success": False, "error": "originalEmail required"}), 400

    result = database.update_user_profile(
        original_email=data['originalEmail'],
        name=data.get('name'),
        new_email=data.get('newEmail'),
        current_password=data.get('currentPassword'),
        new_password=data.get('newPassword')
    )
    return jsonify(result), (200 if result.get('success') else 400)


# -----------------------------
# AI ANALYSIS (STAGE-AWARE)
# -----------------------------
@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    """
    This endpoint supports MULTI-STAGE AI responses.
    Frontend must read `stage` and act accordingly.
    """
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                "stage": "analysis",
                "response": "No input text provided",
                "questions": None,
                "is_medical": False
            }), 400

        user_text = data['text']

        # OPTIONAL CONTEXT SUPPORT
        # Frontend may send previous conversation summary
        context = data.get('context')
        if context:
            user_text = f"Conversation so far:\n{context}\n\nNew message:\n{user_text}"

        result = ai_service.analyze_text(user_text)

        # DEBUG LOG (remove in production)
        print("AI RESULT:", result)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "stage": "analysis",
            "response": "Server error occurred",
            "questions": None,
            "is_medical": False,
            "error": str(e)
        }), 500


# -----------------------------
# CHAT STORAGE (OPTIONAL)
# -----------------------------
@app.route('/api/chats/save', methods=['POST'])
def save_chat():
    try:
        data = request.get_json()
        result = database.save_user_chat(data['user_id'], data['chat_data'])
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/chats/load', methods=['GET'])
def load_chats():
    try:
        user_id = request.args.get('user_id')
        chats = database.get_user_chats(user_id)
        return jsonify({"success": True, "chats": chats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f" Backend running on port {port}")
    print(f"AI configured: {'YES' if ai_service.client else 'NO'}")
    app.run(debug=True, host='0.0.0.0', port=port)
