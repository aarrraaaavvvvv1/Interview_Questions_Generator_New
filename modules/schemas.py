from typing import List, Optional, Literal
from pydantic import BaseModel
QuestionType = Literal["mcq", "coding", "short", "theory"]
class MCQOption(BaseModel):
    option: str
    is_correct: bool = False
    explanation: Optional[str] = None
class Question(BaseModel):
    id: str
    type: QuestionType
    text: str
    difficulty: Literal["easy", "medium", "hard"]
    is_generic: bool = False
    options: Optional[List[MCQOption]] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    code: Optional[str] = None
class GenerationResult(BaseModel):
    topic: str
    context: List[str]
    difficulty: str
    question_types: List[QuestionType]
    total_questions: int
    generic_count: int
    practical_count: int
    generation_time: float
    questions: List[Question]
