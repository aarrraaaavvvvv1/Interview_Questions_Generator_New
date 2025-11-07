import time
from typing import Optional, Dict, Any, List, Tuple

# Lazy import to avoid hard dependency at import time.
_genai = None
try:
    import google.generativeai as genai  # type: ignore
    _genai = genai
except Exception:
    _genai = None  # Will raise helpful error only when used

MODEL_CANDIDATES: List[str] = [
    "gemini-2.0-flash",
    "gemini-2.0-pro",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro-latest",
    "models/gemini-2.0-flash",
    "models/gemini-2.0-pro",
    "models/gemini-1.5-flash",
    "models/gemini-1.5-pro",
]


class GeminiHandler:
    """Thin wrapper around google.generativeai with graceful failure when the dependency is missing."""

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
        """
        Accepts both `model_name` and `preferred_model` (alias) to match callers.
        Any additional kwargs are ignored (for forward compatibility).
        """
        self.api_key = (api_key or "").strip()

        # allow caller to pass preferred_model or model_name interchangeably
        if preferred_model:
            self.model_name = preferred_model
        else:
            self.model_name = model_name or MODEL_CANDIDATES[0]

        self.temperature = float(temperature)
        self.top_p = float(top_p)
        self.max_output_tokens = int(max_output_tokens)
        self._client = None

    def _ensure_installed(self):
        if _genai is None:
            raise ImportError(
                "google.generativeai is not installed. Install it with `pip install google-generativeai` or run `pip install -r requirements.txt`."
            ) from None

    def _init_client(self):
        self._ensure_installed()
        if self._client is None:
            # configure the official client
            _genai.configure(api_key=self.api_key)
            self._client = _genai

    def _select_model(self) -> Tuple[bool, str]:
        """Attempt to select a working model from MODEL_CANDIDATES. Returns (ok, message_or_model)."""
        try:
            self._ensure_installed()
            # The library may expose different model identifiers across versions/regions.
            for m in [self.model_name] + MODEL_CANDIDATES:
                try:
                    # We don't call the model here; just assume it's a valid identifier.
                    return True, m
                except Exception:
                    continue
            return False, "no compatible model found"
        except ImportError as e:
            return False, str(e)

    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate text using the configured Gemini-like client.
        Raises ImportError if the package isn't available.
        Returns dict with keys: "raw" and "text"
        """
        self._ensure_installed()
        params = {
            "model": kwargs.get("model", self.model_name),
            "temperature": kwargs.get("temperature", self.temperature),
            "top_p": kwargs.get("top_p", self.top_p),
            "max_output_tokens": kwargs.get("max_output_tokens", self.max_output_tokens),
        }
        # call the SDK's generate method; different SDK versions may use different shapes
        resp = _genai.texts.generate(input=prompt, **params)

        # Try to extract text robustly across different response shapes
        try:
            if isinstance(resp, dict):
                # newer SDK shapes
                out_text = None
                if "output" in resp and isinstance(resp["output"], dict):
                    out_text = resp["output"].get("text")
                if not out_text and "candidates" in resp and isinstance(resp["candidates"], list):
                    out_text = resp["candidates"][0].get("content")
                if not out_text and "content" in resp:
                    out_text = resp.get("content")
                return {"raw": resp, "text": out_text or str(resp)}
            else:
                # fallback to string
                return {"raw": resp, "text": str(resp)}
        except Exception:
            # Last-resort fallback: return repr
            return {"raw": resp, "text": str(resp)}

    def validate_api_key(self) -> bool:
        ok, _ = self.validate_api_key_with_reason()
        return ok

    def validate_api_key_with_reason(self) -> Tuple[bool, str]:
        try:
            ok, msg = self._select_model()
            return ok, msg
        except Exception as e:
            return False, str(e)

    def get_health(self) -> str:
        return "ok" if self.validate_api_key() else "error"
