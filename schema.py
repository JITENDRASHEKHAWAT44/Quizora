from pydantic import BaseModel, Field
from typing import List


class MCQ(BaseModel):
    question: str
    options: List[str] = Field(min_length=4, max_length=4)
    correct_answer: str
    explanation: str


class MCQTest(BaseModel):
    questions: List[MCQ]