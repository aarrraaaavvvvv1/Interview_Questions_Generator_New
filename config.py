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

# FireCrawl configuration
FIRECRAWL_MAX_PAGES = 5
FIRECRAWL_TIMEOUT = 60

# Document generation settings
DOCUMENT_TITLE_FORMAT = "Interview Questions - {topic}"
DOCUMENT_FOOTER = "Generated using AI-Powered Interview Questions Generator | For Educational Purposes"

# Validation settings
MIN_QUESTIONS = 1
MAX_QUESTIONS = 15  # Reduced to save quota
MIN_PERCENTAGE = 0
MAX_PERCENTAGE = 100

# Professional profile information
PROFESSIONAL_CONTEXT = {
    "experience_level": "Senior (15+ years)",
    "target_audience": "Working professionals from IIT/IIM collaborated courses",
    "study_material": True
}
