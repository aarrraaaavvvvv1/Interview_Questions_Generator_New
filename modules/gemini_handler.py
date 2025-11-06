import google.generativeai as genai
import time
from typing import Optional, Dict, Any, List

# Keep a small compatibility list; the first one that works will be used
MODEL_CANDIDATES: List[str] = [
    "gemini-1.5-flash",        # most installs of google-generativeai >=0.5
    "gemini-1.5-pro",
    "models/gemini-1.5-flash", # older code patterns
    "models/gemini-1.5-pro"
]

DEFAULT_GEN_CFG = {
    "temperature": 0.2,
    "top_p": 0.8,
    "max_output_tokens": 2048
}

class GeminiHandler:
    """Wrapper for Gemini API with model fallback and good error messages."""

    def __init__(self, api_key: str, preferred_model: Optional[str] = None):
        self.api_key = (api_key or "").strip()
        if not self.api_key:
            raise ValueError("Gemini API key is empty.")
        genai.configure(api_key=self.api_key)

        self.model_name = preferred_model or MODEL_CANDIDATES[0]
        self.model = None
        self._select_model()

    def _select_model(self):
        """Try to instantiate a working model from candidates."""
        last_err = None
        candidates = [self.model_name] + [m for m in MODEL_CANDIDATES if m != self.model_name]
        for name in candidates:
            try:
                self.model = genai.GenerativeModel(name)
                # ping
                _ = self.model.generate_content("ping", generation_config={"max_output_tokens": 2})
                self.model_name = name
                return
            except Exception as e:
                last_err = e
                self.model = None
        raise RuntimeError(f"Failed to initialize a Gemini model. Last error: {last_err}")

    def _extract_text(self, response) -> str:
        try:
            if hasattr(response, "text") and isinstance(response.text, str):
                return response.text
            return response.candidates[0].content.parts[0].text
        except Exception:
            return str(response)

    def generate(
        self,
        prompt: str,
        retry_count: int = 3,
        generation_config: Optional[Dict[str, Any]] = None
    ) -> str:
        if not self.model:
            self._select_model()

        cfg = dict(DEFAULT_GEN_CFG)
        if generation_config:
            cfg.update(generation_config)

        last_err = None
        for attempt in range(retry_count):
            try:
                resp = self.model.generate_content(prompt, generation_config=cfg)
                return self._extract_text(resp)
            except Exception as e:
                last_err = e
                # common, actionable hints
                hint = (
                    "Check: 1) API key valid and has access, 2) quota not exhausted, "
                    "3) model name supported for your google-generativeai version."
                )
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise Exception(f"Gemini API error after {retry_count} retries: {last_err}. {hint}")

    def validate_api_key(self) -> bool:
        try:
            # call with current model; if it fails, try fallback selection
            if not self.model:
                self._select_model()
            self.model.generate_content("ping", generation_config={"max_output_tokens": 2})
            return True
        except Exception:
            # try to re-select a model once more, then fail
            try:
                self._select_model()
                self.model.generate_content("ping", generation_config={"max_output_tokens": 2})
                return True
            except Exception:
                return False

    def get_health(self) -> str:
        return "ok" if self.validate_api_key() else "error"
