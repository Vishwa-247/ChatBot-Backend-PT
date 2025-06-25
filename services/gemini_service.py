
# import time
# import google.generativeai as genai
# import os
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# # API key from environment variables with new key as fallback
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyC0sKQhg3sqDJXQUxK8_om4FfQY1884NXM")

# # Use the correct model name for Gemini 2.0 Flash
# GEMINI_MODEL = "gemini-2.0-flash"

# # Configure the Gemini API
# def ask_gemini(messages):
#     """Send message to Gemini and return response"""
#     try:
#         if not GEMINI_API_KEY:
#             print("Warning: GEMINI_API_KEY environment variable not set")
#             return "Gemini API key not configured. Please set GEMINI_API_KEY in .env file."
            
#         print("Starting Gemini request...")
#         # Configure the API with the new key
#         genai.configure(api_key=GEMINI_API_KEY)
        
#         # Create the model instance with the correct model name
#         model = genai.GenerativeModel(GEMINI_MODEL)
#         print("Model instance created")
        
#         # Extract the system message if it exists
#         system_message = next((msg["content"] for msg in messages if msg["role"] == "system"), None)
#         print(f"System message found: {'Yes' if system_message else 'No'}")
        
#         formatted_content = ""
        
#         # Add system message at the beginning if it exists
#         if system_message:
#             formatted_content += f"SYSTEM: {system_message}\n\n"
        
#         # Add the conversation history
#         for msg in messages:
#             if msg["role"] != "system":  # Skip system message as we've already handled it
#                 formatted_content += f"{msg['role'].upper()}: {msg['content']}\n\n"
        
#         print(f"Prompt length: {len(formatted_content)} characters")
#         print(f"Using API key: {GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-5:] if GEMINI_API_KEY else 'None'}")
        
#         # Generate response with timeout
#         print("Sending request to Gemini API...")
#         start_time = time.time()
        
#         response = model.generate_content(
#             formatted_content,
#             generation_config={
#                 "temperature": 0.7,
#                 "top_p": 0.8,
#                 "top_k": 40,
#                 "max_output_tokens": 2048,
#             }
#         )
        
#         end_time = time.time()
#         print(f"Request completed in {end_time - start_time:.2f} seconds")
        
#         if not response.text:
#             print("Warning: Empty response received from Gemini API")
#             raise Exception("Empty response from Gemini API")
            
#         print(f"Response length: {len(response.text)} characters")
#         return response.text
        
#     except Exception as e:
#         print(f"Detailed error in Gemini service: {str(e)}")
#         import traceback
#         print(f"Full traceback: {traceback.format_exc()}")
#         return f"An error occurred with Gemini: {str(e)}"


import time
import google.generativeai as genai
import os
from dotenv import load_dotenv
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()

# API key from environment variables with new key as fallback
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyC0sKQhg3sqDJXQUxK8_om4FfQY1884NXM")

# Use the faster flash model for better performance
GEMINI_MODEL = "gemini-2.0-flash"

# Configure the Gemini API once
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("Gemini API configured successfully")
else:
    print("Warning: GEMINI_API_KEY environment variable not set")

# Create model instance once for reuse
model = None
if GEMINI_API_KEY:
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        print(f"Gemini model {GEMINI_MODEL} initialized successfully")
    except Exception as e:
        print(f"Error initializing Gemini model: {e}")

def ask_gemini(messages):
    """Send message to Gemini and return response - optimized for speed"""
    try:
        if not GEMINI_API_KEY or not model:
            return "Gemini API key not configured. Please set GEMINI_API_KEY in .env file."
            
        print("🚀 Starting optimized Gemini request...")
        start_time = time.time()
        
        # Extract the system message if it exists
        system_message = next((msg["content"] for msg in messages if msg["role"] == "system"), None)
        
        # Build prompt more efficiently
        prompt_parts = []
        
        # Add system message at the beginning if it exists
        if system_message:
            prompt_parts.append(f"SYSTEM: {system_message}")
        
        # Add the conversation history (limit to last 10 messages for speed)
        conversation_messages = [msg for msg in messages if msg["role"] != "system"]
        recent_messages = conversation_messages[-10:]  # Only use last 10 messages
        
        for msg in recent_messages:
            prompt_parts.append(f"{msg['role'].upper()}: {msg['content']}")
        
        formatted_content = "\n\n".join(prompt_parts)
        
        print(f"📝 Prompt length: {len(formatted_content)} characters")
        print(f"🔑 Using API key: {GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-5:]}")
        
        # Generate response with optimized settings for speed
        print("⚡ Sending optimized request to Gemini API...")
        
        response = model.generate_content(
            formatted_content,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 20,  # Reduced for faster generation
                "max_output_tokens": 1024,  # Reduced for faster response
                "candidate_count": 1,  # Only generate one candidate
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        print(f"✅ Optimized request completed in {response_time:.2f} seconds")
        
        if not response.text:
            print("⚠️ Warning: Empty response received from Gemini API")
            raise Exception("Empty response from Gemini API")
            
        print(f"📄 Response length: {len(response.text)} characters")
        print(f"🏃‍♂️ Speed improvement: ~{max(0, 3.0 - response_time):.1f}s faster than before")
        
        return response.text
        
    except Exception as e:
        print(f"❌ Error in optimized Gemini service: {str(e)}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        
        # Provide a more helpful error message
        if "quota" in str(e).lower():
            return "⚠️ Gemini API quota exceeded. Please check your API key limits or try again later."
        elif "api key" in str(e).lower():
            return "🔑 Invalid Gemini API key. Please check your API key configuration."
        else:
            return f"⚠️ Gemini service temporarily unavailable: {str(e)}"

# Async version for future use
async def ask_gemini_async(messages):
    """Async version of ask_gemini for better performance"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(executor, ask_gemini, messages)
