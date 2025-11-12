import re
import time
import uuid
from typing import List, Dict, Any, Optional
from modules.gemini_handler import GeminiHandler
from app_utils.json_safety import try_load_json

# ---------------------------------------------------------------------------
# Stronger prompt with explicit example and constraints
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTIONS = """You are an expert technical interviewer. 
Your task is to generate ONLY valid JSON (no markdown, no code fences, no explanations).
The JSON must exactly follow this structure and contain exactly the number of questions requested.

### REQUIRED JSON FORMAT EXAMPLE ###
{
  "topic": "Python OOP",
  "context": ["Object-Oriented Programming concepts"],
  "difficulty": "medium",
  "question_types": ["mcq", "coding", "short", "theory"],
  "total_questions": 5,
  "generic_count": 2,
  "practical_count": 3,
  "generation_time": 0.0,
  "questions": [
    {
      "id": "uuid",
      "type": "mcq",
      "text": "What is encapsulation in Python?",
      "difficulty": "medium",
      "is_generic": true,
      "options": [
        {"option": "Hiding implementation details", "is_correct": true, "explanation": "Encapsulation hides data and methods."},
        {"option": "Multiple inheritance", "is_correct": false, "explanation": "This is a separate concept."}
      ],
      "answer": "Encapsulation hides implementation details and protects object data.",
      "explanation": "Encapsulation uses private variables and getters/setters.",
      "code": ""
    }
  ]
}

### RULES ###
- Return strictly valid JSON only.
- Do NOT include markdown code blocks (no ```).
- Do NOT include any text outside the JSON.
- The JSON must contain exactly {num_questions} questions.
- If you generate fewer, your output is INVALID.
"""

PROMPT_TEMPLATE = """{system}

TOPIC: {topic}
CONTEXT: {context_str}

REQUIREMENTS:
- Number of questions: {num_questions}
- Difficulty: {difficulty}
- Generic percentage: {generic_percentage}%
- Practical percentage: {practical_percentage}%
- Allowed question types: {question_types}
- Include answers: {include_answers}

Now generate the JSON object following the exact schema and rules above.
"""

# ---------------------------------------------------------------------------
# QuestionGenerator class
# ---------------------------------------------------------------------------

class QuestionGenerator:
    """Generates interview questions using Gemini with robust JSON enforcement."""

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
        # Strip markdown code fences and ```json markers
        cleaned = re.sub(r"```(?:json)?", "", text)
        # Extract first JSON block between { }
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return match.group(0)
        return cleaned.strip()

    def _parse_and_validate(self, text: str, difficulty: str) -> Dict[str, Any]:
        """Try loading JSON, repairing if necessary."""
        extracted = self._extract_json_block(text)
        parsed, err = try_load_json(extracted)

        if not parsed:
            # Try repairing trailing commas
            repaired = re.sub(r",(\s*[}\]])", r"\1", extracted)
            parsed, _ = try_load_json(repaired)

        if not parsed:
            raise ValueError("Gemini returned no valid JSON block.")

        # Ensure every question has an ID and answer
        questions = parsed.get("questions", [])
        for q in questions:
            q.setdefault("id", str(uuid.uuid4()))
            q.setdefault("answer", "")
            q.setdefault("explanation", "")
            q.setdefault("is_generic", False)
            q.setdefault("difficulty", difficulty)
            if "options" not in q:
                q["options"] = []

        parsed["questions"] = questions
        parsed["difficulty"] = difficulty
        parsed["total_questions"] = len(questions)
        parsed["generic_count"] = sum(1 for q in questions if q.get("is_generic"))
        parsed["practical_count"] = parsed["total_questions"] - parsed["generic_count"]
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
        """Main entrypoint compatible with app.py"""
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

        # Step 1: generate
        raw = self.gemini.generate(prompt)
        raw_text = raw.get("text") if isinstance(raw, dict) else str(raw)

        # Step 2: parse
        try:
            payload = self._parse_and_validate(raw_text, difficulty_level)
        except Exception:
            # Retry with explicit repair prompt
            repair_prompt = f"Please convert this into valid JSON following the schema. Output JSON only:\n\n{raw_text[:2000]}"
            repaired = self.gemini.generate(repair_prompt)
            payload = self._parse_and_validate(
                repaired.get("text") if isinstance(repaired, dict) else str(repaired),
                difficulty_level,
            )

        payload["generation_time"] = round(time.time() - start, 2)

        # Fallback if Gemini returned fewer than expected
        total = len(payload.get("questions", []))
        if total < num_questions:
            # Add placeholder questions
            for _ in range(num_questions - total):
                payload["questions"].append({
                    "id": str(uuid.uuid4()),
                    "type": "short",
                    "text": f"⚠️ Placeholder: Gemini returned fewer than {num_questions} questions.",
                    "difficulty": difficulty_level,
                    "is_generic": True,
                    "answer": "",
                    "explanation": ""
                })
            payload["total_questions"] = len(payload["questions"])

        return payload
