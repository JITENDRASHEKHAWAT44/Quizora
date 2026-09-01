import os 
from dotenv import load_dotenv

from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core import VectorStoreIndex,StorageContext,Settings,load_index_from_storage
from llama_index.llms.groq import Groq
load_dotenv()

embed_model = GoogleGenAIEmbedding(model_name="models/gemini-embedding-001",api_key=os.getenv("GOOGLE_API_KEY"))
Settings.embed_model = embed_model
llm = Groq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
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

storage_context = StorageContext.from_defaults(vector_store=vector_store)

index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

retriever = index.as_query_engine(
    similarity_top_k = 5
)

def retrieve_context(query: str):

    nodes = retriever.retrieve(query)

    context_parts = []

    for node in nodes:
        context_parts.append(node.get_content())

    return "\n\n".join(context_parts)
