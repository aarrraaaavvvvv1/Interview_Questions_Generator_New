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
        self.model = None
        self._find_available_model()
    
    def _find_available_model(self):
        try:
            available_models = genai.list_models()
            
            # Priority list of models (newer models first)
            preferred_models = [
                "gemini-1.5-flash", # Often faster with better limits
                "gemini-1.5-pro",
                "gemini-pro"
            ]
            
            # Try to find a preferred model first
            for pref in preferred_models:
                for model in available_models:
                    if pref in model.name:
                        self.model = genai.GenerativeModel(model.name)
                        return

            # Fallback search if exact names don't match
            for model in available_models:
                if 'generateContent' in model.supported_generation_methods:
                    model_name = model.name.split('/')[-1]
                    if 'exp' in model_name: # Skip experimental unless necessary
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
        # Increased retries and backoff for stability
        max_retries = 5 
        base_delay = 5  # Start with 5 seconds wait
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=4000,
                        temperature=0.5,
                    )
                )
                
                if response and hasattr(response, 'text') and response.text:
                    return response.text
                
                # If response is empty but no error, wait briefly and retry
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                    
                raise Exception("Empty response from Gemini")
                
            except Exception as e:
                error_str = str(e)
                # Handle Rate Limits (429) and Quota issues specifically
                if "429" in error_str or "quota" in error_str.lower() or "resource_exhausted" in error_str.lower():
                    if attempt < max_retries - 1:
                        # Exponential backoff: 5s, 10s, 20s, 40s
                        wait_time = base_delay * (2 ** attempt) 
                        # Add jitter to prevent threads hitting API at exact same ms
                        jitter = random.uniform(0, 1)
                        total_wait = wait_time + jitter
                        time.sleep(total_wait)
                        continue
                    raise Exception("Rate limit exceeded. The API is busy, please wait a minute and try again.")
                
                # Handle Overloaded Model (503)
                if "503" in error_str or "overloaded" in error_str.lower():
                     if attempt < max_retries - 1:
                        time.sleep(5)
                        continue
                        
                raise
    
    def parse_qa_pairs(self, response_text: str, expected_count: int = None) -> List[Dict[str, str]]:
        if not response_text:
            return []
        
        qa_pairs = []
        response_text = response_text.replace('```', '')

        # Improved regex to handle various markdown headers
        question_splits = re.split(
            r'\*{0,2}QUESTION\s+(\d+)\s*:?\*{0,2}',
            response_text,
            flags=re.IGNORECASE
        )
        
        i = 1
        while i < len(question_splits) - 1:
            content = question_splits[i + 1]
            
            # Robust answer finding
            answer_match = re.search(
                r'\*{0,2}ANSWER\s+\d+\s*:?\*{0,2}\s*(.+?)(?=\*{0,2}QUESTION|\Z)',
                content,
                re.IGNORECASE | re.DOTALL
            )
            
            if answer_match:
                question_text = content[:answer_match.start()].strip()
                answer_text = answer_match.group(1).strip()
            else:
                # Fallback splitting
                parts = content.split('\n\n', 1)
                if len(parts) < 2:
                    i += 2
                    continue
                question_text = parts[0].strip()
                answer_text = parts[1].strip()
            
            # Cleanup formatting asterisks
            question_text = re.sub(r'\*+', '', question_text).strip()
            answer_text = re.sub(r'\*+', '', answer_text).strip()
            
            # Type detection
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
