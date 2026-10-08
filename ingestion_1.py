import os
from pathlib import Path

from dotenv import load_dotenv

from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    Settings,
)

from llama_index.core.node_parser import SentenceSplitter

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.postgres import PGVectorStore


load_dotenv()
os.environ.setdefault("HF_HUB_OFFLINE", "1")


def ingest_document(pdf_path=None):

    # ==========================================
    # 1. Gemini Embedding Model
    # ==========================================

    embed_model = HuggingFaceEmbedding(
        model_name="Qwen/Qwen3-Embedding-0.6B",
        trust_remote_code=True,
        device="cuda",
        embed_batch_size=16,
    )

    Settings.embed_model = embed_model


    # ==========================================
    # 2. Load PDF
    # ==========================================

    target_path = Path(pdf_path) if pdf_path else Path("data")
    print(f"Ingesting from: {target_path}")

    if target_path.is_file():
        pdf_files = [target_path]
    elif target_path.is_dir():
        pdf_files = list(target_path.glob("*.pdf"))
        if not pdf_files:
            raise FileNotFoundError(f"No .pdf files found in {target_path}")
    else:
        raise FileNotFoundError(f"Path does not exist: {target_path}")

    documents = SimpleDirectoryReader(
        input_files=[str(p) for p in pdf_files],
    ).load_data()

    print(
        f"Loaded {len(documents)} document pages."
    )


    # ==========================================
    # 3. Split into chunks
    # ==========================================

    splitter = SentenceSplitter(
        chunk_size=800,
        chunk_overlap=120,
    )

    chunks = splitter.get_nodes_from_documents(
        documents
    )

    print(
        f"Created {len(chunks)} chunks."
    )


    # ==========================================
    # 4. PostgreSQL + pgvector
    # ==========================================

    vector_store = PGVectorStore.from_params(
        database="quizora",
        host="localhost",
        password="quizora123",
        port=5433,
        user="postgres",
        table_name="QWEN_pdf_chunks",
        embed_dim=1024,
    )


    # ==========================================
    # 5. Storage Context
    # ==========================================

    storage_context = StorageContext.from_defaults(
        vector_store=vector_store
    )


    # ==========================================
    # 6. Create Vector Index
    # ==========================================

    index = VectorStoreIndex(
        chunks,
        storage_context=storage_context,
        show_progress=True,
    )


    print(
        "Document successfully indexed in PostgreSQL."
    )


    return index


# ==========================================
# Run directly
# ==========================================

if __name__ == "__main__":

    ingest_document()