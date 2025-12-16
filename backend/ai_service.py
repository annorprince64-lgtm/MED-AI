import os
from groq import Groq
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

class AIService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("WARNING: GROQ_API_KEY not found in .env file.")
        else:
            self.client = Groq(api_key=self.api_key)
            self.model = "llama-3.3-70b-versatile" 
        
        # Dictionary to store conversation history by user/chat ID
        self.conversation_history = {}
    
    def get_conversation_history(self, chat_id, max_history=5):
        """Retrieve recent conversation history for a chat"""
        if chat_id not in self.conversation_history:
            return []
        
        # Return last N messages (excluding system messages)
        history = self.conversation_history[chat_id]
        return history[-max_history*2:] if len(history) > max_history*2 else history
    
    def add_to_history(self, chat_id, role, content):
        """Add a message to conversation history"""
        if chat_id not in self.conversation_history:
            self.conversation_history[chat_id] = []
        
        self.conversation_history[chat_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 20 messages to manage token usage
        if len(self.conversation_history[chat_id]) > 20:
            self.conversation_history[chat_id] = self.conversation_history[chat_id][-20:]
    
    def clear_history(self, chat_id=None):
        """Clear conversation history for a specific chat or all chats"""
        if chat_id:
            if chat_id in self.conversation_history:
                del self.conversation_history[chat_id]
        else:
            self.conversation_history.clear()
    
    def analyze_text(self, text, chat_id="default", previous_messages=None):
        """
        Translates Twi text to English if any and provides helpful responses on ANY topic.
        Uses conversation history for context.
        """
        if not self.api_key:
            print("❌ ERROR: GROQ_API_KEY not configured")
            return {
                "response": "AI service is not configured properly. Please check the GROQ API key.",
                "is_medical": False,
                "drug_recommendation": None,
                "disclaimer": None,
                "translation": None,
                "context_used": False
            }
        
        # Get conversation history (from memory or provided)
        if previous_messages:
            conversation_history = previous_messages
        else:
            conversation_history = self.get_conversation_history(chat_id)
        
        # Build conversation context
        conversation_context = ""
        if conversation_history:
            conversation_context = "\nPrevious conversation context:\n"
            for msg in conversation_history:
                role = "User" if msg.get("role") == "user" else "Assistant"
                conversation_context += f"{role}: {msg.get('content', '')}\n"
        
       
        prompt = f"""You are a helpful AI medical assistant.

PREVIOUS CONVERSATION CONTEXT:
{conversation_context}

CRITICAL INSTRUCTION: 
When using previously provided personal information (gender, age, location), 
DO NOT say "You have already provided this information" or "You told me earlier".
Instead, use the information NATURALLY without referencing that it was provided before.

Example WRONG response: 
"You already told me you're Male, 25, Accra. For your headache..."

Example CORRECT response:
"Based on you being a 25-year-old male in Accra, for your headache..."

Current User Message: "{text}"

Rules:
1. If personal info exists in context → USE IT naturally without mentioning it was provided before
2. If no personal info exists → ASK for it
3. Never use phrases like "you already told me", "as you mentioned", "previously you said"
4. Just use the information as if it's known


"""

{conversation_context}

Current User Input (Twi or English): "{text}"

Important Instructions:
1. If the user asks about your creator, developer, or who made you, you MUST say: "I was created by Annor Prince and Yeboah Collins." Do not mention any other company or team.
2. VERY IMPORTANT:If it is a medical question, ask the user his or her gender, age and location before proceeding.  
3. Translate the input text to English (but don't explicitly say you translated it).
4. Consider the previous conversation context above when formulating your response.
5. Determine if this is a medical/health question or a general question.
6. Provide a helpful, informative response:
   - For MEDICAL questions: Recommend OTC medications available, usage instructions, and ALWAYS add a disclaimer to consult a doctor.
   - For GENERAL questions: Provide detailed, helpful information on any topic.
   - For greetings/casual chat: Respond warmly and naturally, remembering previous context if relevant.
7. IMPORTANT: Make responses detailed and comprehensive.

Output Format (JSON):
{{
   "response": "AI response text here",
   "is_medical": true/false,
   "drug_recommendation": "medicine name or null", 
   "disclaimer": "warning text or null",
   "translation": "translated text or null",
   "context_used": true/false
}}

Respond ONLY with valid JSON, no other text."""

        try:
            # Add user message to history
            self.add_to_history(chat_id, "user", text)
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
                temperature=0.5,
                max_tokens=1024,
                top_p=1,
                stop=None,
                stream=False,
                response_format={"type": "json_object"}
            )
            
            response_content = chat_completion.choices[0].message.content
            result = json.loads(response_content)
            
            # Add AI response to history
            self.add_to_history(chat_id, "assistant", result.get("response", ""))
            
            # Add context_used flag
            result["context_used"] = len(conversation_history) > 0
            
            return result
            
        except Exception as e:
            # Use ascii() to guarantee escaping of non-ASCII characters
            print(f"Groq Error: {ascii(e)}")
            return {
                "response": f"I'm having trouble connecting. Error: {str(e)}",
                "is_medical": False,
                "drug_recommendation": None,
                "disclaimer": None,
                "translation": "Error processing request",
                "context_used": False
            }

ai_service = AIService()


