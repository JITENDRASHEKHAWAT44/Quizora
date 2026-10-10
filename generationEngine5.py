import os
import json

from dotenv import load_dotenv
from groq_client import groq_complete

from schema import MCQTest


# ==========================================
# 1. Configuration
# ==========================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env")


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
You are an expert university professor creating a high-stakes academic exam.

Generate EXACTLY ONE high-quality Multiple Choice Question (MCQ) for EACH QUESTION ID below.

QUESTION REQUIREMENTS:
{instructions}

SOURCE MATERIAL FOR EACH QUESTION:
{context}

CRITICAL RULES & PEDAGOGICAL STANDARDS:

1. TEST REAL CONCEPTS & UNDERSTANDING:
   - Every question must test domain understanding: definitions, formulas, principles, mechanisms, algorithm steps, behavior under conditions, time/space complexity, comparisons, and trade-offs.
   - Example GOOD: "What is the primary condition required for binary search to function correctly?"
   - Example GOOD: "In worst-case analysis, which asymptotic notation provides a tight bound?"
   - Example GOOD: "Why is dynamic programming preferred over divide-and-conquer for the Fibonacci sequence?"

2. ABSOLUTELY FORBIDDEN QUESTION PATTERNS (DO NOT GENERATE):
   - FORBIDDEN: Asking about word frequency, text layout, or mentions (e.g., "Which term is repeatedly mentioned?", "What is the main topic of the passage?", "Which phrase appears most often?").
   - FORBIDDEN: Referring to the text directly (e.g., "According to the provided text", "In the passage", "In the source material", "For Question ID X", "As mentioned by the author").
   - The question must stand alone as an authentic exam question.

3. OPTIONS & DISTRACTORS:
   - Provide exactly FOUR distinct, plausible technical options (A, B, C, D).
   - Only ONE option must be correct.
   - The 3 distractors must be realistic domain concepts, NOT trivial mutations or jokes.
   - Do NOT make the correct answer identical across multiple questions.

4. DIFFICULTY CALIBRATION:
   - Easy: Direct definition, foundational concept, or basic identification.
   - Medium: Conceptual comparison, procedural steps, or behavior under specific inputs.
   - Hard: In-depth analysis, trade-offs, edge cases, or complexity derivations.

Return ONLY valid JSON matching this exact format:

{{
    "questions": [
        {{
            "question": "Clear, direct conceptual question here?",
            "options": [
                "Plausible Option A",
                "Plausible Option B",
                "Plausible Option C",
                "Plausible Option D"
            ],
            "correct_answer": "Plausible Option A",
            "explanation": "Clear explanation of why this answer is correct based on the subject matter."
        }}
    ]
}}
"""

    print(
        f"Sending batch of "
        f"{len(questions_to_generate)} "
        f"questions to Groq..."
    )

    response = groq_complete(prompt)
    raw_output = response.text.strip()

    # Robust JSON extraction
    import re
    cleaned = raw_output
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r'(\{[\s\S]*\})', raw_output)
        if match:
            data = json.loads(match.group(1))
        else:
            print("\nInvalid JSON returned by LLM:")
            print(raw_output)
            raise

    # Pydantic validation
    result = MCQTest.model_validate(data)
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