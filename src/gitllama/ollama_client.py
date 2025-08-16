"""Ollama API client for terminal chat interface."""

import json
import requests
from typing import Dict, List, Optional, Generator
import tiktoken

# TODO Properly integrate this function
def count_tokens(messages: list[dict], model: str = "gpt-4") -> int:
    """
    Counts the number of tokens in a list of messages.
    This is an estimation, as the exact token count can vary by model.
    """
    try:
        # Note: "cl100k_base" is a safe general-purpose default
        encoding = tiktoken.get_encoding("cl100k_base")
    except Exception:
        # Fallback if the encoding is not found
        encoding = tiktoken.encoding_for_model(model)
        
    num_tokens = 0
    for message in messages:
        # Every message adds a few tokens for formatting (role, content, etc.)
        num_tokens += 4 
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
    
    # Every reply is primed with <|start|>assistant<|message|>
    num_tokens += 3  
    return num_tokens

# TODO Properly integrate this function
def trim_messages(messages: list[dict], max_tokens: int) -> list[dict]:
    """
    Trims the message history to fit within the token limit.
    It preserves the first message (usually the system prompt) and
    removes messages from the beginning of the conversation.
    """
    while count_tokens(messages) > max_tokens:
        if len(messages) > 1:
            # Remove the oldest message after the system prompt
            messages.pop(1) 
        else:
            # Cannot trim further
            break
    return messages

class OllamaClient:
    """Client for interacting with local Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize the Ollama client.
        
        Args:
            base_url: The base URL for the Ollama API server
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def is_available(self) -> bool:
        """Check if Ollama server is running and accessible."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def list_models(self) -> List[str]:
        """Get list of available models."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        except requests.exceptions.RequestException:
            return []

    # TODO Properly integrate this function
    def get_model_details(self, model: str) -> Dict:
        """Get details for a specific model."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/show",
                json={"name": model}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return {}
        
    # Add this method inside your OllamaClient class
    def pull_model(self, model: str) -> bool:
        """Pull a model if it's not available locally."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json={"name": model},
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'status' in data:
                        print(f"\r{data['status']}", end='', flush=True)
                    if data.get('status') == 'success':
                        print()  # New line after completion
                        return True
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error pulling model: {e}")
            return False
    
    def chat_stream(self, model: str, messages: List[Dict[str, str]], 
                   system: Optional[str] = None) -> Generator[str, None, None]:
        """Stream chat responses from Ollama.
        
        Args:
            model: The model to use for chat
            messages: List of message dicts with 'role' and 'content'
            system: Optional system message
            
        Yields:
            Response chunks as strings
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        if system:
            payload["system"] = system
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'message' in data and 'content' in data['message']:
                        yield data['message']['content']
                    if data.get('done', False):
                        break
                        
        except requests.exceptions.RequestException as e:
            yield f"Error: {e}"