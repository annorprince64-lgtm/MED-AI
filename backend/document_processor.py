"""
Document Processor Module
Handles extraction of text from PDF, DOCX, and image files.

Author: Annor Prince & Collins Yeboah
"""

import os
import io
import base64
import re
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

# PDF Processing
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

# DOCX Processing
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Image Processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# OCR
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


@dataclass
class ProcessedDocument:
    """Result of document processing"""
    success: bool = False
    text: str = ""
    page_count: int = 0
    file_type: str = ""
    has_images: bool = False
    has_tables: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunks: List[str] = field(default_factory=list)
    error: Optional[str] = None


class DocumentProcessor:
    """
    Process various document formats and extract text.
    Supports: PDF, DOCX, Images (with OCR)
    """
    
    def __init__(self, enable_ocr: bool = True):
        """Initialize the document processor"""
        self.enable_ocr = enable_ocr and TESSERACT_AVAILABLE
        self.max_chunk_size = 2000
        
        print(f"📄 Document Processor initialized")
        print(f"   - PDF Support: {PDF_AVAILABLE or PDFPLUMBER_AVAILABLE}")
        print(f"   - DOCX Support: {DOCX_AVAILABLE}")
        print(f"   - OCR Support: {self.enable_ocr}")
    
    def process_base64(self, base64_data: str, filename: str) -> ProcessedDocument:
        """
        Process a document from base64 encoded data.
        
        Args:
            base64_data: Base64 encoded file data
            filename: Original filename to determine type
            
        Returns:
            ProcessedDocument with extracted text and metadata
        """
        try:
            # Decode base64 data
            if base64_data.startswith('data:'):
                # Remove data URL prefix
                base64_data = base64_data.split(',', 1)[1]
            
            file_bytes = base64.b64decode(base64_data)
            file_ext = os.path.splitext(filename)[1].lower()
            
            # Process based on file type
            if file_ext == '.pdf':
                return self._process_pdf(file_bytes, filename)
            elif file_ext in ['.docx', '.doc']:
                return self._process_docx(file_bytes, filename)
            elif file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                return self._process_image(file_bytes, filename)
            elif file_ext in ['.txt', '.md', '.csv']:
                return self._process_text(file_bytes, filename)
            else:
                return ProcessedDocument(
                    success=False,
                    error=f"Unsupported file type: {file_ext}"
                )
                
        except Exception as e:
            return ProcessedDocument(
                success=False,
                error=f"Error processing document: {str(e)}"
            )
    
    def _process_pdf(self, file_bytes: bytes, filename: str) -> ProcessedDocument:
        """Extract text from PDF file"""
        text = ""
        page_count = 0
        has_images = False
        has_tables = False
        metadata = {}
        
        try:
            # Try pdfplumber first (better table extraction)
            if PDFPLUMBER_AVAILABLE:
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    page_count = len(pdf.pages)
                    
                    for page in pdf.pages:
                        page_text = page.extract_text() or ""
                        text += page_text + "\n\n"
                        
                        # Check for tables
                        tables = page.extract_tables()
                        if tables:
                            has_tables = True
                            for table in tables:
                                # Format table as text
                                table_text = self._format_table(table)
                                text += table_text + "\n"
        
            # Fallback to PyPDF2 if pdfplumber failed
            elif PDF_AVAILABLE:
                reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                page_count = len(reader.pages)
                
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    text += page_text + "\n\n"
                
                # Try to get metadata
                if reader.metadata:
                    metadata = {
                        'title': reader.metadata.get('/Title', ''),
                        'author': reader.metadata.get('/Author', ''),
                        'subject': reader.metadata.get('/Subject', ''),
                    }
            
            else:
                return ProcessedDocument(
                    success=False,
                    error="No PDF library available"
                )
            
            # Clean up text
            text = self._clean_text(text)
            
            # Create chunks
            chunks = self._create_chunks(text)
            
            return ProcessedDocument(
                success=True,
                text=text,
                page_count=page_count,
                file_type='pdf',
                has_images=has_images,
                has_tables=has_tables,
                metadata=metadata,
                chunks=chunks
            )
            
        except Exception as e:
            return ProcessedDocument(
                success=False,
                error=f"Error processing PDF: {str(e)}"
            )
    
    def _process_docx(self, file_bytes: bytes, filename: str) -> ProcessedDocument:
        """Extract text from DOCX file"""
        if not DOCX_AVAILABLE:
            return ProcessedDocument(
                success=False,
                error="DOCX library not available"
            )
        
        try:
            doc = Document(io.BytesIO(file_bytes))
            
            text_parts = []
            has_tables = False
            
            # Extract paragraphs
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            
            # Extract tables
            for table in doc.tables:
                has_tables = True
                table_data = []
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells]
                    table_data.append(row_data)
                table_text = self._format_table(table_data)
                text_parts.append(table_text)
            
            text = "\n\n".join(text_parts)
            text = self._clean_text(text)
            
            chunks = self._create_chunks(text)
            
            # Try to get metadata
            metadata = {}
            try:
                core_props = doc.core_properties
                metadata = {
                    'title': core_props.title or '',
                    'author': core_props.author or '',
                    'subject': core_props.subject or '',
                }
            except:
                pass
            
            return ProcessedDocument(
                success=True,
                text=text,
                page_count=1,
                file_type='docx',
                has_images=False,
                has_tables=has_tables,
                metadata=metadata,
                chunks=chunks
            )
            
        except Exception as e:
            return ProcessedDocument(
                success=False,
                error=f"Error processing DOCX: {str(e)}"
            )
    
    def _process_image(self, file_bytes: bytes, filename: str) -> ProcessedDocument:
        """Extract text from image using OCR"""
        if not PIL_AVAILABLE:
            return ProcessedDocument(
                success=False,
                error="Image processing not available (PIL not installed)"
            )
        
        try:
            image = Image.open(io.BytesIO(file_bytes))
            
            # Perform OCR if enabled
            if self.enable_ocr:
                text = pytesseract.image_to_string(image)
            else:
                text = "[Image content - OCR not enabled]"
            
            text = self._clean_text(text)
            chunks = self._create_chunks(text)
            
            return ProcessedDocument(
                success=True,
                text=text,
                page_count=1,
                file_type='image',
                has_images=True,
                has_tables=False,
                metadata={'format': image.format, 'size': image.size},
                chunks=chunks
            )
            
        except Exception as e:
            return ProcessedDocument(
                success=False,
                error=f"Error processing image: {str(e)}"
            )
    
    def _process_text(self, file_bytes: bytes, filename: str) -> ProcessedDocument:
        """Process plain text files"""
        try:
            text = file_bytes.decode('utf-8')
            text = self._clean_text(text)
            chunks = self._create_chunks(text)
            
            file_ext = os.path.splitext(filename)[1].lower()
            file_type = 'text'
            if file_ext == '.md':
                file_type = 'markdown'
            elif file_ext == '.csv':
                file_type = 'csv'
            
            return ProcessedDocument(
                success=True,
                text=text,
                page_count=1,
                file_type=file_type,
                has_images=False,
                has_tables=False,
                metadata={},
                chunks=chunks
            )
            
        except Exception as e:
            return ProcessedDocument(
                success=False,
                error=f"Error processing text file: {str(e)}"
            )
    
    def _format_table(self, table_data: List[List[str]]) -> str:
        """Format table data as text"""
        if not table_data:
            return ""
        
        lines = []
        for row in table_data:
            # Clean row data
            clean_row = [str(cell).strip() if cell else '' for cell in row]
            lines.append(' | '.join(clean_row))
        
        return '\n'.join(lines)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Fix broken sentences (common in PDF extraction)
        text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)
        
        return text.strip()
    
    def _create_chunks(self, text: str) -> List[str]:
        """Split text into chunks for processing"""
        if len(text) <= self.max_chunk_size:
            return [text]
        
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) + 1 > self.max_chunk_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks


# Convenience function for direct import
def process_document_base64(base64_data: str, filename: str) -> ProcessedDocument:
    """Process a document from base64 data"""
    processor = DocumentProcessor(enable_ocr=True)
    return processor.process_base64(base64_data, filename)
