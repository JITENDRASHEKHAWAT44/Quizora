import os
from dotenv import load_dotenv

load_dotenv()


def get_embedding_model():
    """
    Returns (embed_model, embed_dim, table_name).
    Prefers Google Gemini API embeddings (35 MB RAM, ultra-lightweight for cloud hosts like Render)
    and falls back to local HuggingFace Qwen (requires PyTorch, ~1.5 GB RAM).
    """
    google_key = os.getenv("GOOGLE_API_KEY")
    if google_key:
        try:
            from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
            print("Using Google Gemini Embeddings (lightweight, cloud-optimized)...")
            return (
                GoogleGenAIEmbedding(
                    model_name="models/text-embedding-004",
                    api_key=google_key,
                ),
                768,
                "gemini_pdf_chunks",
            )
        except Exception as e:
            print(f"Gemini embedding init error, falling back to HuggingFace: {e}")

    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        device = "cpu"

    print(f"Using HuggingFace Qwen embeddings on device '{device}'...")
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    return (
        HuggingFaceEmbedding(
            model_name="Qwen/Qwen3-Embedding-0.6B",
            trust_remote_code=True,
            device=device,
            embed_batch_size=8,
        ),
        1024,
        "QWEN_pdf_chunks",
    )


def get_vector_store(table_name="gemini_pdf_chunks", embed_dim=768):
    """
    Connects to Supabase PostgreSQL if DATABASE_URL is set, otherwise falls back to local PostgreSQL.
    """
    from llama_index.vector_stores.postgres import PGVectorStore

    db_url = os.getenv("DATABASE_URL")
    if db_url:
        from urllib.parse import urlparse
        u = urlparse(db_url)
        return PGVectorStore.from_params(
            database=u.path.lstrip("/"),
            host=u.hostname,
            password=u.password,
            port=u.port or 5432,
            user=u.username,
            table_name=table_name,
            embed_dim=embed_dim,
        )

    return PGVectorStore.from_params(
        database="quizora",
        host="localhost",
        password="quizora123",
        port=5433,
        user="postgres",
        table_name=table_name,
        embed_dim=embed_dim,
    )
