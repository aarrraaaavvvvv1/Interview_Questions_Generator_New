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
        
        type_descriptions = {
            "Multiple Choice": "Generate exactly 4 options (A, B, C, D). Question MUST include all 4 options in the question field. Format: 'Question text\nA) Option 1\nB) Option 2\nC) Option 3\nD) Option 4'. Answer field MUST be: 'The correct answer is [A/B/C/D]. Explanation: [detailed explanation of why this is correct]'",
            "Short Answer": "Questions answerable in 1-2 sentences. Answer field should contain the concise answer",
            "Long Answer": "Questions requiring detailed 3-5 paragraph answers. Answer field should contain full detailed answer",
            "Code-based": "Questions asking to write or analyze code. Question should specify what code to write. Answer field should contain the complete code solution with comments and explanation",
            "Scenario-based": "Real-world scenario questions describing a situation. Question should describe the scenario fully. Answer field should explain how to handle it",
            "Debugging": "Questions asking to find and fix bugs in provided code. Question should include buggy code. Answer field should show corrected code and explain the fix"
        }
        
        type_details = "\n".join([f"- {t}: {type_descriptions.get(t, t)}" for t in question_types])
        
        prompt = f"""You are an expert interview question generator. Generate EXACTLY {num_questions} interview questions in valid JSON format.

CRITICAL REQUIREMENTS:
1. Generate EXACTLY {num_questions} questions - no more, no less
2. MUST stick to ONLY the question types specified below
3. EACH question MUST be of ONE of the selected types
4. Distribute question types EVENLY across all questions
5. DO NOT mix types (e.g., don't make a "Long Answer" when "Multiple Choice" is selected)
6. If user selected only "Multiple Choice", ALL questions MUST be multiple choice
7. If user selected only "Code-based", ALL questions MUST have code in them

TOPIC & SUBTOPICS:
- Topic: {topic}
- Sub-topics to cover: {context_str}
- Difficulty level: {difficulty_level}

QUESTION TYPES (MUST FOLLOW THESE EXACTLY):
{type_details}

GENERIC VS PRACTICAL:
- Generic/theoretical questions: {generic_count} (is_generic: true)
- Practical/real-world questions: {practical_count} (is_generic: false)

INCLUDE ANSWERS: {'Yes, detailed answers' if include_answers else 'No, only questions'}

CONTEXT FOR ACCURACY:
{enhanced_context if enhanced_context else "Use your general knowledge"}

STRICT JSON REQUIREMENTS:
1. Output ONLY valid JSON array starting with [ and ending with ]
2. NO markdown formatting, NO code blocks, NO explanations outside JSON
3. NO extra text before or after JSON
4. Each question MUST have ALL these fields with correct values
5. All special characters in strings MUST be escaped properly
6. Use commas between array elements correctly

QUESTION TYPE VALIDATION:
- Multiple Choice: MUST have A), B), C), D) options in question text AND answer with explanation
- Short Answer: Should be 1-2 sentence answer
- Long Answer: Should be 3-5 paragraph detailed answer
- Code-based: MUST have code in question and/or answer
- Scenario-based: MUST describe a real scenario
- Debugging: MUST include buggy code to fix

JSON STRUCTURE (repeat {num_questions} times, ONLY these types: {', '.join(question_types)}):
{{
  "question_number": <number>,
  "question": "<COMPLETE question text including all options for Multiple Choice or full scenario for Scenario-based>",
  "type": "<EXACTLY one of: {', '.join(question_types)}>",
  "difficulty": "{difficulty_level}",
  "is_generic": <true or false>,
  "category": "<one of the sub-topics or {topic}>",
  "answer": "<detailed answer with explanation if applicable>",
  "keywords": ["<keyword1>", "<keyword2>", "<keyword3>"]
}}

EXAMPLE FOR MULTIPLE CHOICE:
{{
  "question_number": 1,
  "question": "What is the output of this Python code?\\nprint(2 ** 3)\\n\\nA) 5\\nB) 6\\nC) 8\\nD) 9",
  "type": "Multiple Choice",
  "difficulty": "{difficulty_level}",
  "is_generic": false,
  "category": "Python",
  "answer": "The correct answer is C) 8. Explanation: The ** operator is the exponentiation operator in Python. 2 ** 3 means 2 raised to the power of 3, which equals 8.",
  "keywords": ["exponentiation", "python", "operators"]
}}

EXAMPLE FOR CODE-BASED:
{{
  "question_number": 2,
  "question": "Write a Python function that takes a list of numbers and returns the sum of all even numbers in the list.",
  "type": "Code-based",
  "difficulty": "{difficulty_level}",
  "is_generic": false,
  "category": "Python",
  "answer": "def sum_even_numbers(numbers):\\n    total = 0\\n    for num in numbers:\\n        if num % 2 == 0:\\n            total += num\\n    return total\\n\\nExplanation: This function iterates through the list, checks if each number is even using modulo operator (%), and adds it to the total if it is.",
  "keywords": ["functions", "loops", "conditional"]
}}

NOW GENERATE EXACTLY {num_questions} QUESTIONS OF THESE TYPES: {', '.join(question_types)}

Start with [ and end with ]. Generate exactly {num_questions} questions. VALIDATE that each question is ONE of the selected types."""
        
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
    
    def _validate_questions(self, questions: List[Dict], num_questions: int, generic_percentage: int, question_types: List[str]) -> bool:
        """Validate questions match requirements"""
        if len(questions) != num_questions:
            print(f"Warning: Expected {num_questions} questions, got {len(questions)}")
            return False
        
        generic_count = sum(1 for q in questions if q.get("is_generic", False))
        expected_generic = int(num_questions * generic_percentage / 100)
        if abs(generic_count - expected_generic) > 1:
            print(f"Warning: Expected {expected_generic} generic questions, got {generic_count}")
        
        # Validate question types
        for i, q in enumerate(questions):
            q_type = q.get("type", "")
            if q_type not in question_types:
                print(f"Warning: Question {i+1} has type '{q_type}' but selected types are {question_types}")
        
        return True
    
    def generate_questions(self, topic: str, context: List[str], num_questions: int, generic_percentage: int, difficulty_level: str, question_types: List[str], include_answers: bool, enhanced_context: str = "") -> Dict:
        start_time = time.time()
        
        prompt = self._create_prompt(topic, context, num_questions, generic_percentage, difficulty_level, question_types, include_answers, enhanced_context)
        
        response = self.gemini_handler.generate_content(prompt, 0.7, 8000)
        
        questions = self._parse_questions(response)
        
        self._validate_questions(questions, num_questions, generic_percentage, question_types)
        
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
