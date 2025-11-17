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
            available_models = genai.list_models()
            
            for model in available_models:
                if 'generateContent' in model.supported_generation_methods:
                    model_name = model.name.split('/')[-1]
                    
                    # Skip experimental models and high-quota models
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
            raise Exception(f"Error generating questions with Gemini: {str(e)}")
    
    def parse_qa_pairs(self, response_text: str) -> List[Dict[str, str]]:
        """Parse the generated response into Q&A pairs with correct type detection"""
        qa_pairs = []
        
        # Split by QUESTION pattern more carefully
        questions = re.split(r'\*\*QUESTION \d+:\*\*', response_text)
        
        for i, section in enumerate(questions[1:], 1):
            # Split question and answer
            parts = re.split(r'\*\*ANSWER \d+:\*\*', section, maxsplit=1)
            
            if len(parts) >= 2:
                question_text = parts[0].strip()
                answer_text = parts[1].strip()
                
                # Clean up the text
                question_text = question_text.strip()
                answer_text = answer_text.strip()
                
                # Extract question type - look for (GENERIC) or (PRACTICAL) at end of question
                question_type = "generic"  # default
                
                # Check for type markers in the question text
                if "(PRACTICAL)" in question_text:
                    question_type = "practical"
                    question_text = question_text.replace("(PRACTICAL)", "").strip()
                elif "(GENERIC)" in question_text:
                    question_type = "generic"
                    question_text = question_text.replace("(GENERIC)", "").strip()
                
                # Additional check: if type not found, check answer for hints
                if question_type == "generic" and ("(PRACTICAL)" in answer_text):
                    question_type = "practical"
                
                # Only add if both question and answer exist
                if question_text and answer_text:
                    # Limit answer to reasonable length (remove extra content)
                    answer_text = answer_text[:500]
                    
                    qa_pairs.append({
                        "id": i,
                        "question": question_text,
                        "answer": answer_text,
                        "type": question_type
                    })
        
        return qa_pairs
