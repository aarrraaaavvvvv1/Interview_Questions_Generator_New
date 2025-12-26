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
        # Default to gemini-1.5-flash which is faster and has better rate limits
        # We skip list_models() here to save 1 API call per request
        self.model_name = "gemini-1.5-flash"
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate_questions(self, prompt: str) -> str:
        # Retry configuration
        max_retries = 4 
        base_delay = 4  # Start with 4 seconds wait
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=3000, # Reduced to 3000 to be safe on limits
                        temperature=0.5,
                    )
                )
                
                if response and hasattr(response, 'text') and response.text:
                    return response.text
                
                # If response is empty but no error, wait briefly and retry
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                    
                raise Exception("Empty response received from Gemini API.")
                
            except Exception as e:
                error_str = str(e)
                
                # Handle Rate Limits (429) and Quota (ResourceExhausted)
                if "429" in error_str or "quota" in error_str.lower() or "resource_exhausted" in error_str.lower():
                    if attempt < max_retries - 1:
                        # Exponential backoff: 4s, 8s, 16s...
                        wait_time = (base_delay * (2 ** attempt)) + random.uniform(0.5, 1.5)
                        time.sleep(wait_time)
                        continue
                    raise Exception("Rate limit exceeded (HTTP 429). Please wait 1-2 minutes before trying again.")
                
                # Handle Model Not Found (404) - Fallback to gemini-pro if flash is unavailable
                if "404" in error_str or "not found" in error_str.lower():
                    if self.model_name == "gemini-1.5-flash":
                        self.model_name = "gemini-pro"
                        self.model = genai.GenerativeModel("gemini-pro")
                        continue 

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
