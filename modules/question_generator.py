import time
import uuid
from typing import List, Dict, Any, Optional
from modules.gemini_handler import GeminiHandler
from modules.schemas import GenerationResult
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

Each question object must have:
- id (string)
- type ("mcq"|"coding"|"short"|"theory")
- text (string)
- difficulty ("easy"|"medium"|"hard")
- is_generic (boolean)
- options (for mcq: array of { "option": "...", "is_correct": true/false, "explanation": "..." })
- answer (string, optional)
- explanation (string, optional)
- code (string, optional)

Return strictly valid JSON — no markdown, code fences, or commentary.
"""

PROMPT_TEMPLATE = """{system}

TOPIC: {topic}

CONTEXT: {context_str}

REQUIREMENTS:
- Total questions: {num_questions}
- Generic vs Practical ratio: {generic_percentage}% generic / {practical_percentage}% practical
- Difficulty: {difficulty}
- Allowed types: {question_types}
- Include answers: {include_answers}

Make sure JSON is valid and escaped properly.
"""

class QuestionGenerator:
    """Generates interview questions using Gemini with JSON parsing, validation, and schema normalization."""

    def __init__(self, gemini_handler: GeminiHandler):
        self.gemini = gemini_handler

    def _build_prompt(
        self,
        topic: str,
        context: List[str],
        num_questions: int,
        generic_percentage: int,
        difficulty_level: str,
        question_types: List[str],
        include_answers: bool
    ) -> str:
        practical = 100 - generic_percentage
        context_str = ", ".join(context) if context else "(none)"
        return PROMPT_TEMPLATE.format(
            system=SYSTEM_INSTRUCTIONS,
            topic=topic,
            context_str=context_str,
            num_questions=num_questions,
            generic_percentage=generic_percentage,
            practical_percentage=practical,
            difficulty=difficulty_level,
            question_types=", ".join(question_types),
            include_answers=str(include_answers).lower(),
        )

    def _parse_validate(self, raw_json: str, expected_difficulty: str) -> Dict[str, Any]:
        parsed, err = try_load_json(raw_json)
        if parsed is None:
            raise ValueError(f"Gemini did not return valid JSON. Error: {err}")
        # Validate schema using Pydantic
        validated = GenerationResult.parse_obj(parsed)
        try:
            return validated.model_dump()
        except Exception:
            return validated.dict()

    def _repair_once(self, bad_output: str) -> str:
        """Ask Gemini to repair invalid JSON once."""
        fix_prompt = f"Fix this to valid JSON only:\n\n{bad_output[:800]}"
        resp = self.gemini.generate(fix_prompt)
        return resp.get("text") if isinstance(resp, dict) else str(resp)

    def generate_questions(
        self,
        topic: str,
        context: Optional[List[str]],
        num_questions: int,
        generic_percentage: int,
        difficulty_level: str,
        question_types: List[str],
        include_answers: bool,
    ) -> Dict[str, Any]:
        """Main public entry — matches app.py’s call signature."""
        start = time.time()
        prompt = self._build_prompt(
            topic,
            context or [],
            num_questions,
            generic_percentage,
            difficulty_level,
            question_types,
            include_answers,
        )

        raw = self.gemini.generate(prompt)
        raw_text = raw.get("text") if isinstance(raw, dict) else str(raw)

        try:
            payload = self._parse_validate(raw_text, difficulty_level)
        except Exception:
            repaired = self._repair_once(raw_text)
            payload = self._parse_validate(repaired, difficulty_level)

        payload["generation_time"] = round(time.time() - start, 2)
        payload["total_questions"] = len(payload.get("questions", []))
        payload["generic_count"] = sum(1 for q in payload.get("questions", []) if q.get("is_generic"))
        payload["practical_count"] = payload["total_questions"] - payload["generic_count"]
        return payload
