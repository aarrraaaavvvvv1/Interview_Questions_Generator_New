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
        # Using gemini-1.5-flash as it has higher rate limits (15 RPM) than Pro (2 RPM in some tiers)
        self.model_name = "gemini-1.5-flash"
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate_questions(self, prompt: str) -> str:
        # Aggressive retry strategy: up to 5 attempts with exponential backoff
        max_retries = 5 
        base_delay = 5  # Start with 5 seconds
        
        for attempt in range(max_retries):
            try:
                # Reduced max tokens slightly to improve speed/reliability
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=3000, 
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
                
                # Check for Rate Limit (429) or Quota (ResourceExhausted) errors
                if "429" in error_str or "quota" in error_str.lower() or "resource_exhausted" in error_str.lower():
                    if attempt < max_retries - 1:
                        # Exponential backoff: 5s, 10s, 20s, 40s...
                        # Random jitter added to prevent synchronized retries
                        wait_time = (base_delay * (2 ** attempt)) + random.uniform(1, 3)
                        time.sleep(wait_time)
                        continue
                    
                    # If all retries fail, show this DISTINCT message
                    raise Exception("⚠️ Google API Busy: Rate limit reached. Please wait 60 seconds and try again.")
                
                # Handle Model Not Found (404) - Fallback to gemini-pro if flash isn't available
                if "404" in error_str or "not found" in error_str.lower():
                    if self.model_name == "gemini-1.5-flash":
                        self.model_name = "gemini-pro"
                        self.model = genai.GenerativeModel("gemini-pro")
                        time.sleep(1)
                        continue 

                # Handle Overloaded (503)
                if "503" in error_str or "overloaded" in error_str.lower():
                     if attempt < max_retries - 1:
                        time.sleep(10)
                        continue
                        
                raise Exception(f"Gemini API Error: {error_str}")
    
    def parse_qa_pairs(self, response_text: str, expected_count: int = None) -> List[Dict[str, str]]:
        if not response_text:
            return []
        
        qa_pairs = []
        response_text = response_text.replace('```', '')

        # Regex to find questions
        question_splits = re.split(
            r'\*{0,2}QUESTION\s+(\d+)\s*:?\*{0,2}',
            response_text,
            flags=re.IGNORECASE
        )
        
        i = 1
        while i < len(question_splits) - 1:
            content = question_splits[i + 1]
            
            # Regex to find answer within the chunk
            answer_match = re.search(
                r'\*{0,2}ANSWER\s+\d+\s*:?\*{0,2}\s*(.+?)(?=\*{0,2}QUESTION|\Z)',
                content,
                re.IGNORECASE | re.DOTALL
            )
            
            if answer_match:
                question_text = content[:answer_match.start()].strip()
                answer_text = answer_match.group(1).strip()
            else:
                # Fallback: split by double newline if specific tags aren't found
                parts = content.split('\n\n', 1)
                if len(parts) < 2:
                    i += 2
                    continue
                question_text = parts[0].strip()
                answer_text = parts[1].strip()
            
            # Cleanup asterisks/markdown
            question_text = re.sub(r'\*+', '', question_text).strip()
            answer_text = re.sub(r'\*+', '', answer_text).strip()
            
            # Determine type
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
