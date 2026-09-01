import os
import json

from dotenv import load_dotenv

from llama_index.core import Settings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core import VectorStoreIndex

from llama_index.llms.groq import Groq


load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

embed_model = GoogleGenAIEmbedding(
    model_name="models/gemini-embedding-001",
    api_key=GOOGLE_API_KEY,
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
    table_name="pdf_chunks",
    embed_dim=3072,
)


index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store
)

retriever = index.as_retriever(
    similarity_top_k=20
)


def analyze_document():

    print("Analyzing document...")

    # Broad query to retrieve representative material
    nodes = retriever.retrieve(
        "main topics chapters sections concepts definitions algorithms"
    )

    if not nodes:
        raise ValueError("No document content found.")

    # Keep the context comfortably below Groq's TPM limit
    MAX_CONTEXT_CHARS = 24000

    context_parts = []
    current_length = 0

    for node in nodes:

        text = node.get_content().strip()

        if current_length + len(text) > MAX_CONTEXT_CHARS:
            break

        context_parts.append(text)
        current_length += len(text)

    context = "\n\n".join(context_parts)

    print(
        f"Using {len(context_parts)} chunks "
        f"for document analysis."
    )

    print(
        f"Context size: {len(context)} characters."
    )


    prompt = f"""
You are analyzing an academic document for an educational
MCQ generation system.

Identify the major topics and sections represented in the
provided document material.

Do NOT invent topics that are not supported by the material.

Return ONLY valid JSON in this exact format:

{{
    "topics": [
        {{
            "name": "Topic name",
            "description": "Short description",
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

    try:
        document_map = json.loads(raw_output)

    except json.JSONDecodeError:
        print("LLM returned invalid JSON:")
        print(raw_output)
        raise

    with open(
        "document_map.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            document_map,
            file,
            indent=4,
            ensure_ascii=False
        )


    print("\nDocument analysis completed.")

    print(
        f"Identified {len(document_map['topics'])} topics."
    )

    print("\nTopics:")

    for topic in document_map["topics"]:

        print(
            f"- {topic['name']} "
            f"({topic['importance']})"
        )
    
    return document_map


if __name__ == "__main__":
    analyze_document()