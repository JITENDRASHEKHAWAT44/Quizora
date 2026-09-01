import json
import shutil
from pathlib import Path

from ingestion_1 import ingest_document
from document_analyzer_2 import analyze_document
from questionplanner3 import create_quiz_plan
from retrieval_engine4 import retrieve_quiz_context
from generationEngine5 import generate_quiz
from check6 import validate_quiz
from correction7 import semantic_validate_quiz

# ============================================================
# PATHS
# ============================================================

DATA_DIR = Path("data")
WORK_DIR = Path("pipeline_data")
OUTPUT_DIR = Path("output")


# ============================================================
# MAIN PIPELINE
# ============================================================

def generate_quiz_pipeline(
    pdf_path: str,
    number_of_questions: int,
    easy_percent: float = 30,
    medium_percent: float = 50,
    hard_percent: float = 20,
):
    """
    Run the complete Quizora pipeline.

    PDF
      ↓
    Ingestion
      ↓
    Document Analysis
      ↓
    Question Planning
      ↓
    Retrieval
      ↓
    MCQ Generation
      ↓
    Structural Validation
      ↓
    Semantic Validation
      ↓
    Final JSON
    """

    # ========================================================
    # 0. Prepare directories
    # ========================================================

    DATA_DIR.mkdir(
        exist_ok=True
    )

    WORK_DIR.mkdir(
        exist_ok=True
    )

    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )


    # ========================================================
    # 1. INGESTION
    # ========================================================

    print("\n" + "=" * 60)
    print("STEP 1 — INGESTION")
    print("=" * 60)

    ingest_document(
        pdf_path=str(pdf_path)
    )


    # ========================================================
    # 2. DOCUMENT ANALYSIS
    # ========================================================

    print("\n" + "=" * 60)
    print("STEP 2 — DOCUMENT ANALYSIS")
    print("=" * 60)

    document_map = analyze_document()


    document_map_path = (
        WORK_DIR / "document_map.json"
    )

    with open(
        document_map_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            document_map,
            file,
            indent=4,
            ensure_ascii=False,
        )


    # ========================================================
    # 3. QUESTION PLANNING
    # ========================================================

    print("\n" + "=" * 60)
    print("STEP 3 — QUESTION PLANNING")
    print("=" * 60)

    quiz_plan = create_quiz_plan(
        total_questions=number_of_questions,
        easy_percent=easy_percent,
        medium_percent=medium_percent,
        hard_percent=hard_percent,
    )


    quiz_plan_path = (
        WORK_DIR / "quiz_plan.json"
    )

    with open(
        quiz_plan_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            quiz_plan,
            file,
            indent=4,
            ensure_ascii=False,
        )


    # ========================================================
    # 4. RETRIEVAL
    # ========================================================

    print("\n" + "=" * 60)
    print("STEP 4 — RETRIEVAL")
    print("=" * 60)

    retrieved_context = retrieve_quiz_context(
        quiz_plan
    )


    retrieved_context_path = (
        WORK_DIR / "retrieved_context.json"
    )

    with open(
        retrieved_context_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            retrieved_context,
            file,
            indent=4,
            ensure_ascii=False,
        )


    # ========================================================
    # 5. MCQ GENERATION
    # ========================================================

    print("\n" + "=" * 60)
    print("STEP 5 — MCQ GENERATION")
    print("=" * 60)

    generated_quiz = generate_quiz(
        retrieved_context
    )


    generated_quiz_path = (
        WORK_DIR / "generated_quiz.json"
    )

    with open(
        generated_quiz_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            generated_quiz,
            file,
            indent=4,
            ensure_ascii=False,
        )


    # ========================================================
    # 6. STRUCTURAL VALIDATION
    # ========================================================

    print("\n" + "=" * 60)
    print("STEP 6 — STRUCTURAL VALIDATION")
    print("=" * 60)

    validated_quiz, rejected_questions = (
        validate_quiz(
            generated_quiz
        )
    )


    if rejected_questions:

        print(
            f"Structural validator rejected "
            f"{len(rejected_questions)} questions."
        )

    else:

        print(
            "All generated questions passed "
            "structural validation."
        )


    # ========================================================
    # 7. SEMANTIC VALIDATION + REGENERATION
    # ========================================================

    print("\n" + "=" * 60)
    print("STEP 7 — SEMANTIC VALIDATION")
    print("=" * 60)

    final_quiz, semantic_rejections = semantic_validate_quiz(
        quiz=validated_quiz,
        retrieval=retrieved_context,
        batch_size=2,
    )

    final_questions = final_quiz["questions"]


    if semantic_rejections:

        print(
            f"Semantic validator rejected "
            f"{len(semantic_rejections)} questions."
        )

    else:

        print(
            "All generated questions passed "
            "semantic validation."
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    final_quiz = {
        "total_questions": len(
            final_questions
        ),

        "questions": final_questions,
    }


    # ========================================================
    # SAVE FINAL JSON
    # ========================================================

    final_json_path = (
        OUTPUT_DIR / "quiz.json"
    )

    with open(
        final_json_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            final_quiz,
            file,
            indent=4,
            ensure_ascii=False,
        )


    # ========================================================
    # SAVE DEBUG INFORMATION
    # ========================================================

    with open(
        OUTPUT_DIR / "rejected_questions.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            rejected_questions,
            file,
            indent=4,
            ensure_ascii=False,
        )


    with open(
        OUTPUT_DIR / "semantic_rejections.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            semantic_rejections,
            file,
            indent=4,
            ensure_ascii=False,
        )


    # ========================================================
    # FINAL REPORT
    # ========================================================

    print("\n" + "=" * 60)
    print("QUIZORA PIPELINE COMPLETE")
    print("=" * 60)

    print(
        f"Requested questions : "
        f"{number_of_questions}"
    )

    print(
        f"Final questions     : "
        f"{len(final_questions)}"
    )

    print(
        f"Structural rejects  : "
        f"{len(rejected_questions)}"
    )

    print(
        f"Semantic rejects    : "
        f"{len(semantic_rejections)}"
    )

    print(
        f"Final JSON          : "
        f"{final_json_path}"
    )

    print("=" * 60)


    return final_quiz

if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("QUIZORA — TEST MODE")
    print("=" * 60)

    number_of_questions = int(
        input("\nNumber of questions: ")
    )

    easy_percent = float(
        input("Easy percentage (default 30): ") or 30
    )

    medium_percent = float(
        input("Medium percentage (default 50): ") or 50
    )

    hard_percent = float(
        input("Hard percentage (default 20): ") or 20
    )

    result = generate_quiz_pipeline(
        pdf_path="data",
        number_of_questions=number_of_questions,
        easy_percent=easy_percent,
        medium_percent=medium_percent,
        hard_percent=hard_percent,
    )

    print("\nFINAL RESULT")
    print("=" * 60)

    print(
        f"Generated questions: "
        f"{result['total_questions']}"
    )

    print("\nFINAL RESULT:")
    print(result)