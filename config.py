import os

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
EMBEDDING_MODEL = "text-embedding-3-small"  

# API Configuration
VKB_API_KEY = os.environ.get("VKB_API_KEY")
if not VKB_API_KEY:
    raise ValueError("VKB_API_KEY environment variable is not set")

# ChromaDB Configuration
CHROMA_PERSIST_DIR = "chroma_db"

# API Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  
ALLOWED_FILE_TYPES = ["application/pdf"]