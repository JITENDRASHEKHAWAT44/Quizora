import os
import json

from dotenv import load_dotenv
from llama_index.llms.groq import Groq

from schema import MCQTest


# ==========================================
# 1. Configuration
# ==========================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env")


# ==========================================
# 2. Configure Groq
# ==========================================

llm = Groq(
    model="openai/gpt-oss-120b",
    api_key=GROQ_API_KEY,
)


# ==========================================
# 3. Generate a BATCH of MCQs
# ==========================================

def generate_question_batch(
    questions_to_generate: list,
):
    """
    Generate multiple MCQs in a single LLM request.
    """

    question_instructions = []
    context_parts = []

    for item in questions_to_generate:

        question_id = item["question_id"]
        topic = item["topic"]
        difficulty = item["difficulty"]
        sources = item["sources"]

        # ------------------------------------------
        # Question requirements
        # ------------------------------------------

        question_instructions.append(
            f"""
QUESTION ID: {question_id}
TOPIC: {topic}
REQUIRED DIFFICULTY: {difficulty}
"""
        )

        # ------------------------------------------
        # Limit source material
        # ------------------------------------------

        MAX_SOURCE_CHARS = 5000

        source_parts = []
        current_length = 0

        for source in sources:

            text = source["text"].strip()

            remaining = (
                MAX_SOURCE_CHARS -
                current_length
            )

            if remaining <= 0:
                break

            piece = text[:remaining]

            source_parts.append(piece)

            current_length += len(piece)

        source_text = "\n\n".join(
            source_parts
        )

        context_parts.append(
            f"""
QUESTION ID: {question_id}

SOURCE MATERIAL:
-------------------------
{source_text}
-------------------------
"""
        )

    # ==========================================
    # Build prompt
    # ==========================================

    instructions = "\n".join(
        question_instructions
    )

    context = "\n".join(
        context_parts
    )

    prompt = f"""
You are an expert academic assessment generator.

Generate EXACTLY ONE MCQ for EACH QUESTION ID below.

QUESTION REQUIREMENTS:
{instructions}

SOURCE MATERIAL FOR EACH QUESTION:
{context}

STRICT RULES:

1. Use ONLY the source material provided.
2. Do NOT use outside knowledge.
3. Generate exactly ONE question for EACH QUESTION ID.
4. Generate exactly FOUR options for every question.
5. Only ONE option must be correct.
6. The correct answer MUST be directly supported
   by the corresponding source material.
7. Distractors must be plausible.
8. Do not create ambiguous questions.
9. Do not mention the source material in the question.
10. Include a concise explanation.
11. Match the requested difficulty.
12. Do not create a question whose answer cannot
    be determined from the source material.
13. Do not omit any requested question.
14. Do not create additional questions.

Return ONLY valid JSON.

Use exactly this format:

{{
    "questions": [
        {{
            "question": "...",
            "options": [
                "...",
                "...",
                "...",
                "..."
            ],
            "correct_answer": "...",
            "explanation": "..."
        }}
    ]
}}
"""

    print(
        f"Sending batch of "
        f"{len(questions_to_generate)} "
        f"questions to Groq..."
    )

    # ==========================================
    # Call Groq
    # ==========================================

    response = llm.complete(prompt)

    raw_output = response.text.strip()

    # ==========================================
    # Remove markdown fences
    # ==========================================

    if raw_output.startswith("```"):

        raw_output = raw_output.replace(
            "```json",
            "",
        )

        raw_output = raw_output.replace(
            "```",
            "",
        )

        raw_output = raw_output.strip()

    # ==========================================
    # Parse JSON
    # ==========================================

    try:

        data = json.loads(
            raw_output
        )

    except json.JSONDecodeError:

        print(
            "\nInvalid JSON returned by LLM:"
        )

        print(raw_output)

        raise

    # ==========================================
    # Pydantic validation
    # ==========================================

    result = MCQTest.model_validate(
        data
    )

    return result.questions


# ==========================================
# 4. Generate complete quiz
# ==========================================

def generate_quiz(
    retrieved_context,
    batch_size=2,
):

    questions = retrieved_context[
        "questions"
    ]

    generated_questions = []

    # ==========================================
    # Split questions into batches
    # ==========================================

    batches = [
        questions[i:i + batch_size]
        for i in range(
            0,
            len(questions),
            batch_size,
        )
    ]

    print(
        f"\nTotal questions: "
        f"{len(questions)}"
    )

    print(
        f"Batch size: {batch_size}"
    )

    print(
        f"Total LLM batches: "
        f"{len(batches)}"
    )

    # ==========================================
    # Generate batches
    # ==========================================

    for batch_number, batch in enumerate(
        batches,
        start=1,
    ):

        print(
            f"\nGenerating batch "
            f"{batch_number}/{len(batches)}"
        )

        generated_batch = generate_question_batch(
            batch
        )

        # ==========================================
        # Match generated MCQs to requested IDs
        # ==========================================

        if len(generated_batch) != len(batch):

            raise ValueError(
                f"Expected {len(batch)} questions "
                f"but LLM generated "
                f"{len(generated_batch)}."
            )

        generated_by_id = {
            item["question_id"]: question
            for item, question in zip(
                batch,
                generated_batch,
            )
        }

        # ==========================================
        # Process each generated question
        # ==========================================

        for item in batch:

            question_id = item[
                "question_id"
            ]

            if question_id not in generated_by_id:

                raise ValueError(
                    f"LLM failed to generate "
                    f"question {question_id}"
                )

            mcq = generated_by_id[
                question_id
            ]

            sources = item[
                "sources"
            ]

            generated_questions.append({

                "question_id": question_id,

                "topic": item[
                    "topic"
                ],

                "difficulty": item[
                    "difficulty"
                ],

                "question": mcq.question,

                "options": mcq.options,

                "correct_answer": (
                    mcq.correct_answer
                ),

                "explanation": (
                    mcq.explanation
                ),

                "sources": [
                    {
                        "page": source[
                            "metadata"
                        ].get(
                            "page_label"
                        ),

                        "score": source[
                            "score"
                        ],
                    }

                    for source in sources
                ],
            })

    # ==========================================
    # Sort questions
    # ==========================================

    generated_questions.sort(
        key=lambda x: x[
            "question_id"
        ]
    )

    # ==========================================
    # Final result
    # ==========================================

    return {

        "total_questions": len(
            generated_questions
        ),

        "questions": generated_questions,
    }


# ==========================================
# 5. Main
# ==========================================

if __name__ == "__main__":

    print(
        "Quizora Generation Engine"
    )

    print(
        "-------------------------"
    )

    # ==========================================
    # Load retrieval output
    # ==========================================

    if not os.path.exists(
        "retrieved_context.json"
    ):

        raise FileNotFoundError(
            "retrieved_context.json not found. "
            "Run retrieval_engine.py first."
        )

    with open(
        "retrieved_context.json",
        "r",
        encoding="utf-8",
    ) as file:

        retrieved_context = json.load(
            file
        )

    # ==========================================
    # Generate quiz
    # ==========================================

    quiz = generate_quiz(
        retrieved_context,
        batch_size=2,
    )

    # ==========================================
    # Save generated quiz
    # ==========================================

    with open(
        "generated_quiz.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            quiz,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print(
        "\nQuiz generation completed."
    )

    print(
        f"Generated "
        f"{quiz['total_questions']} questions."
    )

    print(
        "Saved to generated_quiz.json"
    )