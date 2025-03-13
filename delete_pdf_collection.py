import chromadb
from services.embedding_service import EmbeddingService
from chromadb.utils.embedding_functions import EmbeddingFunction

CHROMA_PERSIST_DIR = "chroma_db"

class CustomEmbeddingFunction(EmbeddingFunction):
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    def __call__(self, texts):
        embeddings = [self.embedding_service.generate_embedding(text) for text in texts]
        return embeddings

# Initialize embedding service and embedding function
embedding_service = EmbeddingService()
embedding_func = CustomEmbeddingFunction(embedding_service)

# Create client
client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

# Get the collection explicitly with the embedding function
collection = client.get_collection(
    name="pdf_documents",
    embedding_function=embedding_func
)

# Delete the collection
client.delete_collection("pdf_documents")
print("Deleted 'pdf_documents' collection.")