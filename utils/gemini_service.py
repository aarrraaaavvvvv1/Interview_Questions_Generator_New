"""Gemini API integration for question generation"""

import google.generativeai as genai
import re
import time
from typing import List, Dict

class GeminiService:
    """Service for interacting with Google Gemini API"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = None
        self._find_available_model()
    
    def _find_available_model(self):
        try:
            available_models = genai.list_models()
            
            for model in available_models:
                if 'generateContent' in model.supported_generation_methods:
                    model_name = model.name.split('/')[-1]
                    
                    if 'exp' in model_name or '2.5' in model_name:
                        continue
                    
                    try:
                        self.model = genai.GenerativeModel(model_name)
                        return
                    except:
                        continue
            
            self.model = genai.GenerativeModel("gemini-pro")
        except:
            self.model = genai.GenerativeModel("gemini-pro")
    
    def generate_questions(self, prompt: str) -> str:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=2000,
                        temperature=0.5,
                    )
                )
                
                if response and hasattr(response, 'text') and response.text:
                    return response.text
                
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                    
                raise Exception("Empty response from Gemini")
                
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    if attempt < max_retries - 1:
                        time.sleep(5 * (attempt + 1))
                        continue
                    raise Exception("Rate limit exceeded. Please wait and try again.")
                raise
    
    def parse_qa_pairs(self, response_text: str, expected_count: int = None) -> List[Dict[str, str]]:
        if not response_text:
            return []
        
        qa_pairs = []
        response_text = response_text.replace('```
        
        question_splits = re.split(
            r'\*{0,2}QUESTION\s+(\d+)\s*:?\*{0,2}',
            response_text,
            flags=re.IGNORECASE
        )
        
        i = 1
        while i < len(question_splits) - 1:
            content = question_splits[i + 1]
            
            answer_match = re.search(
                r'\*{0,2}ANSWER\s+\d+\s*:?\*{0,2}\s*(.+?)(?=\*{0,2}QUESTION|\Z)',
                content,
                re.IGNORECASE | re.DOTALL
            )
            
            if answer_match:
                question_text = content[:answer_match.start()].strip()
                answer_text = answer_match.group(1).strip()
            else:
                parts = content.split('\n\n', 1)
                if len(parts) < 2:
                    i += 2
                    continue
                question_text = parts.strip()
                answer_text = parts.strip()[1]
            
            question_text = re.sub(r'\*+', '', question_text).strip()
            answer_text = re.sub(r'\*+', '', answer_text).strip()
            
            question_type = "generic"
            if "(PRACTICAL)" in question_text.upper():
                question_type = "practical"
                question_text = re.sub(r'\(PRACTICAL\)', '', question_text, flags=re.IGNORECASE).strip()
            elif "(GENERIC)" in question_text.upper():
                question_text = re.sub(r'\(GENERIC\)', '', question_text, flags=re.IGNORECASE).strip()
            
            if question_text and answer_text and len(question_text) > 10:
                qa_pairs.append({
                    "id": len(qa_pairs) + 1,
                    "question": question_text,
                    "answer": answer_text,
                    "type": question_type
                })
            
            i += 2
        
        return qa_pairs
