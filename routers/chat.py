
from datetime import datetime

from database.mongodb import MongoDB
from flask import Blueprint, jsonify, request
from services.claude_service import ask_claude
from services.gemini_service import ask_gemini
from services.grok_service import ask_grok
from services.openai_service import ask_openai
from services.ollama_service import ask_ollama
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB client
mongo_db = MongoDB()

# Create a blueprint for chat routes
chat_router = Blueprint('chat', __name__, url_prefix='/api')

# In-memory conversation cache (temporary, before saving to MongoDB)
conversations_cache = {}

# Default system message (used as fallback)
default_system_message = {
    "role": "system",
    "content": (
        "You are an AI assistant that provides helpful, accurate, and friendly responses. "
        "Answer user questions clearly and concisely, providing additional context when needed. "
        "If you don't know something, admit it rather than making up information."
    )
}

@chat_router.route('/chat', methods=['POST'])
def chat():
    data = request.json
    logger.info(f"📨 Received chat request: {data}")
    
    model = data.get('model', 'gpt-4o')
    message = data.get('message', '')
    conversation_id = data.get('conversation_id')
    system_prompt = data.get('system_prompt', None)
    
    logger.info(f"🎯 Processing request - Model: {model}, ConvID: {conversation_id}")
    
    try:
        # Create a new conversation if it doesn't exist
        if not conversation_id:
            logger.info("🆕 Creating new conversation...")
            if system_prompt:
                conversation_id = mongo_db.create_chat(model=model, title=message[:30], system_prompt=system_prompt)
                logger.info(f"✅ New conversation created with ID: {conversation_id} and custom system prompt")
                conversations_cache[conversation_id] = [{
                    "role": "system",
                    "content": system_prompt
                }]
            else:
                conversation_id = mongo_db.create_chat(model=model, title=message[:30])
                logger.info(f"✅ New conversation created with ID: {conversation_id} with default system prompt")
                conversations_cache[conversation_id] = [default_system_message]
        elif conversation_id not in conversations_cache:
            logger.info(f"📚 Loading conversation history for ID: {conversation_id}")
            messages_db = mongo_db.get_chat_history(conversation_id)
            
            chat_data = mongo_db.get_chat_by_id(conversation_id)
            system_prompt_content = chat_data.get('system_prompt', default_system_message["content"]) if chat_data else default_system_message["content"]
            
            conversations_cache[conversation_id] = [{
                "role": "system",
                "content": system_prompt_content
            }]
            
            for msg in messages_db:
                if msg["role"] != "system":
                    conversations_cache[conversation_id].append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
        
        # Add user message to conversation cache
        conversations_cache[conversation_id].append({
            "role": "user",
            "content": message
        })
        
        # Save user message to MongoDB
        logger.info("💾 Saving user message to MongoDB...")
        mongo_db.save_message(conversation_id, "user", message)
        
        # Get response based on selected model
        logger.info(f"🤖 Getting response from {model}...")
        response_text = ""
        
        try:
            if model in ['gpt-4o', 'gpt-4o-mini']:
                logger.info(f"🔵 Calling OpenAI with model {model}")
                response_text = ask_openai(conversations_cache[conversation_id], model)
            elif model == 'gemini-2.0-flash':
                logger.info("🟢 Calling Gemini API")
                response_text = ask_gemini(conversations_cache[conversation_id])
            elif model == 'claude-3-sonnet':
                logger.info("🟣 Calling Claude API")
                response_text = ask_claude(conversations_cache[conversation_id])
            elif model == 'grok-2':
                logger.info("🟡 Calling Grok API")
                response_text = ask_grok(conversations_cache[conversation_id])
            elif model == 'phi3:mini':
                logger.info("🟠 Calling Ollama with phi3:mini")
                response_text = ask_ollama(conversations_cache[conversation_id], model)
            else:
                logger.warning(f"⚠️ Unknown model {model}, defaulting to OpenAI")
                response_text = ask_openai(conversations_cache[conversation_id], "gpt-4o")
            
            logger.info(f"✅ Response received from {model}: {len(response_text)} characters")
            
        except Exception as model_error:
            logger.error(f"❌ Error with {model}: {str(model_error)}")
            # Fallback to a working model
            logger.info("🔄 Attempting fallback to Gemini...")
            try:
                response_text = ask_gemini(conversations_cache[conversation_id])
                logger.info("✅ Fallback successful")
            except Exception as fallback_error:
                logger.error(f"❌ Fallback failed: {str(fallback_error)}")
                response_text = f"Sorry, I encountered an error processing your request with {model}. Please try again or switch to a different model."
        
        # Add assistant response to conversation cache
        conversations_cache[conversation_id].append({
            "role": "assistant",
            "content": response_text
        })
        
        # Save assistant response to MongoDB
        logger.info("💾 Saving assistant response to MongoDB...")
        mongo_db.save_message(conversation_id, "assistant", response_text)
        
        logger.info(f"🎉 Request completed successfully for conversation {conversation_id}")
        
        return jsonify({
            "role": "assistant",
            "content": response_text,
            "conversation_id": conversation_id
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"💥 Detailed error: {error_details}")
        return jsonify({
            "error": str(e),
            "details": error_details
        }), 500

# ... keep existing code (other endpoints like get_chats, delete_chat, etc.)
@chat_router.route('/chats', methods=['GET'])
def get_chats():
    try:
        chats = mongo_db.get_all_chats()
        return jsonify({"chats": chats})
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@chat_router.route('/chats/<chat_id>', methods=['GET'])
def get_chat_history(chat_id):
    try:
        limit = request.args.get('limit', 50, type=int)
        messages = mongo_db.get_chat_history(chat_id, limit)
        return jsonify({"messages": messages})
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@chat_router.route('/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    try:
        success = mongo_db.delete_chat(chat_id)
        
        if success:
            if chat_id in conversations_cache:
                del conversations_cache[chat_id]
            
            return jsonify({
                "success": True,
                "message": "Chat deleted successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to delete chat"
            }), 500
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@chat_router.route('/chats/<chat_id>/system-prompt', methods=['PATCH'])
def update_system_prompt(chat_id):
    try:
        data = request.json
        system_prompt = data.get('system_prompt', '')
        
        success = mongo_db.update_system_prompt(chat_id, system_prompt)
        
        if success:
            if chat_id in conversations_cache:
                system_idx = next((i for i, msg in enumerate(conversations_cache[chat_id]) if msg["role"] == "system"), None)
                
                if system_idx is not None:
                    conversations_cache[chat_id][system_idx]["content"] = system_prompt
                else:
                    conversations_cache[chat_id].insert(0, {
                        "role": "system",
                        "content": system_prompt
                    })
            
            return jsonify({
                "success": True,
                "message": "System prompt updated successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to update system prompt"
            }), 500
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
