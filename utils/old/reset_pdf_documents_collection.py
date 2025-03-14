# reset_pdf_documents_collection.py
import chromadb
import logging
import sys
import os

# Adjust the path to import from your project directories
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.embedding_service import EmbeddingService
from services.vector_store import CustomEmbeddingFunction
from config import CHROMA_DB_PATH

# Set up basic logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger("reset-collection")

def reset_collection():
    try:
        logger.info("Initializing ChromaDB client...")
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

        # Initialize embedding service and embedding function
        logger.info("Initializing embedding service...")
        embedding_service = EmbeddingService()
        embedding_func = CustomEmbeddingFunction(embedding_service)

        # Delete existing collection if it exists
        existing_collections = client.list_collections()
        logger.info(f"Existing collections before deletion: {existing_collections}")
        if "pdf_documents" in existing_collections:
            logger.info("Deleting existing 'pdf_documents' collection...")
            client.delete_collection("pdf_documents")
            logger.info("Deleted existing 'pdf_documents' collection.")
        else:
            logger.info("'pdf_documents' collection does not exist. No deletion needed.")

        # Recreate collection explicitly with embedding function
        logger.info("Recreating 'pdf_documents' collection with correct embedding function...")
        collection = client.get_or_create_collection(
            name="pdf_documents",
            embedding_function=embedding_func,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("Successfully recreated 'pdf_documents' collection with correct embedding function.")

        # Verify collection creation immediately
        collections_after_creation = client.list_collections()
        logger.info(f"Existing collections after creation: {collections_after_creation}")

    except Exception as e:
        logger.error(f"Error resetting collection: {str(e)}", exc_info=True)

if __name__ == "__main__":
    reset_collection()
    