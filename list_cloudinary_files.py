import os

from services.cloudinary_service import CloudinaryService


def list_all_cloudinary_files():
    """List all files stored in Cloudinary"""
    print("🔍 Checking Cloudinary Document Storage")
    print("=" * 50)
    
    try:
        # Initialize Cloudinary service
        cloudinary_service = CloudinaryService()
        
        if not cloudinary_service.is_configured():
            print("❌ Cloudinary is not configured")
            return
        
        print("✅ Cloudinary is configured")
        print(f"📁 Folder: {cloudinary_service.folder}")
        print("\n📋 Listing all files...")
        
        # List all files in the main folder
        all_files = cloudinary_service.list_files(limit=100)
        
        if not all_files:
            print("📭 No files found in Cloudinary")
            return
        
        print(f"📊 Found {len(all_files)} files:")
        print("-" * 50)
        
        # Group files by chat ID
        files_by_chat = {}
        for file_info in all_files:
            filename = file_info.get('filename', 'Unknown')
            file_size = file_info.get('file_size', 0)
            upload_time = file_info.get('upload_time', 'Unknown')
            public_id = file_info.get('public_id', 'Unknown')
            
            # Extract chat ID from public_id
            parts = public_id.split('/')
            if len(parts) >= 3:
                chat_id = parts[2]  # ai-chatbot-documents/chat_id/filename
            else:
                chat_id = "root"
            
            if chat_id not in files_by_chat:
                files_by_chat[chat_id] = []
            
            files_by_chat[chat_id].append({
                'filename': filename,
                'size': file_size,
                'upload_time': upload_time,
                'public_id': public_id
            })
        
        # Display files grouped by chat
        for chat_id, files in files_by_chat.items():
            print(f"\n💬 Chat ID: {chat_id}")
            print(f"📄 Files: {len(files)}")
            print("-" * 30)
            
            for i, file_info in enumerate(files, 1):
                size_mb = file_info['size'] / (1024 * 1024) if file_info['size'] > 0 else 0
                print(f"{i}. 📄 {file_info['filename']}")
                print(f"   📏 Size: {size_mb:.2f} MB")
                print(f"   📅 Upload: {file_info['upload_time']}")
                print(f"   🔗 ID: {file_info['public_id']}")
                print()
        
        print("=" * 50)
        print("✅ Cloudinary file listing complete!")
        
    except Exception as e:
        print(f"❌ Error listing Cloudinary files: {e}")

def check_specific_chat_files(chat_id):
    """Check files for a specific chat ID"""
    print(f"🔍 Checking files for Chat ID: {chat_id}")
    print("=" * 50)
    
    try:
        cloudinary_service = CloudinaryService()
        
        if not cloudinary_service.is_configured():
            print("❌ Cloudinary is not configured")
            return
        
        # List files for specific chat
        chat_files = cloudinary_service.list_files(chat_id=chat_id, limit=50)
        
        if not chat_files:
            print(f"📭 No files found for chat {chat_id}")
            return
        
        print(f"📊 Found {len(chat_files)} files for chat {chat_id}:")
        print("-" * 50)
        
        for i, file_info in enumerate(chat_files, 1):
            filename = file_info.get('filename', 'Unknown')
            file_size = file_info.get('file_size', 0)
            upload_time = file_info.get('upload_time', 'Unknown')
            
            size_mb = file_size / (1024 * 1024) if file_size > 0 else 0
            print(f"{i}. 📄 {filename}")
            print(f"   📏 Size: {size_mb:.2f} MB")
            print(f"   📅 Upload: {upload_time}")
            print()
        
    except Exception as e:
        print(f"❌ Error checking chat files: {e}")

if __name__ == "__main__":
    print("🚀 Cloudinary Document Storage Checker")
    print("=" * 50)
    
    # Check if environment variables are set
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
    api_key = os.getenv('CLOUDINARY_API_KEY')
    api_secret = os.getenv('CLOUDINARY_API_SECRET')
    
    print(f"🔧 Cloud Name: {cloud_name or 'Not set'}")
    print(f"🔑 API Key: {api_key[:10] + '...' if api_key else 'Not set'}")
    print(f"🔐 API Secret: {api_secret[:10] + '...' if api_secret else 'Not set'}")
    print()
    
    # List all files
    list_all_cloudinary_files()
    
    # You can also check specific chat files
    # Uncomment the line below and replace with your chat ID
    # check_specific_chat_files("your_chat_id_here") 
