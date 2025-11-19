"""Prompt templates - OPTIMIZED FOR TOKEN EFFICIENCY"""

def get_question_generation_prompt(
    topic: str,
    curriculum_context: str,
    num_questions: int,
    practical_percentage: float,
    difficulty: str,
    web_content: str = ""
) -> str:
    """Generate optimized prompt that enforces exact count with minimal tokens"""
    
    num_practical = max(1, round((practical_percentage / 100) * num_questions))
    num_generic = num_questions - num_practical
    
    # Trim web content to avoid token bloat
    if web_content and len(web_content) > 800:
        web_content = web_content[:800] + "..."
    
    web_context = f"\n\nCurrent trends:\n{web_content}" if web_content else ""
    
    # OPTIMIZED: Shorter, more direct prompt
    prompt = f"""Generate EXACTLY {num_questions} interview Q&A pairs.

STRICT REQUIREMENTS:
- Total: {num_questions} questions (count as you generate)
- First {num_generic} questions: (GENERIC) - conceptual knowledge
- Last {num_practical} questions: (PRACTICAL) - real-world applications
- Each answer: 80-120 words, practical examples
- Stop immediately after question {num_questions}

TOPIC: {topic}
LEVEL: {difficulty}

CURRICULUM:
{curriculum_context}
{web_context}

FORMAT (use exactly):
**QUESTION 1:**
[question text] (GENERIC)

**ANSWER 1:**
[80-120 word answer with examples]

**QUESTION 2:**
[question text] (GENERIC)

**ANSWER 2:**
[80-120 word answer]

[Continue pattern...]

**QUESTION {num_generic + 1}:**
[question text] (PRACTICAL)

**ANSWER {num_generic + 1}:**
[80-120 word answer with business context]

[Continue until question {num_questions}]

**QUESTION {num_questions}:**
[final question] (PRACTICAL)

**ANSWER {num_questions}:**
[final answer]

CRITICAL:
- Generate ALL {num_questions} questions before stopping
- Mark type clearly: (GENERIC) or (PRACTICAL)
- Keep answers 80-120 words each
- No preamble, no apologies, just generate

Begin with **QUESTION 1:**"""
    
    return prompt
