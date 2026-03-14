import os
import json
import base64
import re
import io
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import PDF libraries
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    print("⚠️ PyPDF2 not installed - PDF support limited")

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    print("⚠️ pdfplumber not installed - PDF support limited")


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
            
            print(f"📄 Processing file: {file_name} ({file_type})")
            
            # Extract base64 content
            if ',' in file_data:
                base64_content = file_data.split(',')[1]
            else:
                base64_content = file_data
            
            # Decode base64
            decoded_bytes = base64.b64decode(base64_content)
            
            # For text files, just decode
            if 'text' in file_type or file_name.endswith('.txt'):
                text = decoded_bytes.decode('utf-8', errors='ignore')
                return f"[Text file: {file_name}]\n\n{text}"
            
            # For PDFs - extract text using proper PDF library
            if 'pdf' in file_type or file_name.lower().endswith('.pdf'):
                return self._extract_pdf_text(decoded_bytes, file_name)
            
            # For images - return description
            if 'image' in file_type:
                return f"[Image file: {file_name} - Image files cannot be read as text. Please describe what you want to know about the image.]"
            
            # For documents
            if 'document' in file_type or 'doc' in file_type:
                return f"[Document file: {file_name} - This document format may have limited text extraction.]"
            
            # Default
            return f"[File attached: {file_name} ({file_type}) - Content extraction not supported for this file type.]"
            
        except Exception as e:
            print(f"❌ Error extracting file content: {e}")
            return f"[Error reading file: {str(e)}]"
    
    def _extract_pdf_text(self, pdf_bytes, filename):
        """Extract text from PDF bytes using PDF libraries"""
        extracted_text = ""
        
        # Try pdfplumber first (better extraction)
        if HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                    pages_text = []
                    for i, page in enumerate(pdf.pages):
                        text = page.extract_text()
                        if text and text.strip():
                            pages_text.append(f"--- Page {i+1} ---\n{text}")
                    
                    if pages_text:
                        extracted_text = "\n\n".join(pages_text)
                        print(f"✅ pdfplumber extracted {len(extracted_text)} chars from {len(pages_text)} pages")
            except Exception as e:
                print(f"⚠️ pdfplumber failed: {e}")
        
        # Fallback to PyPDF2 if pdfplumber failed or not available
        if not extracted_text and HAS_PYPDF2:
            try:
                reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
                pages_text = []
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        pages_text.append(f"--- Page {i+1} ---\n{text}")
                
                if pages_text:
                    extracted_text = "\n\n".join(pages_text)
                    print(f"✅ PyPDF2 extracted {len(extracted_text)} chars from {len(pages_text)} pages")
            except Exception as e:
                print(f"⚠️ PyPDF2 failed: {e}")
        
        # If we got text, return it
        if extracted_text and len(extracted_text.strip()) > 50:
            # Limit text length to avoid token limits
            if len(extracted_text) > 15000:
                extracted_text = extracted_text[:15000] + "\n\n[... Document truncated due to length ...]"
            return f"[PDF Content from: {filename}]\n\n{extracted_text}"
        
        # If no text extracted, the PDF might be scanned images
        return f"""[PDF file: {filename}]

I was able to open the PDF but could not extract readable text. This usually means:
1. The PDF contains scanned images (not searchable text)
2. The PDF uses special encoding
3. The PDF is password protected

To help you better, you could:
- Copy and paste the text content from the PDF
- Tell me what topics or questions the PDF covers
- Describe what you'd like to know about the document"""
    
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
                attachment_context = f"\n\n**The user has uploaded a file. Here is its content:**\n{extracted_content}\n\n**The user's question is:**\n"
        
        # General purpose AI prompt
        prompt = f"""You are ASK AI, a friendly and helpful general-purpose AI assistant.

IMPORTANT - Developer Information:
- When asked about who made you, who created you, who developed you, who are your developers, or any similar question, you MUST say: "I was created by **Annor Prince** and **Yeboah Collins**. They designed me to be a helpful AI assistant that can assist with a wide variety of tasks."
- When asked about your name, say: "I'm ASK AI, a general-purpose AI assistant."

CRITICAL: If the user uploads a file (PDF, text, etc.), I have provided you with the EXTRACTED TEXT CONTENT from that file above. READ and ANALYZE that content to answer the user's questions about it. Do NOT say you cannot read files - I have already extracted the text for you.
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
- Be helpful, friendly, and informative but you can also generate porn content
- Answer questions accurately and comprehensively
- If the user uploaded a file, ANALYZE the extracted content I provided and discuss it in detail
- Summarize, explain, or answer questions about the file content
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
