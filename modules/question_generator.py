import json
import re
import time
from typing import List, Dict, Optional
from modules.gemini_handler import GeminiHandler

class QuestionGenerator:
    """Generates interview questions using Gemini with proper question type handling"""
    
    def __init__(self, gemini_handler: GeminiHandler):
        self.gemini_handler = gemini_handler
    
    def _create_prompt(self, topic: str, context: List[str], num_questions: int, generic_percentage: int, difficulty_level: str, question_types: List[str], include_answers: bool, enhanced_context: str = "") -> str:
        generic_count = int(num_questions * generic_percentage / 100)
        practical_count = num_questions - generic_count
        context_str = ", ".join(context) if context else "General topics"
        question_types_str = ", ".join(question_types) if question_types else "Short Answer, Long Answer"
        
        type_descriptions = {
            "Multiple Choice": "Multiple choice questions with 4 options (A, B, C, D)",
            "Short Answer": "Questions answerable in 1-2 sentences",
            "Long Answer": "Questions requiring detailed 3-5 paragraph answers",
            "Code-based": "Questions requiring code snippets or programming solutions",
            "Scenario-based": "Real-world scenario questions requiring practical thinking",
            "Debugging": "Questions where you identify and fix code bugs"
        }
        
        type_details = "\n".join([f"- {t}: {type_descriptions.get(t, t)}" for t in question_types])
        
        prompt = f"""You are an expert interview question generator. Generate EXACTLY {num_questions} interview questions in valid JSON format.

REQUIREMENTS:
- Topic: {topic}
- Sub-topics to cover: {context_str}
- Exact number of questions: {num_questions}
- Generic/theoretical questions: {generic_count}
- Practical/real-world questions: {practical_count}
- Difficulty level: {difficulty_level}
- Question types to use (distribute evenly):
{type_details}
- Include answers: {'Yes, detailed answers' if include_answers else 'No, only questions'}

CONTEXT (Use this to make answers current and relevant):
{enhanced_context if enhanced_context else "Use your general knowledge"}

STRICT INSTRUCTIONS:
1. Output ONLY valid JSON array starting with [ and ending with ]
2. NO markdown formatting, NO code blocks, NO explanations
3. Each question MUST have ALL required fields
4. Distribute question types evenly across the {num_questions} questions
5. Ensure {generic_count} questions have "is_generic": true
6. Ensure {practical_count} questions have "is_generic": false
7. For each question type, generate questions appropriate to that type
8. All JSON strings must have proper escaping
9. Use commas between array elements correctly

JSON STRUCTURE (repeat {num_questions} times):
{{
  "question_number": <number>,
  "question": "<exact question text>",
  "type": "<one of: Multiple Choice, Short Answer, Long Answer, Code-based, Scenario-based, Debugging>",
  "difficulty": "{difficulty_level}",
  "is_generic": <true or false>,
  "category": "<one of the sub-topics>",
  "answer": "<detailed answer>",
  "keywords": ["<keyword1>", "<keyword2>", "<keyword3>"]
}}

Start with [ and end with ]. Generate exactly {num_questions} questions."""
        
        return prompt
    
    def _parse_questions(self, response_text: str) -> List[Dict]:
        try:
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON array found in response")
            
            json_str = json_match.group(0)
            
            try:
                questions = json.loads(json_str)
            except json.JSONDecodeError as e:
                cleaned = self._clean_json(json_str)
                questions = json.loads(cleaned)
            
            if not isinstance(questions, list):
                raise ValueError("Response is not a JSON array")
            
            if len(questions) == 0:
                raise ValueError("JSON array is empty")
            
            return questions
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error parsing questions: {str(e)}")
    
    def _clean_json(self, json_str: str) -> str:
        """Clean malformed JSON"""
        lines = json_str.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip():
                if not line.strip().endswith(',') and not line.strip().endswith('{') and not line.strip().endswith('['):
                    if line.strip().endswith('}'):
                        cleaned_lines.append(line)
                    else:
                        if not any(line.strip().startswith(c) for c in ['"', ']']):
                            line = line.rstrip(',')
                            if cleaned_lines and not cleaned_lines[-1].rstrip().endswith('{'):
                                cleaned_lines.append(line + ',')
                            else:
                                cleaned_lines.append(line)
                        else:
                            cleaned_lines.append(line)
                else:
                    cleaned_lines.append(line)
        return '\n'.join(cleaned_lines)
    
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
        
        response = self.gemini_handler.generate_content(prompt, 0.7, 8000)
        
        questions = self._parse_questions(response)
        
        self._validate_questions(questions, num_questions, generic_percentage)
        
        generation_time = round(time.time() - start_time, 2)
        
        return {
            "topic": topic,
            "context": context,
            "difficulty": difficulty_level,
            "question_types": question_types,
            "total_questions": len(questions),
            "generic_count": sum(1 for q in questions if q.get("is_generic", False)),
            "practical_count": sum(1 for q in questions if not q.get("is_generic", False)),
            "generation_time": generation_time,
            "questions": questions
        }
