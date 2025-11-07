import time
import uuid
from typing import List, Dict, Any, Optional
from modules.gemini_handler import GeminiHandler
from modules.schemas import GenerationResult, Question, MCQOption
from app_utils.json_safety import try_load_json

SYSTEM_INSTRUCTIONS = """You are an expert technical interviewer. Generate high-quality interview questions.

Return ONLY a single JSON object with keys:
- topic (string)
- context (array of strings)
- difficulty ("easy"|"medium"|"hard")
- question_types (array of "mcq"|"coding"|"short"|"theory")
- total_questions (int)
- generic_count (int)
- practical_count (int)
- generation_time (float seconds)
- questions (array of question objects)

Each question object should include:
- id (string)
- type ("mcq"|"coding"|"short"|"theory")
- text (string)
- difficulty ("easy"|"medium"|"hard")
- is_generic (bool)
- options (for mcq: array of { "option": "...", "is_correct": true/false, "explanation": "..." })
- answer (for non-mcq / helpful short answers)
- explanation (optional)
- code (optional, for coding questions)

Return strictly valid JSON only.
"""

class QuestionGenerator:
    """Generates interview questions via Gemini with JSON enforcement and schema validation."""

    def __init__(self, gemini_handler: GeminiHandler):
        self.gemini = gemini_handler

    def _build_prompt(self, topic: str, context: Optional[List[str]] = None, difficulty: str = "medium", total: int = 8) -> str:
        ctx = context or []
        prompt = SYSTEM_INSTRUCTIONS + "\n\n"
        prompt += f"Topic: {topic}\n"
        if ctx:
            prompt += "Context:\n" + "\n".join(f"- {c}" for c in ctx) + "\n"
        prompt += f"Difficulty: {difficulty}\n"
        prompt += f"Total questions: {total}\n\n"
        prompt += "Make sure returned JSON follows the schema precisely and escape strings where needed. Do not return markdown or extraneous text."
        return prompt

    def _parse_validate(self, raw_json: Any, expected_difficulty: str) -> Dict[str, Any]:
        """
        Validate/normalize the parsed JSON to match GenerationResult
        Returns a plain dict suitable for downstream use.
        Raises Exception on validation failure.
        """
        # if it's already a dict-like structure, use it; else try_load_json should have produced it
        # Use pydantic model to validate
        payload = raw_json
        # Normalize missing fields with defaults (so validation errors are informative)
        if "questions" not in payload or not isinstance(payload["questions"], list):
            payload["questions"] = []
        # ensure each question has an id
        for q in payload.get("questions", []):
            if "id" not in q or not q["id"]:
                q["id"] = str(uuid.uuid4())
        # If difficulty missing, set expected
        if "difficulty" not in payload:
            payload["difficulty"] = expected_difficulty
        # Try to validate via pydantic model; GenerationResult expects exact fields
        validated = GenerationResult.parse_obj(payload)
        # Convert back to plain dict (pydantic provides `.model_dump()` for v2)
        try:
            return validated.model_dump()
        except Exception:
            # fallback for older pydantic
            return validated.dict()

    def _repair_once(self, text: str) -> Any:
        """
        Attempt a basic repair of malformed JSON text: strip markdown fences, fix unquoted keys, remove trailing commas.
        This uses the same heuristics as app_utils.json_safety.try_load_json which is the main parser.
        """
        parsed, err = try_load_json(text)
        if parsed is not None:
            return parsed
        # If repair failed, raise with the last error
        raise ValueError("Unable to parse JSON from model output. Last attempt failed.")

    def generate_questions(
        self,
        topic: str,
        context: Optional[List[str]] = None,
        difficulty: str = "medium",
        total_questions: int = 8,
        model_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate questions via GeminiHandler and return a validated payload dict.
        Raises ImportError if GeminiHandler cannot run (i.e., missing dependency).
        """
        model_kwargs = model_kwargs or {}
        start = time.time()
        prompt = self._build_prompt(topic, context=context, difficulty=difficulty, total=total_questions)

        # call the gemini handler; may raise ImportError if library missing
        resp = self.gemini.generate(prompt, **model_kwargs)
        raw_text = resp.get("text") if isinstance(resp, dict) else str(resp)

        # Try to parse JSON
        parsed, err = try_load_json(raw_text or "")
        if parsed is None:
            # attempt one repair (the generator may include code fences or stray commas)
            try:
                parsed = self._repair_once(raw_text or "")
            except Exception as e:
                raise ValueError(f"Failed to parse JSON from model output: {e}")

        # Validate and normalize
        payload = self._parse_validate(parsed, difficulty)
        # Fill computed fields AFTER validation-friendly defaults
        payload["generation_time"] = round(time.time() - start, 2)
        payload["total_questions"] = len(payload.get("questions", []))
        payload["generic_count"] = sum(1 for q in payload.get("questions", []) if q.get("is_generic"))
        payload["practical_count"] = payload["total_questions"] - payload["generic_count"]
        return payload
