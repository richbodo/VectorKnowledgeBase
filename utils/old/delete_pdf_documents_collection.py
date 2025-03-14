#!/usr/bin/env python3
import sys
import os
import logging
import chromadb

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import CHROMA_DB_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("delete-collection")

def delete_collection():
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    existing_collections = client.list_collections()
    logger.info(f"Existing collections before deletion: {existing_collections}")

    if "pdf_documents" in existing_collections:
        logger.info("Deleting existing 'pdf_documents' collection...")
        client.delete_collection("pdf_documents")
        logger.info("Deleted existing 'pdf_documents' collection.")
    else:
        logger.info("'pdf_documents' collection does not exist. No deletion needed.")

    existing_collections_after = client.list_collections()
    logger.info(f"Existing collections after deletion: {existing_collections_after}")

if __name__ == "__main__":
    delete_collection()
    