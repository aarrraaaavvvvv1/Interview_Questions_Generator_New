import google.generativeai as genai
import time
from typing import Optional, Dict, Any
from config import MODEL_NAME, TEMPERATURE, TOP_P, MAX_OUTPUT_TOKENS

class GeminiHandler:
    """Wrapper for Gemini API interactions with retries and configurable params"""

    def __init__(self, api_key: str, model_name: str = MODEL_NAME):
        self.api_key = api_key or ""
        self.model_name = model_name
        genai.configure(api_key=self.api_key)
        try:
            self.model = genai.GenerativeModel(self.model_name)
        except Exception:
            # Delay instantiation errors until first call
            self.model = None

    def _ensure_model(self):
        if self.model is None:
            self.model = genai.GenerativeModel(self.model_name)

    def _extract_text(self, response) -> str:
        try:
            return response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
        except Exception:
            # Fallback best-effort
            return str(response)

    def generate(
        self,
        prompt: str,
        retry_count: int = 3,
        generation_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate content with backoff and basic extraction."""
        self._ensure_model()
        cfg = {
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "max_output_tokens": MAX_OUTPUT_TOKENS
        }
        if generation_config:
            cfg.update(generation_config)

        last_err = None
        for attempt in range(retry_count):
            try:
                resp = self.model.generate_content(prompt, generation_config=cfg)
                return self._extract_text(resp)
            except Exception as e:
                last_err = e
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
        raise Exception(f"Gemini API error after {retry_count} retries: {str(last_err)}")

    def validate_api_key(self) -> bool:
        """Test if API key is valid"""
        try:
            self.generate("Ping", retry_count=1, generation_config={"max_output_tokens": 4})
            return True
        except Exception:
            return False

    def get_health(self) -> str:
        return "ok" if self.validate_api_key() else "error"
