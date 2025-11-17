"""Prompt templates for question generation"""

def get_question_generation_prompt(
    topic: str,
    curriculum_context: str,
    num_questions: int,
    practical_percentage: float,
    difficulty: str,
    web_content: str = ""
) -> str:
    """Generate a structured prompt for question generation"""
    
    num_practical = max(1, round((practical_percentage / 100) * num_questions))
    num_generic = num_questions - num_practical
    
    # Ensure we have the exact count
    assert num_practical + num_generic == num_questions, "Math error in distribution"
    
    web_context = ""
    if web_content:
        web_context = f"""

RECENT WEB RESEARCH:
{web_content}"""
    
    prompt = f"""You are an expert curriculum designer creating interview questions for professional study materials.

CRITICAL REQUIREMENT: Generate EXACTLY {num_questions} questions with EXACT distribution:
- {num_generic} GENERIC/CONCEPTUAL questions
- {num_practical} PRACTICAL/BUSINESS-BASED questions
- TOTAL: {num_questions} questions

TOPIC: {topic}

CURRICULUM CONTENT:
{curriculum_context}
{web_context}

DIFFICULTY: {difficulty}

INSTRUCTIONS:
1. Generate EXACTLY {num_questions} question-answer pairs
2. Mark each question type CLEARLY: (GENERIC) or (PRACTICAL)
3. First {num_generic} questions should be marked (GENERIC)
4. Last {num_practical} questions should be marked (PRACTICAL)
5. Each answer: 100-200 words, practical examples

RESPONSE FORMAT:
Use this EXACT format for ALL {num_questions} questions:

**QUESTION 1:**
[Question text] (GENERIC)

**ANSWER 1:**
[Comprehensive answer 100-200 words]

**QUESTION 2:**
[Question text] (GENERIC)

**ANSWER 2:**
[Comprehensive answer 100-200 words]

[Continue pattern...]

**QUESTION {num_generic + 1}:**
[Question text] (PRACTICAL)

**ANSWER {num_generic + 1}:**
[Comprehensive answer 100-200 words]

[Continue with PRACTICAL until question {num_questions}]

CRITICAL RULES:
- Generate EXACTLY {num_questions} questions (no more, no less)
- EVERY question must have (GENERIC) or (PRACTICAL) marker
- First {num_generic} are GENERIC, rest are PRACTICAL
- No other text before or after questions
- Start immediately with **QUESTION 1:**
- End after **ANSWER {num_questions}:**

Now generate all {num_questions} questions:"""
    
    return prompt
