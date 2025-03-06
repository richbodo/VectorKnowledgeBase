import os

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
EMBEDDING_MODEL = "text-embedding-ada-002"
VECTOR_DIMENSION = 1536  # Dimension of OpenAI embeddings

# Vector Store Configuration
FAISS_INDEX_PATH = "faiss_index"
DOCUMENT_STORE_PATH = "document_store.json"

# API Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_FILE_TYPES = ["application/pdf"]