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
import logging
logger = logging.getLogger(__name__)

# Check environment information
for env_var in ['REPL_HOME', 'REPL_SLUG', 'REPL_OWNER', 'REPL_ID', 'REPL_IMAGE']:
    if env_var in os.environ:
        logger.info(f"{env_var}: {os.environ[env_var]}")
    else:
        logger.info(f"{env_var} not set")

# For Replit deployments, we'll use a persistent path based on REPL_SLUG
# which should remain consistent across deployments
if os.environ.get('REPL_SLUG'):
    # We're in Replit environment
    repl_slug = os.environ.get('REPL_SLUG', '')  # Use empty string as fallback
    REPL_STORAGE_DIR = os.path.join('/home/runner', repl_slug, 'storage')
    # Create the storage directory if it doesn't exist
    os.makedirs(REPL_STORAGE_DIR, exist_ok=True)
    CHROMA_DB_PATH = os.path.join(REPL_STORAGE_DIR, 'chroma_db')
    logger.info(f"Using persistent ChromaDB path: {CHROMA_DB_PATH}")
    logger.info(f"Storage directory exists: {os.path.exists(REPL_STORAGE_DIR)}")
else:
    # Local development or other environment
    default_path = 'chroma_db'
    path_from_env = os.environ.get('CHROMA_DB_PATH')
    CHROMA_DB_PATH = os.path.abspath(path_from_env if path_from_env else default_path)
    logger.info(f"Using local ChromaDB path: {CHROMA_DB_PATH}")

# API Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
ALLOWED_FILE_TYPES = ["application/pdf"]