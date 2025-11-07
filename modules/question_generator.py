import time, uuid, json
from typing import List, Dict
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
- generation_time (float)
- questions (array)

If you return a top-level array, the app will wrap it automatically.
Do NOT include any commentary or code fences — JSON only."""

PROMPT_TEMPLATE = """{system}

TOPIC: {topic}

SUBTOPICS/CONTEXT: {context_str}

REQUIREMENTS:
- Total questions: {num_questions}
- Generic vs Practical ratio: {generic_percentage}% generic, {practical_percentage}% practical
- Difficulty: {difficulty}
- Allowed types: {question_types}
- Include answers/explanations: {include_answers}

Return JSON ONLY.
"""

FIX_TEMPLATE = """You previously returned invalid JSON. Repair it to valid minified JSON that matches the schema.
If you returned a list of questions, wrap it as:
{{"topic": "<topic>", "context": [], "difficulty": "<difficulty>", "question_types": [], "questions": [ ... ]}}.

Invalid JSON sample (truncated):
{bad_snippet}

Now return the corrected JSON:"""

class QuestionGenerator:
    """Generates interview questions via Gemini with strict JSON enforcement and repair."""

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
        ctx = ", ".join([c.strip() for c in context if c.strip()]) or "(none)"
        return PROMPT_TEMPLATE.format(
            system=SYSTEM_INSTRUCTIONS,
            topic=topic.strip(),
            context_str=ctx,
            num_questions=num_questions,
            generic_percentage=generic_percentage,
            practical_percentage=practical,
            difficulty=difficulty_level,
            question_types=", ".join(question_types),
            include_answers=str(bool(include_answers)).lower()
        )

    def _ensure_ids(self, payload: Dict) -> Dict:
        for q in payload.get("questions", []):
            if not q.get("id"):
                q["id"] = uuid.uuid4().hex[:8]
        return payload

    def _normalize_top_level(self, data):
        """Ensure we always have a dict with 'questions' key."""
        if isinstance(data, list):
            # Gemini returned a plain array of questions
            return {
                "topic": "General",
                "context": [],
                "difficulty": "medium",
                "question_types": [],
                "questions": data,
            }
        elif isinstance(data, dict):
            return data
        else:
            raise ValueError("Unexpected JSON structure: not dict or list.")

    def _parse_validate(self, raw: str) -> Dict:
        data, err = try_load_json(raw)
        if data is None:
            raise ValueError(f"Model did not return valid JSON. Parse error: {err}")

        data = self._normalize_top_level(data)
        data.setdefault("questions", [])
        data.setdefault("question_types", [])

        data = self._ensure_ids(data)
        validated = GenerationResult.model_validate(data)  # pydantic
        return validated.model_dump()

    def _repair_once(self, bad: str, topic: str, difficulty: str) -> str:
        snippet = bad[:800]
        fix_prompt = FIX_TEMPLATE.format(bad_snippet=snippet)
        return self.gemini.generate(
            fix_prompt,
            generation_config={"response_mime_type": "application/json"},
        )

    def generate_questions(
        self,
        topic: str,
        context: List[str],
        num_questions: int,
        generic_percentage: int,
        difficulty_level: str,
        question_types: List[str],
        include_answers: bool,
    ) -> Dict:
        start = time.time()
        prompt = self._build_prompt(
            topic,
            context,
            num_questions,
            generic_percentage,
            difficulty_level,
            question_types,
            include_answers,
        )

        # First attempt
        raw = self.gemini.generate(prompt)

        # Parse and repair logic
        try:
            payload = self._parse_validate(raw)
        except Exception:
            repaired = self._repair_once(raw, topic, difficulty_level)
            payload = self._parse_validate(repaired)

        # Fill computed fields
        payload["generation_time"] = round(time.time() - start, 2)
        payload["total_questions"] = len(payload.get("questions", []))
        payload["generic_count"] = sum(1 for q in payload.get("questions", []) if q.get("is_generic"))
        payload["practical_count"] = payload["total_questions"] - payload["generic_count"]
        return payload
