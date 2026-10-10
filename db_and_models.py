import os
from dotenv import load_dotenv

load_dotenv()


def get_embedding_model():
    """
    Always uses HuggingFace sentence-transformers/all-MiniLM-L6-v2.
    ~90 MB RAM — well within Render's 512 MB free tier.
    embed_dim = 384, table = minilm_pdf_chunks.
    """
    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        device = "cpu"

    print(f"Using HuggingFace MiniLM embeddings on device '{device}'...")
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    return (
        HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            device=device,
            embed_batch_size=32,
        ),
        384,
        "minilm_pdf_chunks",
    )



def get_vector_store(table_name="minilm_pdf_chunks", embed_dim=384):
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
