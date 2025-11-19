"""Gemini API integration for question generation"""

import google.generativeai as genai
import re
import time
from typing import List, Dict

class GeminiService:
    """Service for interacting with Google Gemini API"""
    
    def __init__(self, api_key: str):
        """Initialize Gemini API with API key"""
        genai.configure(api_key=api_key)
        self.model = None
        self._find_available_model()
    
    def _find_available_model(self):
        """Find the first available model that supports generateContent"""
        try:
            available_models = genai.list_models()
            
            for model in available_models:
                if 'generateContent' in model.supported_generation_methods:
                    model_name = model.name.split('/')[-1]
                    
                    if 'exp' in model_name or '2.5' in model_name:
                        continue
                    
                    try:
                        self.model = genai.GenerativeModel(model_name)
                        print(f"✓ Using model: {model_name}")
                        return
                    except:
                        continue
            
            if available_models:
                first_model = available_models[0].name.split('/')[-1]
                self.model = genai.GenerativeModel(first_model)
                print(f"✓ Using first available model: {first_model}")
                return
            
            raise Exception("No available models found.")
        
        except Exception as e:
            for model_name in ["gemini-pro", "gemini-1.5-flash-latest", "gemini-1.5-flash"]:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    print(f"✓ Using fallback model: {model_name}")
                    return
                except:
                    continue
            
            raise Exception("Could not find any working model.")
    
    def generate_questions(self, prompt: str, num_questions: int = 10) -> str:
        """
        Generate questions using Gemini API with retry logic
        
        Args:
            prompt: The generation prompt
            num_questions: Number of questions
        
        Returns:
            Generated text response
        """
        if self.model is None:
            raise Exception("Model not initialized")
        
        max_retries = 5
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=2000,
                        temperature=0.5,
                    )
                )
                return response.text
                
            except Exception as e:
                error_message = str(e)
                
                if "429" in error_message or "Resource exhausted" in error_message or "quota" in error_message.lower():
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"⚠️ Rate limit hit. Waiting {delay} seconds...")
                        time.sleep(delay)
                        continue
                    else:
                        raise Exception(f"Rate limit exceeded. Please wait a few minutes and try again.")
                else:
                    raise Exception(f"Error generating questions with Gemini: {error_message}")
        
        raise Exception("Failed to generate questions after retries")
    
    def parse_qa_pairs(self, response_text: str, expected_count: int = None) -> List[Dict[str, str]]:
        """Parse response into Q&A pairs"""
        qa_pairs = []
        
        response_text = response_text.replace
