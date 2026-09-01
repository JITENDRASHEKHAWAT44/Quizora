import os
import json
from pathlib import Path

from dotenv import load_dotenv
from llama_index.llms.groq import Groq

from schema import MCQTest


# ==========================================
# 1. Configuration
# ==========================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is missing from .env"
    )


INPUT_FILE = "generated_quiz.json"
CONTEXT_FILE = "retrieved_context.json"

OUTPUT_FILE = "final_quiz.json"
REJECTED_FILE = "semantic_rejected.json"

MAX_RETRIES = 3

# Keep validation requests small
MAX_SOURCE_CHARS = 5000

# Number of questions checked per Groq request
VALIDATION_BATCH_SIZE = 2


# ==========================================
# 2. Groq
# ==========================================

llm = Groq(
    model="openai/gpt-oss-120b",
    api_key=GROQ_API_KEY,
)


# ==========================================
# 3. Normalize text
# ==========================================

def normalize(text):

    return " ".join(
        text.lower()
        .strip()
        .split()
    )


# ==========================================
# 4. Limit source context
# ==========================================

def build_context(sources):

    source_parts = []
    current_length = 0

    for source in sources:

        text = source["text"].strip()

        remaining = (
            MAX_SOURCE_CHARS
            - current_length
        )

        if remaining <= 0:
            break

        piece = text[:remaining]

        source_parts.append(piece)

        current_length += len(piece)

    return "\n\n".join(
        source_parts
    )


# ==========================================
# 5. Check ONE question
# ==========================================

def check_grounding(
    question,
    sources,
):
    """
    Check one question.

    This function is kept for compatibility
    with the existing pipeline.
    """

    context = build_context(
        sources
    )

    prompt = f"""
You are a strict academic content verifier.

Determine whether this MCQ is fully supported
by the provided source material.

SOURCE MATERIAL:
-------------------------
{context}
-------------------------

QUESTION:
{question["question"]}

OPTIONS:
{json.dumps(
    question["options"],
    ensure_ascii=False
)}

CORRECT ANSWER:
{question["correct_answer"]}

EXPLANATION:
{question["explanation"]}

Evaluate using these rules:

1. The correct answer must be supported by the source.
2. The explanation must be supported by the source.
3. The question must be answerable using the source.
4. Do not use outside knowledge.
5. Do not assume facts not present in the source.
6. The question must not contradict the source.

Return ONLY valid JSON:

{{
    "supported": true,
    "reason": "Short explanation"
}}

If the source does not sufficiently support
the question, return supported=false.
"""

    response = llm.complete(
        prompt
    )

    raw = response.text.strip()

    if raw.startswith("```"):

        raw = raw.replace(
            "```json",
            ""
        )

        raw = raw.replace(
            "```",
            ""
        )

        raw = raw.strip()

    try:

        result = json.loads(raw)

    except json.JSONDecodeError:

        return {
            "supported": False,
            "reason": (
                "Verifier returned invalid JSON."
            ),
        }

    return result


# ==========================================
# 6. BATCH semantic validation
# ==========================================

def check_grounding_batch(
    questions_to_check
):
    """
    Validate multiple questions in ONE
    Groq request.
    """

    question_blocks = []

    for item in questions_to_check:

        question_id = item[
            "question_id"
        ]

        sources = item[
            "sources"
        ]

        context = build_context(
            sources
        )

        question_blocks.append(
            f"""
QUESTION ID: {question_id}

SOURCE MATERIAL:
-------------------------
{context}
-------------------------

QUESTION:
{item["question"]}

OPTIONS:
{json.dumps(
    item["options"],
    ensure_ascii=False
)}

CORRECT ANSWER:
{item["correct_answer"]}

EXPLANATION:
{item["explanation"]}
"""
        )

    questions_text = "\n".join(
        question_blocks
    )

    prompt = f"""
You are a strict academic content verifier.

Validate EACH QUESTION ID independently.

{questions_text}

For every question evaluate:

1. The correct answer must be supported by the source.
2. The explanation must be supported by the source.
3. The question must be answerable using the source.
4. Do not use outside knowledge.
5. Do not assume facts not present in the source.
6. The question must not contradict the source.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "results": [
        {{
            "question_id": 1,
            "supported": true,
            "reason": "Short explanation"
        }}
    ]
}}

IMPORTANT:

- Return exactly one result for every QUESTION ID.
- Do not omit any QUESTION ID.
- Do not create additional QUESTION IDs.
- Keep QUESTION IDs exactly as provided.
"""

    print(
        f"Sending validation batch of "
        f"{len(questions_to_check)} "
        f"questions to Groq..."
    )

    response = llm.complete(
        prompt
    )

    raw = response.text.strip()

    if raw.startswith("```"):

        raw = raw.replace(
            "```json",
            ""
        )

        raw = raw.replace(
            "```",
            ""
        )

        raw = raw.strip()

    try:

        data = json.loads(raw)

    except json.JSONDecodeError:

        print(
            "\nInvalid validation JSON:"
        )

        print(raw)

        # Fail safely
        return {
            item["question_id"]: {
                "supported": False,
                "reason": (
                    "Validator returned invalid JSON."
                ),
            }
            for item in questions_to_check
        }

    results = data.get(
        "results",
        []
    )

    validation_lookup = {}

    for result in results:

        question_id = result.get(
            "question_id"
        )

        validation_lookup[
            question_id
        ] = {
            "supported": result.get(
                "supported",
                False
            ),

            "reason": result.get(
                "reason",
                ""
            ),
        }

    # Make sure every requested question
    # receives a validation result.

    for item in questions_to_check:

        question_id = item[
            "question_id"
        ]

        if question_id not in validation_lookup:

            validation_lookup[
                question_id
            ] = {
                "supported": False,
                "reason": (
                    "No validation result "
                    "returned by LLM."
                ),
            }

    return validation_lookup


# ==========================================
# 7. Regenerate ONE question
# ==========================================

def regenerate_question(
    topic,
    difficulty,
    sources,
):
    """
    Generate a replacement question using
    ONLY the retrieved source material.
    """

    context = build_context(
        sources
    )

    prompt = f"""
You are an expert academic MCQ generator.

Generate EXACTLY ONE high-quality MCQ.

TOPIC:
{topic}

DIFFICULTY:
{difficulty}

SOURCE MATERIAL:
-------------------------
{context}
-------------------------

STRICT REQUIREMENTS:

1. Use ONLY the source material.
2. Do not use outside knowledge.
3. Generate exactly four options.
4. Only one option can be correct.
5. The correct answer must be explicitly
   supported by the source.
6. The explanation must be supported by
   the source.
7. Avoid ambiguity.
8. Avoid trivial wording.
9. Make the question appropriate for the
   requested difficulty.
10. Do not mention that a source was provided.

Return ONLY valid JSON:

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

    response = llm.complete(
        prompt
    )

    raw = response.text.strip()

    if raw.startswith("```"):

        raw = raw.replace(
            "```json",
            ""
        )

        raw = raw.replace(
            "```",
            ""
        )

        raw = raw.strip()

    data = json.loads(raw)

    result = MCQTest.model_validate(
        data
    )

    if len(result.questions) != 1:

        raise ValueError(
            "Regenerator did not return "
            "exactly one MCQ."
        )

    return result.questions[0]


# ==========================================
# 8. Process ONE question
# ==========================================

def process_question(
    question,
    sources,
):
    """
    Validate one question and regenerate
    if necessary.

    Kept for compatibility with the
    existing pipeline.
    """

    topic = question[
        "topic"
    ]

    difficulty = question[
        "difficulty"
    ]

    current_question = question

    attempts = 0

    while attempts <= MAX_RETRIES:

        print(
            f"Checking Q"
            f"{current_question['question_id']} "
            f"(attempt {attempts + 1})..."
        )

        result = check_grounding(
            current_question,
            sources,
        )

        if result.get(
            "supported"
        ) is True:

            print(
                f"Q"
                f"{current_question['question_id']} "
                f"PASSED grounding."
            )

            current_question[
                "grounding"
            ] = {
                "supported": True,
                "reason": result.get(
                    "reason",
                    ""
                ),
            }

            return (
                current_question,
                None
            )

        print(
            f"Q"
            f"{current_question['question_id']} "
            f"FAILED grounding."
        )

        print(
            f"Reason: "
            f"{result.get('reason', '')}"
        )

        attempts += 1

        if attempts > MAX_RETRIES:

            return (
                None,
                {
                    "question": current_question,
                    "reason": result.get(
                        "reason",
                        "Grounding failed."
                    ),
                    "attempts": attempts,
                }
            )

        print(
            f"Regenerating Q"
            f"{current_question['question_id']}..."
        )

        new_mcq = regenerate_question(
            topic=topic,
            difficulty=difficulty,
            sources=sources,
        )

        current_question = {

            "question_id":
                current_question[
                    "question_id"
                ],

            "topic": topic,

            "difficulty": difficulty,

            "question":
                new_mcq.question,

            "options":
                new_mcq.options,

            "correct_answer":
                new_mcq.correct_answer,

            "explanation":
                new_mcq.explanation,

            "sources":
                current_question[
                    "sources"
                ],
        }

    return (
        None,
        {
            "question": current_question,
            "reason":
                "Maximum retries exceeded.",
            "attempts": attempts,
        }
    )


# ==========================================
# 9. Main batch validation pipeline
# ==========================================

def semantic_validate_quiz(
    quiz,
    retrieval,
    batch_size=VALIDATION_BATCH_SIZE,
):
    """
    Batch validate the complete quiz.

    Only failed questions are regenerated.
    """

    # ------------------------------------------
    # Create source lookup
    # ------------------------------------------

    context_lookup = {}

    for item in retrieval[
        "questions"
    ]:

        context_lookup[
            item["question_id"]
        ] = item["sources"]

    final_questions = []

    rejected_questions = []

    questions = quiz[
        "questions"
    ]

    # ------------------------------------------
    # Split into validation batches
    # ------------------------------------------

    batches = [
        questions[i:i + batch_size]
        for i in range(
            0,
            len(questions),
            batch_size,
        )
    ]

    print(
        f"\nValidation batch size: "
        f"{batch_size}"
    )

    print(
        f"Total validation batches: "
        f"{len(batches)}"
    )

    # ==========================================
    # Batch validation
    # ==========================================

    for batch_number, batch in enumerate(
        batches,
        start=1,
    ):

        print(
            f"\nValidating batch "
            f"{batch_number}/"
            f"{len(batches)}"
        )

        questions_with_sources = []

        for question in batch:

            question_id = question[
                "question_id"
            ]

            sources = context_lookup.get(
                question_id,
                []
            )

            if not sources:

                rejected_questions.append({
                    "question": question,
                    "reason":
                        "No retrieved source context.",
                })

                continue

            question_copy = dict(
                question
            )

            question_copy[
                "sources"
            ] = sources

            questions_with_sources.append(
                question_copy
            )

        if not questions_with_sources:
            continue

        # --------------------------------------
        # ONE LLM call for this batch
        # --------------------------------------

        validation_results = (
            check_grounding_batch(
                questions_with_sources
            )
        )

        # ======================================
        # Process validation results
        # ======================================

        for question in questions_with_sources:

            question_id = question[
                "question_id"
            ]

            result = validation_results[
                question_id
            ]

            # ----------------------------------
            # PASSED
            # ----------------------------------

            if result[
                "supported"
            ]:

                question[
                    "grounding"
                ] = {
                    "supported": True,
                    "reason": result[
                        "reason"
                    ],
                }

                final_questions.append(
                    question
                )

                print(
                    f"Q{question_id} "
                    f"PASSED grounding."
                )

                continue

            # ----------------------------------
            # FAILED
            # ----------------------------------

            print(
                f"Q{question_id} "
                f"FAILED grounding."
            )

            print(
                f"Reason: "
                f"{result['reason']}"
            )

            # ----------------------------------
            # Regenerate failed question
            # ----------------------------------

            topic = question[
                "topic"
            ]

            difficulty = question[
                "difficulty"
            ]

            current_question = question

            regenerated_successfully = False

            for attempt in range(
                1,
                MAX_RETRIES + 1,
            ):

                print(
                    f"Regenerating Q"
                    f"{question_id} "
                    f"(attempt "
                    f"{attempt}/"
                    f"{MAX_RETRIES})..."
                )

                try:

                    new_mcq = (
                        regenerate_question(
                            topic=topic,
                            difficulty=difficulty,
                            sources=question[
                                "sources"
                            ],
                        )
                    )

                    current_question = {

                        "question_id":
                            question_id,

                        "topic":
                            topic,

                        "difficulty":
                            difficulty,

                        "question":
                            new_mcq.question,

                        "options":
                            new_mcq.options,

                        "correct_answer":
                            new_mcq.correct_answer,

                        "explanation":
                            new_mcq.explanation,

                        "sources":
                            question[
                                "sources"
                            ],
                    }

                    # ----------------------------------
                    # Validate regenerated question
                    # ----------------------------------

                    regenerated_check = (
                        check_grounding(
                            current_question,
                            question[
                                "sources"
                            ],
                        )
                    )

                    if regenerated_check.get(
                        "supported"
                    ) is True:

                        current_question[
                            "grounding"
                        ] = {
                            "supported": True,
                            "reason":
                                regenerated_check.get(
                                    "reason",
                                    ""
                                ),
                        }

                        final_questions.append(
                            current_question
                        )

                        print(
                            f"Q{question_id} "
                            f"PASSED after regeneration."
                        )

                        regenerated_successfully = True

                        break

                    print(
                        f"Q{question_id} "
                        f"still failed."
                    )

                except Exception as e:

                    print(
                        f"Regeneration error "
                        f"for Q{question_id}: "
                        f"{e}"
                    )

            # ----------------------------------
            # Rejected after retries
            # ----------------------------------

            if not regenerated_successfully:

                rejected_questions.append({

                    "question":
                        current_question,

                    "reason":
                        "Failed semantic validation "
                        "after maximum retries.",

                    "attempts":
                        MAX_RETRIES,
                })

    # ==========================================
    # Sort
    # ==========================================

    final_questions.sort(
        key=lambda x:
            x["question_id"]
    )

    # ==========================================
    # Final quiz
    # ==========================================

    final_quiz = {

        "total_questions":
            len(final_questions),

        "questions":
            final_questions,
    }

    return (
        final_quiz,
        rejected_questions
    )


# ==========================================
# 10. Main
# ==========================================

if __name__ == "__main__":

    print(
        "Quizora Semantic Validation"
    )

    print(
        "---------------------------"
    )

    # ==========================================
    # Check files
    # ==========================================

    if not Path(
        INPUT_FILE
    ).exists():

        raise FileNotFoundError(
            f"{INPUT_FILE} not found."
        )

    if not Path(
        CONTEXT_FILE
    ).exists():

        raise FileNotFoundError(
            f"{CONTEXT_FILE} not found."
        )

    # ==========================================
    # Load generated quiz
    # ==========================================

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        quiz = json.load(
            file
        )

    # ==========================================
    # Load retrieval context
    # ==========================================

    with open(
        CONTEXT_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        retrieval = json.load(
            file
        )

    # ==========================================
    # Validate
    # ==========================================

    final_quiz, rejected_questions = (
        validate_quiz(
            quiz,
            retrieval,
            batch_size=VALIDATION_BATCH_SIZE,
        )
    )

    # ==========================================
    # Save final quiz
    # ==========================================

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            final_quiz,
            file,
            indent=4,
            ensure_ascii=False,
        )

    # ==========================================
    # Save rejected
    # ==========================================

    with open(
        REJECTED_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            rejected_questions,
            file,
            indent=4,
            ensure_ascii=False,
        )

    # ==========================================
    # Report
    # ==========================================

    print(
        "\n=============================="
    )

    print(
        "Semantic validation completed"
    )

    print(
        "=============================="
    )

    print(
        f"Original questions : "
        f"{len(quiz['questions'])}"
    )

    print(
        f"Final questions    : "
        f"{len(final_quiz['questions'])}"
    )

    print(
        f"Rejected questions : "
        f"{len(rejected_questions)}"
    )

    print(
        f"\nFinal quiz saved to: "
        f"{OUTPUT_FILE}"
    )

    print(
        f"Rejected saved to: "
        f"{REJECTED_FILE}"
    )