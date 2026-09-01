import os

from dotenv import load_dotenv

from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    Settings,
)

from llama_index.core.node_parser import SentenceSplitter

from llama_index.embeddings.google_genai import (
    GoogleGenAIEmbedding,
)

from llama_index.vector_stores.postgres import (
    PGVectorStore,
)


load_dotenv()


def ingest_document(pdf_path=None):

    # ==========================================
    # 1. Gemini Embedding Model
    # ==========================================

    embed_model = GoogleGenAIEmbedding(
        model_name="models/gemini-embedding-001",
        api_key=os.getenv("GOOGLE_API_KEY"),
    )

    Settings.embed_model = embed_model


    # ==========================================
    # 2. Load PDF
    # ==========================================

    documents = SimpleDirectoryReader(
        input_dir="data",
        recursive=True,
        required_exts=[".pdf"],
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
        table_name="pdf_chunks",
        embed_dim=3072,
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