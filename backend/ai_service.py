import os
import json
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIService:
    """
    AIService handles all interactions with the Groq LLM.
    It supports multi-stage medical reasoning (questioning -> analysis)
   
    """

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("⚠️ WARNING: GROQ_API_KEY not found. AI responses will fail.")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
        
        # Centralized model config
        self.model = "llama-3.3-70b-versatile"

  # Update the analyze_text method in your AIService class

def analyze_text(self, text: str) -> dict:
    """
    Analyze user input and return structured JSON response with modern formatting.
    """
    
    if not self.client:
        return self._error_response("AI service is not configured correctly.")

    # Updated prompt for modern formatting
    prompt = f"""
    You are a highly professional AI medical and general knowledge assistant.
    Your responses MUST use modern formatting with clear sections, bullet points, and tables when appropriate.

    Input Text: "{text}"

    ====================
    RESPONSE FORMATTING RULES (STRICT):
    ====================
    1. **ALWAYS** use Markdown-style formatting:
       - Use ## for section headings
       - Use ### for subheadings
       - Use bullet points (* or -) for lists
       - Use **bold** for important terms
       - Use tables when comparing multiple items

    2. **For Medical Questions**:
       - Start with "## Medical Assessment"
       - Use clear sections: Symptoms, Possible Conditions, Recommendations, Prevention
       - Create comparison tables when listing multiple conditions
       - Example table format:
         | Condition | Probability | Key Symptoms | Recommended Action |
         |-----------|-------------|--------------|-------------------|
         | Condition A | High | Symptom 1, 2 | Action A |
         | Condition B | Medium | Symptom 3 | Action B |

    3. **For Drug Information**:
       - Use sections: Overview, Dosage, Side Effects, Precautions
       - Create dosage tables by age group:
         | Age Group | Dosage | Frequency | Duration |
         |-----------|--------|-----------|----------|
         | Adults | 500mg | 3x daily | 7 days |
         | Children | 250mg | 2x daily | 5 days |

    4. **For General Questions**:
       - Still use structured formatting
       - Break down complex topics into digestible sections

    5. **For Questions Needing More Info**:
       - Use numbered questions
       - Format: "## Additional Information Needed"
       - Then: "1. First question..."
       - Keep questions concise and relevant

    ====================
    CONTENT RULES:
    ====================
    - Be direct, avoid lengthy introductions
    - Use professional but accessible language
    - Present information in scannable format
    - Highlight key points with **bold**
    - Never use "In conclusion" or essay-style endings

    ====================
    OUTPUT FORMAT:
    ====================
    Return ONLY valid JSON:
    {{
      "stage": "questions" | "analysis" | "general",
      "response": "Formatted response with markdown",
      "questions": ["Q1", "Q2"] or null,
      "is_medical": true/false,
      "drug_recommendation": "medicine names or null",
      "disclaimer": "disclaimer text or null",
      "translation": "translated English text or null",
      "format_type": "structured"  # Always include this
    }}

    Now analyze this input: "{text}"
    """

    try:
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Lower temperature for more consistent formatting
            max_tokens=1800,  # Increased for formatted content
            response_format={"type": "json_object"}
        )

        content = completion.choices[0].message.content
        parsed = json.loads(content)

        # Safety defaults
        parsed.setdefault("stage", "analysis")
        parsed.setdefault("questions", None)
        parsed.setdefault("drug_recommendation", None)
        parsed.setdefault("disclaimer", None)
        parsed.setdefault("translation", None)
        parsed.setdefault("format_type", "structured")

        return parsed

    except Exception as e:
        print(f"❌ Groq Error: {ascii(e)}")
        return self._error_response(str(e))
    def _error_response(self, error_msg: str) -> dict:
        """Standardized error response"""
        return {
            "stage": "analysis",
            "response": f"An error occurred while processing your request: {error_msg}",
            "questions": None,
            "is_medical": False,
            "drug_recommendation": None,
            "disclaimer": None,
            "translation": None
        }


# Singleton instance (USED BY app.py)
ai_service = AIService()

