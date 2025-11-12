import re
import time
import uuid
from typing import List, Dict, Any, Optional
from modules.gemini_handler import GeminiHandler
from modules.schemas import GenerationResult
from app_utils.json_safety import try_load_json

SYSTEM_INSTRUCTIONS = """You are an expert technical interviewer. 
Generate ONLY a JSON object (no markdown, no explanations, no code fences).
The JSON must have this structure:

{
  "topic": "string",
  "context": ["optional context strings"],
  "difficulty": "easy|medium|hard",
  "question_types": ["mcq", "coding", "short", "theory"],
  "total_questions": int,
  "generic_count": int,
  "practical_count": int,
  "generation_time": float,
  "questions": [
    {
      "id": "uuid",
      "type": "mcq|coding|short|theory",
      "text": "question text",
      "difficulty": "easy|medium|hard",
      "is_generic": true|false,
      "options": [{"option": "text", "is_correct": true|false, "explanation": "string"}],
      "answer": "string",
      "explanation": "string",
      "code": "string"
    }
  ]
}
Return JSON only.
"""

PROMPT_TEMPLATE = """{system}

TOPIC: {topic}
CONTEXT: {context_str}

REQUIREMENTS:
- Total questions: {num_questions}
- Generic vs Practical ratio: {generic_percentage}% vs {practical_percentage}%
- Difficulty: {difficulty}
- Allowed types: {question_types}
- Include answers: {include_answers}

Return only valid JSON (no markdown, no ``` fences, no commentary).
"""

class QuestionGenerator:
    """Generates interview questions using Gemini with JSON parsing and repair."""

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
        context_str = ", ".join(context) if context else "(none)"
        practical_percentage = 100 - generic_percentage
        return PROMPT_TEMPLATE.format(
            system=SYSTEM_INSTRUCTIONS,
            topic=topic,
            context_str=context_str,
            num_questions=num_questions,
            generic_percentage=generic_percentage,
            practical_percentage=practical_percentage,
            difficulty=difficulty_level,
            question_types=", ".join(question_types),
            include_answers=str(include_answers).lower()
        )

    def _extract_json_block(self, text: str) -> str:
        """Extract JSON-like block from Gemini output if wrapped in text or code fences."""
        if not text:
            return ""
        # Remove code fences and markdown formatting
        cleaned = re.sub(r"```(?:json)?", "", text)
        # Find first {...} block
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return match.group(0)
        return cleaned.strip()

    def _parse_and_validate(self, text: str, difficulty: str) -> Dict[str, Any]:
        """Try loading and validating JSON; attempt one repair if necessary."""
        extracted = self._extract_json_block(text)
        parsed, err = try_load_json(extracted)
        if not parsed:
            # Last-ditch: remove trailing commas and retry
            repaired = re.sub(r",(\s*[}\]])", r"\1", extracted)
            parsed, _ = try_load_json(repaired)
        if not parsed:
            raise ValueError("Gemini returned no valid JSON block.")

        # Ensure IDs and schema compliance
        for q in parsed.get("questions", []):
            q.setdefault("id", str(uuid.uuid4()))

        # Add missing metadata
        parsed.setdefault("difficulty", difficulty)
        parsed.setdefault("total_questions", len(parsed.get("questions", [])))
        parsed.setdefault("generic_count", sum(1 for q in parsed.get("questions", []) if q.get("is_generic")))
        parsed.setdefault("practical_count", parsed["total_questions"] - parsed["generic_count"])
        return parsed

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
            topic, context or [], num_questions,
            generic_percentage, difficulty_level,
            question_types, include_answers
        )

        raw = self.gemini.generate(prompt)
        raw_text = raw.get("text") if isinstance(raw, dict) else str(raw)

        try:
            payload = self._parse_and_validate(raw_text, difficulty_level)
        except Exception:
            # Try repair prompt to force JSON return
            repair_prompt = f"Please convert this to valid JSON only:\n\n{raw_text[:1000]}"
            repaired = self.gemini.generate(repair_prompt)
            payload = self._parse_and_validate(
                repaired.get("text") if isinstance(repaired, dict) else str(repaired),
                difficulty_level
            )

        payload["generation_time"] = round(time.time() - start, 2)
        payload["total_questions"] = len(payload.get("questions", []))
        payload["generic_count"] = sum(1 for q in payload.get("questions", []) if q.get("is_generic"))
        payload["practical_count"] = payload["total_questions"] - payload["generic_count"]

        # If no questions, add a notice placeholder
        if not payload["questions"]:
            payload["questions"] = [{
                "id": str(uuid.uuid4()),
                "type": "short",
                "text": "⚠️ Gemini returned no questions — try increasing total or changing topic.",
                "difficulty": difficulty_level,
                "is_generic": True,
                "answer": "",
                "explanation": ""
            }]
        return payload
