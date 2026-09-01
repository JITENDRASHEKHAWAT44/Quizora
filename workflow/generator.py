import os
import json

from dotenv import load_dotenv
from llama_index.llms.groq import Groq

from schema import MCQTest

load_dotenv()

llm = Groq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
)


def generate_mcqs(context: str, number_of_questions: int) -> MCQTest:

    prompt = f"""
You are an expert academic MCQ generator.

Generate exactly {number_of_questions} MCQs using ONLY the study material below.

STUDY MATERIAL:
{context}

RULES:
- Generate exactly {number_of_questions} questions.
- Every question must have exactly 4 options.
- There must be exactly ONE correct answer.
- The correct answer must be supported by the study material.
- Do not use outside knowledge.
- Do not repeat questions.
- Make distractors plausible.
- Include a short explanation for every answer.

Return ONLY valid JSON.
Do not use markdown.
Do not add any text before or after the JSON.

Use exactly this structure:

{{
    "questions": [
        {{
            "question": "Question text",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
            ],
            "correct_answer": "Option A",
            "explanation": "Why this answer is correct."
        }}
    ]
}}
"""

    response = llm.complete(prompt)

    raw_output = response.text

    # Convert JSON text into Python dictionary
    data = json.loads(raw_output)

    # Validate with Pydantic
    result = MCQTest.model_validate(data)

    return result