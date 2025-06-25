import hashlib
import logging
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import docx
import mammoth
import PyPDF2

logger = logging.getLogger(__name__)

class SimpleRAG:
    def __init__(self):
        # Initialize Cloudinary service
        try:
            from services.cloudinary_service import CloudinaryService
            self.cloudinary_service = CloudinaryService()
            self.use_cloudinary = self.cloudinary_service.is_configured()
        except Exception as e:
            logger.warning(f"Cloudinary not configured, falling back to local storage: {e}")
            self.use_cloudinary = False
            self.cloudinary_service = None
        
        # Fallback local storage
        self.documents_dir = Path("documents")
        self.documents_dir.mkdir(exist_ok=True)
        
        self.documents_metadata = []
        # Store documents per chat
        self.chat_documents = {}  # chat_id -> {file_id: document_data}
        
        # Enhanced web search trigger keywords
        self.search_triggers = [
            # Time-sensitive keywords
            'latest', 'recent', 'current', 'today', 'now', 'this week', 'this month',
            'yesterday', 'breaking', 'update', 'news', 'new', 'fresh', 'live',
            
            # Weather keywords
            'weather', 'temperature', 'forecast', 'climate', 'rain', 'sunny', 'cloudy',
            'humidity', 'wind', 'storm', 'hot', 'cold', 'degrees',
            
            # Real-time data keywords
            'stock price', 'exchange rate', 'cryptocurrency', 'bitcoin', 'price',
            'market', 'cost', 'trending', 'viral', 'popular',
            
            # Current events keywords
            'happening', 'events', 'breaking news',
            
            # Question words that often need real-time answers
            'what is the current', 'how much does', 'when did', 'who is currently',
            'where is now', 'what happened today', 'tell me the current'
        ]
        
        # Keywords that should NOT trigger search (document-focused)
        self.no_search_keywords = [
            'document', 'file', 'upload', 'analyze this', 'summarize this',
            'from the document', 'in the pdf', 'according to the file'
        ]
    
    def save_file(self, file_content: bytes, filename: str, chat_id: str = None) -> Dict[str, Any]:
        """Save uploaded file and return file metadata"""
        if self.use_cloudinary and self.cloudinary_service:
            # Use Cloudinary for cloud storage
            return self.cloudinary_service.upload_file(file_content, filename, chat_id)
        else:
            # Fallback to local storage
            return self._save_local(file_content, filename)
    
    def _save_local(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Save file locally (fallback method)"""
        file_hash = hashlib.md5(file_content).hexdigest()[:10]
        extension = Path(filename).suffix
        safe_filename = f"{file_hash}_{filename}"
        
        file_path = self.documents_dir / safe_filename
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
            
        return {
            "storage_type": "local",
            "file_path": str(file_path),
            "filename": filename,
            "safe_filename": safe_filename,
            "file_size": len(file_content),
            "upload_time": str(datetime.now())
        }
    
    def get_file_content(self, file_metadata: Dict[str, Any]) -> Optional[bytes]:
        """Get file content from storage"""
        if file_metadata.get("storage_type") == "cloudinary" and self.cloudinary_service:
            return self.cloudinary_service.download_file(file_metadata)
        elif file_metadata.get("storage_type") == "local":
            file_path = file_metadata.get("file_path")
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return f.read()
        return None
    
    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file content"""
        try:
            text = ""
            # Create temporary file for PyPDF2
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""
    
    def extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file content"""
        try:
            # Create temporary file for mammoth
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, "rb") as docx_file:
                    result = mammoth.extract_raw_text(docx_file)
                    return result.value
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            return ""
    
    def extract_text_from_txt(self, file_content: bytes) -> str:
        """Extract text from TXT file content"""
        try:
            return file_content.decode('utf-8')
        except Exception as e:
            logger.error(f"Error extracting text from TXT: {e}")
            return ""
    
    def extract_text(self, file_content: bytes, filename: str) -> str:
        """Extract text from various file formats"""
        extension = Path(filename).suffix.lower()
        
        if extension == '.pdf':
            return self.extract_text_from_pdf(file_content)
        elif extension == '.docx':
            return self.extract_text_from_docx(file_content)
        elif extension in ['.txt', '.md']:
            return self.extract_text_from_txt(file_content)
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
            
            if end < len(text):
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
    
    def process_document(self, file_content: bytes, filename: str, chat_id: str = None) -> Dict[str, Any]:
        """Process a document and store it for a specific chat"""
        try:
            # Save file to storage (Cloudinary or local)
            file_metadata = self.save_file(file_content, filename, chat_id)
            
            # Extract text from file content
            text = self.extract_text(file_content, filename)
            
            if not text:
                raise ValueError("No text could be extracted from the document")
            
            chunks = self.chunk_text(text)
            file_id = hashlib.md5(file_content).hexdigest()[:10]
            
            # Store document for specific chat
            if chat_id:
                if chat_id not in self.chat_documents:
                    self.chat_documents[chat_id] = {}
                
                self.chat_documents[chat_id][file_id] = {
                    "filename": filename,
                    "chunks": chunks,
                    "full_text": text,
                    "upload_time": str(datetime.now()),
                    "file_metadata": file_metadata
                }
            
            # Update global metadata
            self.documents_metadata.append({
                "id": file_id,
                "filename": filename,
                "file_metadata": file_metadata,
                "chunks": len(chunks),
                "upload_time": str(datetime.now()),
                "chat_id": chat_id
            })
            
            logger.info(f"Processed document {filename} with {len(chunks)} chunks for chat {chat_id}")
            
            return {
                "filename": filename,
                "chunk_count": len(chunks),
                "file_metadata": file_metadata,
                "file_id": file_id
            }
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            raise Exception(f"Document processing failed: {str(e)}")
    
    def should_trigger_web_search(self, query: str) -> bool:
        """Enhanced determination if a query should trigger web search"""
        query_lower = query.lower()
        
        # Don't search if it's clearly about documents
        for keyword in self.no_search_keywords:
            if keyword in query_lower:
                logger.info(f"🚫 Web search disabled by document keyword: '{keyword}'")
                return False
        
        # Check for search trigger keywords
        for trigger in self.search_triggers:
            if trigger in query_lower:
                logger.info(f"🔍 Web search triggered by keyword: '{trigger}'")
                return True
        
        # Enhanced weather detection patterns
        weather_patterns = [
            r'weather.*in.*',
            r'temperature.*in.*',
            r'how.*hot.*today',
            r'how.*cold.*today',
            r'rain.*today',
            r'forecast.*for.*',
            r'climate.*in.*'
        ]
        
        for pattern in weather_patterns:
            if re.search(pattern, query_lower):
                logger.info(f"🌤️ Weather search triggered by pattern: '{pattern}'")
                return True
        
        # Enhanced question patterns that often need real-time data
        question_patterns = [
            r'what.*is.*price',
            r'how.*much.*cost',
            r'when.*did.*happen',
            r'who.*is.*currently',
            r'where.*is.*now',
            r'what.*happened.*today',
            r'latest.*on',
            r'current.*weather',
            r'tell.*me.*current',
            r'what.*is.*the.*current'
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, query_lower):
                logger.info(f"🔍 Web search triggered by question pattern: '{pattern}'")
                return True
        
        # Check for direct weather requests
        if any(word in query_lower for word in ['weather', 'temperature', 'forecast', 'climate']):
            logger.info(f"🌤️ Web search triggered by weather keywords")
            return True
        
        return False
    
    def simple_search(self, query: str, chat_id: str = None, top_k: int = 3) -> str:
        """Simple keyword-based search through documents for a specific chat"""
        if not chat_id or chat_id not in self.chat_documents or not self.chat_documents[chat_id]:
            return query
        
        try:
            query_words = query.lower().split()
            relevant_chunks = []
            
            for file_id, doc_data in self.chat_documents[chat_id].items():
                for chunk in doc_data["chunks"]:
                    chunk_lower = chunk.lower()
                    score = sum(1 for word in query_words if word in chunk_lower)
                    
                    if score > 0:
                        relevant_chunks.append({
                            "chunk": chunk,
                            "score": score,
                            "filename": doc_data["filename"]
                        })
            
            # Sort by relevance score
            relevant_chunks.sort(key=lambda x: x["score"], reverse=True)
            top_chunks = relevant_chunks[:top_k]
            
            if not top_chunks:
                return query
            
            # Build context
            context_parts = []
            for i, chunk_data in enumerate(top_chunks, 1):
                source = chunk_data["filename"]
                context_parts.append(f"[Document Reference {i}: {source}]\n{chunk_data['chunk']}")
            
            context = "\n\n".join(context_parts)
            
            enhanced_prompt = f"""You have access to relevant information from uploaded documents. Use this knowledge naturally in your response.

Available Context:
{context}

User Query: {query}

Please provide a comprehensive and helpful response:"""
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return query
    
    def enhance_with_web_search(self, query: str, web_search_results: str) -> str:
        """Enhance query with web search results"""
        if not web_search_results:
            return query
        
        enhanced_prompt = f"""You have access to current web search results. Use this information to provide an up-to-date and comprehensive response.

Current Web Information:
{web_search_results}

User Query: {query}

Please provide a comprehensive response using the latest information available. Note: This response includes real-time data from web search (🤖 Agent Response).

Please provide your response:"""
        
        return enhanced_prompt
    
    def combine_sources(self, query: str, document_context: str, web_search_results: str, chat_id: str = None) -> str:
        """Combine document context with web search results"""
        sources = []
        
        # Add document context if available
        if chat_id and self.has_documents(chat_id):
            doc_context = self.simple_search(query, chat_id)
            if doc_context != query:  # If document context was found
                sources.append("Document Knowledge Base")
        
        # Add web search results if available
        if web_search_results:
            sources.append("Current Web Information")
        
        if not sources:
            return query
        
        # Build combined prompt
        combined_prompt = f"""You have access to multiple information sources. Use all available information to provide a comprehensive response.

"""
        
        if document_context and document_context != query:
            combined_prompt += f"Document Context:\n{document_context}\n\n"
        
        if web_search_results:
            combined_prompt += f"Current Web Information:\n{web_search_results}\n\n"
        
        combined_prompt += f"""User Query: {query}

Note: This response combines document analysis with real-time web data (🤖 Agent Response).

Please provide a comprehensive response using all available sources:"""
        
        return combined_prompt
    
    def is_url_analysis_request(self, message: str) -> bool:
        """Check if the message is asking to analyze URL content"""
        url_indicators = [
            "analyze and summarize the following content from:",
            "please analyze",
            "content summary:",
            "url:",
            "title:",
            "please provide a comprehensive summary"
        ]
        
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in url_indicators)
    
    def has_documents(self, chat_id: str = None) -> bool:
        """Check if any documents are loaded for a specific chat"""
        if not chat_id:
            return len(self.documents_metadata) > 0
        return chat_id in self.chat_documents and len(self.chat_documents[chat_id]) > 0
    
    def get_document_list(self, chat_id: str = None) -> List[Dict]:
        """Get list of uploaded documents for a specific chat"""
        if not chat_id:
            return self.documents_metadata
        
        if chat_id not in self.chat_documents:
            return []
        
        return [
            {
                "id": file_id,
                "filename": doc_data["filename"],
                "file_path": doc_data.get("file_path", ""),
                "chunks": len(doc_data["chunks"]),
                "upload_time": doc_data["upload_time"]
            }
            for file_id, doc_data in self.chat_documents[chat_id].items()
        ]
    
    def delete_document(self, filename: str, chat_id: str = None) -> bool:
        """Delete document from storage"""
        try:
            # Find document metadata
            file_metadata = None
            for doc in self.documents_metadata:
                if doc["filename"] == filename and doc.get("chat_id") == chat_id:
                    file_metadata = doc.get("file_metadata")
                    break
            
            if not file_metadata:
                logger.warning(f"Document {filename} not found for deletion")
                return False
            
            # Delete from storage
            if file_metadata.get("storage_type") == "cloudinary" and self.cloudinary_service:
                success = self.cloudinary_service.delete_file(file_metadata)
            elif file_metadata.get("storage_type") == "local":
                file_path = file_metadata.get("file_path")
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                    success = True
                else:
                    success = False
            else:
                success = False
            
            # Remove from memory
            if chat_id and chat_id in self.chat_documents:
                for file_id, doc_data in list(self.chat_documents[chat_id].items()):
                    if doc_data["filename"] == filename:
                        del self.chat_documents[chat_id][file_id]
                        break
            
            # Remove from metadata
            self.documents_metadata = [
                doc for doc in self.documents_metadata 
                if not (doc["filename"] == filename and doc.get("chat_id") == chat_id)
            ]
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting document {filename}: {e}")
            return False
