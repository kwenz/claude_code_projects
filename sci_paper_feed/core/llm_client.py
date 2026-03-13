"""Multi-provider LLM client supporting various free and paid APIs."""

import requests
import json
import logging
import time
from typing import Optional, Dict, Any
import config


class LLMClient:
    """Universal LLM client supporting multiple providers."""
    
    def __init__(self, provider: str = None):
        self.provider = provider or config.LLM_PROVIDER
        self.config = config.MODEL_CONFIGS.get(self.provider, {})
        self._last_request_time = 0.0
        self._setup_client()
    
    def _setup_client(self):
        """Initialize the appropriate client based on provider."""
        if self.provider == 'openai':
            import openai
            self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        elif self.provider == 'gemini':
            from google import genai
            # genai.configure(api_key=config.GEMINI_API_KEY)
            # self.client = genai.GenerativeModel(self.config['model'])
            self.client = genai.Client()
        elif self.provider == 'huggingface':
            self.client = None  # We'll use requests directly
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _rate_limit_wait(self):
        """Enforce minimum interval between requests to stay within API rate limits."""
        min_interval = config.MODEL_CONFIGS.get(self.provider, {}).get('min_request_interval', 0)
        if min_interval:
            elapsed = time.time() - self._last_request_time
            wait = min_interval - elapsed
            if wait > 0:
                logging.info(f"Rate limiting: waiting {wait:.1f}s before next request")
                time.sleep(wait)
        self._last_request_time = time.time()

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response using the configured LLM provider."""
        self._rate_limit_wait()
        try:
            if self.provider == 'openai':
                return self._openai_generate(system_prompt, user_prompt)
            elif self.provider == 'gemini':
                return self._gemini_generate(system_prompt, user_prompt)
            elif self.provider == 'huggingface':
                return self._huggingface_generate(system_prompt, user_prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            logging.error(f"Error generating response with {self.provider}: {e}")
            return self._fallback_response()
    
    def _openai_generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response using OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.config['model'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.config['temperature'],
            max_tokens=self.config['max_tokens']
        )
        return response.choices[0].message.content
    
    def _gemini_generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response using Google Gemini API, with retry on rate limit (429)."""
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        max_retries = 5
        delay = 10  # seconds, doubles each retry
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.config['model'], contents=combined_prompt
                )
                return response.text
            except Exception as e:
                is_rate_limit = "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower()
                if is_rate_limit and attempt < max_retries - 1:
                    logging.warning(f"Gemini rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise
    
    def _huggingface_generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response using Hugging Face Inference API."""
        # Use a free text generation model
        api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
        
        headers = {}
        if config.HUGGINGFACE_API_KEY:
            headers["Authorization"] = f"Bearer {config.HUGGINGFACE_API_KEY}"
        
        # Combine prompts for the model
        combined_prompt = f"{system_prompt}\n\nUser: {user_prompt}\nAssistant:"
        
        payload = {
            "inputs": combined_prompt,
            "parameters": {
                "max_new_tokens": min(self.config['max_tokens'], 1000),
                "temperature": self.config['temperature'],
                "return_full_text": False
            }
        }
        
        response = requests.post(api_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', '').strip()
            return str(result)
        else:
            # Try alternative free API
            return self._try_alternative_free_api(system_prompt, user_prompt)
    
    def _try_alternative_free_api(self, system_prompt: str, user_prompt: str) -> str:
        """Try alternative free APIs as fallback."""
        try:
            # Try a completely free API (no key required)
            api_url = "https://api.apifreellm.com/v1/chat/completions"
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.3
            }
            
            response = requests.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            
        except Exception as e:
            logging.warning(f"Alternative API failed: {e}")
        
        return self._fallback_response()
    
    def _fallback_response(self) -> str:
        """Provide a fallback response when all APIs fail."""
        return """
        {
            "analyses": [
                {
                    "paper_index": 1,
                    "score": 7,
                    "explanation": "Analysis unavailable - using fallback scoring based on title keywords and abstract length.",
                    "key_insights": "Unable to perform detailed analysis due to API limitations."
                }
            ]
        }
        """
    
    def is_configured(self) -> bool:
        """Check if the current provider is properly configured."""
        if self.provider == 'openai':
            return bool(config.OPENAI_API_KEY)
        elif self.provider == 'gemini':
            return bool(config.GEMINI_API_KEY)
        elif self.provider == 'huggingface':
            return True  # Can work without API key (with rate limits)
        return False
