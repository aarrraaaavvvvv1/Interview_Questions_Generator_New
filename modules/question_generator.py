import json
import re
import time
from typing import List, Dict, Optional
from modules.gemini_handler import GeminiHandler

class QuestionGenerator:
    """Generates interview questions using Gemini"""
    
    def __init__(self, gemini_handler: GeminiHandler):
        self.gemini_handler = gemini_handler
    
    def _create_prompt(self, topic: str, context: List[str], num_questions: int, generic_percentage: int, difficulty_level: str, question_types: List[str], include_answers: bool, enhanced_context: str = "") -> str:
        generic_count = int(num_questions * generic_percentage / 100)
        practical_count = num_questions - generic_count
        context_str = ", ".join(context) if context else "General topics"
        question_types_str = ", ".join(question_types) if question_types else "Short Answer, Long Answer"
        
        prompt = f"""You are an expert interview question generator. Generate exactly {num_questions} interview questions.

REQUIREMENTS:
- Topic: {topic}
- Sub-topics to cover: {context_str}
- Number of generic/theoretical questions: {generic_count}
- Number of practical/real-world questions: {practical_count}
- Difficulty level: {difficulty_level}
- Question types: {question_types_str}
- Include answers: {'Yes, provide detailed answers' if include_answers else 'No, only questions'}

ADDITIONAL CONTEXT:
{enhanced_context if enhanced_context else "No additional context"}

IMPORTANT INSTRUCTIONS:
1. Return ONLY a valid JSON array - nothing else
2. Do not include any markdown formatting or code blocks
3. Each question must be a separate object in the array
4. Start your response with [ and end with ]

FORMAT - Return ONLY this JSON structure (no other text):
[
  {{
    "question_number": 1,
    "question": "The actual question text here",
    "type": "Short Answer",
    "difficulty": "{difficulty_level}",
    "is_generic": true,
    "category": "sub-topic name",
    "answer": "Detailed answer here",
    "keywords": ["keyword1", "keyword2", "keyword3"]
  }}
]

Generate {num_questions} questions following this exact format. Make sure to include {generic_count} generic questions (is_generic: true) and {practical_count} practical questions (is_generic: false)."""
        return prompt
    
    def _parse_questions(self, response_text: str) -> List[Dict]:
        try:
            response_text = response_text.replace("``````", "")
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("Could not find JSON array in response")
            json_str = json_match.group(0)
            questions = json.loads(json_str)
            if not isinstance(questions, list):
                raise ValueError("Response is not a JSON array")
            if len(questions) == 0:
                raise ValueError("JSON array is empty")
            return questions
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error parsing questions: {str(e)}")
    
    def _validate_questions(self, questions: List[Dict], num_questions: int, generic_percentage: int) -> bool:
        if len(questions) != num_questions:
            return False
        generic_count = sum(1 for q in questions if q.get("is_generic", False))
        expected_generic = int(num_questions * generic_percentage / 100)
        if abs(generic_count - expected_generic) > 1:
            return False
        return True
    
    def generate_questions(self, topic: str, context: List[str], num_questions: int, generic_percentage: int, difficulty_level: str, question_types: List[str], include_answers: bool, enhanced_context: str = "") -> Dict:
        start_time = time.time()
        prompt = self._create_prompt(topic, context, num_questions, generic_percentage, difficulty_level, question_types, include_answers, enhanced_context)
        response = self.gemini_handler.generate_content(prompt, 0.7, 4000)
        questions = self._parse_questions(response)
        self._validate_questions(questions, num_questions, generic_percentage)
        generation_time = round(time.time() - start_time, 2)
        
        return {
            "topic": topic,
            "context": context,
            "difficulty": difficulty_level,
            "total_questions": len(questions),
            "generic_count": sum(1 for q in questions if q.get("is_generic", False)),
            "practical_count": sum(1 for q in questions if not q.get("is_generic", False)),
            "generation_time": generation_time,
            "questions": questions
        }
