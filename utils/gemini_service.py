"""Gemini API integration for question generation"""

import google.generativeai as genai
import re
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
            # List all available models
            available_models = genai.list_models()
            
            # Find models that support generateContent
            for model in available_models:
                if 'generateContent' in model.supported_generation_methods:
                    model_name = model.name.split('/')[-1]
                    print(f"Available model: {model_name}")
                    
                    # Skip experimental models and high-quota models
                    if 'exp' in model_name or '2.5' in model_name:
                        print(f"Skipping experimental model: {model_name}")
                        continue
                    
                    try:
                        self.model = genai.GenerativeModel(model_name)
                        print(f"✓ Using model: {model_name}")
                        return
                    except Exception as e:
                        print(f"✗ Cannot use {model_name}: {str(e)}")
                        continue
            
            # If we get here, just use the first available model
            if available_models:
                first_model = available_models[0].name.split('/')[-1]
                self.model = genai.GenerativeModel(first_model)
                print(f"✓ Using first available model: {first_model}")
                return
            
            raise Exception("No available models found. Check your API key.")
        
        except Exception as e:
            print(f"Error listing models: {str(e)}")
            # Fallback to known working models
            for model_name in ["gemini-pro", "gemini-1.5-flash-latest", "gemini-1.5-flash"]:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    print(f"✓ Using fallback model: {model_name}")
                    return
                except:
                    continue
            
            raise Exception("Could not find any working model. Please check your API key and quota.")
    
    def generate_questions(self, prompt: str) -> str:
        """Generate questions using Gemini API"""
        try:
            if self.model is None:
                raise Exception("Model not initialized")
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1500,
                    temperature=0.7,
                )
            )
            return response.text
        except Exception as e:
            error_msg = str(e)
            raise Exception(f"Error generating questions with Gemini: {error_msg}")
    
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
                
                if question_text and answer_text:
                    qa_pairs.append({
                        "id": i,
                        "question": question_text,
                        "answer": answer_text,
                        "type": question_type
                    })
        
        return qa_pairs
