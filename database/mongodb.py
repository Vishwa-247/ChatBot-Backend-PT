
import os
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "AI_Chat_db"  # Fixed database name

class MongoDB:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.chats = self.db["chats"]
        self.messages = self.db["messages"]
    
    def create_chat(self, user_id="anonymous", title="New Chat", model="gemini-2.0-flash", system_prompt=None):
        """Create a new chat and return its ID"""
        chat_data = {
            "user_id": user_id,
            "title": title,
            "model": model,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        if system_prompt:
            chat_data["system_prompt"] = system_prompt
        
        result = self.chats.insert_one(chat_data)
        return str(result.inserted_id)
    
    def save_message(self, chat_id, role, content):
        """Save a message to the chat history"""
        try:
            message_data = {
                "chat_id": chat_id,
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow()
            }
            
            self.messages.insert_one(message_data)
            
            # Update chat's last updated timestamp
            if ObjectId.is_valid(chat_id):
                self.chats.update_one(
                    {"_id": ObjectId(chat_id)}, 
                    {"$set": {"updated_at": datetime.utcnow()}}
                )
            
            return True
        except Exception as e:
            print(f"Error saving message: {e}")
            return False
    
    def get_chat_history(self, chat_id, limit=50):
        """Get messages for a specific chat"""
        try:
            messages = list(self.messages.find(
                {"chat_id": chat_id}
            ).sort("timestamp", 1).limit(limit))
            
            # Convert ObjectId to string
            for msg in messages:
                if "_id" in msg:
                    msg["_id"] = str(msg["_id"])
                    
            return messages
        except Exception as e:
            print(f"Error getting chat history: {e}")
            return []
    
    def get_chat_by_id(self, chat_id):
        """Get a chat by its ID"""
        try:
            if ObjectId.is_valid(chat_id):
                chat = self.chats.find_one({"_id": ObjectId(chat_id)})
            else:
                chat = self.chats.find_one({"_id": chat_id})
            
            if chat and "_id" in chat:
                chat["_id"] = str(chat["_id"])
                    
            return chat
        except Exception as e:
            print(f"Error getting chat by ID: {e}")
            return None
    
    def get_all_chats(self, user_id="anonymous", limit=20):
        """Get all chats for a user"""
        try:
            chats = list(self.chats.find(
                {"user_id": user_id}
            ).sort("updated_at", -1).limit(limit))
            
            # Convert ObjectId to string
            for chat in chats:
                if "_id" in chat:
                    chat["_id"] = str(chat["_id"])
                    
            return chats
        except Exception as e:
            print(f"Error getting all chats: {e}")
            return []
    
    def delete_chat(self, chat_id):
        """Delete a chat and all its messages"""
        try:
            # Delete all messages in the chat
            self.messages.delete_many({"chat_id": chat_id})
            
            # Delete the chat itself
            if ObjectId.is_valid(chat_id):
                self.chats.delete_one({"_id": ObjectId(chat_id)})
            else:
                self.chats.delete_one({"_id": chat_id})
            
            return True
        except Exception as e:
            print(f"Error deleting chat: {e}")
            return False
            
    def update_system_prompt(self, chat_id, system_prompt):
        """Update the system prompt for a chat"""
        try:
            if ObjectId.is_valid(chat_id):
                result = self.chats.update_one(
                    {"_id": ObjectId(chat_id)},
                    {"$set": {"system_prompt": system_prompt, "updated_at": datetime.utcnow()}}
                )
            else:
                result = self.chats.update_one(
                    {"_id": chat_id},
                    {"$set": {"system_prompt": system_prompt, "updated_at": datetime.utcnow()}}
                )
            
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating system prompt: {e}")
            return False
