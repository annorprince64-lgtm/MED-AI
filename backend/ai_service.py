"""
AI Service Module
Handles AI interactions with document processing integration.

Author: Annor Prince & Collins Yeboah
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv

# Import our document processor
from document_processor import DocumentProcessor, ProcessedDocument

# Load environment variables
load_dotenv()


class AIService:
    """
    AI Service class that handles:
    - Text analysis with conversation memory
    - Document processing and understanding
    - Multi-format file support
    """
    
    def __init__(self):
        """Initialize the AI service with Groq client and document processor"""
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = "llama-3.3-70b-versatile"
        
        # Initialize Groq client
        if not self.api_key:
            print("⚠️ WARNING: GROQ_API_KEY not found in environment")
            self.client = None
        else:
            try:
                self.client = Groq(api_key=self.api_key)
                print("✅ Groq client initialized successfully")
            except Exception as e:
                print(f"❌ Error initializing Groq client: {e}")
                self.client = None
        
        # Initialize document processor
        try:
            self.doc_processor = DocumentProcessor(enable_ocr=True)
            print("✅ Document processor initialized")
        except Exception as e:
            print(f"⚠️ Document processor initialization issue: {e}")
            self.doc_processor = None
        
        # Maximum context length for documents
        self.max_doc_length = 15000  # Characters
    
    def process_attachment(self, attachment: dict) -> tuple:
        """
        Process an attached file using the document processor.
        
        Args:
            attachment: Dict with 'data', 'name', 'type' keys
            
        Returns:
            Tuple of (extracted_text, success, error_message)
        """
        if not attachment:
            return (None, False, "No attachment provided")
        
        if not self.doc_processor:
            return (None, False, "Document processor not available")
        
        file_data = attachment.get('data', '')
        file_name = attachment.get('name', 'unknown')
        
        print(f"📄 Processing file: {file_name}")
        
        try:
            # Process the document
            result: ProcessedDocument = self.doc_processor.process_base64(
                base64_data=file_data,
                filename=file_name
            )
            
            if not result.success:
                return (None, False, result.error or "Failed to process document")
            
            # Truncate if too long
            text = result.text
            if len(text) > self.max_doc_length:
                text = text[:self.max_doc_length]
                text += f"\n\n[... Document truncated. Original length: {len(result.text)} characters ...]"
            
            # Build context with metadata
            context_parts = [
                f"**Document: {file_name}**",
                f"- Type: {result.file_type.upper()}",
                f"- Pages: {result.page_count}",
            ]
            
            if result.has_images:
                context_parts.append("- Contains images")
            if result.has_tables:
                context_parts.append("- Contains tables")
            
            if result.metadata:
                if result.metadata.get('title'):
                    context_parts.append(f"- Title: {result.metadata['title']}")
                if result.metadata.get('author'):
                    context_parts.append(f"- Author: {result.metadata['author']}")
            
            context_parts.append("")
            context_parts.append("**Extracted Content:**")
            context_parts.append(text)
            
            full_context = "\n".join(context_parts)
            
            print(f"✅ Document processed: {len(text)} chars, {result.page_count} pages")
            return (full_context, True, None)
            
        except Exception as e:
            print(f"❌ Error processing attachment: {e}")
            return (None, False, str(e))
    
    def analyze_text(
        self,
        text: str,
        conversation_history: list = None,
        attachment: dict = None
    ) -> dict:
        """
        Analyze user input with conversation memory and optional file attachment.
        
        Args:
            text: User's message
            conversation_history: List of previous messages for context
            attachment: Optional file attachment dict
            
        Returns:
            Dict with AI response
        """
        
        if not self.client:
            return self._error_response("AI service not configured. Please set GROQ_API_KEY.")
        
        # Build conversation context
        history_context = self._build_history_context(conversation_history)
        
        # Process attachment if present
        attachment_context = ""
        if attachment:
            extracted_content, success, error = self.process_attachment(attachment)
            if success and extracted_content:
                attachment_context = f"""
**The user has uploaded a document. Here is the EXTRACTED CONTENT:**

{extracted_content}

---
**Now respond to the user's question about this document:**
"""
            elif error:
                attachment_context = f"""
**The user tried to upload a file but there was an error: {error}**

Please help them understand what went wrong and suggest alternatives.
"""
        
        # Build the full prompt
        prompt = self._build_prompt(text, history_context, attachment_context)
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2500,
                response_format={"type": "json_object"}
            )
            
            content = completion.choices[0].message.content
            result = json.loads(content)
            
            # Ensure all required fields exist
            result.setdefault("stage", "analysis")
            result.setdefault("response", "")
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
            return self._error_response("AI response format error. Please try again.")
        except Exception as e:
            print(f"❌ Error in AI analysis: {e}")
            return self._error_response(f"An error occurred: {str(e)}")
    
    def _build_history_context(self, conversation_history: list) -> str:
        """Build context string from conversation history"""
        if not conversation_history or len(conversation_history) == 0:
            return ""
        
        history_context = "\n\n**Previous conversation (for context):**\n"
        
        # Take last 10 messages for context
        recent_messages = conversation_history[-10:]
        
        for msg in recent_messages[:-1]:  # Exclude the current message
            role = "User" if msg.get('role') == 'user' else "Assistant"
            content = msg.get('content', '')
            
            # Limit each message to 500 chars
            if len(content) > 500:
                content = content[:500] + "..."
            
            history_context += f"\n**{role}:** {content}\n"
        
        history_context += "\n**Current message:**\n"
        return history_context
    
    def _build_prompt(self, text: str, history_context: str, attachment_context: str) -> str:
        """Build the full prompt for the AI"""
        
        prompt = f"""You are ASK AI, a friendly and helpful general-purpose AI assistant created by **Annor Prince** and **Yeboah Collins**.

## About You
- Your name is ASK AI
- You were created by **Annor Prince** and **Yeboah Collins**
- When asked about who made you, who created you, or who developed you, always say: "I was created by **Annor Prince** and **Yeboah Collins**"
- You are a general-purpose AI assistant capable of helping with a wide variety of tasks

## Document Handling
- If the user uploads a document, READ and ANALYZE the extracted content carefully
- Answer questions about the document in detail
- Summarize, explain, or discuss the document content
- If the document contains tables, preserve the table structure in your response
{history_context}{attachment_context}

## User's Message:
"{text}"

## Response Guidelines
- Be helpful, friendly, and informative
- Use **bold text** for important terms
- Use bullet points for lists
- Use headings (# ## ###) when organizing complex information
- Use tables when comparing things or showing data
- Use code blocks (```) when showing code
- For math problems, show your work step by step
- For creative tasks, be creative and engaging
- If you don't know something, say so honestly
- Always be respectful and professional

## Response Format
Return ONLY valid JSON in this exact format:
{{
  "stage": "analysis",
  "response": "Your formatted response here (use markdown formatting)",
  "questions": null,
  "is_medical": false,
  "drug_recommendation": null,
  "disclaimer": null,
  "translation": null,
  "format_type": "structured"
}}"""
        
        return prompt
    
    def _error_response(self, error_msg: str) -> dict:
        """Generate an error response"""
        return {
            "stage": "analysis",
            "response": f"## Error\n\n{error_msg}\n\nPlease try again or rephrase your question.",
            "questions": None,
            "is_medical": False,
            "drug_recommendation": None,
            "disclaimer": None,
            "translation": None,
            "format_type": "structured"
        }


# Singleton instance for easy import
ai_service = AIService()
