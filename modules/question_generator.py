import time, uuid
from typing import List, Dict
from modules.gemini_handler import GeminiHandler
from modules.schemas import GenerationResult
from app_utils.json_safety import try_load_json
SYSTEM_INSTRUCTIONS = """You are an expert technical interviewer. Generate high-quality interview questions.
Output MUST be a single JSON object with the following keys:
- topic (string)
- context (array of strings)
- difficulty ("easy"|"medium"|"hard")
- question_types (array of "mcq"|"coding"|"short"|"theory")
- total_questions (int)
- generic_count (int)
- practical_count (int)
- generation_time (float, seconds) // leave 0.0; the app fills it
- questions (array) where each item has:
  - id (string, unique)
  - type ("mcq"|"coding"|"short"|"theory")
  - text (string)
  - difficulty ("easy"|"medium"|"hard")
  - is_generic (boolean)
  - options (array, optional; for mcq) items: { option (string), is_correct (boolean), explanation (string optional) }
  - answer (string, optional)
  - explanation (string, optional)
  - code (string, optional; for coding)
Return ONLY JSON. Do NOT add commentary or code fences."""
PROMPT_TEMPLATE = """{system}
TOPIC: {topic}
SUBTOPICS/CONTEXT (optional): {context_str}
REQUIREMENTS:
- Total questions: {num_questions}
- Generic vs Practical ratio: {generic_percentage}% generic, {practical_percentage}% practical
- Difficulty: {difficulty}
- Allowed types: {question_types}
- Include answers/explanations: {include_answers}
If MCQs are included:
- Provide at least 4 options; exactly ONE should be marked is_correct=true.
- Provide a brief explanation for why the correct option is correct.
If coding questions are included:
- Provide a short problem statement and, if answers are included, a sample solution in 'code'.
Ensure the final output strictly follows the JSON schema described above."""
class QuestionGenerator:
    def __init__(self, gemini_handler: GeminiHandler):
        self.gemini = gemini_handler
    def _build_prompt(self, topic: str, context: List[str], num_questions: int, generic_percentage: int,
                      difficulty_level: str, question_types: List[str], include_answers: bool) -> str:
        practical = 100 - generic_percentage
        ctx = ", ".join([c.strip() for c in context if c.strip()]) or "(none)"
        return PROMPT_TEMPLATE.format(system=SYSTEM_INSTRUCTIONS, topic=topic.strip(), context_str=ctx,
                                     num_questions=num_questions, generic_percentage=generic_percentage,
                                     practical_percentage=practical, difficulty=difficulty_level,
                                     question_types=", ".join(question_types),
                                     include_answers=str(bool(include_answers)).lower())
    def _ensure_ids(self, payload: Dict) -> Dict:
        for q in payload.get("questions", []):
            if not q.get("id"): q["id"] = uuid.uuid4().hex[:8]
        return payload
    def _validate_and_fix(self, raw_json: str) -> Dict:
        data, err = try_load_json(raw_json)
        if data is None:
            raise ValueError(f"Model did not return valid JSON. Parse error: {err}\nSnippet: {raw_json[:300]}...")
        data.setdefault("questions", []); data.setdefault("question_types", [])
        data = self._ensure_ids(data)
        validated = GenerationResult.model_validate(data)  # type: ignore
        return validated.model_dump()
    def generate_questions(self, topic: str, context: List[str], num_questions: int, generic_percentage: int,
                           difficulty_level: str, question_types: List[str], include_answers: bool) -> Dict:
        start = time.time()
        prompt = self._build_prompt(topic, context, num_questions, generic_percentage, difficulty_level, question_types, include_answers)
        raw = self.gemini.generate(prompt)
        payload = self._validate_and_fix(raw)
        payload["generation_time"] = round(time.time() - start, 2)
        payload["total_questions"] = len(payload.get("questions", []))
        payload["generic_count"] = sum(1 for q in payload.get("questions", []) if q.get("is_generic"))
        payload["practical_count"] = payload["total_questions"] - payload["generic_count"]
        return payload
