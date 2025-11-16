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
        self.model_name = GEMINI_MODEL
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the model with fallback options"""
        models_to_try = [
            self.model_name,
            "gemini-pro",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]
        
        for model_name in models_to_try:
            try:
                self.model = genai.GenerativeModel(model_name)
                # Test if model works with a simple call
                self.model.generate_content("test")
                print(f"✓ Using model: {model_name}")
                return
            except Exception as e:
                print(f"✗ Model {model_name} not available: {str(e)}")
                continue
        
        # If no model works, try to list available models
        try:
            available_models = genai.list_models()
            available_model_names = [m.name.split('/')[-1] for m in available_models if 'generateContent' in m.supported_generation_methods]
            if available_model_names:
                self.model = genai.GenerativeModel(available_model_names[0])
                print(f"✓ Using available model: {available_model_names[0]}")
                return
        except:
            pass
        
        raise Exception("No suitable Gemini model found. Please check your API key and available models.")
    
    def generate_questions(self, prompt: str) -> str:
        """Generate questions using Gemini API"""
        try:
            if self.model is None:
                raise Exception("Model not initialized. Please check your API key.")
            
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
