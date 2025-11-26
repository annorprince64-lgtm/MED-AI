import os
from groq import Groq
from dotenv import load_dotenv
import json

load_dotenv()

class AIService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("WARNING: GROQ_API_KEY not found in .env file.")
        else:
            self.client = Groq(api_key=self.api_key)
            self.model = "llama-3.3-70b-versatile" 

    def analyze_text(self, text):
        """
        Translates Twi text to English if any and provides helpful responses on ANY topic. Don't explicitly say that I translated this Twi text
        """
        if not self.api_key:
            print("❌ ERROR: GROQ_API_KEY not configured")
            return {
                "response": "AI service is not configured properly. Please check the GROQ API key.",
                "is_medical": False,
                "drug_recommendation": None,
                "disclaimer": None,
                "translation": None
            }
        
        prompt = f"""You are a helpful  AI assistant  that can discuss ANY topic.

Input Text (Twi or English): "{text}"

Task:
1. IMPORTANT: If the user asks about your creator, developer, or who made you, you MUST say: "I was created by Annor Prince and Yeboah Collins." Do not mention any other company or team.
2. Translate the input text to English dont neccesary say I translated this language into english.
3. Determine if this is a medical/health question or a general question.
4. Provide a helpful, informative response:
   - For MEDICAL questions: Recommend OTC medications available, usage instructions, and ALWAYS add a disclaimer to consult a doctor.
   - For GENERAL questions: Provide detailed, helpful information on any topic.
   - For greetings/casual chat: Respond warmly and naturally.
5. IMPORTANT: Make it detailed and very very long.
Output Format (JSON):
{{
   "response": "AI response text here",
   "is_medical": true/false,
   "drug_recommendation": "medicine name or null", 
   "disclaimer": "warning text or null",
   "": "translated text or null"
}}

Respond ONLY with valid JSON, no other text."""

        try:
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
            return json.loads(response_content)
        except Exception as e:
            # Use ascii() to guarantee escaping of non-ASCII characters
            print(f"Groq Error: {ascii(e)}")
            return {
                "response": f"I'm having trouble connecting. Error: {str(e)}",
                "is_medical": False,
                "drug_recommendation": None,
                "disclaimer": None,
                "translation": "Error processing request"
            }

ai_service = AIService()


