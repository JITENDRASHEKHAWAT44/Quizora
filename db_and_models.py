import os
from dotenv import load_dotenv

load_dotenv()


def get_embedding_model():
    """
    Returns (embed_model, embed_dim, table_name).
    Prefers Jina AI Embeddings API (zero local RAM, 100% cloud-optimized for 512 MB Render limit).
    Falls back to local HuggingFace MiniLM-L6-v2 if JINA_API_KEY is not set.
    """
    jina_key = os.getenv("JINA_API_KEY")
    if jina_key:
        try:
            from llama_index.embeddings.jinaai import JinaEmbedding
            print("Using Jina AI Embeddings (API-based, zero local RAM, cloud-optimized)...")
            return (
                JinaEmbedding(
                    api_key=jina_key,
                    model="jina-embeddings-v3",
                    task="retrieval.passage",
                    dimensions=1024,
                ),
                1024,
                "jina_pdf_chunks",
            )
        except Exception as e:
            print(f"Jina AI initialization failed: {e}. Falling back to HuggingFace...")

    try:
        import torch
        torch.set_num_threads(1)
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
        import re
        from urllib.parse import unquote

        # Match postgresql://user:password@host:port/database robustly
        m = re.match(
            r"^postgres(?:ql)?://(?:(?P<user>[^:]+)(?::(?P<password>.*))?@)?(?P<host>[^:/]+)(?::(?P<port>\d+))?/(?P<database>[^?]+)",
            db_url.strip(),
        )
        if m:
            gd = m.groupdict()
            raw_pwd = gd.get("password") or ""
            # Strip accidental surrounding brackets [password] if user entered them literally
            if raw_pwd.startswith("[") and raw_pwd.endswith("]"):
                raw_pwd = raw_pwd[1:-1]

            return PGVectorStore.from_params(
                database=gd.get("database") or "postgres",
                host=gd.get("host"),
                password=unquote(raw_pwd) if raw_pwd else None,
                port=int(gd.get("port") or 5432),
                user=unquote(gd.get("user") or "postgres"),
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
