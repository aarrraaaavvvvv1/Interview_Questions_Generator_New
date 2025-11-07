import time, uuid
from typing import List, Dict, Any
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

Each question object must have:
- id (string, unique)
- type ("mcq"|"coding"|"short"|"theory")
- text (string)
- difficulty ("easy"|"medium"|"hard")
- is_generic (boolean)
- options (array, optional; for mcq) items: { "option": string, "is_correct": boolean, "explanation": string optional }
- answer (string, optional)
- explanation (string, optional)
- code (string, optional; for coding)

Do not include any commentary or code fences — JSON only.
All strings must be valid JSON strings (escape newlines as \\n)."""

PROMPT_TEMPLATE = """{system}

TOPIC: {topic}

SUBTOPICS/CONTEXT: {context_str}

REQUIREMENTS:
- Total questions: {num_questions}
- Generic vs Practical ratio: {generic_percentage}% generic, {practical_percentage}% practical
- Difficulty: {difficulty}
- Allowed types: {question_types}
- Include answers/explanations: {include_answers}

MCQs: At least 4 options and exactly ONE with "is_correct": true (+ a brief explanation).
Coding: Provide a brief problem and (if answers included) a short sample solution in "code".

Return JSON ONLY.
"""

FIX_TEMPLATE = """You previously returned invalid JSON or incorrect schema. Repair it to valid minified JSON that matches the schema.
Rules:
- Return ONLY JSON (no markdown or fences).
- Ensure all strings are escaped.
- MCQs must have options as objects: { "option": "...", "is_correct": true/false } with exactly one true.
- Include required fields (topic, context, difficulty, question_types, total_questions, generic_count, practical_count, generation_time, questions).

Invalid sample (truncated):
{bad_snippet}

Now return the corrected JSON:"""

class QuestionGenerator:
    """Generates interview questions via Gemini with strict JSON enforcement and schema normalization."""

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

    # ---------------- Normalization helpers ----------------

    def _ensure_ids(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        for q in payload.get("questions", []) or []:
            if not q.get("id"):
                q["id"] = uuid.uuid4().hex[:8]
        return payload

    def _infer_type(self, q: Dict[str, Any]) -> str:
        if q.get("type"):
            return q["type"]
        if q.get("options"):
            return "mcq"
        if q.get("code"):
            return "coding"
        if q.get("answer"):
            return "short" if len(str(q.get("answer", ""))) < 180 else "theory"
        return "theory"

    # ---- NEW: aggressive key cleanup / mapping ----

    _SMART_QUOTES = {
        "\u2018": "", "\u2019": "",  # ‘ ’
        "\u201C": "", "\u201D": "",  # “ ”
        "\u00AB": "", "\u00BB": "",  # « »
    }

    def _strip_all_quotes_spaces(self, s: Any) -> str:
        if s is None:
            return ""
        t = str(s).strip()
        # strip ascii quotes
        if t.startswith('"') and t.endswith('"') and len(t) >= 2:
            t = t[1:-1].strip()
        if t.startswith("'") and t.endswith("'") and len(t) >= 2:
            t = t[1:-1].strip()
        # strip smart quotes
        for q, repl in self._SMART_QUOTES.items():
            t = t.replace(q, repl)
        return t.strip()

    def _clean_key(self, k: Any) -> str:
        t = self._strip_all_quotes_spaces(k).lower()
        # collapse multiple spaces / punctuation around words
        t = " ".join(t.split())
        t = t.replace("_", " ")
        # canonicalize by containment
        if "option" in t:
            return "option"
        if "correct" in t or "answer" in t or "is correct" in t:
            return "is_correct"
        if "explanation" in t or "reason" in t or "why" in t:
            return "explanation"
        if t in {"label", "name", "value", "choice", "text"}:
            return "option"
        return t

    def _coerce_bool(self, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        return s in {"1", "true", "yes", "y", "correct"}

    def _opt_text_from_dict(self, od: Dict[str, Any]) -> str:
        # After cleaning keys, try common names
        for key in ("option", "text", "label", "value", "name", "choice"):
            if key in od and od[key]:
                return self._strip_all_quotes_spaces(od[key])
        # fallback to any first non-empty value
        for v in od.values():
            if v:
                return self._strip_all_quotes_spaces(v)
        return ""

    def _normalize_options(self, q: Dict[str, Any]) -> List[Dict[str, Any]]:
        opts = q.get("options")
        if not opts:
            return []

        normalized: List[Dict[str, Any]] = []

        if isinstance(opts, list):
            for item in opts:
                # Case 1: raw string option
                if isinstance(item, str):
                    normalized.append({"option": self._strip_all_quotes_spaces(item), "is_correct": False})
                    continue

                # Case 2: dict with messy keys
                if isinstance(item, dict):
                    norm_dict: Dict[str, Any] = {}
                    for k, v in item.items():
                        ck = self._clean_key(k)
                        # don't clobber a meaningful 'option' with empty text
                        if ck not in norm_dict or (ck == "option" and not norm_dict.get("option")):
                            norm_dict[ck] = v

                    text = self._opt_text_from_dict(norm_dict) or self._strip_all_quotes_spaces(str(item))
                    is_corr = self._coerce_bool(norm_dict.get("is_correct", False))
                    explanation = norm_dict.get("explanation") or None

                    normalized.append({
                        "option": text or "Option",
                        "is_correct": bool(is_corr),
                        "explanation": explanation
                    })
                    continue

                # Case 3: any other type → stringified
                normalized.append({"option": self._strip_all_quotes_spaces(item), "is_correct": False})

        # Enforce exactly one correct
        answer_text = self._strip_all_quotes_spaces(q.get("answer") or q.get("correct") or "")
        if normalized:
            # If multiple marked correct, keep the first only
            first_found = False
            for opt in normalized:
                if self._coerce_bool(opt.get("is_correct", False)):
                    if not first_found:
                        opt["is_correct"] = True
                        first_found = True
                    else:
                        opt["is_correct"] = False

            if not first_found:
                # try to match by answer text
                if answer_text:
                    for opt in normalized:
                        if self._strip_all_quotes_spaces(opt.get("option", "")).lower() == answer_text.lower():
                            opt["is_correct"] = True
                            first_found = True
                            break
                if not first_found and normalized:
                    normalized[0]["is_correct"] = True

        # Guarantee schema keys exist (no KeyError later)
        for opt in normalized:
            if "option" not in opt:
                opt["option"] = "Option"
            if "is_correct" not in opt:
                opt["is_correct"] = False
        return normalized

    def _normalize_question(self, q: Dict[str, Any], fallback_difficulty: str) -> Dict[str, Any]:
        q = dict(q)

        # Map alternate keys to text
        if not q.get("text") and q.get("question"):
            q["text"] = q.get("question")

        # Defaults
        q["difficulty"] = (q.get("difficulty") or fallback_difficulty or "medium").lower()
        q["type"] = self._infer_type(q)
        if "is_generic" not in q:
            q["is_generic"] = False

        # Normalize options for MCQ (even if type not set but options present)
        if q["type"] == "mcq" or q.get("options"):
            q["options"] = self._normalize_options(q)
            # if options ended up empty, unset to None
            if not q["options"]:
                q["options"] = None
        else:
            q["options"] = q.get("options") or None

        if not q.get("text"):
            q["text"] = q.get("prompt") or q.get("title") or "Question"

        if not q.get("id"):
            q["id"] = uuid.uuid4().hex[:8]

        return q

    def _normalize_top_level(self, data: Any, difficulty: str) -> Dict[str, Any]:
        """Accept dict or list; always return dict with required top-level keys present."""
        if isinstance(data, list):
            data = {
                "topic": "General",
                "context": [],
                "difficulty": difficulty or "medium",
                "question_types": [],
                "questions": data
            }
        if not isinstance(data, dict):
            raise ValueError("Unexpected JSON structure: not dict or list.")

        # Required top-level defaults BEFORE validation
        data.setdefault("topic", "General")
        data.setdefault("context", [])
        data.setdefault("difficulty", difficulty or "medium")
        data.setdefault("question_types", [])
        data.setdefault("total_questions", 0)
        data.setdefault("generic_count", 0)
        data.setdefault("practical_count", 0)
        data.setdefault("generation_time", 0.0)

        # Normalize questions
        qs = data.get("questions") or []
        norm_qs = []
        for q in qs:
            if isinstance(q, dict):
                norm_qs.append(self._normalize_question(q, data["difficulty"]))
            else:
                norm_qs.append(self._normalize_question({"text": str(q)}, data["difficulty"]))
        data["questions"] = norm_qs
        return data

    def _parse_validate(self, raw: str, difficulty: str) -> Dict[str, Any]:
        data, err = try_load_json(raw)
        if data is None:
            raise ValueError(f"Model did not return valid JSON. Parse error: {err}")
        data = self._normalize_top_level(data, difficulty)
        data = self._ensure_ids(data)
        validated = GenerationResult.model_validate(data)  # pydantic
        return validated.model_dump()

    def _repair_once(self, bad: str) -> str:
        snippet = bad[:800]
        fix_prompt = FIX_TEMPLATE.format(bad_snippet=snippet)
        return self.gemini.generate(
            fix_prompt,
            generation_config={"response_mime_type": "application/json"},
        )

    # ---------------- Public API ----------------

    def generate_questions(
        self,
        topic: str,
        context: List[str],
        num_questions: int,
        generic_percentage: int,
        difficulty_level: str,
        question_types: List[str],
        include_answers: bool,
    ) -> Dict[str, Any]:
        start = time.time()
        prompt = self._build_prompt(
            topic, context, num_questions, generic_percentage,
            difficulty_level, question_types, include_answers
        )

        # First attempt
        raw = self.gemini.generate(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        # Try parse/validate; if fails, do one repair attempt
        try:
            payload = self._parse_validate(raw, difficulty_level)
        except Exception:
            repaired = self._repair_once(raw)
            payload = self._parse_validate(repaired, difficulty_level)

        # Fill computed fields AFTER validation-friendly defaults
        payload["generation_time"] = round(time.time() - start, 2)
        payload["total_questions"] = len(payload.get("questions", []))
        payload["generic_count"] = sum(1 for q in payload.get("questions", []) if q.get("is_generic"))
        payload["practical_count"] = payload["total_questions"] - payload["generic_count"]
        return payload
