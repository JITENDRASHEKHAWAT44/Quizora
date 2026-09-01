from dotenv import load_dotenv
load_dotenv()
import os
#PDF -> load -> CHUNK -> Embeddings -> PostgreSQL + pgvector

from llama_index.core  import SimpleDirectoryReader,VectorStoreIndex,StorageContext,Settings

from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.postgres import PGVectorStore

embed_model = GoogleGenAIEmbedding(
    model_name="models/gemini-embedding-001",
    api_key=os.getenv("GOOGLE_API_KEY"),
)
Settings.embed_model = embed_model

vector_store = PGVectorStore.from_params(
    database="quizora",
    host="localhost",
    password="quizora123",
    port=5433,
    user="postgres",
    table_name="pdf_chunks",
    embed_dim=3072,
)

#load data - Chunk
documents = SimpleDirectoryReader(input_dir="data").load_data()

storage_context = StorageContext.from_defaults(vector_store=vector_store)

index = VectorStoreIndex.from_documents(documents,storage_context=storage_context)

print("Done")