"""Gemini API integration for question generation"""

import google.generativeai as genai
import re
import time
import random
from typing import List, Dict

class GeminiService:
    """Service for interacting with Google Gemini API"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = self._get_best_available_model()
    
    def _get_best_available_model(self):
        """Dynamically find the best available model to avoid 404 errors"""
        try:
            available_models = list(genai.list_models())
            
            # Priority list (Fastest/Best -> Fallback)
            priority_order = [
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-1.0-pro",
                "gemini-pro"
            ]
            
            # 1. Try to find a specific match from our priority list
            for preferred in priority_order:
                for model in available_models:
                    if preferred in model.name and 'generateContent' in model.supported_generation_methods:
                        print(f"Selected model: {model.name}")
                        return genai.GenerativeModel(model.name)

            # 2. If no exact match, grab the first one that supports content generation
            for model in available_models:
                if 'generateContent' in model.supported_generation_methods:
                    print(f"Fallback model: {model.name}")
                    return genai.GenerativeModel(model.name)
            
            # 3. Absolute fallback (blind guess if list_models fails)
            return genai.GenerativeModel("gemini-1.5-flash")
            
        except Exception as e:
            print(f"Error listing models: {e}. Defaulting to gemini-1.5-flash")
            return genai.GenerativeModel("gemini-1.5-flash")

    def generate_questions(self, prompt: str) -> str:
        max_retries = 4 
        base_delay = 5 
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=3000, 
                        temperature=0.5,
                    )
                )
                
                if response and hasattr(response, 'text') and response.text:
                    return response.text
                
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                    
                raise Exception("Empty response received from Gemini API.")
                
            except Exception as e:
                error_str = str(e)
                
                # Handle Rate Limits (429) / Quota
                if "429" in error_str or "quota" in error_str.lower() or "resource_exhausted" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = (base_delay * (2 ** attempt)) + random.uniform(1, 3)
                        time.sleep(wait_time)
                        continue
                    raise Exception("⚠️ API Busy: Rate limit reached. Please wait 30-60 seconds.")
                
                # Handle Overloaded (503)
                if "503" in error_str or "overloaded" in error_str.lower():
                     if attempt < max_retries - 1:
                        time.sleep(5)
                        continue
                        
                raise Exception(f"Gemini API Error: {error_str}")
    
    def parse_qa_pairs(self, response_text: str, expected_count: int = None) -> List[Dict[str, str]]:
        if not response_text:
            return []
        
        qa_pairs = []
        response_text = response_text.replace('```', '')

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
                question_text = parts[0].strip()
                answer_text = parts[1].strip()
            
            question_text = re.sub(r'\*+', '', question_text).strip()
            answer_text = re.sub(r'\*+', '', answer_text).strip()
            
            question_type = "generic"
            if "(PRACTICAL)" in question_text.upper():
                question_type = "practical"
                question_text = re.sub(r'\(PRACTICAL\)', '', question_text, flags=re.IGNORECASE).strip()
            elif "(GENERIC)" in question_text.upper():
                question_text = re.sub(r'\(GENERIC\)', '', question_text, flags=re.IGNORECASE).strip()
            
            if question_text and answer_text and len(question_text) > 5:
                qa_pairs.append({
                    "id": len(qa_pairs) + 1,
                    "question": question_text,
                    "answer": answer_text,
                    "type": question_type
                })
            
            i += 2
        
        return qa_pairs
