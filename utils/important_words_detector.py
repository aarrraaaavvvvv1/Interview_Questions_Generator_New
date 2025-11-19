"""AI-based important words detector for highlighting key terms"""

import re
from typing import List

class ImportantWordsDetector:
    """Detect and extract important technical terms from answers"""
    
    # Fallback keyword list for common technical terms
    TECHNICAL_KEYWORDS = [
        # Machine Learning
        "machine learning", "deep learning", "neural network", "algorithm",
        "supervised learning", "unsupervised learning", "reinforcement learning",
        "training data", "test data", "validation", "overfitting", "underfitting",
        "accuracy", "precision", "recall", "F1 score", "confusion matrix",
        "gradient descent", "backpropagation", "optimization",
        
        # Data Science
        "data science", "data analysis", "statistics", "probability",
        "regression", "classification", "clustering", "dimensionality reduction",
        "feature engineering", "feature selection", "cross-validation",
        
        # Programming
        "python", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
        "API", "framework", "library", "deployment", "production",
        
        # Business
        "ROI", "KPI", "metrics", "business intelligence", "analytics",
        "stakeholder", "strategy", "implementation", "scalability"
    ]
    
    def __init__(self, use_ai: bool = False):
        """
        Initialize detector
        
        Args:
            use_ai: Whether to use AI-based detection (requires Gemini API)
        """
        self.use_ai = use_ai
    
    def detect_from_text(self, answer: str) -> List[str]:
        """
        Detect important words from answer text using keyword matching
        
        Args:
            answer: Answer text to analyze
        
        Returns:
            List of important words/phrases found
        """
        important = []
        answer_lower = answer.lower()
        
        # Find matching keywords (case-insensitive)
        for keyword in self.TECHNICAL_KEYWORDS:
            if keyword.lower() in answer_lower:
                # Find actual case in original text
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                matches = pattern.findall(answer)
                if matches:
                    important.append(matches[0])  # Keep original case
        
        # Remove duplicates while preserving order
        seen = set()
        unique_important = []
        for word in important:
            if word.lower() not in seen:
                seen.add(word.lower())
                unique_important.append(word)
        
        return unique_important
    
    def detect_batch(self, qa_pairs: List[dict], gemini_service=None) -> dict:
        """
        Detect important words for multiple Q&A pairs
        
        Args:
            qa_pairs: List of Q&A pair dictionaries
            gemini_service: Optional GeminiService for AI detection
        
        Returns:
            Dictionary mapping answer IDs to important words
        """
        results = {}
        
        for qa in qa_pairs:
            qa_id = qa.get('id')
            answer = qa.get('answer', '')
            
            important = self.detect_from_text(answer)
            results[qa_id] = important
        
        return results
