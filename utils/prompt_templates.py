"""Prompt templates for question generation"""

def get_question_generation_prompt(
    topic: str,
    curriculum_context: str,
    num_questions: int,
    generic_percentage: float,
    practical_percentage: float,
    difficulty: str
) -> str:
    """Generate a structured prompt for question generation"""
    
    num_generic = int((generic_percentage / 100) * num_questions)
    num_practical = int((practical_percentage / 100) * num_questions)
    
    prompt = f"""You are an expert interviewer and curriculum designer preparing interview questions for professional study materials used in IIT/IIM collaborative courses.

TASK: Generate exactly {num_questions} interview questions based on the following specifications:

TOPIC: {topic}
CURRICULUM CONTEXT: {curriculum_context}
DIFFICULTY LEVEL: {difficulty}
TARGET AUDIENCE: Working professionals with 15+ years of experience

QUESTION DISTRIBUTION:
- Generic Questions (Conceptual): {num_generic} questions
- Practical/Business-Based Questions: {num_practical} questions

REQUIREMENTS:
1. Generic questions should test conceptual understanding and theoretical knowledge
2. Practical questions should focus on real-world scenarios, business applications, and hands-on problem-solving
3. Questions should be relevant to professional working environments
4. Include both definition-style and scenario-based questions
5. Ensure appropriate difficulty level ({difficulty})
6. Questions should be clear, concise, and unambiguous

RESPONSE FORMAT:
Generate exactly {num_questions} question-answer pairs in the following format:

**QUESTION 1:**
[Question text for generic/practical question type]

**ANSWER 1:**
[Comprehensive answer with key points, examples, and business context where applicable]

**QUESTION 2:**
[Next question]

**ANSWER 2:**
[Corresponding answer]

[Continue this pattern for all {num_questions} questions]

IMPORTANT:
- Start each question with **QUESTION N:** 
- Start each answer with **ANSWER N:**
- Ensure answers are comprehensive (200-300 words) with practical examples where relevant
- Mark whether each question is [GENERIC] or [PRACTICAL] at the beginning of the question line
- Questions should progressively increase in depth if difficulty is set to intermediate/advanced levels

Begin generating the questions:"""
    
    return prompt

def get_web_content_prompt(
    web_content: str,
    topic: str,
    curriculum_context: str,
    num_questions: int
) -> str:
    """Generate a prompt for question generation from web content"""
    
    prompt = f"""You are an expert interviewer analyzing current web content to create relevant interview questions for professional study materials.

TOPIC: {topic}
CURRICULUM CONTEXT: {curriculum_context}
NUMBER OF QUESTIONS: {num_questions}

WEB CONTENT TO ANALYZE:
{web_content}

TASK:
Based on the above web content, generate {num_questions} relevant interview questions and answers. Focus on:
1. Current trends and updates in the {topic} field
2. Practical applications mentioned in the content
3. Key concepts and their real-world implications
4. Critical thinking questions about the content

RESPONSE FORMAT:
**QUESTION 1:**
[Question based on web content]

**ANSWER 1:**
[Answer with references to the content and practical implications]

[Continue for all {num_questions} questions]

Ensure all questions are grounded in the provided web content and relevant to working professionals."""
    
    return prompt
