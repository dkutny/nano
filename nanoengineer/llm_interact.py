from typing import List, Dict, Any, Optional, Union
import json
from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate_response(self,
                          messages: List[Dict[str, Any]],
                          system_prompt: str="",
                          **kwargs) -> str:
        """Generate a response from the LLM"""
        pass

class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider implementation"""
    
    def __init__(self, model: str, api_key: Optional[str] = None):
        try:
            import anthropic
            self.client = anthropic.Client(api_key=api_key)
            self.model=model
        except ImportError:
            raise ImportError("Please install anthropic package: pip install anthropic")

    
    def generate_response(self,
                          messages: List[Dict[str, Any]],
                          system_prompt: str="",
                          **kwargs) -> str:
        # Convert history format to Anthropic messages format
        formatted_messages = []
        for msg in messages:
            role = "assistant" if msg.get("role") == "assistant" else "user"
            content = msg.get("content", "")
            formatted_messages.append({"role": role, "content": content})
        
        response = self.client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=formatted_messages,
            max_tokens=kwargs.get("max_tokens", 1000)
        )
        return response.content[0].text

class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider implementation"""
    
    def __init__(self, model: str, api_key: Optional[str] = None):
        try:
            import openai
            self.client = openai.Client(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("Please install openai package: pip install openai")
    
    def generate_response(self,
                          messages: List[Dict[str, Any]],
                          system_prompt: str="",
                          **kwargs) -> str:
        if system_prompt != "":
            messages = [
                {"role": "developer", "content": [{"type": "text", "text": system_prompt}]},
                *messages
            ]
        response = self.client.chat.completions.create(
            model=self.model,#kwargs.get("model", "gpt-4"),
            messages=messages,
            max_tokens=kwargs.get("max_tokens", 1000)
        )
        
        return response.choices[0].message.content


class OllamaProvider(BaseLLMProvider):
    """Ollama provider implementation"""
    
    def __init__(self, model: str, api_key: Optional[str] = None):
        try:
            import ollama
            self.client = ollama
            self.model = model
        except ImportError:
            raise ImportError("Please install ollama package: pip install ollama")
    
    def generate_response(self,
                          messages: List[Dict[str, Any]], 
                          system_prompt: str="",
                          **kwargs) -> str:
        # Convert history format to Ollama messages format
        formatted_messages = []

        if system_prompt:
            formatted_messages.insert(0, {"role": "system", "content": system_prompt})
            
        for msg in messages:
            role = "assistant" if msg.get("role") == "assistant" else "user"
            content = msg.get("content", "")
            formatted_messages.append({"role": role, "content": content})

            
        response = self.client.chat(
            model=self.model,
            messages=formatted_messages,
            stream=False
        )
        
        return response['message']['content']


class LLMInteract:
    """Main class for interacting with LLMs"""
    
    PROVIDERS = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "ollama": OllamaProvider
    }
    
    def __init__(self, provider: str, model: str, api_key: Optional[str] = None, **kwargs):
        """
        Initialize LLM interaction
        
        Args:
            provider: String identifier for the LLM provider (e.g., "anthropic/claude")
            api_key: Optional API key for the provider
            **kwargs: Additional provider-specific configuration
        """
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}. Available providers: {list(self.PROVIDERS.keys())}")
        
        self.provider_class = self.PROVIDERS[provider]
        self.provider = self.provider_class(model=model, api_key=api_key)
        self.history: List[Dict[str, Any]] = []
        self.config = kwargs

    def set_system_prompt(self, system_prompt: str):
        self.system_prompt = system_prompt
    
    def append(self, content: Union[str, Dict[str, Any]], role: str = "user", schema: Optional[str] = None) -> 'LLMInteract':
        """
        Append a message to the conversation history
        
        Args:
            content: Message content (string or dict)
            role: Message role (default: "user")
            schema: Optional response format schema ("json" for JSON responses)
        
        Returns:
            self for method chaining
        """
        if isinstance(content, dict):
            message = {"role": role, "content": json.dumps(content)}
        else:
            message = {"role": role, "content": content}
        
        if schema:
            message["schema"] = schema
        
        self.history.append(message)
        return self
    
    def response(self, **kwargs) -> str:
        """
        Generate a response based on the conversation history
        
        Args:
            **kwargs: Additional provider-specific parameters
        
        Returns:
            Generated response string
        """
        if not self.history:
            raise ValueError("No messages in history")
        
        # Check if JSON schema is requested
        last_message = self.history[-1]
        if last_message.get("schema") == "json":
            kwargs["format"] = "json"
        
        # Merge with default config
        params = {**self.config, **kwargs}
        
        return self.provider.generate_response(self.history,
                                               system_prompt=self.system_prompt,
                                               **params)
    
    def last_msg(self):
        return self.history[-1]
    
    def clear_history(self) -> 'LLMInteract':
        """Clear conversation history"""
        self.history = []
        return self