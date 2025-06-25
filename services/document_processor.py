
import os
import hashlib
from typing import List, Dict, Any
import asyncio
from pathlib import Path
import logging

# For different file types
import PyPDF2
import docx
import mammoth

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
    def save_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file and return file path"""
        # Create a hash-based filename to avoid conflicts
        file_hash = hashlib.md5(file_content).hexdigest()[:10]
        extension = Path(filename).suffix
        safe_filename = f"{file_hash}_{filename}"
        
        file_path = self.upload_dir / safe_filename
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
            
        return str(file_path)
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            with open(file_path, "rb") as docx_file:
                result = mammoth.extract_raw_text(docx_file)
                return result.value
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {e}")
            return ""
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error extracting text from TXT {file_path}: {e}")
            return ""
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from various file formats"""
        extension = Path(file_path).suffix.lower()
        
        if extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif extension == '.docx':
            return self.extract_text_from_docx(file_path)
        elif extension in ['.txt', '.md']:
            return self.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into chunks with overlap"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence or paragraph boundaries
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start + chunk_size//2, end - 100), -1):
                    if text[i] in '.!?\n':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def process_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process a document and return metadata"""
        try:
            # Save the file
            file_path = self.save_file(file_content, filename)
            
            # Extract text
            text = self.extract_text(file_path)
            
            if not text:
                raise ValueError("No text could be extracted from the document")
            
            # Create chunks
            chunks = self.chunk_text(text)
            
            return {
                "file_path": file_path,
                "filename": filename,
                "text": text,
                "chunks": chunks,
                "chunk_count": len(chunks),
                "text_length": len(text)
            }
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            raise Exception(f"Document processing failed: {str(e)}")
