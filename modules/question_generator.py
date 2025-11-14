import re
import time
import uuid
import json
from typing import List, Dict, Any, Optional
from modules.gemini_handler import GeminiHandler
from app_utils.json_safety import try_load_json


SYSTEM_INSTRUCTIONS = """You are an expert technical interviewer.

Return **only** valid JSON (no markdown, no code fences, no commentary).
The JSON must match this structure and include exactly {num_questions} questions:

{
  "topic": "string",
  "context": ["string"],
  "difficulty": "easy|medium|hard",
  "question_types": ["mcq","coding","short","theory"],
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
      "options": [{"option": "text","is_correct":true|false,"explanation":"string"}],
      "answer": "string",
      "explanation": "string",
      "code": "string"
    }
  ]
}

If you include anything besides valid JSON, your output is invalid.
"""


class QuestionGenerator:
    """Gemini-based question generator with resilient JSON parsing and repair."""

    def __init__(self, gemini_handler: GeminiHandler):
        self.gemini = gemini_handler

    # -----------------------------------------------------------------------
    # JSON Extraction & Repair Helpers (REWRITTEN FOR ROBUSTNESS)
    # -----------------------------------------------------------------------
    def _extract_json_block(self, text: str) -> Optional[str]:
        """
        Finds the first and last curly braces in the text to extract the main
        JSON block. More robust than balanced bracket counting for LLM output.
        """
        if not text:
            return None
        
        # Remove markdown fences
        text = re.sub(r"```(?:json)?", "", text.strip())
        
        try:
            # Find the first '{'
            first_brace = text.index("{")
            # Find the last '}'
            last_brace = text.rindex("}")
            
            if last_brace > first_brace:
                return text[first_brace : last_brace + 1]
            else:
                return None
        except ValueError:
            # Raised if '{' or '}' not found
            return None

    def _parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Attempt to parse JSON after extraction."""
        extracted = self._extract_json_block(text)
        if not extracted:
            return None
        
        # Try loading with the safety util first
        parsed, _ = try_load_json(extracted)
        if parsed:
            return parsed
            
        # Try a final time with standard lib, just in case
        try:
            return json.loads(extracted)
        except Exception:
            return None

    # -----------------------------------------------------------------------
    # Main generator
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
Return JSON only.
"""
        )

        # Generate
        raw = self.gemini.generate(prompt)
        raw_text = raw.get("text") if isinstance(raw, dict) else str(raw)

        parsed = self._parse_json(raw_text)

        # Retry once with repair prompt if still invalid
        if not parsed:
            repair_prompt = f"Fix this into valid JSON only (no text):\n\n{raw_text[:1500]}"
            repaired = self.gemini.generate(repair_prompt)
            raw_text = repaired.get("text") if isinstance(repaired, dict) else str(repaired)
            parsed = self._parse_json(raw_text)

        if not parsed:
            raise ValueError("Gemini returned no valid JSON block even after repair.")

        # Normalize
        questions = parsed.get("questions", [])
        for q in questions:
            q.setdefault("id", str(uuid.uuid4()))
            q.setdefault("answer", "")
            q.setdefault("explanation", "")
            q.setdefault("is_generic", False)
            q.setdefault("difficulty", difficulty_level)
            if "options" not in q:
                q["options"] = []

        parsed["difficulty"] = difficulty_level
        parsed["generation_time"] = round(time.time() - start, 2)
        parsed["total_questions"] = len(questions)
        parsed["generic_count"] = sum(1 for q in questions if q.get("is_generic"))
        parsed["practical_count"] = parsed["total_questions"] - parsed["generic_count"]

        # Guarantee at least num_questions (fill placeholders)
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
