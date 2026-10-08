import os
import json

from dotenv import load_dotenv

from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core import VectorStoreIndex

from llama_index.llms.groq import Groq


load_dotenv()
os.environ.setdefault("HF_HUB_OFFLINE", "1")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def analyze_document():
    # ==========================================
    # Setup (lazy — only runs when called)
    # ==========================================

    embed_model = HuggingFaceEmbedding(
        model_name="Qwen/Qwen3-Embedding-0.6B",
        trust_remote_code=True,
        device="cuda",
    )

    Settings.embed_model = embed_model

    llm = Groq(
        model="openai/gpt-oss-120b",
        api_key=GROQ_API_KEY,
    )

    Settings.llm = llm

    vector_store = PGVectorStore.from_params(
        database="quizora",
        host="localhost",
        password="quizora123",
        port=5433,
        user="postgres",
        table_name="QWEN_pdf_chunks",
        embed_dim=1024,
    )

    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store
    )

    retriever = index.as_retriever(
        similarity_top_k=15
    )

    print("Analyzing document for diverse topics...")

    # Multi-angle retrieval to capture different sections and concepts
    queries = [
        "table of contents syllabus overview main topics chapters",
        "key definitions algorithms methods theorems techniques",
        "analysis complexity formulas examples problems applications",
    ]

    seen_texts = set()
    context_parts = []
    current_length = 0
    MAX_CONTEXT_CHARS = 24000

    for q in queries:
        try:
            nodes = retriever.retrieve(q)
            for node in nodes:
                text = node.get_content().strip()
                if text and text not in seen_texts:
                    seen_texts.add(text)
                    if current_length + len(text) <= MAX_CONTEXT_CHARS:
                        context_parts.append(text)
                        current_length += len(text)
        except Exception as e:
            print(f"Retrieval warning for query '{q}': {e}")

    if not context_parts:
        # Fallback to single broad query
        nodes = retriever.retrieve("main topics chapters concepts definitions algorithms")
        for node in nodes:
            t = node.get_content().strip()
            if t:
                context_parts.append(t)

    if not context_parts:
        raise ValueError("No document content found for analysis.")

    context = "\n\n".join(context_parts)

    print(
        f"Using {len(context_parts)} distinct chunks "
        f"for document analysis."
    )
    print(
        f"Context size: {len(context)} characters."
    )

    prompt = f"""
You are an expert academic curriculum designer analyzing study material for an exam assessment system.

Your goal is to extract 5 to 12 distinct, specific topics, concepts, theorems, or problem areas from the material so that a well-balanced quiz can be created.

CRITICAL RULES:
1. Do NOT return just a single generic title (like "Computer Science", "Designing of an Algorithm", or "Lecture Notes").
2. Extract specific academic sub-topics and core concepts covered in the material.
   For example, instead of just "Algorithms", extract:
   - "Time and Space Complexity Analysis"
   - "Asymptotic Notations (Big-O, Omega, Theta)"
   - "Divide and Conquer Technique"
   - "Recurrence Relations & Master Theorem"
   - "Greedy Approach Principles"
   - "Algorithm Efficiency Comparisons"
3. Identify between 4 and 10 specific topics.
4. Each topic must represent a distinct testable subject area.
5. Return ONLY valid JSON in this exact structure:

{{
    "topics": [
        {{
            "name": "Specific Topic Name",
            "description": "Specific concepts, methods, and rules included in this topic",
            "importance": "high"
        }}
    ]
}}

Use "high", "medium", or "low" for importance.

DOCUMENT MATERIAL:
------------------
{context}
------------------
"""

    response = llm.complete(prompt)
    raw_output = response.text.strip()

    # Robust JSON extraction
    def parse_json_safely(text):
        import re
        t = text.strip()
        if t.startswith("```"):
            t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
            t = re.sub(r"\s*```$", "", t)
            t = t.strip()
        try:
            return json.loads(t)
        except json.JSONDecodeError:
            match = re.search(r'(\{[\s\S]*\})', t)
            if match:
                return json.loads(match.group(1))
            raise

    try:
        document_map = parse_json_safely(raw_output)
    except Exception as e:
        print(f"LLM returned non-JSON output, error: {e}")
        print(f"Raw output: {raw_output[:500]}")
        # Graceful fallback: construct default topics
        document_map = {
            "topics": [
                {"name": "Core Principles and Definitions", "description": "Fundamental concepts and terminology", "importance": "high"},
                {"name": "Methodologies and Algorithms", "description": "Specific procedural steps and algorithmic methods", "importance": "high"},
                {"name": "Performance and Complexity Analysis", "description": "Efficiency, bounds, and comparisons", "importance": "medium"},
                {"name": "Practical Applications and Scenarios", "description": "Real-world usage, edge cases, and problem solving", "importance": "medium"}
            ]
        }

    topics = document_map.get("topics", [])
    # If the LLM returned only 1 topic or none, enhance it
    if len(topics) < 3:
        existing_name = topics[0].name if (topics and hasattr(topics[0], 'name')) else (topics[0].get("name", "Subject Overview") if topics else "Subject Overview")
        document_map["topics"] = [
            {"name": f"{existing_name} — Core Concepts & Definitions", "description": "Fundamental definitions and terminology", "importance": "high"},
            {"name": f"{existing_name} — Methodology & Execution", "description": "Specific steps, rules, and procedures", "importance": "high"},
            {"name": f"{existing_name} — Analysis & Properties", "description": "Performance, complexity, and theoretical properties", "importance": "medium"},
            {"name": f"{existing_name} — Comparisons & Trade-offs", "description": "Advantages, disadvantages, and alternative approaches", "importance": "medium"}
        ]

    with open("document_map.json", "w", encoding="utf-8") as file:
        json.dump(document_map, file, indent=4, ensure_ascii=False)

    print("\nDocument analysis completed.")
    print(f"Identified {len(document_map['topics'])} topics:")
    for topic in document_map["topics"]:
        name = str(topic.get('name', '')).encode('ascii', 'replace').decode('ascii')
        imp = str(topic.get('importance', ''))
        print(f"- {name} ({imp})")

    return document_map



if __name__ == "__main__":
    analyze_document()