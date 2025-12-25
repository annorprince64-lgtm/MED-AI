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
    
    def analyze_text(self, text: str) -> dict:
        """Analyze user input with modern formatting"""
        
        if not self.client:
            return self._error_response("AI service not configured")
        
        # Clean, simple prompt
        prompt = f"""You are DRUGBOT, a modern AI medical assistant.

User input: "{text}"

Provide a helpful, well-formatted response using:
- **Bold text** for important terms
- Bullet points for lists
- Headings ( main,  sub)
- Tables when comparing things
- Clear sections

For medical topics, structure like:
Medical Assessment
Possible Conditions
- Condition 1: explanation
- Condition 2: explanation

Recommendations
- Recommendation 1
- Recommendation 2

For drugs:
Drug Information
| Age Group | Dosage | Frequency |
|-----------|--------|-----------|
| Adults | 500mg | 2x daily |
| Children | 250mg | 1x daily |

Always respond in modern chat format, not essay format.

Return ONLY this JSON format:
{{
  "stage": "analysis",
  "response": "Your formatted response here",
  "questions": null,
  "is_medical": true/false,
  "drug_recommendation": "Medicine name or null",
  "disclaimer": "Warning if needed or null",
  "translation": null,
  "format_type": "structured"
}}"""
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500,
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
            "response": f"System Error\n\n{error_msg}\n\nPlease try again.",
            "questions": None,
            "is_medical": False,
            "drug_recommendation": None,
            "disclaimer": None,
            "translation": None,
            "format_type": "structured"
        }

# Singleton instance
ai_service = AIService()

