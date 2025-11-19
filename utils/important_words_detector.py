"""Important words detector"""

import re
from typing import List

class ImportantWordsDetector:
    TECHNICAL_KEYWORDS = [
        "machine learning", "deep learning", "neural network", "algorithm",
        "supervised learning", "unsupervised learning", "training data",
        "accuracy", "precision", "recall", "regression", "classification"
    ]
    
    def __init__(self, use_ai: bool = False):
        self.use_ai = use_ai
    
    def detect_from_text(self, answer: str) -> List[str]:
        important = []
        answer_lower = answer.lower()
        
        for keyword in self.TECHNICAL_KEYWORDS:
            if keyword.lower() in answer_lower:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                matches = pattern.findall(answer)
                if matches:
                    important.append(matches)
        
        seen = set()
        unique = []
        for word in important:
            if word.lower() not in seen:
                seen.add(word.lower())
                unique.append(word)
        
        return unique
    
    def detect_batch(self, qa_pairs: List[dict], gemini_service=None) -> dict:
        results = {}
        for qa in qa_pairs:
            results[qa.get('id')] = self.detect_from_text(qa.get('answer', ''))
        return results
