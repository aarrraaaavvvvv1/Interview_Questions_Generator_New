import time
from typing import Optional, Dict, Any, List, Tuple
import google.generativeai as genai

# Broad set for compatibility across library versions/regions
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
    "models/gemini-1.5-flash-8b",
    "models/gemini-1.5-pro",
]

DEFAULT_GEN_CFG = {
    "temperature": 0.2,
    "top_p": 0.8,
    "max_output_tokens": 2048,
    # ★ THIS makes Gemini serialize proper JSON
    "response_mime_type": "application/json",
}


class GeminiHandler:
    """Gemini wrapper with model fallback and JSON-friendly defaults."""

    def __init__(self, api_key: str, preferred_model: Optional[str] = None):
        self.api_key = (api_key or "").strip()
        self.preferred_model = preferred_model
        self.model_name: Optional[str] = None
        self.model = None

    def _configure(self):
        if not self.api_key:
            raise ValueError("Gemini API key is empty.")
        genai.configure(api_key=self.api_key)

    def _select_model(self) -> Tuple[bool, str]:
        self._configure()
        candidates = []
        if self.preferred_model:
            candidates.append(self.preferred_model)
        candidates += [m for m in MODEL_CANDIDATES if m != self.preferred_model]

        last_err = None
        for name in candidates:
            try:
                m = genai.GenerativeModel(name)
                _ = m.generate_content("ping", generation_config={"max_output_tokens": 2})
                self.model = m
                self.model_name = name
                return True, f"Using model: {name}"
            except Exception as e:
                last_err = e
        return False, f"Failed to initialize any Gemini model. Last error: {last_err}"

    def _ensure_model(self):
        if self.model is None:
            ok, msg = self._select_model()
            if not ok:
                raise RuntimeError(msg)

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
        self._ensure_model()
        cfg = dict(DEFAULT_GEN_CFG)
        if generation_config:
            cfg.update(generation_config)

        last_err = None
        for attempt in range(retry_count):
            try:
                resp = self.model.generate_content(prompt, generation_config=cfg)  # type: ignore
                return self._extract_text(resp)
            except Exception as e:
                last_err = e
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
        hint = ("Check API key validity/quota and model availability for your google-generativeai version.")
        raise Exception(f"Gemini API error after {retry_count} retries: {last_err}. {hint}")

    # -------- validation helpers --------

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
