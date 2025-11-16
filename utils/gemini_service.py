"""Gemini API integration for question generation"""

import google.generativeai as genai
from config import GEMINI_MODEL, GEMINI_MAX_TOKENS, GEMINI_TEMPERATURE
import re
from typing import List, Dict

class GeminiService:
    """Service for interacting with Google Gemini API"""
    
    def __init__(self, api_key: str):
        """Initialize Gemini API with API key"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
    
    def generate_questions(self, prompt: str) -> str:
        """Generate questions using Gemini API"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=GEMINI_MAX_TOKENS,
                    temperature=GEMINI_TEMPERATURE,
                )
            )
            return response.text
        except Exception as e:
            raise Exception(f"Error generating questions with Gemini: {str(e)}")
    
    def parse_qa_pairs(self, response_text: str) -> List[Dict[str, str]]:
        """Parse the generated response into Q&A pairs"""
        qa_pairs = []
        
        # Split by QUESTION pattern
        questions = re.split(r'\*\*QUESTION \d+:\*\*', response_text)
        
        for i, section in enumerate(questions[1:], 1):
            # Split question and answer
            parts = re.split(r'\*\*ANSWER \d+:\*\*', section)
            
            if len(parts) >= 2:
                question_text = parts[0].strip()
                answer_text = parts[1].strip()
                
                # Extract question type if present
                question_type = "generic"
                if "[PRACTICAL]" in question_text:
                    question_type = "practical"
                    question_text = question_text.replace("[PRACTICAL]", "").strip()
                elif "[GENERIC]" in question_text:
                    question_type = "generic"
                    question_text = question_text.replace("[GENERIC]", "").strip()
                
                qa_pairs.append({
                    "id": i,
                    "question": question_text,
                    "answer": answer_text,
                    "type": question_type
                })
        
        return qa_pairs
