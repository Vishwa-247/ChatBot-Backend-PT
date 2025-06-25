
import os
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain.docstore.document import Document
import tempfile
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LangChainRAG:
    def __init__(self):
        self.documents_dir = Path("documents")
        self.documents_dir.mkdir(exist_ok=True)
        
        # Initialize Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Initialize embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Vector store
        self.vector_store = None
        self.documents_metadata = []
        
        # Load existing documents if any
        self.load_existing_documents()
    
    def save_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file and return file path"""
        file_hash = hashlib.md5(file_content).hexdigest()[:10]
        extension = Path(filename).suffix
        safe_filename = f"{file_hash}_{filename}"
        
        file_path = self.documents_dir / safe_filename
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
            
        return str(file_path)
    
    def process_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process a document using LangChain"""
        try:
            # Save the file
            file_path = self.save_file(file_content, filename)
            
            # Load document based on file type
            if filename.lower().endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            elif filename.lower().endswith(('.txt', '.md')):
                loader = TextLoader(file_path, encoding='utf-8')
            else:
                raise ValueError(f"Unsupported file type: {filename}")
            
            # Load and split documents
            documents = loader.load()
            texts = self.text_splitter.split_documents(documents)
            
            # Add metadata
            for doc in texts:
                doc.metadata.update({
                    "filename": filename,
                    "file_path": file_path,
                    "upload_time": str(datetime.now())
                })
            
            # Create or update vector store
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(texts, self.embeddings)
            else:
                self.vector_store.add_documents(texts)
            
            # Save vector store
            self.vector_store.save_local("vector_store")
            
            # Update metadata
            self.documents_metadata.append({
                "filename": filename,
                "file_path": file_path,
                "chunks": len(texts),
                "upload_time": str(datetime.now())
            })
            
            logger.info(f"Processed document {filename} with {len(texts)} chunks")
            
            return {
                "filename": filename,
                "chunk_count": len(texts),
                "file_path": file_path
            }
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            raise Exception(f"Document processing failed: {str(e)}")
    
    def query_documents(self, query: str, k: int = 3) -> str:
        """Query documents and return enhanced prompt"""
        if self.vector_store is None:
            return query
        
        try:
            # Search for relevant documents
            relevant_docs = self.vector_store.similarity_search(query, k=k)
            
            if not relevant_docs:
                return query
            
            # Build context from relevant documents
            context_parts = []
            for i, doc in enumerate(relevant_docs, 1):
                source = doc.metadata.get("filename", "Unknown")
                context_parts.append(f"[Source {i}: {source}]\n{doc.page_content}")
            
            context = "\n\n".join(context_parts)
            
            enhanced_prompt = f"""Based on the following context from uploaded documents, please answer the question. If the context doesn't contain enough information, say so.

Context:
{context}

Question: {query}

Answer based on the context:"""
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error querying documents: {e}")
            return query
    
    def has_documents(self) -> bool:
        """Check if any documents are loaded"""
        return self.vector_store is not None and len(self.documents_metadata) > 0
    
    def get_document_list(self) -> List[Dict]:
        """Get list of uploaded documents"""
        return self.documents_metadata
    
    def load_existing_documents(self):
        """Load existing vector store if available"""
        try:
            if Path("vector_store").exists():
                self.vector_store = FAISS.load_local("vector_store", self.embeddings)
                logger.info("Loaded existing vector store")
        except Exception as e:
            logger.error(f"Error loading existing vector store: {e}")
