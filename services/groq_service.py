
import os
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# GROQ API key from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def ask_groq(messages):
    """Send message to GROQ API and return response"""
    try:
        print("🟡 Starting GROQ API request...")
        
        if not GROQ_API_KEY:
            print("⚠️ GROQ API key not configured")
            return "GROQ API key not configured. Please set GROQ_API_KEY in environment variables."
        
        # Format messages for GROQ API
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": formatted_messages,
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "temperature": 0.7,
            "max_tokens": 1024,
            "stream": False
        }
        
        print(f"🟡 Sending request to GROQ API with {len(formatted_messages)} messages")
        print(f"🟡 Using API key: {GROQ_API_KEY[:5]}...{GROQ_API_KEY[-5:] if GROQ_API_KEY else 'None'}")
        start_time = time.time()
        
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )
        
        end_time = time.time()
        print(f"🟡 GROQ API request completed in {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("choices") and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print(f"✅ GROQ response received: {len(content)} characters")
                return content
            else:
                print("⚠️ No choices in GROQ response")
                return "No response generated from GROQ"
        else:
            print(f"❌ GROQ API error: {response.status_code}")
            print(f"Error details: {response.text}")
            return f"GROQ API error: {response.status_code}. Please check your API key and try again."
            
    except requests.exceptions.Timeout:
        print("⏰ GROQ API request timed out")
        return "GROQ API request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        print("🔌 Cannot connect to GROQ API")
        return "Cannot connect to GROQ API. Please check your internet connection."
    except Exception as e:
        print(f"💥 Error in GROQ service: {str(e)}")
        return f"An error occurred with GROQ API: {str(e)}"
