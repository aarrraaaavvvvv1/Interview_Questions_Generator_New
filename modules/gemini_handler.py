import google.generativeai as genai
import time
from typing import Optional

class GeminiHandler:
    """Wrapper for Gemini API interactions"""
    
    def __init__(self, api_key: str, model_name: str = "models/gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def generate_content(self, prompt: str, temperature: float = 0.7, max_tokens: int = 10000, retry_count: int = 3) -> Optional[str]:
        """Generate content with retry logic"""
        for attempt in range(retry_count):
            try:
                generation_config = genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    top_p=0.95,
                    top_k=40
                )
                response = self.model.generate_content(prompt, generation_config=generation_config)
                return response.text
            except Exception as e:
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Gemini API error after {retry_count} retries: {str(e)}")
    
    def validate_api_key(self) -> bool:
        """Test if API key is valid"""
        try:
            self.model.generate_content("Test")
            return True
        except:
            return False
