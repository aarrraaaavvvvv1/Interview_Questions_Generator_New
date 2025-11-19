"""Important words detector"""

import re
from typing import List

class ImportantWordsDetector:
    TECHNICAL_KEYWORDS = [
        "machine learning", "deep learning", "neural network", "algorithm",
        "supervised learning", "unsupervised learning", "reinforcement learning",
        "training data", "test data", "validation", "overfitting", "underfitting",
        "accuracy", "precision", "recall", "F1 score", "confusion matrix",
        "gradient descent", "backpropagation", "optimization",
        "data science", "data analysis", "statistics", "probability",
        "regression", "classification", "clustering", "dimensionality reduction",
        "feature engineering", "feature selection", "cross-validation",
        "python", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
        "API", "framework", "library", "deployment", "production",
        "ROI", "KPI", "metrics", "business intelligence", "analytics",
        "stakeholder", "strategy", "implementation", "scalability"
    ]
    
    def __init__(self, use_ai: bool = False):
        self.use_ai = use_ai
    
    def detect_from_text(self, answer: str) -> List[str]:
        if not answer or not isinstance(answer, str):
            return []
        
        important = []
        answer_lower = answer.lower()
        
        for keyword in self.TECHNICAL_KEYWORDS:
            if keyword.lower() in answer_lower:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                matches = pattern.findall(answer)
                if matches:
                    important.append(matches[0])
        
        seen = set()
        unique = []
        for word in important:
            if word and word.lower() not in seen:
                seen.add(word.lower())
                unique.append(word)
        
        return unique
    
    def detect_batch(self, qa_pairs: List[dict], gemini_service=None) -> dict:
        results = {}
        for qa in qa_pairs:
            qa_id = qa.get('id')
            answer = qa.get('answer', '')
            important_words = self.detect_from_text(answer)
            results[qa_id] = important_words
        return results
