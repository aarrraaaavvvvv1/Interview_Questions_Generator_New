"""Configuration and constants for the Interview Questions Generator"""

# Question generation settings
QUESTION_TYPES = {
    "generic": "General knowledge and conceptual questions",
    "practical": "Practical, hands-on, and business-based questions"
}

DIFFICULTY_LEVELS = ["Beginner", "Intermediate", "Advanced"]

# Gemini configuration - Model is auto-detected
GEMINI_MAX_TOKENS = 1200
GEMINI_TEMPERATURE = 0.6
GEMINI_MODEL = "gemini-pro"  # Model auto-detected, this is just a fallback

# FireCrawl configuration
FIRECRAWL_MAX_PAGES = 5
FIRECRAWL_TIMEOUT = 60

# Document generation settings
DOCUMENT_TITLE_FORMAT = "Interview Questions - {topic}"

# Validation settings
MIN_QUESTIONS = 1
MAX_QUESTIONS = 15
MIN_PRACTICAL_PERCENTAGE = 0
MAX_PRACTICAL_PERCENTAGE = 100

# Professional profile information
PROFESSIONAL_CONTEXT = {
    "experience_level": "Senior (15+ years)",
    "target_audience": "Working professionals",
    "study_material": True
}
