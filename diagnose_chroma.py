
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

print("\n===== Testing ChromaDB Access =====")

# Try different client configurations
client_configs = [
    {
        "name": "Default configuration",
        "client": chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    },
    {
        "name": "App configuration",
        "client": chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=chromadb.Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                persist_directory=CHROMA_PERSIST_DIR
            )
        )
    },
    {
        "name": "CLI configuration",
        "client": chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=chromadb.Settings(
                anonymized_telemetry=False
            )
        )
    }
]

for config in client_configs:
    print(f"\nTesting {config['name']}:")
    client = config['client']
    
    try:
        collections = client.list_collections()
        print(f"  Found {len(collections)} collections: {[c.name for c in collections]}")
        
        for collection in collections:
            print(f"\n  Collection '{collection.name}':")
            try:
                # Get the collection to verify access
                coll = client.get_collection(name=collection.name)
                count = coll.count()
                print(f"    Documents count: {count}")
                
                # Try to get all data to see if there's any content
                if count == 0:
                    print("    No documents found.")
                else:
                    # Get everything with no filters
                    try:
                        all_data = coll.get()
                        print(f"    Retrieved {len(all_data['ids'])} entries")
                        
                        # Check embeddings
                        if 'embeddings' in all_data and all_data['embeddings']:
                            print(f"    Embeddings found: {len(all_data['embeddings'])} items")
                            print(f"    First embedding dimensions: {len(all_data['embeddings'][0])}")
                        else:
                            print("    No embeddings found.")
                            
                        # Check for document IDs
                        doc_ids = set()
                        if all_data['metadatas']:
                            for metadata in all_data['metadatas']:
                                if metadata and 'document_id' in metadata:
                                    doc_ids.add(metadata['document_id'])
                        
                        print(f"    Unique document IDs: {len(doc_ids)}")
                        if doc_ids:
                            print(f"    Sample document IDs: {list(doc_ids)[:3]}")
                        
                        # Try querying specifically for document_id field
                        try:
                            # Pick a sample document_id if available
                            sample_id = list(doc_ids)[0] if doc_ids else None
                            if sample_id:
                                doc_filter = {"document_id": sample_id}
                                filtered_results = coll.get(where=doc_filter)
                                print(f"    Query for document_id '{sample_id}' returned {len(filtered_results['ids'])} chunks")
                        except Exception as e:
                            print(f"    Error querying by document_id: {str(e)}")
                            
                    except Exception as e:
                        print(f"    Error retrieving all data: {str(e)}")
            except Exception as e:
                print(f"    Error accessing collection: {str(e)}")
    except Exception as e:
        print(f"  Error listing collections: {str(e)}")

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
