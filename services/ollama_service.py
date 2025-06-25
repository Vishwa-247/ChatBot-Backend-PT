import json
import time

import requests

OLLAMA_BASE_URL = "http://localhost:11434"

class OllamaService:
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL

    def is_available(self):
        """Check if Ollama service is running"""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def ask(self, messages, model="phi3:mini"):
        """Send message to Ollama and return response with optimizations"""
        try:
            print(f"Starting Ollama request with model: {model}")
            
            if not self.is_available():
                return "Ollama service is not running. Please start Ollama and ensure the phi3:mini model is installed."
            
            # Format messages for Ollama
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            print(f"Formatted {len(formatted_messages)} messages")
            
            # Optimized request payload
            payload = {
                "model": model,
                "messages": formatted_messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_ctx": 2048,  # Reduce context window for faster processing
                    "num_predict": 512,  # Limit response length for speed
                    "repeat_penalty": 1.1,
                    "mirostat": 2,  # Enable mirostat for better quality/speed balance
                    "mirostat_tau": 5.0,
                    "mirostat_eta": 0.1,
                }
            }
            
            print("Sending optimized request to Ollama...")
            start_time = time.time()
            
            # Make request with longer timeout but optimized settings
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60,  # Increased timeout
                headers={"Content-Type": "application/json"}
            )
            
            end_time = time.time()
            print(f"Ollama request completed in {end_time - start_time:.2f} seconds")
            
            if response.status_code == 200:
                result = response.json()
                if "message" in result and "content" in result["message"]:
                    content = result["message"]["content"]
                    print(f"Received response: {len(content)} characters")
                    return content
                else:
                    print(f"Unexpected response format: {result}")
                    return "Received unexpected response format from Ollama"
            else:
                error_msg = f"Ollama request failed with status {response.status_code}: {response.text}"
                print(error_msg)
                return error_msg
                
        except requests.exceptions.Timeout:
            return "Request to Ollama timed out. The model might be processing a complex query."
        except requests.exceptions.ConnectionError:
            return "Could not connect to Ollama. Please ensure Ollama is running on localhost:11434"
        except Exception as e:
            error_msg = f"Error communicating with Ollama: {str(e)}"
            print(error_msg)
            return error_msg
