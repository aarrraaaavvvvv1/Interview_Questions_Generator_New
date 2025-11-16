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
    
    web_context = ""
    if web_content:
        web_context = f"""

ADDITIONAL CONTEXT FROM WEB RESEARCH:
{web_content}

Consider this web research to make questions more current and relevant."""
    
    prompt = f"""You are an expert curriculum designer and interviewer creating interview questions for professional study materials.

TASK: Generate EXACTLY {num_questions} interview question-answer pairs with the following distribution:
- Generic/Conceptual Questions: {num_generic} questions
- Practical/Business-Based Questions: {num_practical} questions

TOPIC: {topic}

CURRICULUM CONTENT:
{curriculum_context}
{web_context}

DIFFICULTY LEVEL: {difficulty}

TARGET AUDIENCE: Working professionals with 15+ years of experience

QUESTION REQUIREMENTS:
1. Generic questions test conceptual understanding, definitions, and theoretical knowledge
2. Practical questions focus on real-world scenarios, decision-making, and business applications
3. All questions must be directly relevant to the provided curriculum content
4. Questions should reflect how these concepts apply in professional environments
5. Mix of definition-style, scenario-based, and application questions
6. Clear, concise, unambiguous phrasing

RESPONSE FORMAT:
Generate EXACTLY {num_questions} questions in this precise format:

**QUESTION 1:**
[Question text - mark type at end: (GENERIC) or (PRACTICAL)]

**ANSWER 1:**
[Comprehensive answer with key points, examples, and business context - 150-250 words]

**QUESTION 2:**
[Next question - mark type: (GENERIC) or (PRACTICAL)]

**ANSWER 2:**
[Corresponding answer]

[Continue exactly {num_questions} times]

CRITICAL REQUIREMENTS:
- Generate EXACTLY {num_generic} generic questions and {num_practical} practical questions
- Each question MUST be marked with (GENERIC) or (PRACTICAL) at the end
- Each answer should be 150-250 words with practical examples
- Start each question with **QUESTION N:**
- Start each answer with **ANSWER N:**
- No markdown symbols except ** for bold
- Questions should progress from foundational to applied

Begin:"""
    
    return prompt
