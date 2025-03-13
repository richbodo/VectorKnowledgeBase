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

EMBEDDING_MODEL = "text-embedding-3-small"  

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
if IS_DEPLOYMENT:
    CHROMA_PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR", "chroma_db_prod")
    import logging
    logging.info(f"Using production ChromaDB directory: {CHROMA_PERSIST_DIR}")
else:
    CHROMA_PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR", "chroma_db_dev")
    import logging
    logging.info(f"Using development ChromaDB directory: {CHROMA_PERSIST_DIR}")

# API Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
ALLOWED_FILE_TYPES = ["application/pdf"]