
#!/usr/bin/env python3
import chromadb
import os

# Use the same directory as the application
CHROMA_PERSIST_DIR = "chroma_db"

print(f"ChromaDB version: {chromadb.__version__}")
print(f"Directory exists: {os.path.exists(CHROMA_PERSIST_DIR)}")
print(f"Directory contents: {os.listdir(CHROMA_PERSIST_DIR)}")

# Create client with same configuration as the application
client = chromadb.PersistentClient(
    path=CHROMA_PERSIST_DIR,
    settings=chromadb.Settings(
        anonymized_telemetry=False,
        allow_reset=True,
        persist_directory=CHROMA_PERSIST_DIR
    )
)

# List collections using newer API approach
print("Collections:", client.list_collections())

# Try to get the collection by name
collection = client.get_collection(name="pdf_documents")
print(f"Collection 'pdf_documents' exists, contains {collection.count()} documents")

# Check if there are any documents in the collection
if collection.count() > 0:
    # Get sample data
    sample = collection.get(limit=1)
    print(f"Sample ID: {sample['ids'][0] if sample['ids'] else 'None'}")
    print(f"Total unique documents: {len(set([m.get('document_id') for m in sample['metadatas'] if m]))}")
else:
    print("Collection exists but contains no documents")
