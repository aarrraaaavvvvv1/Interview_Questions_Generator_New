import re
import time
import uuid
import json
from typing import List, Dict, Any, Optional
from modules.gemini_handler import GeminiHandler
from app_utils.json_safety import try_load_json


SYSTEM_INSTRUCTIONS = """You are an expert technical interviewer.

Your ONLY task: output a single valid JSON object that contains exactly {num_questions} interview questions.

Do NOT include markdown, code fences, commentary, or explanations outside the JSON.
If you include anything else, your output is invalid.

### JSON SCHEMA EXAMPLE ###
{
  "topic": "Python OOP",
  "context": ["Object-oriented programming principles"],
  "difficulty": "medium",
  "question_types": ["mcq", "coding", "short", "theory"],
  "total_questions": 3,
  "generic_count": 1,
  "practical_count": 2,
  "generation_time": 0.0,
  "questions": [
    {
      "id": "uuid",
      "type": "mcq",
      "text": "What is encapsulation in Python?",
      "difficulty": "medium",
      "is_generic": true,
      "options": [
        {"option": "Hiding data", "is_correct": true, "explanation": "Encapsulation hides data."},
        {"option": "Multiple inheritance", "is_correct": false, "explanation": ""}
      ],
      "answer": "Encapsulation hides data and behavior in a single unit.",
      "explanation": "Encapsulation prevents direct access to object internals.",
      "code": ""
    }
  ]
}
"""


class QuestionGenerator:
    """Gemini-based question generator with strong JSON enforcement and fallback repair."""

    def __init__(self, gemini_handler: GeminiHandler):
        self.gemini = gemini_handler

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------
    def _extract_json(self, text: str) -> Optional[str]:
        """Extract first balanced {...} JSON block from a string."""
        if not text:
            return None
        # Remove code fences and markdown
        cleaned = re.sub(r"```(?:json)?", "", text)
        # Find first balanced brace block
        depth = 0
        start = None
        for i, ch in enumerate(cleaned):
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start is not None:
                    return cleaned[start : i + 1]
        # fallback: return whole thing
        return cleaned.strip()

    def _parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Try multiple ways to parse text into JSON."""
        extracted = self._extract_json(text)
        if not extracted:
            return None

        parsed, _ = try_load_json(extracted)
        if parsed:
            return parsed

        # Try a relaxed regex repair (remove trailing commas)
        repaired = re.sub(r",(\s*[}\]])", r"\1", extracted)
        try:
            return json.loads(repaired)
        except Exception:
            return None

    # -----------------------------------------------------------------------
    # Main generation logic
    # -----------------------------------------------------------------------
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
        start = time.time()
        context_str = ", ".join(context) if context else "(none)"
        practical_percentage = 100 - generic_percentage

        # Build strong prompt
        prompt = (
            SYSTEM_INSTRUCTIONS.format(num_questions=num_questions)
            + f"""

TOPIC: {topic}
CONTEXT: {context_str}

REQUIREMENTS:
- Exactly {num_questions} questions.
- Generic vs Practical ratio: {generic_percentage}% vs {practical_percentage}%.
- Difficulty: {difficulty_level}.
- Allowed types: {', '.join(question_types)}.
- Include answers: {include_answers}.
Output valid JSON only.
"""
        )

        # Use new SDK hint if available
        extra_args = {}
        if hasattr(self.gemini, "_model") and hasattr(self.gemini._model, "generate_content"):
            extra_args["response_format"] = "json"

        # Generate
        raw = self.gemini.generate(prompt, **extra_args)
        raw_text = raw.get("text") if isinstance(raw, dict) else str(raw)

        parsed = self._parse_json(raw_text)

        # Retry once with repair prompt if JSON missing
        if not parsed:
            repair_prompt = (
                f"The following text failed JSON validation. "
                f"Fix it and return valid JSON only:\n\n{raw_text[:1500]}"
            )
            repair = self.gemini.generate(repair_prompt)
            raw_text = repair.get("text") if isinstance(repair, dict) else str(repair)
            parsed = self._parse_json(raw_text)

        if not parsed:
            raise ValueError("Gemini returned no valid JSON block.")

        # Normalize fields
        for q in parsed.get("questions", []):
            q.setdefault("id", str(uuid.uuid4()))
            q.setdefault("answer", "")
            q.setdefault("explanation", "")
            q.setdefault("is_generic", False)
            q.setdefault("difficulty", difficulty_level)
            if "options" not in q:
                q["options"] = []

        parsed["difficulty"] = difficulty_level
        parsed["generation_time"] = round(time.time() - start, 2)
        parsed["total_questions"] = len(parsed.get("questions", []))
        parsed["generic_count"] = sum(1 for q in parsed.get("questions", []) if q.get("is_generic"))
        parsed["practical_count"] = parsed["total_questions"] - parsed["generic_count"]

        # Guarantee at least num_questions (add placeholders if short)
        while len(parsed["questions"]) < num_questions:
            parsed["questions"].append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "short",
                    "text": f"⚠️ Placeholder: Gemini returned fewer than {num_questions} questions.",
                    "difficulty": difficulty_level,
                    "is_generic": True,
                    "answer": "",
                    "explanation": "",
                }
            )
        parsed["total_questions"] = len(parsed["questions"])
        return parsed
