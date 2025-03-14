import chromadb

CHROMA_PERSIST_DIR = "chroma_db"
client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

# list_collections() now returns a list of strings directly
collections = client.list_collections()

print(f"Existing collections: {collections}")