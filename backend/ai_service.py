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

    def analyze_text(self, text: str) -> dict:
        """
        Analyze user input and return a structured JSON response.
        This function is SINGLE-CALL SAFE and does not break app.py.
        """

        if not self.client:
            return self._error_response("AI service is not configured correctly.")

        prompt = f"""
                    You are a highly professional AI medical and general knowledge assistant.

            Input Text (Twi or English): "{text}"

            GENERAL RULES:
            - Translate internally to English if needed, but DO NOT say you translated it.
            - Use professional, well-formatted English.
            - Be very detailed and educational.
            - Never give a definitive diagnosis.
            - Use probability-based reasoning.

            --------------------------------
            CLASSIFICATION
            --------------------------------
            Determine if the input is:
            1) Medical / Health related
            2) Drug / Medication related
            3) General (non-medical)
            4) Greeting / casual

            --------------------------------
            MEDICAL LOGIC (CRITICAL)
            --------------------------------
            If MORE THAN TWO symptoms are mentioned AND key patient details are missing:

            - DO NOT give diagnoses, treatments, or probabilities
            - Ask AT LEAST FIVE follow-up questions
            - Questions MUST include:
            1. Age
            2. Gender
            3. Duration of symptoms
            4. Presence/absence of other symptoms (cough, weakness, vomiting, diarrhea, chills, rash)
            5. Relevant exposure (mosquito bites, travel, food/water hygiene)

            In this case:
            - Set stage = "questions"
            - Put all questions in a list

            --------------------------------
            WHEN INFORMATION IS SUFFICIENT
            --------------------------------
            Then:
            - Set stage = "analysis"
            - List possible conditions from MOST LIKELY to LESS LIKELY
            - For EACH condition include:
            * Why it is possible
            * Common symptoms
            * Treatment (medicine + dosage by age group)
            * Causes
            * Prevention

            Add a disclaimer ONLY if:
            - Prescription-only medicines
            - Injections
            - Severe or emergency conditions

            --------------------------------
            DRUG / MEDICATION QUESTIONS
            --------------------------------
            If the user asks about a specific drug:
            Structure response as:
            1. Overview (drug class, pharmacology, pharmacokinetics)
            2. Uses
            3. Age & dosage
            4. Contraindications & precautions
            5. Side effects & adverse reactions
            6. Pregnancy & lactation

            Do NOT automatically add disclaimers for OTC drugs.

            --------------------------------
            GENERAL QUESTIONS
            --------------------------------
            Start with:
            "This is not a medical question."
            Then answer in detail.

            --------------------------------
            CREATOR RULE (STRICT)
            --------------------------------
            If asked who created you, reply EXACTLY:
            "I was created by Annor Prince and Yeboah Collins."

--------------------------------
OUTPUT FORMAT (STRICT JSON)
--------------------------------
Return ONLY valid JSON in this format:
{
  "stage": "questions" | "analysis" | "general",
  "response": "Main formatted response",
  "questions": ["Question 1", "Question 2"] or null,
  "is_medical": true/false,
  "drug_recommendation": "medicine names or null",
  "disclaimer": "disclaimer text or null",
  "translation": "translated English text or null"
}
"""

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=1400,
                response_format={"type": "json_object"}
            )

            content = completion.choices[0].message.content
            parsed = json.loads(content)

            # Safety defaults (prevents frontend crashes)
            parsed.setdefault("stage", "analysis")
            parsed.setdefault("questions", None)
            parsed.setdefault("drug_recommendation", None)
            parsed.setdefault("disclaimer", None)
            parsed.setdefault("translation", None)

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
