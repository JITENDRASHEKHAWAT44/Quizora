import os
import json

from dotenv import load_dotenv

from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.postgres import PGVectorStore


# ==========================================
# 1. Configuration
# ==========================================

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is missing from .env")


# ==========================================
# 2. Configure Gemini Embeddings
# ==========================================

embed_model = GoogleGenAIEmbedding(
    model_name="models/gemini-embedding-001",
    api_key=GOOGLE_API_KEY,
)

Settings.embed_model = embed_model


# ==========================================
# 3. Connect to PostgreSQL + pgvector
# ==========================================

vector_store = PGVectorStore.from_params(
    database="quizora",
    host="localhost",
    password="quizora123",
    port=5433,
    user="postgres",
    table_name="pdf_chunks",
    embed_dim=3072,
)


# ==========================================
# 4. Load existing vector index
# ==========================================

index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store
)


# ==========================================
# 5. Create Retriever
# ==========================================

retriever = index.as_retriever(
    similarity_top_k=8
)


# ==========================================
# 6. Retrieve material for ONE question
# ==========================================

def retrieve_for_question(
    topic: str,
    difficulty: str,
    question_id: int,
):
    """
    Retrieve source material for one planned question.
    """

    query = f"""
    Academic material about:
    {topic}

    Focus on concepts, definitions, principles,
    examples, applications, comparisons, and important
    details related to this topic.
    """

    nodes = retriever.retrieve(query)

    sources = []

    for node in nodes:

        metadata = node.metadata or {}

        sources.append({
            "question_id": question_id,
            "topic": topic,
            "difficulty": difficulty,
            "text": node.get_content(),
            "score": node.score,
            "metadata": metadata,
        })

    return sources


# ==========================================
# 7. Load Quiz Plan
# ==========================================

def load_quiz_plan(path="quiz_plan.json"):

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found. "
            "Run question_planner.py first."
        )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ==========================================
# 8. Retrieve complete quiz context
# ==========================================

def retrieve_quiz_context(quiz_plan):

    retrieved_questions = []

    generation_plan = quiz_plan.get(
        "generation_plan",
        {}
    )

    for difficulty in [
        "easy",
        "medium",
        "hard",
    ]:

        planned_questions = generation_plan.get(
            difficulty,
            []
        )

        for item in planned_questions:

            question_id = item["question_id"]
            topic = item["topic"]

            print(
                f"Retrieving Q{question_id}: "
                f"{topic} [{difficulty}]"
            )

            sources = retrieve_for_question(
                topic=topic,
                difficulty=difficulty,
                question_id=question_id,
            )

            retrieved_questions.append({
                "question_id": question_id,
                "topic": topic,
                "difficulty": difficulty,
                "sources": sources,
            })

    return {
        "total_questions": quiz_plan["total_questions"],
        "questions": retrieved_questions,
    }


# ==========================================
# 9. Main
# ==========================================

if __name__ == "__main__":

    print("Quizora Retrieval Engine")
    print("------------------------")

    quiz_plan = load_quiz_plan()

    result = retrieve_quiz_context(
        quiz_plan
    )

    # Save for debugging / inspection
    with open(
        "retrieved_context.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            result,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("\nRetrieval completed successfully.")

    print(
        f"Retrieved context for "
        f"{len(result['questions'])} questions."
    )

    print(
        "Saved to retrieved_context.json"
    )