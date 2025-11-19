"""Configuration and constants for the Interview Questions Generator - OPTIMIZED FOR TOKEN LIMITS"""

# Question generation settings
QUESTION_TYPES = {
    "generic": "General knowledge and conceptual questions",
    "practical": "Practical, hands-on, and business-based questions"
}

DIFFICULTY_LEVELS = ["Beginner", "Intermediate", "Advanced"]

# Gemini configuration - OPTIMIZED
GEMINI_MAX_TOKENS = 4000  # Increased from 1200 to 4000 (ensures long responses complete)
GEMINI_TEMPERATURE = 0.4  # Lower for more consistent formatting
GEMINI_MODEL = "gemini-pro"  # Model auto-detected, this is just a fallback

# Question/Answer length constraints - OPTIMIZED
MIN_ANSWER_WORDS = 80  # Minimum words per answer (was too strict before)
MAX_ANSWER_WORDS = 150  # Maximum words per answer (keeps responses focused)
TARGET_ANSWER_WORDS = 100  # Target words per answer

# FireCrawl configuration
FIRECRAWL_MAX_PAGES = 5
FIRECRAWL_TIMEOUT = 60

# Document generation settings
DOCUMENT_TITLE_FORMAT = "Interview Questions - {topic}"

# Validation settings
MIN_QUESTIONS = 1
MAX_QUESTIONS = 15  # Reasonable upper limit
MIN_PRACTICAL_PERCENTAGE = 0
MAX_PRACTICAL_PERCENTAGE = 100

# Professional profile information
PROFESSIONAL_CONTEXT = {
    "experience_level": "Senior (15+ years)",
    "target_audience": "Working professionals",
    "study_material": True
}

# Token budget calculation helper
def estimate_tokens_needed(num_questions: int, target_words_per_answer: int = 100) -> int:
    """
    Estimate tokens needed for N questions
    
    Rough estimate:
    - Question: ~30 tokens
    - Answer: ~(words * 1.3) tokens (accounting for formatting)
    - Overhead: ~100 tokens
    
    Args:
        num_questions: Number of questions to generate
        target_words_per_answer: Target word count per answer
    
    Returns:
        Estimated token count
    """
    question_tokens = 30
    answer_tokens = int(target_words_per_answer * 1.3)
    overhead = 100
    
    total = (question_tokens + answer_tokens) * num_questions + overhead
    return total

# Safety margin multiplier
TOKEN_SAFETY_MARGIN = 1.3  # Request 30% more tokens than estimated
