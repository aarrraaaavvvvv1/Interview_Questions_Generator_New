import time
from typing import Optional, Dict, Any, List, Tuple, Callable

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
    """Thin wrapper around google.generativeai with resilient generation method across SDK versions."""

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
        # support alias preferred_model
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
        """Configure the SDK client (if available)."""
        self._ensure_installed()
        if self._client is None:
            # many SDKs provide a configure function
            if hasattr(_genai, "configure"):
                _genai.configure(api_key=self.api_key)
                self._client = _genai
            else:
                # fallback: keep module as client
                self._client = _genai

    def _try_call_variants(self, prompt: str, params: Dict[str, Any]):
        """
        Try a sequence of likely SDK call shapes and return the first successful response.
        If none succeed, raise RuntimeError with diagnostic info.
        """
        self._init_client()

        attempts = []

        # Variant 1: genai.texts.generate(input=..., model=...)
        if hasattr(_genai, "texts") and hasattr(_genai.texts, "generate"):
            attempts.append(lambda: _genai.texts.generate(input=prompt, **params))

        # Variant 2: genai.generate(input=...) or genai.generate(prompt=...)
        if hasattr(_genai, "generate"):
            def try_gen():
                try:
                    return _genai.generate(input=prompt, **params)
                except TypeError:
                    return _genai.generate(prompt=prompt, **params)
            attempts.append(try_gen)

        # Variant 3: genai.generate_text / genai.generateText
        if hasattr(_genai, "generate_text"):
            attempts.append(lambda: _genai.generate_text(input=prompt, **params))
            attempts.append(lambda: _genai.generate_text(prompt=prompt, **params))
        if hasattr(_genai, "generateText"):
            attempts.append(lambda: _genai.generateText(input=prompt, **params))

        # Variant 4: some SDKs expose a client factory e.g., TextGenerationClient or similar
        # Try common client attribute names and call .generate or .create
        client_attr_names = ["TextGenerationClient", "TextClient", "TextsClient", "Client"]
        for attr in client_attr_names:
            if hasattr(_genai, attr):
                client_cls = getattr(_genai, attr)
                try:
                    client = client_cls()
                    if hasattr(client, "generate"):
                        attempts.append(lambda c=client: c.generate(input=prompt, **params))
                    if hasattr(client, "create"):
                        attempts.append(lambda c=client: c.create(input=prompt, **params))
                except Exception:
                    # constructing client failed; skip
                    pass

        last_exc = None
        for attempt in attempts:
            try:
                resp = attempt()
                return resp
            except Exception as e:
                last_exc = e
                # keep trying other variants
                continue

        # Nothing worked — build helpful diagnostic
        avail = dir(_genai) if _genai is not None else []
        raise RuntimeError(
            "Unable to call a supported generation method on google.generativeai.\n"
            "Tried multiple call shapes (texts.generate, generate, generate_text, client.generate, client.create) but all failed.\n"
            f"Last error: {last_exc}\n"
            f"Available attributes on module: {sorted([a for a in avail if not a.startswith('_')])[:50]}"
        )

    def _extract_text_from_response(self, resp) -> str:
        """Try to get a user-facing string from various SDK response shapes."""
        # if the SDK returned a simple dict-like object
        try:
            if isinstance(resp, dict):
                # common shapes
                if "output" in resp and isinstance(resp["output"], dict):
                    t = resp["output"].get("text")
                    if t:
                        return t
                if "candidates" in resp and isinstance(resp["candidates"], list) and resp["candidates"]:
                    cand = resp["candidates"][0]
                    if isinstance(cand, dict) and "content" in cand:
                        return cand["content"]
                if "content" in resp:
                    return resp.get("content")
                # fallback: try flattening possible lists
                for key in ("outputs", "response", "responses"):
                    if key in resp and isinstance(resp[key], list) and resp[key]:
                        first = resp[key][0]
                        if isinstance(first, dict) and "text" in first:
                            return first["text"]
                # last resort: stringify
                return str(resp)
            else:
                # not a dict — try common attributes
                if hasattr(resp, "text"):
                    return getattr(resp, "text")
                if hasattr(resp, "content"):
                    return getattr(resp, "content")
                # fallback to str()
                return str(resp)
        except Exception:
            return str(resp)

    def _select_model(self) -> Tuple[bool, str]:
        """Check for at least one viable model identifier; return boolean and message/model."""
        try:
            self._ensure_installed()
            for m in [self.model_name] + MODEL_CANDIDATES:
                try:
                    # we can't truly test model validity without calling the API,
                    # so just return the first candidate.
                    return True, m
                except Exception:
                    continue
            return False, "no compatible model found"
        except ImportError as e:
            return False, str(e)

    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Universal generate wrapper. Tries multiple SDK shapes and returns a dict:
            { "raw": <raw-response>, "text": <extracted-text> }

        If the SDK is not installed, raises ImportError.
        If no supported call shape could be found, raises RuntimeError with diagnostics.
        """
        self._init_client()
        # construct common params mapping
        params = {
            "model": kwargs.get("model", self.model_name),
            "temperature": kwargs.get("temperature", self.temperature),
            "top_p": kwargs.get("top_p", self.top_p),
            "max_output_tokens": kwargs.get("max_output_tokens", self.max_output_tokens),
        }

        # try known call shapes
        resp = self._try_call_variants(prompt, params)
        text = self._extract_text_from_response(resp)
        return {"raw": resp, "text": text}

    def validate_api_key(self) -> bool:
        ok, _ = self._select_model()
        return ok

    def validate_api_key_with_reason(self) -> Tuple[bool, str]:
        try:
            ok, msg = self._select_model()
            return ok, msg
        except Exception as e:
            return False, str(e)

    def get_health(self) -> str:
        return "ok" if self.validate_api_key() else "error"
