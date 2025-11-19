"""Gemini API integration - OPTIMIZED WITH DYNAMIC TOKEN ALLOCATION"""

import google.generativeai as genai
import re
from typing import List, Dict

class GeminiService:
    """Service for interacting with Google Gemini API with optimized token handling"""
    
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
    
    def calculate_optimal_tokens(self, num_questions: int) -> int:
        """
        Calculate optimal max_output_tokens based on number of questions
        
        Formula:
        - Question header: ~10 tokens
        - Question text: ~25 tokens
        - Answer header: ~10 tokens  
        - Answer (100 words): ~130 tokens
        - Formatting overhead: ~5 tokens per Q&A
        
        Total per Q&A: ~180 tokens
        Add 20% safety margin
        """
        tokens_per_qa = 180
        safety_margin = 1.2
        
        optimal = int(tokens_per_qa * num_questions * safety_margin)
        
        # Clamp between reasonable bounds
        min_tokens = 1000
        max_tokens = 8000  # Gemini's limit
        
        return max(min_tokens, min(optimal, max_tokens))
    
    def generate_questions(self, prompt: str, num_questions: int = 10) -> str:
        """
        Generate questions using Gemini API with dynamic token allocation
        
        Args:
            prompt: The generation prompt
            num_questions: Number of questions (for token calculation)
        
        Returns:
            Generated text response
        """
        try:
            if self.model is None:
                raise Exception("Model not initialized")
            
            # Calculate optimal tokens for this request
            optimal_tokens = self.calculate_optimal_tokens(num_questions)
            
            print(f"✓ Allocating {optimal_tokens} tokens for {num_questions} questions")
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=optimal_tokens,
                    temperature=0.4,  # Lower for consistency
                    top_p=0.9,
                    top_k=40
                )
            )
            return response.text
        except Exception as e:
            raise Exception(f"Error generating questions with Gemini: {str(e)}")
    
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
        response_text = response_text.replace('```', '')
        
        # Pattern to match QUESTION markers (flexible)
        question_splits = re.split(
            r'\*{0,2}QUESTION\s+(\d+)\s*:?\*{0,2}',
            response_text,
            flags=re.IGNORECASE
        )
        
        # Process pairs: question_splits = [preamble, num1, content1, num2, content2, ...]
        i = 1
        while i < len(question_splits):
            if i + 1 >= len(question_splits):
                break
            
            question_num = question_splits[i]
            content = question_splits[i + 1]
            
            # Split content by ANSWER marker
            answer_match = re.search(
                r'\*{0,2}ANSWER\s+\d+\s*:?\*{0,2}\s*(.+?)(?=\*{0,2}QUESTION|\Z)',
                content,
                re.IGNORECASE | re.DOTALL
            )
            
            if answer_match:
                question_text = content[:answer_match.start()].strip()
                answer_text = answer_match.group(1).strip()
            else:
                # Fallback: split by double newline
                parts = content.split('\n\n', 1)
                if len(parts) < 2:
                    i += 2
                    continue
                question_text = parts[0].strip()
                answer_text = parts[1].strip()
            
            # Clean markdown symbols
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
                # Word count validation for answers (should be 80-150 words)
                word_count = len(answer_text.split())
                
                # Truncate if too long
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
        
        # Validation
        if expected_count and len(qa_pairs) != expected_count:
            print(f"⚠️ Warning: Expected {expected_count} questions, got {len(qa_pairs)}")
        
        return qa_pairs
