import os
import json
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("⚠️ WARNING: GROQ_API_KEY not found.")
            self.client = None
        else:
            try:
                self.client = Groq(api_key=self.api_key)
                print("✅ Groq client initialized")
            except Exception as e:
                print(f"❌ Error initializing Groq client: {e}")
                self.client = None
        
        self.model = "llama-3.3-70b-versatile"
    
    def analyze_text(self, text: str, conversation_history: list = None) -> dict:
        """Analyze user input with conversation memory"""
        
        if not self.client:
            return self._error_response("AI service not configured")
        
        # Build conversation context
        history_context = ""
        if conversation_history and len(conversation_history) > 0:
            history_context = "\n\n**Previous conversation (for context):**\n"
            for msg in conversation_history[:-1]:  # Exclude the current message
                role = "User" if msg.get('role') == 'user' else "Assistant"
                content = msg.get('content', '')[:500]  # Limit each message to 500 chars
                history_context += f"{role}: {content}\n"
            history_context += "\n**Current message:**\n"
        
        # General purpose AI prompt
        prompt = f"""You are ASK AI, a friendly and helpful general-purpose AI assistant created by **Annor Prince** and **Yeboah Collins**.

IMPORTANT - Developer Information:
- When asked about who made you, who created you, who developed you, who are your developers, or any similar question, you MUST say: "I was created by **Annor Prince** and **Yeboah Collins**. They designed me to be a helpful AI assistant that can assist with a wide variety of tasks."
- When asked about your name, say: "I'm ASK AI, a general-purpose AI assistant created by Annor Prince and Yeboah Collins."
{history_context}
User input: "{text}"

Provide a helpful, well-formatted response using:
- **Bold text** for important terms
- Bullet points for lists
- Headings (# for main, ## for sub) when appropriate
- Tables when comparing things
- Clear sections
- Code blocks when showing code

Guidelines:
- Be helpful, friendly, and informative
- Answer questions accurately and comprehensively
- For coding questions, provide clear code examples
- For math, show your work
- For creative tasks, be creative and engaging
- If you don't know something, say so honestly
- Always be respectful and professional

Respond in a modern chat format, keeping responses well-structured but conversational.

Return ONLY this JSON format:
{{
  "stage": "analysis",
  "response": "Your formatted response here",
  "questions": null,
  "is_medical": false,
  "drug_recommendation": null,
  "disclaimer": null,
  "translation": null,
  "format_type": "structured"
}}"""
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            content = completion.choices[0].message.content
            result = json.loads(content)
            
            # Ensure all fields exist
            result.setdefault("stage", "analysis")
            result.setdefault("questions", None)
            result.setdefault("drug_recommendation", None)
            result.setdefault("disclaimer", None)
            result.setdefault("translation", None)
            result.setdefault("is_medical", False)
            result.setdefault("format_type", "structured")
            
            print(f"✅ AI Response generated: {len(result.get('response', ''))} chars")
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            return self._error_response("AI response format error")
        except Exception as e:
            print(f"❌ Error: {e}")
            return self._error_response(str(e))
    
    def _error_response(self, error_msg: str) -> dict:
        return {
            "stage": "analysis",
            "response": f"**Error**\n\n{error_msg}\n\nPlease try again.",
            "questions": None,
            "is_medical": False,
            "drug_recommendation": None,
            "disclaimer": None,
            "translation": None,
            "format_type": "structured"
        }

# Singleton instance
ai_service = AIService()
