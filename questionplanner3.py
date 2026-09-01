import json
from pathlib import Path


DOCUMENT_MAP_FILE = "document_map.json"
OUTPUT_FILE = "quiz_plan.json"

def load_document_map():

    path = Path(DOCUMENT_MAP_FILE)

    if not path.exists():
        raise FileNotFoundError(
            f"{DOCUMENT_MAP_FILE} not found. "
            "Run document_analyzer.py first."
        )

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_difficulty_distribution(
    total_questions: int,
    easy_percent: float,
    medium_percent: float,
    hard_percent: float,
):

    total_percent = (
        easy_percent +
        medium_percent +
        hard_percent
    )

    if abs(total_percent - 100) > 0.001:
        raise ValueError(
            "Easy + Medium + Hard percentages must equal 100."
        )

    easy = round(total_questions * easy_percent / 100)
    medium = round(total_questions * medium_percent / 100)

    # Give remaining questions to hard so the total
    # is ALWAYS exactly correct.
    hard = total_questions - easy - medium

    return {
        "easy": easy,
        "medium": medium,
        "hard": hard,
    }

def calculate_topic_distribution(
    topics,
    total_questions: int,
):

    if not topics:
        raise ValueError("No topics found in document map.")

    # Importance weights
    weights = {
        "high": 3,
        "medium": 2,
        "low": 1,
    }

    topic_weights = []

    for topic in topics:

        importance = topic.get(
            "importance",
            "medium"
        ).lower()

        weight = weights.get(
            importance,
            2
        )

        topic_weights.append(
            weight
        )

    total_weight = sum(topic_weights)

    distribution = []

    for topic, weight in zip(
        topics,
        topic_weights
    ):

        raw_count = (
            total_questions *
            weight /
            total_weight
        )

        distribution.append({
            "topic": topic["name"],
            "importance": topic.get(
                "importance",
                "medium"
            ),
            "raw_count": raw_count,
            "question_count": int(raw_count),
        })


    assigned = sum(
        item["question_count"]
        for item in distribution
    )

    remaining = total_questions - assigned

    distribution.sort(
        key=lambda x: (
            x["raw_count"] -
            x["question_count"]
        ),
        reverse=True,
    )

    for i in range(remaining):
        distribution[i]["question_count"] += 1

    return distribution


def create_quiz_plan(
    total_questions: int,
    easy_percent: float = 30,
    medium_percent: float = 50,
    hard_percent: float = 20,
):

    if total_questions <= 0:
        raise ValueError(
            "Number of questions must be greater than 0."
        )

    document_map = load_document_map()

    topics = document_map.get(
        "topics",
        []
    )

    difficulty = calculate_difficulty_distribution(
        total_questions,
        easy_percent,
        medium_percent,
        hard_percent,
    )

    topic_distribution = calculate_topic_distribution(
        topics,
        total_questions,
    )

    quiz_plan = {
        "total_questions": total_questions,

        "difficulty_distribution": difficulty,

        "topic_distribution": topic_distribution,

        "generation_plan": {
            "easy": [],
            "medium": [],
            "hard": [],
        },
    }


    topic_counts = [
        item["question_count"]
        for item in topic_distribution
    ]

    topic_names = [
        item["topic"]
        for item in topic_distribution
    ]

    # Simple deterministic allocation
    question_number = 1

    difficulty_sequence = []

    for difficulty_name, count in difficulty.items():

        difficulty_sequence.extend(
            [difficulty_name] * count
        )

    for difficulty_name in [
        "easy",
        "medium",
        "hard",
    ]:

        difficulty_questions = [
            d
            for d in difficulty_sequence
            if d == difficulty_name
        ]

        for topic, count in zip(
            topic_names,
            topic_counts
        ):

            for _ in range(
                min(
                    count,
                    len(difficulty_questions)
                )
            ):

                quiz_plan[
                    "generation_plan"
                ][difficulty_name].append({
                    "question_id": question_number,
                    "topic": topic,
                    "difficulty": difficulty_name,
                })

                question_number += 1

                difficulty_questions.pop(0)

            if not difficulty_questions:
                break

    return quiz_plan

if __name__ == "__main__":

    print("Quizora Question Planner")
    print("------------------------")

    total_questions = int(
        input("Number of questions: ")
    )

    easy_percent = float(
        input("Easy percentage (default 30): ")
        or 30
    )

    medium_percent = float(
        input("Medium percentage (default 50): ")
        or 50
    )

    hard_percent = float(
        input("Hard percentage (default 20): ")
        or 20
    )

    plan = create_quiz_plan(
        total_questions=total_questions,
        easy_percent=easy_percent,
        medium_percent=medium_percent,
        hard_percent=hard_percent,
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            plan,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("\nQuiz plan created successfully.")
    print(f"Saved to: {OUTPUT_FILE}")

    print(
        "\nDifficulty distribution:"
    )

    for difficulty, count in plan[
        "difficulty_distribution"
    ].items():

        print(
            f"  {difficulty.capitalize()}: {count}"
        )

    print("\nTopic distribution:")

    for topic in plan[
        "topic_distribution"
    ]:

        print(
            f"  {topic['topic']}: "
            f"{topic['question_count']}"
        )