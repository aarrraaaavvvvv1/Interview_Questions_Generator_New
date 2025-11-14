import time
from typing import Optional, Dict, Any, List, Tuple
from config import MODEL_CHOICES # Import from config

# Lazy import to avoid hard dependency at import time.
_genai = None
try:
    import google.generativeai as genai  # type: ignore
    _genai = genai
except Exception:
    _genai = None  # Will raise helpful error only when used

MODEL_CANDIDATES = MODEL_CHOICES # Use list from config


class GeminiHandler:
    """Gemini handler compatible with the latest google-generativeai SDK (GenerativeModel)."""

    def __init__(
        self,
        api_key: str = "",
        model_name: Optional[str] = None,
        preferred_model: Optional[str] = None,
        temperature: float = 0.2,
        top_p: float = 0.8,
        max_output_tokens: int = 1024,
        **kwargs,
    ):
        self.api_key = (api_key or "").strip()
        self.model_name = preferred_model or model_name or MODEL_CANDIDATES[0]
        self.temperature = float(temperature)
        self.top_p = float(top_p)
        self.max_output_tokens = int(max_output_tokens)
        self._client = None
        self._model = None

    def _ensure_installed(self):
        if _genai is None:
            raise ImportError(
                "google-generativeai is not installed. Install it with `pip install google-generativeai`."
            ) from None

    def _init_client(self):
        """Configure the SDK and create a GenerativeModel if available."""
        self._ensure_installed()
        if hasattr(_genai, "configure"):
            _genai.configure(api_key=self.api_key)
        # Try to instantiate the GenerativeModel (new SDK)
        try:
            if hasattr(_genai, "GenerativeModel"):
                self._model = _genai.GenerativeModel(self.model_name)
        except Exception as e:
            self._model = None
            print(f"Warning: could not create GenerativeModel: {e}")

    def _select_model(self) -> Tuple[bool, str]:
        """Select first available model name."""
        try:
            self._ensure_installed()
            return True, self.model_name or MODEL_CANDIDATES[0]
        except ImportError as e:
            return False, str(e)

    def _extract_text(self, resp) -> str:
        """Safely extract text from various response formats."""
        if resp is None:
            return ""
        try:
            # Most common: response.text
            if hasattr(resp, "text"):
                return resp.text
            # Sometimes responses have candidates -> content -> parts -> text
            if hasattr(resp, "candidates"):
                cand = resp.candidates[0]
                if hasattr(cand, "content") and hasattr(cand.content, "parts"):
                    parts = cand.content.parts
                    if parts and hasattr(parts[0], "text"):
                        return parts[0].text
            # fallback
            return str(resp)
        except Exception:
            return str(resp)

    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate text with Google Gemini API.
        Uses the GenerativeModel API when available (latest SDK).
        Returns {"raw": <response>, "text": <string>}.
        """
        self._init_client()

        # Case 1: New-style GenerativeModel
        if self._model and hasattr(self._model, "generate_content"):
            try:
                response = self._model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": kwargs.get("temperature", self.temperature),
                        "top_p": kwargs.get("top_p", self.top_p),
                        "max_output_tokens": kwargs.get("max_output_tokens", self.max_output_tokens),
                    },
                )
                text = self._extract_text(response)
                return {"raw": response, "text": text}
            except Exception as e:
                raise RuntimeError(f"Gemini API call failed: {e}")

        # Case 2: Fallback to old API shapes if GenerativeModel not present
        if hasattr(_genai, "generate_text"):
            try:
                resp = _genai.generate_text(prompt=prompt)
                text = self._extract_text(resp)
                return {"raw": resp, "text": text}
            except Exception as e:
                raise RuntimeError(f"Legacy generate_text() failed: {e}")

        raise RuntimeError(
            "No compatible Gemini generation method found. "
            "Your google-generativeai SDK seems to require GenerativeModel.generate_content, "
            "but initialization failed."
        )

    def validate_api_key(self) -> bool:
        ok, _ = self.validate_api_key_with_reason()
        return ok

    # --- THIS IS THE CORRECT, FIXED FUNCTION ---
    def validate_api_key_with_reason(self) -> Tuple[bool, str]:
        """
        Attempts a lightweight API call (list_models) to validate the API key.
        """
        try:
            # _init_client() configures the SDK with the key
            self._init_client() 
            if not _genai:
                return False, "google-generativeai is not installed."
            
            # This is the actual test. It will raise an exception if the key is bad.
            _ = list(_genai.list_models()) 
            
            return True, "API key is valid."

        except Exception as e:
            # Provide a more useful error message
            error_msg = str(e)
            if "API_KEY_INVALID" in error_msg:
                return False, "The provided API key is invalid."
            if "permission" in error_msg.lower():
                 return False, "API key lacks permission for this operation."
            return False, f"API key validation failed: {error_msg}"
    # --- END OF FIX ---

    def get_health(self) -> str:
        return "ok" if self.validate_api_key() else "error"
