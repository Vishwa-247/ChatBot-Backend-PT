import hashlib
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class CloudStorageService:
    """Service for handling file storage in cloud environments"""
    
    def __init__(self):
        self.storage_type = os.getenv("STORAGE_TYPE", "local")  # local, s3, mongodb
        self.documents_dir = Path("documents")
        self.documents_dir.mkdir(exist_ok=True)
        
    def save_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Save file and return metadata"""
        file_hash = hashlib.md5(file_content).hexdigest()[:10]
        extension = Path(filename).suffix
        safe_filename = f"{file_hash}_{filename}"
        
        if self.storage_type == "local":
            return self._save_local(file_content, safe_filename, filename)
        elif self.storage_type == "mongodb":
            return self._save_mongodb(file_content, safe_filename, filename)
        else:
            # Default to local storage
            return self._save_local(file_content, safe_filename, filename)
    
    def _save_local(self, file_content: bytes, safe_filename: str, original_filename: str) -> Dict[str, Any]:
        """Save file locally (for development)"""
        file_path = self.documents_dir / safe_filename
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
            
        return {
            "storage_type": "local",
            "file_path": str(file_path),
            "filename": original_filename,
            "safe_filename": safe_filename,
            "file_size": len(file_content),
            "upload_time": str(datetime.now())
        }
    
    def _save_mongodb(self, file_content: bytes, safe_filename: str, original_filename: str) -> Dict[str, Any]:
        """Save file metadata to MongoDB (file content stored as binary)"""
        try:
            from database.mongodb import MongoDB
            mongo_db = MongoDB()
            
            # Store file metadata and content in MongoDB
            file_data = {
                "filename": original_filename,
                "safe_filename": safe_filename,
                "file_content": file_content,  # Binary content
                "file_size": len(file_content),
                "upload_time": datetime.utcnow(),
                "storage_type": "mongodb"
            }
            
            # Use a separate collection for files
            result = mongo_db.db["files"].insert_one(file_data)
            
            return {
                "storage_type": "mongodb",
                "file_id": str(result.inserted_id),
                "filename": original_filename,
                "safe_filename": safe_filename,
                "file_size": len(file_content),
                "upload_time": str(datetime.now())
            }
            
        except Exception as e:
            logger.error(f"Error saving file to MongoDB: {e}")
            # Fallback to local storage
            return self._save_local(file_content, safe_filename, original_filename)
    
    def get_file_content(self, file_metadata: Dict[str, Any]) -> Optional[bytes]:
        """Retrieve file content based on storage type"""
        try:
            if file_metadata["storage_type"] == "local":
                file_path = file_metadata["file_path"]
                with open(file_path, 'rb') as f:
                    return f.read()
                    
            elif file_metadata["storage_type"] == "mongodb":
                from database.mongodb import MongoDB
                mongo_db = MongoDB()
                
                file_id = file_metadata["file_id"]
                file_doc = mongo_db.db["files"].find_one({"_id": file_id})
                
                if file_doc and "file_content" in file_doc:
                    return file_doc["file_content"]
                    
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving file content: {e}")
            return None
    
    def delete_file(self, file_metadata: Dict[str, Any]) -> bool:
        """Delete file based on storage type"""
        try:
            if file_metadata["storage_type"] == "local":
                file_path = file_metadata["file_path"]
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
                    
            elif file_metadata["storage_type"] == "mongodb":
                from database.mongodb import MongoDB
                mongo_db = MongoDB()
                
                file_id = file_metadata["file_id"]
                result = mongo_db.db["files"].delete_one({"_id": file_id})
                return result.deleted_count > 0
                
            return False
            
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False 
