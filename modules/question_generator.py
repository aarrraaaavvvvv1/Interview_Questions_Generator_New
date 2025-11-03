import json
import re
import time
from typing import List, Dict, Optional
from modules.gemini_handler import GeminiHandler

class QuestionGenerator:
    """Generates interview questions using Gemini with strict type enforcement"""
    
    def __init__(self, gemini_handler: GeminiHandler):
        self.gemini_handler = gemini_handler
    
    def _create_prompt(self, topic: str, context: List[str], num_questions: int, generic_percentage: int, difficulty_level: str, question_types: List[str], include_answers: bool, enhanced_context: str = "") -> str:
        generic_count = int(num_questions * generic_percentage / 100)
        practical_count = num_questions - generic_count
        context_str = ", ".join(context) if context else "General topics"
        
        type_instructions = {
            "Multiple Choice": """
FORMAT REQUIREMENT:
Question field MUST contain the question followed by exactly 4 options on new lines:
Example:
"What is the capital of France?
A) London
B) Paris
C) Berlin
D) Madrid"

Answer field MUST be formatted as:
"The correct answer is [LETTER]. Explanation: [Why this is correct and why others are wrong]"
Example: "The correct answer is B) Paris. Explanation: Paris is the capital and largest city of France. London is the capital of UK, Berlin is the capital of Germany, and Madrid is the capital of Spain."
""",
            "Short Answer": "Questions that can be answered in 1-2 sentences. Keep answers concise.",
            "Long Answer": "Questions requiring detailed 3-5 paragraph answers with comprehensive explanations.",
            "Code-based": """Questions requiring code solutions. 
Question should ask to write or analyze code.
Answer should contain complete code with comments and explanation wrapped in triple backticks.
Example answer format:
```python
def example_function():
    # Your code here
    pass
```
Explanation: This function does...""",
            "Scenario-based": "Present a real-world scenario in the question. Answer should explain how to handle it step by step.",
            "Debugging": """Question should include buggy code.
Answer should show the corrected code and explain what was wrong.
Format answer as:
```python
# Corrected code here
```
Explanation: The bug was..."""
        }
        
        selected_instructions = "\n".join([f"**{t}**: {type_instructions[t]}" for t in question_types])
        
        prompt = f"""You are an expert interview question generator. Generate EXACTLY {num_questions} interview questions.

CRITICAL RULES - MUST FOLLOW:
1. Generate EXACTLY {num_questions} questions - NO MORE, NO LESS
2. Use ONLY these question types: {', '.join(question_types)}
3. Each question must be ONE of the selected types ONLY
4. If user selected only "Multiple Choice", ALL {num_questions} questions MUST be Multiple Choice
5. If user selected only "Code-based", ALL {num_questions} questions MUST be Code-based
6. Distribute types evenly if multiple types selected
7. DO NOT mix or create other types

TOPIC INFORMATION:
- Main Topic: {topic}
- Sub-topics: {context_str}
- Difficulty: {difficulty_level}
- Generic questions: {generic_count}
- Practical questions: {practical_count}
- Include answers: {'Yes, with detailed explanations' if include_answers else 'No'}

TYPE-SPECIFIC FORMATTING REQUIREMENTS:
{selected_instructions}

ADDITIONAL CONTEXT (use this for current information):
{enhanced_context if enhanced_context else "Use your general knowledge"}

OUTPUT FORMAT - RETURN ONLY VALID JSON:
[
  {{
    "question_number": 1,
    "question": "Question text here (with options for MC, code for debugging, etc.)",
    "type": "EXACTLY one of: {', '.join(question_types)}",
    "difficulty": "{difficulty_level}",
    "is_generic": true or false,
    "category": "{context_str if context else topic}",
    "answer": "Detailed answer following type-specific format",
    "keywords": ["keyword1", "keyword2", "keyword3"]
  }}
]

VALIDATION CHECKLIST before generating:
✓ Question count = {num_questions}
✓ All questions are one of: {', '.join(question_types)}
✓ Multiple Choice has A), B), C), D) options in question
✓ Multiple Choice answer starts with "The correct answer is"
✓ Code questions use triple backticks for code blocks
✓ Generic count = {generic_count}, Practical count = {practical_count}
✓ Output is valid JSON starting with [ and ending with ]

Generate exactly {num_questions} questions now. ONLY these types: {', '.join(question_types)}"""
        
        return prompt
    
    def _parse_questions(self, response_text: str) -> List[Dict]:
        try:
            # Remove markdown code blocks
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            # Find JSON array
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON array found in response")
            
            json_str = json_match.group(0)
            
            # Try to parse
            try:
                questions = json.loads(json_str)
            except json.JSONDecodeError:
                # Try cleaning
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
        # Remove trailing commas before closing braces/brackets
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        return json_str
    
    def _validate_questions(self, questions: List[Dict], num_questions: int, generic_percentage: int, question_types: List[str]) -> bool:
        """Validate questions match requirements"""
        if len(questions) != num_questions:
            print(f"Warning: Expected {num_questions} questions, got {len(questions)}")
        
        # Check types
        for i, q in enumerate(questions):
            q_type = q.get("type", "")
            if q_type not in question_types:
                print(f"Warning: Question {i+1} has type '{q_type}' but selected types are {question_types}")
        
        return True
    
    def generate_questions(self, topic: str, context: List[str], num_questions: int, generic_percentage: int, difficulty_level: str, question_types: List[str], include_answers: bool, enhanced_context: str = "") -> Dict:
        start_time = time.time()
        
        prompt = self._create_prompt(topic, context, num_questions, generic_percentage, difficulty_level, question_types, include_answers, enhanced_context)
        
        # Use higher token limit for complex questions
        response = self.gemini_handler.generate_content(prompt, temperature=0.7, max_tokens=10000)
        
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
