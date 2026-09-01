import json
import re
from pathlib import Path


# ==========================================
# Configuration
# ==========================================

INPUT_FILE = "generated_quiz.json"
OUTPUT_FILE = "validated_quiz.json"
REJECTED_FILE = "rejected_questions.json"

VALID_DIFFICULTIES = {
    "easy",
    "medium",
    "hard",
}


# ==========================================
# Text normalization
# ==========================================

def normalize_text(text: str) -> str:
    """
    Normalize text for duplicate/comparison checks.
    """

    text = text.lower().strip()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    text = re.sub(
        r"[^\w\s]",
        "",
        text,
    )

    return text


# ==========================================
# Validate one question
# ==========================================

def validate_question(question):
    """
    Validate the structure and basic quality
    of one generated MCQ.
    """

    errors = []

    # --------------------------------------
    # Required fields
    # --------------------------------------

    required_fields = [
        "question",
        "options",
        "correct_answer",
        "explanation",
        "topic",
        "difficulty",
        "sources",
    ]

    for field in required_fields:

        if field not in question:
            errors.append(
                f"Missing field: {field}"
            )


    # Stop if required fields are missing
    if errors:
        return False, errors


    # --------------------------------------
    # Question text
    # --------------------------------------

    if not isinstance(
        question["question"],
        str
    ):

        errors.append(
            "Question must be a string."
        )

    elif not question[
        "question"
    ].strip():

        errors.append(
            "Question cannot be empty."
        )


    # --------------------------------------
    # Options
    # --------------------------------------

    options = question["options"]

    if not isinstance(
        options,
        list
    ):

        errors.append(
            "Options must be a list."
        )

    else:

        if len(options) != 4:

            errors.append(
                f"Expected exactly 4 options, "
                f"found {len(options)}."
            )

        # Check each option
        for option in options:

            if not isinstance(
                option,
                str
            ):

                errors.append(
                    "Every option must be a string."
                )

            elif not option.strip():

                errors.append(
                    "Options cannot be empty."
                )

        # Check duplicate options
        normalized_options = [
            normalize_text(option)
            for option in options
        ]

        if len(
            normalized_options
        ) != len(
            set(normalized_options)
        ):

            errors.append(
                "Duplicate options detected."
            )


    # --------------------------------------
    # Correct answer
    # --------------------------------------

    correct_answer = question[
        "correct_answer"
    ]

    if not isinstance(
        correct_answer,
        str
    ):

        errors.append(
            "Correct answer must be a string."
        )

    else:

        normalized_correct = normalize_text(
            correct_answer
        )

        normalized_options = [
            normalize_text(option)
            for option in options
        ]

        if normalized_correct not in normalized_options:

            errors.append(
                "Correct answer is not one "
                "of the four options."
            )


    # --------------------------------------
    # Explanation
    # --------------------------------------

    explanation = question[
        "explanation"
    ]

    if not isinstance(
        explanation,
        str
    ):

        errors.append(
            "Explanation must be a string."
        )

    elif not explanation.strip():

        errors.append(
            "Explanation cannot be empty."
        )


    # --------------------------------------
    # Topic
    # --------------------------------------

    topic = question["topic"]

    if not isinstance(
        topic,
        str
    ) or not topic.strip():

        errors.append(
            "Topic cannot be empty."
        )


    # --------------------------------------
    # Difficulty
    # --------------------------------------

    difficulty = str(
        question["difficulty"]
    ).lower().strip()

    if difficulty not in VALID_DIFFICULTIES:

        errors.append(
            f"Invalid difficulty: {difficulty}"
        )


    # --------------------------------------
    # Sources
    # --------------------------------------

    sources = question["sources"]

    if not isinstance(
        sources,
        list
    ):

        errors.append(
            "Sources must be a list."
        )

    elif len(sources) == 0:

        errors.append(
            "Question has no source material."
        )


    # --------------------------------------
    # Result
    # --------------------------------------

    if errors:
        return False, errors

    return True, []


# ==========================================
# Duplicate detection
# ==========================================

def remove_duplicate_questions(questions):
    """
    Remove duplicate questions.
    """

    unique_questions = []
    duplicates = []

    seen = set()

    for question in questions:

        normalized = normalize_text(
            question["question"]
        )

        if normalized in seen:

            duplicates.append({
                "question": question,
                "reason": "Duplicate question",
            })

            continue

        seen.add(normalized)

        unique_questions.append(
            question
        )

    return unique_questions, duplicates


# ==========================================
# Validate complete quiz
# ==========================================

def validate_quiz(quiz):

    valid_questions = []
    rejected_questions = []

    questions = quiz.get(
        "questions",
        []
    )

    # --------------------------------------
    # Validate individual questions
    # --------------------------------------

    for question in questions:

        valid, errors = validate_question(
            question
        )

        if valid:

            valid_questions.append(
                question
            )

        else:

            rejected_questions.append({
                "question": question,
                "errors": errors,
            })


    # --------------------------------------
    # Remove duplicates
    # --------------------------------------

    valid_questions, duplicates = (
        remove_duplicate_questions(
            valid_questions
        )
    )

    rejected_questions.extend(
        duplicates
    )


    # --------------------------------------
    # Build validated quiz
    # --------------------------------------

    validated_quiz = {
        "total_questions": len(
            valid_questions
        ),

        "questions": valid_questions,
    }


    return (
        validated_quiz,
        rejected_questions,
    )


# ==========================================
# Main
# ==========================================

if __name__ == "__main__":

    print(
        "Quizora Quality Validator"
    )

    print(
        "-------------------------"
    )

    input_path = Path(
        INPUT_FILE
    )

    if not input_path.exists():

        raise FileNotFoundError(
            f"{INPUT_FILE} not found. "
            "Run generation_engine.py first."
        )


    # --------------------------------------
    # Load generated quiz
    # --------------------------------------

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        quiz = json.load(file)


    # --------------------------------------
    # Validate
    # --------------------------------------

    validated_quiz, rejected = (
        validate_quiz(quiz)
    )


    # --------------------------------------
    # Save validated quiz
    # --------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            validated_quiz,
            file,
            indent=4,
            ensure_ascii=False,
        )


    # --------------------------------------
    # Save rejected questions
    # --------------------------------------

    with open(
        REJECTED_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            rejected,
            file,
            indent=4,
            ensure_ascii=False,
        )


    # --------------------------------------
    # Report
    # --------------------------------------

    generated_count = len(
        quiz.get(
            "questions",
            []
        )
    )

    valid_count = len(
        validated_quiz[
            "questions"
        ]
    )

    rejected_count = len(
        rejected
    )


    print("\nValidation completed.")

    print(
        f"Generated questions : "
        f"{generated_count}"
    )

    print(
        f"Valid questions     : "
        f"{valid_count}"
    )

    print(
        f"Rejected questions  : "
        f"{rejected_count}"
    )

    print(
        f"\nSaved valid quiz to: "
        f"{OUTPUT_FILE}"
    )

    print(
        f"Saved rejected questions to: "
        f"{REJECTED_FILE}"
    )