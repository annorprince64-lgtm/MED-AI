import os
import json
import base64
import re
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
    
    def extract_text_from_base64(self, attachment):
        """Extract text content from base64 encoded file"""
        if not attachment:
            return None
        
        try:
            file_data = attachment.get('data', '')
            file_name = attachment.get('name', '')
            file_type = attachment.get('type', '')
            
            # Extract base64 content
            if ',' in file_data:
                base64_content = file_data.split(',')[1]
            else:
                base64_content = file_data
            
            # Decode base64
            decoded_bytes = base64.b64decode(base64_content)
            
            # For text files, just decode
            if 'text' in file_type or file_name.endswith('.txt'):
                return decoded_bytes.decode('utf-8', errors='ignore')
            
            # For PDFs - extract text using basic parsing
            if 'pdf' in file_type or file_name.endswith('.pdf'):
                return self._extract_pdf_text(decoded_bytes, file_name)
            
            # For images - return description
            if 'image' in file_type:
                return f"[Image file: {file_name} - User may ask about this image]"
            
            # For documents
            if 'document' in file_type or 'doc' in file_type:
                return f"[Document file: {file_name} - Content needs to be processed]"
            
            # Default
            return f"[File attached: {file_name} ({file_type})]"
            
        except Exception as e:
            print(f"❌ Error extracting file content: {e}")
            return f"[Error reading file: {str(e)}]"
    
    def _extract_pdf_text(self, pdf_bytes, filename):
        """Extract text from PDF bytes using basic parsing"""
        try:
            # Try to extract text using basic PDF parsing
            text = pdf_bytes.decode('latin-1', errors='ignore')
            
            # Extract text between stream markers (basic approach)
            # This is a simple extraction - for better results, use PyPDF2 or similar
            extracted = []
            
            # Look for text content
            text_patterns = [
                r'BT\s*(.*?)\s*ET',  # Text blocks
                r'Tj\s*\((.*?)\)',    # Text strings
                r'TJ\s*\[(.*?)\]',    # Text arrays
            ]
            
            for pattern in text_patterns:
                matches = re.findall(pattern, text, re.DOTALL)
                for match in matches:
                    # Clean up the extracted text
                    cleaned = re.sub(r'[^a-zA-Z0-9\s\.\,\!\?\-\:\;\(\)]', '', match)
                    if cleaned.strip() and len(cleaned.strip()) > 2:
                        extracted.append(cleaned.strip())
            
            if extracted:
                result = ' '.join(extracted[:50])  # Limit to first 50 text segments
                if len(result) > 2000:
                    result = result[:2000] + "..."
                return f"[PDF Content from {filename}]:\n{result}"
            
            # If no text found, return file info
            return f"[PDF file: {filename} - Text extraction limited. The PDF may contain scanned images or encoded content.]"
            
        except Exception as e:
            return f"[PDF file: {filename} - Could not extract text: {str(e)}]"
    
    def analyze_text(self, text: str, conversation_history: list = None, attachment: dict = None) -> dict:
        """Analyze user input with conversation memory and file support"""
        
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
        
        # Process attachment if present
        attachment_context = ""
        if attachment:
            extracted_content = self.extract_text_from_base64(attachment)
            if extracted_content:
                attachment_context = f"\n\n**User attached file:**\n{extracted_content}\n\n**User's question about the file:**\n"
        
        # General purpose AI prompt
        prompt = f"""You are ASK AI, a friendly and helpful general-purpose AI assistant created by **Annor Prince** and **Yeboah Collins**.

IMPORTANT - Developer Information:
- When asked about who made you, who created you, who developed you, who are your developers, or any similar question, you MUST say: "I was created by **Annor Prince** and **Yeboah Collins**. They designed me to be a helpful AI assistant that can assist with a wide variety of tasks."
- When asked about your name, say: "I'm ASK AI, a general-purpose AI assistant created by Annor Prince and Yeboah Collins."
{history_context}{attachment_context}
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
- If the user uploaded a file, analyze and discuss its content
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
