import hashlib
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import cloudinary
import cloudinary.api
import cloudinary.uploader
import requests

logger = logging.getLogger(__name__)

class CloudinaryService:
    """Service for handling file storage with Cloudinary"""
    
    def __init__(self):
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET")
        )
        
        self.folder = "ai-chatbot-documents"
        
    def upload_file(self, file_content: bytes, filename: str, chat_id: str = None) -> Dict[str, Any]:
        """Upload file to Cloudinary and return metadata"""
        try:
            # Generate unique public ID
            file_hash = hashlib.md5(file_content).hexdigest()[:10]
            extension = os.path.splitext(filename)[1]
            safe_filename = f"{file_hash}_{filename}"
            
            # Create folder structure: ai-chatbot-documents/chat_id/filename
            if chat_id:
                public_id = f"{self.folder}/{chat_id}/{safe_filename}"
            else:
                public_id = f"{self.folder}/{safe_filename}"
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file_content,
                public_id=public_id,
                resource_type="auto",  # Auto-detect file type
                overwrite=True,
                folder=self.folder
            )
            
            # Extract relevant metadata
            file_metadata = {
                "storage_type": "cloudinary",
                "public_id": upload_result.get("public_id"),
                "url": upload_result.get("secure_url"),
                "filename": filename,
                "safe_filename": safe_filename,
                "file_size": len(file_content),
                "file_type": upload_result.get("format"),
                "upload_time": str(datetime.now()),
                "chat_id": chat_id,
                "cloudinary_id": upload_result.get("public_id")
            }
            
            logger.info(f"Successfully uploaded {filename} to Cloudinary: {upload_result.get('public_id')}")
            return file_metadata
            
        except Exception as e:
            logger.error(f"Error uploading file {filename} to Cloudinary: {e}")
            raise Exception(f"Cloudinary upload failed: {str(e)}")
    
    def download_file(self, file_metadata: Dict[str, Any]) -> Optional[bytes]:
        """Download file content from Cloudinary"""
        try:
            url = file_metadata.get("url")
            if not url:
                logger.error("No URL found in file metadata")
                return None
            
            # Download file content
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error downloading file from Cloudinary: {e}")
            return None
    
    def delete_file(self, file_metadata: Dict[str, Any]) -> bool:
        """Delete file from Cloudinary"""
        try:
            public_id = file_metadata.get("public_id")
            if not public_id:
                logger.error("No public_id found in file metadata")
                return False
            
            # Delete from Cloudinary
            result = cloudinary.uploader.destroy(public_id)
            
            if result.get("result") == "ok":
                logger.info(f"Successfully deleted file from Cloudinary: {public_id}")
                return True
            else:
                logger.error(f"Failed to delete file from Cloudinary: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file from Cloudinary: {e}")
            return False
    
    def get_file_url(self, file_metadata: Dict[str, Any], transformation: str = None) -> str:
        """Get file URL with optional transformations"""
        try:
            url = file_metadata.get("url")
            if not url:
                return ""
            
            if transformation:
                # Apply Cloudinary transformations
                public_id = file_metadata.get("public_id")
                if public_id:
                    return cloudinary.CloudinaryImage(public_id).build_url(
                        transformation=transformation
                    )
            
            return url
            
        except Exception as e:
            logger.error(f"Error generating file URL: {e}")
            return file_metadata.get("url", "")
    
    def list_files(self, chat_id: str = None, limit: int = 100) -> list:
        """List files in Cloudinary folder"""
        try:
            # Build search query
            if chat_id:
                search_query = f"folder:{self.folder}/{chat_id}"
            else:
                search_query = f"folder:{self.folder}"
            
            # Search for resources
            result = cloudinary.api.resources(
                type="upload",
                prefix=search_query,
                max_results=limit
            )
            
            files = []
            for resource in result.get("resources", []):
                file_info = {
                    "public_id": resource.get("public_id"),
                    "url": resource.get("secure_url"),
                    "filename": os.path.basename(resource.get("public_id", "")),
                    "file_size": resource.get("bytes", 0),
                    "file_type": resource.get("format"),
                    "upload_time": resource.get("created_at"),
                    "chat_id": chat_id
                }
                files.append(file_info)
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files from Cloudinary: {e}")
            return []
    
    def get_upload_presets(self) -> Dict[str, Any]:
        """Get Cloudinary upload presets for frontend direct uploads"""
        try:
            presets = cloudinary.api.upload_presets()
            return {
                "cloud_name": os.getenv("CLOUDINARY_CLOUD_NAME"),
                "upload_preset": "ai_chatbot_uploads",  # You can create this preset
                "folder": self.folder
            }
        except Exception as e:
            logger.error(f"Error getting upload presets: {e}")
            return {}
    
    def is_configured(self) -> bool:
        """Check if Cloudinary is properly configured"""
        return all([
            os.getenv("CLOUDINARY_CLOUD_NAME"),
            os.getenv("CLOUDINARY_API_KEY"),
            os.getenv("CLOUDINARY_API_SECRET")
        ]) 
