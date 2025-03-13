#!/usr/bin/env python3
import chromadb
import os
import sys
import json

# Use the same directory as the application
CHROMA_PERSIST_DIR = "chroma_db"

print(f"===== ChromaDB Diagnostic Tool =====")
print(f"ChromaDB version: {chromadb.__version__}")
print(f"Database directory: {os.path.abspath(CHROMA_PERSIST_DIR)}")
print(f"Directory exists: {os.path.exists(CHROMA_PERSIST_DIR)}")

if os.path.exists(CHROMA_PERSIST_DIR):
    print(f"Directory contents: {os.listdir(CHROMA_PERSIST_DIR)}")
    print(f"Directory permissions: {oct(os.stat(CHROMA_PERSIST_DIR).st_mode)[-3:]}")

    # Check SQLite file
    sqlite_path = os.path.join(CHROMA_PERSIST_DIR, "chroma.sqlite3")
    if os.path.exists(sqlite_path):
        print(f"SQLite file size: {os.path.getsize(sqlite_path) / 1024:.2f} KB")
        print(f"SQLite file permissions: {oct(os.stat(sqlite_path).st_mode)[-3:]}")
else:
    print("Database directory does not exist!")
    sys.exit(1)

# IMPORTANT: Create a single client configuration that matches the one in vector_store.py
print("\n===== Testing ChromaDB Access =====")
try:
    client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=chromadb.Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            persist_directory=CHROMA_PERSIST_DIR
        )
    )
    print("Successfully connected to ChromaDB with application settings")

    collections = client.list_collections()
    print(f"Found {len(collections)} collections: {collections}")

    if len(collections) > 0:
        collection_name = "pdf_documents"
        collection = client.get_collection(name=collection_name)
        count = collection.count()
        print(f"\nCollection '{collection_name}' contains {count} documents")

        if count > 0:
            # Get sample data
            sample = collection.get(limit=1)
            print(f"Sample ID: {sample['ids'][0] if sample['ids'] else 'None'}")

            # Check for document IDs
            doc_ids = set()
            if sample['metadatas']:
                for metadata in sample['metadatas']:
                    if metadata and 'document_id' in metadata:
                        doc_ids.add(metadata['document_id'])

            print(f"Unique document IDs in sample: {len(doc_ids)}")
            if doc_ids:
                print(f"Sample document ID: {list(doc_ids)[0]}")

                # Try to get all chunks for a specific document
                try:
                    sample_id = list(doc_ids)[0]
                    doc_chunks = collection.get(where={"document_id": sample_id})
                    print(f"Document '{sample_id}' has {len(doc_chunks['ids'])} chunks")
                except Exception as e:
                    print(f"Error querying document chunks: {str(e)}")
        else:
            print("Collection exists but contains no documents")
    else:
        print("No collections found")

except Exception as e:
    print(f"Error accessing ChromaDB: {str(e)}")

print("\n===== Database Structure Analysis =====")
# Try to analyze the database structure directly
try:
    import sqlite3
    conn = sqlite3.connect(os.path.join(CHROMA_PERSIST_DIR, "chroma.sqlite3"))
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"SQLite tables: {[t[0] for t in tables]}")

    # Check key tables
    try:
        cursor.execute("SELECT COUNT(*) FROM embeddings;")
        embedding_count = cursor.fetchone()[0]
        print(f"Embeddings table count: {embedding_count}")
    except sqlite3.OperationalError:
        print("No 'embeddings' table found")

    try:
        cursor.execute("SELECT COUNT(*) FROM collections;")
        collection_count = cursor.fetchone()[0]
        print(f"Collections table count: {collection_count}")

        # Get collection details
        cursor.execute("SELECT * FROM collections;")
        collections = cursor.fetchall()
        for collection in collections:
            print(f"Collection record: {collection}")
    except sqlite3.OperationalError:
        print("No 'collections' table found")

    conn.close()
except Exception as e:
    print(f"Error analyzing SQLite database: {str(e)}")

print("\n===== Diagnostic Complete =====")