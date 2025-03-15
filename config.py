import os

# Detect deployment environment
IS_DEPLOYMENT = bool(os.environ.get("REPL_DEPLOYMENT", False))

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    if IS_DEPLOYMENT:
        OPENAI_API_KEY = ""  # Allow running in deployment even if the key is missing
        import logging
        logging.warning("Deployment mode - continuing without OpenAI API key")
    else:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

EMBEDDING_MODEL = "text-embedding-ada-002"  # Using older model to match existing database dimensions  

# API Configuration
VKB_API_KEY = os.environ.get("VKB_API_KEY")
if not VKB_API_KEY:
    if IS_DEPLOYMENT:
        VKB_API_KEY = ""  # Allow running in deployment even if the key is missing
        import logging
        logging.warning("Deployment mode - continuing without VKB API key")
    else:
        raise ValueError("VKB_API_KEY environment variable is not set")

# ChromaDB Configuration
# Ensure ChromaDB data persists by using an absolute path in the workspace folder
# This will ensure data survives across Replit restarts
if os.environ.get('REPL_HOME'):
    # We're in Replit environment
    CHROMA_DB_PATH = os.path.join(os.environ.get('REPL_HOME'), 'chroma_db')
else:
    # Local development or other environment
    CHROMA_DB_PATH = os.path.abspath(os.environ.get('CHROMA_DB_PATH', 'chroma_db'))

# API Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
ALLOWED_FILE_TYPES = ["application/pdf"]