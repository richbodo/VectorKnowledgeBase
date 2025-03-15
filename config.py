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

# Log all environment variables to help diagnose persistence issues
logger.info("==== Environment Variables for Database Persistence ====")
for env_var, value in os.environ.items():
    if any(x in env_var.lower() for x in ['repl', 'home', 'path', 'dir', 'root']):
        logger.info(f"{env_var}: {value}")

# CRITICAL FIX: Replit persistent storage must be in /home/runner/[data|workspace]
# Persistent storage locations:
# 1. /home/runner/data - absolutely persisted across deployments (best choice)
# 2. /home/runner/ - persisted across deployments, but might be affected by clean operations

# Create these guaranteed locations if they don't exist
REPL_PERSISTENT_DIR = '/home/runner/data'
if not os.path.exists(REPL_PERSISTENT_DIR):
    try:
        os.makedirs(REPL_PERSISTENT_DIR, exist_ok=True)
        logger.info(f"Created persistent directory at {REPL_PERSISTENT_DIR}")
    except Exception as e:
        logger.error(f"Failed to create persistent directory: {str(e)}")

# Set permanent storage path for ChromaDB that will persist across deployments
PERSISTENT_STORAGE_ROOT = os.path.join(REPL_PERSISTENT_DIR, 'chromadb')
logger.info(f"Using persistent ChromaDB storage: {PERSISTENT_STORAGE_ROOT}")

# Log all environment variables for debugging
REPL_ID = os.environ.get('REPL_ID', 'unknown')
REPL_OWNER = os.environ.get('REPL_OWNER', 'unknown')
REPL_SLUG = os.environ.get('REPL_SLUG', 'unknown')
REPL_DEPLOYMENT = 'true' if os.environ.get('REPL_DEPLOYMENT') else 'false'

logger.info(f"=== REPLIT ENVIRONMENT INFO ===")
logger.info(f"REPL_ID: {REPL_ID}")
logger.info(f"REPL_OWNER: {REPL_OWNER}")
logger.info(f"REPL_SLUG: {REPL_SLUG}")
logger.info(f"REPL_DEPLOYMENT: {REPL_DEPLOYMENT}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Full env: {dict(os.environ)}")
logger.info(f"===============================")

# Create the persistent directory if it doesn't exist
os.makedirs(PERSISTENT_STORAGE_ROOT, exist_ok=True)
logger.info(f"Persistent storage exists: {os.path.exists(PERSISTENT_STORAGE_ROOT)}")
logger.info(f"Storage permissions: {oct(os.stat(PERSISTENT_STORAGE_ROOT).st_mode)[-3:]}")

# Set the ChromaDB path to this persistent location
# This matches ChromaDB's own default location when not explicitly configured
CHROMA_DB_PATH = PERSISTENT_STORAGE_ROOT
logger.info(f"Using ChromaDB path: {CHROMA_DB_PATH}")

# Check if there's any existing data
if os.path.exists(CHROMA_DB_PATH):
    logger.info(f"ChromaDB folder already exists at {CHROMA_DB_PATH}")
    if os.path.isdir(CHROMA_DB_PATH):
        contents = os.listdir(CHROMA_DB_PATH)
        logger.info(f"Contents: {contents}")
else:
    logger.info(f"ChromaDB folder does not exist yet, will be created")

# Check for previously used paths to help with migration
old_paths = [
    'chroma_db',
    os.path.join(os.getcwd(), 'chroma_db'),
    '/home/runner/workspace/chroma_db',
    '/home/runner/workspace/storage/chroma_db'
]

for path in old_paths:
    if os.path.exists(path) and os.path.isdir(path):
        logger.info(f"Found old ChromaDB at: {path}")
        if os.path.exists(os.path.join(path, 'chroma.sqlite3')):
            db_size = os.path.getsize(os.path.join(path, 'chroma.sqlite3')) / (1024 * 1024)
            logger.info(f"SQLite file exists with size: {db_size:.2f} MB")
            
            # Optionally migrate data from old location
            if not os.path.exists(CHROMA_DB_PATH):
                try:
                    import shutil
                    logger.info(f"Migrating data from {path} to {CHROMA_DB_PATH}")
                    shutil.copytree(path, CHROMA_DB_PATH)
                    logger.info(f"Migration completed successfully!")
                except Exception as e:
                    logger.error(f"Migration failed: {str(e)}")

# API Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
ALLOWED_FILE_TYPES = ["application/pdf"]