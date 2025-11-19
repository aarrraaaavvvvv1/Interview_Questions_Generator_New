"""Gemini API integration for question generation - WITH RATE LIMIT HANDLING"""

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
        Generate questions using Gemini API with exponential backoff retry
        
        Args:
            prompt: The generation prompt
            num_questions: Number of questions (for context)
        
        Returns:
            Generated text response
        """
        if self.model is None:
            raise Exception("Model not initialized")
        
        max_retries = 5
        base_delay = 2  # Start with 2 seconds
        
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
                
                # Check if it's a rate limit error (429)
                if "429" in error_message or "Resource exhausted" in error_message or "quota" in error_message.lower():
                    if attempt < max_retries - 1:
                        # Exponential backoff: 2s, 4s, 8s, 16s, 32s
                        delay = base_delay * (2 ** attempt)
                        print(f"⚠️ Rate limit hit. Waiting {delay} seconds before retry {attempt + 1}/{max_retries}...")
                        time.sleep(delay)
                        continue
                    else:
                        raise Exception(f"Rate limit exceeded after {max_retries} attempts. Please wait a few minutes and try again.")
                else:
                    # Different error, raise immediately
                    raise Exception(f"Error generating questions with Gemini: {error_message}")
        
        raise Exception("Failed to generate questions after multiple retries")
    
    def parse_qa_pairs(self, response_text: str, expected_count: int = None) -> List[Dict[str, str]]:
        """
        Parse the generated response into Q&A pairs with strict validation
        
        Args:
            response_text: The raw response from Gemini
            expected_count: Expected number of questions (for validation)
        
        Returns:
            List of Q&A pairs with type classification
        """
        qa_pairs = []
        
        # Remove markdown code blocks if present
        response_text = response_text.replace('```
        
        # Pattern to match QUESTION markers
        question_splits = re.split(
            r'\*{0,2}QUESTION\s+(\d+)\s*:?\*{0,2}',
            response_text,
            flags=re.IGNORECASE
        )
        
        # Process pairs
        i = 1
        while i < len(question_splits):
            if i + 1 >= len(question_splits):
                break
            
            question_num = question_splits[i]
            content = question_splits[i + 1]
            
            # Split by ANSWER marker
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
            
            # Clean markdown
            question_text = re.sub(r'\*+', '', question_text).strip()
            answer_text = re.sub(r'\*+', '', answer_text).strip()
            
            # Extract type
            question_type = "generic"
            if "(PRACTICAL)" in question_text.upper():
                question_type = "practical"
                question_text = re.sub(r'\(PRACTICAL\)', '', question_text, flags=re.IGNORECASE).strip()
            elif "(GENERIC)" in question_text.upper():
                question_type = "generic"
                question_text = re.sub(r'\(GENERIC\)', '', question_text, flags=re.IGNORECASE).strip()
            
            # Validate quality
            if question_text and answer_text and len(question_text) > 10 and len(answer_text) > 30:
                word_count = len(answer_text.split())
                
                if word_count > 180:
                    words = answer_text.split()[:150]
                    answer_text = ' '.join(words) + '...'
                
                qa_pairs.append({
                    "id": len(qa_pairs) + 1,
                    "question": question_text,
                    "answer": answer_text,
                    "type": question_type
                })
            
            i += 2
        
        if expected_count and len(qa_pairs) != expected_count:
            print(f"⚠️ Warning: Expected {expected_count} questions, got {len(qa_pairs)}")
        
        return qa_pairs
