
import json
import hashlib
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SimpleVectorStore:
    """Simple in-memory vector store as ChromaDB alternative"""
    
    def __init__(self, storage_dir: str = "vector_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        self.embeddings = []
        self.documents = []
        self.metadata = []
        
        # Load existing data
        self.load_data()
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def add_documents(self, documents: List[str], metadatas: List[Dict] = None):
        """Add documents to the vector store"""
        if metadatas is None:
            metadatas = [{}] * len(documents)
        
        try:
            # Generate embeddings
            embeddings = self.embedding_model.encode(documents)
            
            # Add to storage
            for doc, embedding, metadata in zip(documents, embeddings, metadatas):
                self.documents.append(doc)
                self.embeddings.append(embedding.tolist())
                self.metadata.append(metadata)
            
            # Save to disk
            self.save_data()
            
            logger.info(f"Added {len(documents)} documents to vector store")
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def similarity_search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for similar documents"""
        if not self.documents:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0]
            
            # Calculate similarities
            similarities = []
            for i, doc_embedding in enumerate(self.embeddings):
                similarity = np.dot(query_embedding, doc_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                )
                similarities.append((similarity, i))
            
            # Sort by similarity and get top k
            similarities.sort(reverse=True)
            
            results = []
            for similarity, idx in similarities[:k]:
                results.append({
                    "document": self.documents[idx],
                    "metadata": self.metadata[idx],
                    "similarity": float(similarity)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    def save_data(self):
        """Save vector store data to disk"""
        try:
            data = {
                "documents": self.documents,
                "embeddings": self.embeddings,
                "metadata": self.metadata
            }
            
            with open(self.storage_dir / "vector_store.json", 'w') as f:
                json.dump(data, f)
                
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
    
    def load_data(self):
        """Load vector store data from disk"""
        try:
            file_path = self.storage_dir / "vector_store.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                self.documents = data.get("documents", [])
                self.embeddings = data.get("embeddings", [])
                self.metadata = data.get("metadata", [])
                
                logger.info(f"Loaded {len(self.documents)} documents from storage")
                
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")

class RAGService:
    def __init__(self):
        self.vector_store = SimpleVectorStore()
    
    def add_document(self, text: str, chunks: List[str], metadata: Dict):
        """Add a processed document to RAG"""
        try:
            # Prepare metadata for each chunk
            chunk_metadatas = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_index": i,
                    "chunk_id": hashlib.md5(chunk.encode()).hexdigest()[:10]
                })
                chunk_metadatas.append(chunk_metadata)
            
            # Add chunks to vector store
            self.vector_store.add_documents(chunks, chunk_metadatas)
            
            logger.info(f"Added document with {len(chunks)} chunks to RAG")
            
        except Exception as e:
            logger.error(f"Error adding document to RAG: {e}")
            raise
    
    def retrieve_relevant_chunks(self, query: str, k: int = 5) -> List[Dict]:
        """Retrieve relevant document chunks for a query"""
        try:
            results = self.vector_store.similarity_search(query, k)
            
            # Filter by minimum similarity threshold
            filtered_results = [r for r in results if r["similarity"] > 0.3]
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []
    
    def generate_rag_prompt(self, query: str, retrieved_chunks: List[Dict]) -> str:
        """Generate a prompt with retrieved context"""
        if not retrieved_chunks:
            return query
        
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            source = chunk["metadata"].get("filename", "Unknown")
            context_parts.append(f"[Source {i}: {source}]\n{chunk['document']}")
        
        context = "\n\n".join(context_parts)
        
        prompt = f"""Based on the following context, please answer the question. If the context doesn't contain enough information to answer the question, please say so.

Context:
{context}

Question: {query}

Answer:"""
        
        return prompt
    
    def get_citations(self, retrieved_chunks: List[Dict]) -> List[Dict]:
        """Extract citations from retrieved chunks"""
        citations = []
        seen_sources = set()
        
        for chunk in retrieved_chunks:
            metadata = chunk["metadata"]
            source_id = metadata.get("filename", "Unknown")
            
            if source_id not in seen_sources:
                citations.append({
                    "source": source_id,
                    "filename": metadata.get("filename", "Unknown"),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "similarity": chunk["similarity"]
                })
                seen_sources.add(source_id)
        
        return citations
